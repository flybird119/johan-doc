# -*- coding: utf-8 -*-


def trigger_event(msg):
    try:
        q = queqe_server()
        id = q.incr("RTE_COUNT")
        l = q.llen(REALTIME_EVENT)
        if l >= MAX_TRANS_IN_QUEQE: #队列太长，删除部分
            aa = int(MAX_TRANS_IN_QUEQE / 2)
            dellen = aa
            while l - dellen >= MAX_TRANS_IN_QUEQE:
                dellen += aa
            
            q.ltrim(REALTIME_EVENT, 0, l - dellen - 1)  
            
            #print "%s in queqe, and will remove %s, then %s" % (l, dellen, q.llen(REALTIME_EVENT))
        #print "msg:%s"%msg
        q.lpush(REALTIME_EVENT, msg.encode("gb18030")) #写入到实时事件队列中
    except:
        print_exc()