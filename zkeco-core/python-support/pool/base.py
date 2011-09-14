# -*- coding: utf-8 -*-
"""
pool backend for django.
"""
from django.conf import settings
import sys, time, os
from django.db.backends import *
from django.core.cache import cache
from django.core.cache.backends.filebased import CacheClass
import pickle
from redis.server import queqe_server, start_q_server

e_name="django.db.backends.%s.base"%settings.POOL_DATABASE_ENGINE

__import__(e_name)
e_module=sys.modules[e_name]

#class DatabaseFeatures(BaseDatabaseFeatures):
#class DatabaseOperations(BaseDatabaseOperations):
DatabaseError=e_module.DatabaseError
IntegrityError=e_module.IntegrityError
DatabaseValidation=BaseDatabaseValidation

class DatabaseFeatures(e_module.DatabaseFeatures):
    empty_fetchmany_value = ()

class RedisConnection(object):
    def __init__(self):
        self.q=queqe_server()
    def get_server_info(self):
        return "Redist database pool"
    def rollback(self):
        pass
    def commit(self):
        pass
    def close(self):
        return

class DatabaseWrapper(e_module.DatabaseWrapper):
    def __init__(self, **kwargs):

        super(DatabaseWrapper, self).__init__(**kwargs)
        self.features = DatabaseFeatures()
        self.validation = DatabaseValidation()

    def _valid_connection(self):
        return self.connection is not None
    def _cursor(self, settings):
        cursor = None
        if not self._valid_connection():
            self.connection = RedisConnection()
        cursor=PoolCursorWrapper(self.connection)
        return cursor

class PoolCursorWrapper(object):
    def __init__(self, connection):
        self.connection=connection
        self.arraysize=0
        self.rows=[]
    def wait_ret(self, q):
        my_id="sql_execute_%s"%id(self)
        print "wait ",my_id
        i=10000 #4000*0.05=500s
        while i>0:
            ret=q.get(my_id)
            #ret=cache.get(my_id)
            if ret is None: 
                i-=1
                time.sleep(0.05)
            else:
                q.delete(my_id)
                try:
                    ret=pickle.loads(ret)
                except:
                    if ret=="OK":
                        continue
                    else:
                        raise
                """cache.delete(my_id)
                if ret[0]==-1000:
                    print "try get from file"
                    try:
                        c=CacheClass(settings.ADDITION_FILE_ROOT, {})
                        ret=c.get(my_id)
                        c.delete(my_id)
                    except:
                        import traceback; traceback.print_exc()"""
                break
        q.connection.disconnect()
        if i<=0:
            raise Exception(u"Timeout: %s"%self.sql)
        if ret[0]==-1: #exception
            if ret[1][0]==0:
                raise IntegrityError(ret[1][1])
            elif ret[1][0]==1:
                raise DatabaseError(ret[1][1])
            else:
                raise Exception(u"%s: %s"%(ret[1][0], ret[1][1]))
        self.ret=ret[0]
        self.rows=ret[1]
        self.rowcount=ret[0]
        print "\treturn", self.rowcount #, ret[1]
        self.lastrowid=ret[2]
        self.index=0
        return self.ret
    def execute(self, query, params=None):
        print "SQL execute", query, params
        self.sql=query
        self.connection.q.lpush("sql_execute", pickle.dumps((id(self), query, params,)))
        return self.wait_ret(self.connection.q)
    def executemany(self, query, params=None):
        #print "SQL executemany", query, params
        self.connection.q.lpush("sql_executemany", pickle.dumps((id(self), query, params,)))
        return self.wait_ret(self.connection.q)

    def fetchone(self):
        row = len(self.rows)
        if row==0:
            return None
        try:
            return self.rows[self.index]
        except:
            return None
        finally:
            self.index+=1

    def fetchmany(self, size=None):
        if size is None:
            ret=tuple(self.rows[self.index:])
            self.index+=len(self.rows)
        else:
            if self.index>=len(self.rows):
                return ()
            ret=tuple(self.rows[self.index:self.index+size])
            self.index+=len(ret)
        return ret

    def fetchall(self):
        return tuple(self.rows)

