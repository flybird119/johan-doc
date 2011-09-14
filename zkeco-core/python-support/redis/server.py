# -*- coding: utf-8 -*-
'''
定义了redis 服务器类
'''

import os, time
import redis
from subprocess import Popen

def start_q_server():
    f=file("redis.log","a+")
    exe_name=os.path.split(__file__)[0]+"/redis-server"
    if not os.name=='posix': exe_name+=".exe"
    print "start", exe_name
    Popen(exe_name, stdout=f)
    time.sleep(2)

def queqe_server_path(fp):
    from filequeue import fqueue
    return fqueue(fp)

def queqe_server(q=None):
    '''
    返回队列服务对象
    '''
    from filequeue import fqueue
    return q or fqueue()
#    return q or redis.Redis(host='localhost', port=6379, db=0)    #----本身的键值服务
    """try:
        q.ping()
    except redis.exceptions.InvalidResponse:
        print "InvalidResponse while queqe_server"
    except redis.exceptions.ConnectionError: 
        print "ConnectionError while queqe_server"
    return q"""

def check_and_start_queqe_server(q=None):
    q=queqe_server(q)
    try:
        q.ping()
    except redis.exceptions.ConnectionError: 
        start_q_server()
    except redis.exceptions.InvalidResponse:
        pass
    return q
 
def test_queue(c=100):
    qname='dev'
    q_server=queqe_server()
    q_server.delete(qname)
    fmt="element %d"
    for i in range(0, c):
       aa=fmt%i
       q_server.lpush(qname, aa)
    l=q_server.lrange(qname, 0, -1)
    print len(l)
    for i in range(0, c):
        if not l[i]==fmt%(c-i-1):
            raise Exception("l[%s] is '%s', but except '%s'"%(i, l[i], fmt%(c-i-1)))
    q_server=queqe_server()
    for i in range(0, c):
       acmd=q_server.rpop(qname)
       if not acmd==fmt%i:
            raise Exception("pop %s is '%s', but except '%s'"%(i, acmd, fmt%i))

    for i in range(0, c):
       aa=fmt%i
       q_server.rpush(qname, aa)
    l=q_server.lrange(qname, 0, -1)
    print len(l)
    for i in range(0, c):
        if not l[i]==fmt%i:
            raise Exception("l[%s] is '%s', but except '%s'"%(i, l[i], fmt%i))
    q_server=queqe_server()
    for i in range(0, c):
       acmd=q_server.lpop(qname)
       if not acmd==fmt%i:
            raise Exception("pop %s is '%s', but except '%s'"%(i, acmd, fmt%i))
 
    q_server.delete(qname)
    q_server.set(qname, "1212")
    if not q_server.get(qname)=="1212":
        raise Exception("get/set error")
