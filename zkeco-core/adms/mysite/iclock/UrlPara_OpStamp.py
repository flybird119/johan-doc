# coding=utf-8
from django.db import connections, IntegrityError
conn = connections['default']

def cdata_post_userinfo(device, raw_data,Op, head=None):
    '''
    与用户有关的命令解析
    oplog_stamp 时间戳时
    '''
    from conv_emp import line_to_emp
    import time
    cursor = conn.cursor()
    c = 0;
    ec = 0;
    user = False
    for line in raw_data.splitlines():  #--- 原始数据分行解析
        try:
            if line:
                user = line_to_emp(cursor, device, line,Op)
                c = c + 1
        except Exception, e:
            import traceback;traceback.print_exc()
            ec = ec + 1
            appendFile("ERROR(cdata=%s):%s" % (line, e))
            if isinstance(e, DatabaseError):
                conn.close()
                cursor = conn.cursor()
        time.sleep(0.1)
    conn._commit()
    dlogObj = "TMP"
    try:
        dlogObj = u"%s" % user
    except: pass
    return (c, ec, dlogObj)
