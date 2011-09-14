# -*- coding: utf-8 -*-

from django.db import  connection
import datetime

def custom_sql(sql, action=True):
    '''
    执行sql语言
    '''
    cursor = connection.cursor()
    cursor.execute(sql)
#    if action:
#        connection._commit()
    return cursor

def get_holiday(start_date,end_date):
    '''
    功能: 获取在某期间的节假日
    返回:  ((id, datetime.date(2011, 6, 1), datetime.date(2012, 10, 1), 22),)
    '''
    sql = '''
select HolidayID,StartTime,Duration from holidays
order by StartTime
    '''
    cursor = custom_sql(sql)
    rows = cursor.fetchall()
    result = []
    for e in rows:
        StartTime = datetime.datetime(e[1].year,e[1].month,e[1].day,0,0,0)
        EndTime = datetime.datetime(e[1].year,e[1].month,e[1].day,23,59,59) + datetime.timedelta(days=e[2]-1)
        result.append((e[0],StartTime,EndTime))
    return result

def get_askleave(emp,start_date,end_date):
    '''
    功能: 获取人员在某期间的审核通过的请假
    返回:  ((id, datetime.date(2011, 6, 1), datetime.date(2012, 10, 1), 22),)
    '''
    sql = '''
select id,StartSpecDay,EndSpecDay from user_speday 
where State=2 and UserID=14 and (EndSpecDay>'2011-06-01 00:00:00' and StartSpecDay<'2011-07-01 23:59:59')
order by StartSpecDay
    '''
    cursor = custom_sql(sql)
    return cursor.fetchall()

def get_setleave(emp,start_date,end_date):
    '''
    功能: 获取人员在某期间的调休里的休息类型
    返回:  ((id, datetime.date(2011, 6, 1), datetime.date(2012, 10, 1), 22),)
    '''
    sql = '''
select id,starttime,endtime from setuseratt
where UserID_id = 14 and atttype=2 and (endtime>'2011-06-01 00:00:00' and starttime<'2011-07-01 23:59:59')
order by starttime
    '''
    cursor = custom_sql(sql)
    return cursor.fetchall()


def calc_leave(att_records_origin,att_records,leave_periods,type):       
    for p in leave_periods: ###### 循环所有假休时段
        pass
        start_time = p[1]
        end_time = p[2]
        pid = p[0]
        pre_att_rec = None
        pop_list = []
        for r in att_records:
            if r[2]<=start_time:
                pop_list.append(r)
                pre_att_rec = r
                continue
            else:
                if r[2]<end_time:
                    pop_list.append(r)
                    if r[5]==1:
                        val = end_time - r[2] 
                        '''type: ask, set, hol (6, 7, 8) '''
                        att_records_origin[r[-1]][type] = '%s:%s'%(pid,val.seconds)
                    if r[5]==2:
                        if not pre_att_rec:
                            ''' 第一次 签退 '''
                            val = r[2] - start_time
                            '''type: ask, set, hol (6, 7, 8) '''
                            att_records_origin[r[-1]][type] = '%s:%s'%(pid,val.seconds)
                        else:
                            ''' 非第一次 签退'''
                            val = r[2] - start_time
                            p_len = r[2] - pre_att_rec[2]
                            if val >= p_len:
                                att_records_origin[pre_att_rec[-1]][type] = '%s:%s'%(pid,p_len.seconds)
                                val = p_len
                            '''type: ask, set, hol (6, 7, 8) '''
                            att_records_origin[r[-1]][type] = '%s:%s'%(pid,val.seconds)
                else:
                    break
                pre_att_rec = r
        for e in pop_list:
            att_records.remove(e)

def deal_att_leave(emp=14,start_date=None,end_date=None,):
    '''
    功能: 计算出人员某期间的考勤记录列表(包含假休信息)
    返回: ((empID, SchclassID, set_time, att_time, att_ID, type, ask, set, hol),...............) 按 set_time 先后顺序排列
    '''
    start_date = datetime.datetime(2011,6,1,0,0,0)
    end_date = datetime.datetime(2011,7,1,23,59,59)
    
    askleave = get_askleave(emp,start_date,end_date)
    setleave = get_setleave(emp,start_date,end_date)
    holiday = get_holiday(start_date,end_date)
    from take_card import take_card
    initial_att_records = take_card(emp,start_date,end_date)
    
    att_records_origin = []
    for e in  initial_att_records:
        data = e[:]
        data.append('0:0')
        data.append('0:0')
        data.append('0:0')
        att_records_origin.append(data)
               
    att_records = []
    count = 0
    for e in  att_records_origin:
        data = e[:]
        data.append(count)
        att_records.append(data)
        count +=1
        
    del initial_att_records
    calc_leave(att_records_origin,att_records[:],askleave,7)
    calc_leave(att_records_origin,att_records[:],setleave,8)
    calc_leave(att_records_origin,att_records[:],holiday,9)
    
    for e in att_records_origin:
        print e   

            