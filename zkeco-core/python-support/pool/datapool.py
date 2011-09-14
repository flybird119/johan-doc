# -*- coding: utf-8 -*-
from django.conf import settings
if settings.DATABASE_ENGINE=='pool':
    settings.DATABASE_ENGINE=settings.POOL_DATABASE_ENGINE

import time
import pickle
import threading
import traceback
from django.db import backend, connection
from django.core.cache import cache
from Queue import Queue
import redis
from redis.server import queqe_server, start_q_server
import sys
from django.core.cache.backends.filebased import CacheClass

def runsql(count=10):
    from mysite.utils import test_and_open_tcp_port
    q=queqe_server()    #---redis 键值服务器队列
    
    test_and_open_tcp_port(settings.SQL_POOL_PORT) #打开TCP端口，让别的程序知道自己已经启动

    if settings.DATABASE_ENGINE=="sqlite3": #避免sqlite3的文件互锁
        count=1
    wt=[]
    for i in range(count):
        t=PoolConn(i)
        wt.append(t)
        t.start()
        time.sleep(0.2)
        
    report_time=time.time()+60 #1分钟, 报告一次查询数量
    end_time=time.time()+60*60*2 #2*60分钟，退出进程，系统会重新启动该进程————解决python占用内存越来越大的问题    
    while True: #监控线程，如果其结束，重新创建
        try:
            ret=q.rpop("sql_execute")
            if ret is None:                     #队列中没有sql语句
                now_time=time.time()
                if now_time>report_time:
                    print "total %s queries" % sum([wt[i].i for i in range(count)])
                    report_time=now_time+60 #1分钟
                    if now_time>end_time: #退出进程
                        print "Exit process"
                        break
                time.sleep(0.02)
                continue
        except redis.exceptions.ConnectionError: #读队列错，可能是队列服务器没有开
            #start_q_server()
            continue
        except:
            time.sleep(0.2)
            continue

        try:
            ret=pickle.loads(ret)
            cid, sql, param=ret
        except Exception, e:
            traceback.print_exc()
            data=(3, u"%s"%e)
            sret=-1
            continue

        #发送给处理过相同cid的线程处理
        pt=None
        for i in range(count):
            t=wt[i]
            if not t.isAlive(): 
                wt[i]=None
                del t
                t=PoolConn(i)
                wt[i]=t
                t.start()
            if t.append_sql_by_id(ret): 
                pt=t
                break;
        #新的cid的话随机发送给某个线程
        if pt is None:
            i=int(cid)/8%count
            pt=wt[i]
            if not pt.isAlive():
                wt[i]=None
                del pt
                pt=PoolConn(i)
                wt[i]=pt
                pt.start()
            pt.append_sql(ret)
    q.connection.disconnect()
    #通知各个线程停止工作        
    for i in range(count):
        wt[i].stop_run()
    wait_msec=5000 #最长等待时间（毫秒）
    for i in range(count):
        pt=wt[i]
        if pt.isAlive():
            time.sleep(0.2)
            wait_msec-=200
            if wait_msec<=0: #超时，直接退出
                break
    if wait_msec<=0: #是因为超时而退出的，强行终止
        import os
        os.abort()


class PoolConn(threading.Thread):   #---数据库连接池线程
    '''
    数据库连接池
    '''
    def __init__(self, index):
        super(PoolConn, self).__init__()
        self.connection = backend.DatabaseWrapper(**settings.DATABASE_OPTIONS)  #----数据库连接对象
        self.q=Queue()  #---------？？？？？？？？？？？？
        self.cursor_ids=[]
        self.i=0
        self.index=index
        self.stop=False
    def append_sql(self, query):
        '''
        向池添加待执行的sql
        '''
        self.q.put(query)
        try:
            self.cursor_ids.append(query[0])
            if len(self.cursor_ids)>1000:
                self.cursor_ids=self.cursor_ids[:800]
        except:
            pass
    def append_sql_by_id(self, query):
        if query[0] in self.cursor_ids:
            self.q.put(query)
            return True
        return False
    def stop_run(self):
        self.stop=True
        self.q.put((0, "_EXIT"))
    def run(self):
        '''
        运行池中的任务
        '''
        from django.db import IntegrityError, DatabaseError
        conn=self.connection
        cursor=conn.cursor()
        q=queqe_server()
        print "Start Pool Connection %s"%self.index
        while not self.stop:
            ret=self.q.get()
            if ret:
                sql=ret[1]
                if sql=="_EXIT":
                    break
                if sql=="CLOSE":
                    self.cursor_ids.remove(ret[0])
                    continue
                print sql
                self.i+=1
                data=None
                try:
                    sret=cursor.execute(sql, ret[2])
                except IntegrityError, e:
                    data=(0, u"%s"%e)
                    sret=-1
                except DatabaseError, e:
                    traceback.print_exc()
                    conn.close()
                    cursor=conn.cursor()
                    try:
                        sret=cursor.execute(u"%s"%ret[1], ret[2])
                    except Exception, e:
                        traceback.print_exc()
                        data=(1, u"%s"%e)
                        sret=-1
                except Exception, e:
                    traceback.print_exc()
                    data=(2, u"%s"%e)
                    sret=-1                
                if data is None:
                    try:
                        LOB=sys.modules[connection.__module__].Database.LOB
                    except:
                        LOB=None
                    data=[]
                    try:
                        while True:
                            try:
                                arow=cursor.fetchone()
                            except:
                                break
                            if arow is None: break;
                            if LOB:
                                data.append(tuple([isinstance(value, LOB) and (value.read()) or value for value in arow]))
                            else:
                                data.append(arow)
                    except:
                        traceback.print_exc()
                        pass
                if not type(sret)==type(1):
                    sret=cursor.rowcount
                    if sret==-1:
                        sret=len(data)
                print "\tret:", sret
                try:
                    rowid=cursor.lastrowid
                except: 
                    rowid=0
                n="sql_execute_%s"%ret[0]
                try:
                    data=pickle.dumps((sret, tuple(data), rowid))
                except:
                    data=pickle.dumps((-1, (2, u"%s"%e), 0))
                q.set(n, data)
                q.expire(n, 600)
                """
                try:
                    cache.set(n, (sret, tuple(data), rowid), 600)
                except Exception, e:
                    traceback.print_exc()
                    cache.set(n, (-1, (2, u"%s"%e), 0), 600)
                if not cache.has_key(n):
                    CacheClass(settings.ADDITION_FILE_ROOT, {"max_entries":1024}).set(n, (sret, tuple(data), rowid), 600)
                    cache.set(n, (-1000, 0, 0), 600)
                """
                try:
                    conn._commit()
                except:
                    pass
                print "\t",n
        try:        
            cursor.close()
            conn.close()
        except: pass
        q.connection.disconnect()
        print "End Pool Connection %s, sql=%s"%(self.index, self.i)

