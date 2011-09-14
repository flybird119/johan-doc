# -*- coding: utf-8 -*-
'''
实现了文件队列服务
'''
import time
import glob
from os.path import exists
from os.path import split
from os import makedirs, remove
from shutil import rmtree
from redis.filelock import *

class Connection(object):
    def connect(self, instance):
        pass
    
    def disconnect(self):
        pass

class fqueue(object):
    """
    Implementation of the simple queue like Redis with file system.
    实现缓存文件队列
    key为文件名 
    value为文件内容
    """
    def __init__(self, path=""):
        if path:
            fqpath=path
        else:
            from django.conf import settings
            fqpath="%s/_fqueue/"%settings.APP_HOME
        self.lock_dic={}
        self.db=fqpath  #----self.db 定义文件队列根目录
        try:
            makedirs(fqpath)
        except: pass
        self.connection=Connection()
        
    def has_key(self, name):
        return exists("%s%s"%(self.db, name))   #----实质是文件是否存在
    
    def formatpath(self, spath):
        '''
        格式化路径字符串
        '''
        return spath.replace("\\", "/") 
        
    def set(self, key, value, timeout=0):
        '''
        设置键和值
        '''
        fn="%s%s"%(self.db, key)
        try:
            f=file(fn, "w+")
        except IOError: #---子目录的支持
            makedirs(split(fn)[0])
            f=file(fn, "w+")
        f.write(value)
        f.close()
        
    def get(self, key):
        '''
        得到键的值 值为'' 则返回None
        '''
        fn="%s%s"%(self.db, key)
        try:
            f=file(fn, "r")
            ret=f.read()
            f.close()
            if ret.strip()=="":
                return None
            return ret.strip()
        except:
            return None
        
    def delete(self, key):
        '''
        删除键 文件或者目录
        '''
        fn="%s%s"%(self.db, key)
        try:
            remove(fn)
        except:
            try:
                rmtree(fn)
            except:
                pass

    def deletemore(self, key):  #带*号删除
        '''
        删除带“*”匹配的键 文件或者目录
        '''
        fn="%s%s"%(self.db, key)
        filelist=glob.glob(fn)
        for flist in filelist:
            try:
                remove(flist)
            except:
                try:
                    rmtree(flist)
                except:
                    pass           
        
    def lock(self, name=""):
        '''
        加锁 添加一个名称为name的锁对象
        '''
        try:
            b=self.lock_dic["_lock_%s"%name]
        except:
            self.lock_dic["_lock_%s"%name]=0    #---不循环
        timeout=0
        while True:
            if not self.lock_dic["_lock_%s"%name]: break;
            timeout += 1
            if timeout > 100*30: break;   #30秒(3000次)超时退出
            time.sleep(0.01) #---每次0.01秒
        self.lock_dic["_lock_%s"%name]=1

    def unlock(self,name):
        '''
        解锁  实质是打开退出循环的一个flag
        '''
        self.lock_dic["_lock_%s"%name]=0

    def file_lock(self, name, property):
        '''
        锁定文件 name/property
        '''
        filepath=self.formatpath("%s%s"%(self.db, name))
        if not os.path.exists(filepath):
            os.mkdir(filepath)
        filename="%s/%s"%(filepath, property)   #--- 文件name/property
        bfile=File(filename)
        while True:
            try:
                bfile.obtain_lock()
                break;
            except:
                pass
            time.sleep(0.01)
        return bfile
        
    def file_unlock(self, f_lock):
        '''
        解除已经加锁的文件f_lock
        '''
        #f_lock.release_lock()
        f_lock.close()

    def ping(self):
        return True 
    
    def save(self):
        return True
    
    def incr(self, name):
        '''
        递增计数器
        '''
        self.lock(name)
        value=int(self.get(name) or "0")+1
        self.set(name, str(value))
        self.unlock(name)
        return value
    
    def decr(self, name):
        '''
        递减计数器
        '''
        self.lock(name)
        value=int(self.get(name) or "0")-1
        self.set(name, str(value))
        self.unlock(name)
        return value
    
    def lindex(self, name, index):
        """
        list结构索引取值
        Return the item from list ``name`` at position ``index``
        
        Negative indexes are supported and will return an item at the
        end of the list
        """
        r=int(self.get("%s/_start"%name) or "0")
        return self.get("%s/%s"%(name, r+index))

    def llen(self, name):
        '''
        list结构元素数量
        Return the length of the list ``name``
        '''
        try:
            start=int(self.get("%s/_start"%name) or "0")    #意处断电时出现写入NULL字符
        except:
            start=0
        try:
            end=int(self.get("%s/_end"%name) or "0")
        except:
            end=0
        return end-start
    
    def lock_delete(self, name):
        '''
        先锁定再删除键
        '''
        fe = self.file_lock(name, "_end")
        self.delete(name)
        self.file_unlock(fe)
        self.delete(name)
        
    def lock_rlen(self, name):
        '''
        锁定尾求元素数量
        '''   
        fe = self.file_lock(name, "_end")
        start=int(self.get("%s/_start"%name) or "0")
        try:           
            end=int(fe.read().strip() or "-1")
        except:
            end=-1
        self.file_unlock(fe)
        return end-start

    def lpop(self, name):
        ''' 取第一个 '''
        "Remove and return the first item of the list ``name``"
        ret=None
        fl = self.file_lock(name, "_start") #---锁定文件
        try:
            start=int(fl.read() or "0")
        except:
            start=0
        try:
            end=int(self.get("%s/_end"%name) or "0")
        except:
            end=0
        if start<end:
            ret=self.get("%s/%s"%(name, start))
            self.delete("%s/%s"%(name, start))
            fl.write(str(start+1))
        self.file_unlock(fl)
        return ret
    
    def lpush(self, name, value):
        ''' 加入到头部 '''
        "Push ``value`` onto the head of the list ``name``"
        fl = self.file_lock(name, "_start") #---记录开始位置的锁文件
        try:
            start=int(fl.read() or "0")
        except:
            start=0
        try:
            end=int(self.get("%s/_end"%name) or "0")    #---记录结束位置的文件
        except:
            end=0
        self.set("%s/%s"%(name, start-1), value)    #---加入 name/start-1 文件键
        fl.write(str(start-1))  #---更新开始位置记录
        self.file_unlock(fl)    #---解除锁
        return True

    def lrange(self, name, start, end):
        """
        相当于切片操作 但不删除
        Return a slice of the list ``name`` between position ``start`` and ``end``
        ``start`` and ``end`` can be negative numbers just like
        Python slicing notation
        """
        fs = self.file_lock(name, "_start")
        fe = self.file_lock(name, "_end")
        try:
            _start=int(fs.read() or "0")
        except:
            _start=0
        try:
            _end=int(fe.read() or "0")
        except:
            _end=-1
        
        if not (end==-1):
            r=range(_start, _end)[start:end+1]
        else:
            r=range(_start, _end)[start:]
        ret= [self.get("%s/%s"%(name, i)) for i in r]
        self.file_unlock(fe)
        self.file_unlock(fs)
        return ret

    def rpop(self, name):
        ''' 取最后一个 '''
        "Remove and return the last item of the list ``name``"
        ret=None
        fe = self.file_lock(name, "_end")
        try:
            start=int(self.get("%s/_start"%name) or "0")
        except:
            start=0
        try:
            end=int(fe.read() or "0")
        except:
            end=0
        if start<end:
            end-=1
            ret=self.get("%s/%s"%(name, end))
            self.delete("%s/%s"%(name, end))
            fe.write(str(end))
        self.file_unlock(fe)
        return ret
    
    def getrpop(self, name):
        ''' 取出但不删除 防掉电，命令执行完再rpop删除 '''
        "return the last item of the list ``name``"
        ret=None
        err=0
        fe = self.file_lock(name, "_end")
        try:
            start=int(self.get("%s/_start"%name) or "0")
        except:
            start=0
            err=1
        try:
            end=int(fe.read() or "0")
        except:
            end=0
            err=1
        if err>0:
            ret="QUEUE_ERROR"
        elif start<end:
            end-=1
            ret=self.get("%s/%s"%(name, end))
        self.file_unlock(fe)
        return ret
        
    def rpush(self, name, value):
        ''' 加入到尾部 '''
        "Push ``value`` onto the tail of the list ``name``"
        fe = self.file_lock(name, "_end")   #----尾部锁
        try:
            start=int(self.get("%s/_start"%name) or "0")    #----name/_start
        except:
            start=0
        try:
            end=int(fe.read() or "0")
        except:
            end=0
        ret=self.set("%s/%s"%(name, end), value)
        fe.write(str(end+1))
        self.file_unlock(fe)
        return True

    def ltrim(self, name, start, length):
        ''' 相当于切片操作 '''
        "Push ``value`` onto the tail of the list ``name``"
        fs = self.file_lock(name, "_start")
        fe = self.file_lock(name, "_end")
        try:
            end=int(fe.read() or "0")
        except:
            end=0
        for i in range(0, start, 1):
            self.delete("%s/%s"%(name, i))
        for i in range(start + length, end, 1):
            self.delete("%s/%s"%(name, i))
        fe.write(str(start+length))
        fs.write(str(start))
        self.file_unlock(fe)
        return True
        