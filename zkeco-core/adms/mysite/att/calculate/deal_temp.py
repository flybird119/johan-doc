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

def get_temp_flex_id(emp=None,start_date=None,end_date=None):
    sql = '''
select t.id
from user_temp_sch as t,schclass as s
where t.UserID=14 and t.SchClassID = s.SchclassID and (t.LeaveTime>'2011-06-01 00:00:00' and t.ComeTime<'2011-07-01 23:59:59') and t.SchClassID=1 
order by t.ComeTime 
    '''
    cursor = custom_sql(sql)
    rows = cursor.fetchall()
    id_list = [e[0] for e in rows]
    return id_list

def get_emp_run_time_temp(emp=None,start_date=None,end_date=None):
    sql = '''
select t.ComeTime,t.LeaveTime,t.Flag,t.id,s.CheckInTime1, s.CheckInTime2,s.CheckOutTime1,s.CheckOutTime2
from user_temp_sch as t,schclass as s
where t.UserID=14 and t.SchClassID = s.SchclassID and (t.LeaveTime>'2011-06-01 00:00:00' and t.ComeTime<'2011-07-01 23:59:59') 
order by t.ComeTime 
    '''
    cursor = custom_sql(sql)
    rows = cursor.fetchall()
    run_time_temp = []  
    for e in rows:
        begin = [e[0]][0]
        end = [e[1]][0]
        e_ = list(e)
        e_[0] = e_[0].time()
        e_[1] = e_[1].time()
        from schedul_calculate import deal_cross_day
        result = deal_cross_day(begin,end,e_)
        run_time_temp.append((begin,end,e[3],result[0],result[1],result[2],result[3],e[2]))
    return run_time_temp

def get_run_time(emp=None,start_date=None,end_date=None):
    from schedul_calculate import get_emp_run_time
    run_time = get_emp_run_time(emp,start_date,end_date)
    run_time_temp = get_emp_run_time_temp(emp,start_date,end_date)
    run_time_all = run_time + run_time_temp
    run_time_all.sort(cmp=lambda x,y:cmp(x[0],y[0]))
    run_time_all_for = run_time_all[:]
    pop_list = []
    pre = None
    for e in run_time_all:
        if not pre:
            pre = e
        else:
            ''' 非第一次 '''
            if e[0]>pre[1]:
                ''' 无交集 '''
                pre = e
            else:
                ''' 有交集 '''
                if pre[-1]==-1:
                    ''' 上一个为正常时段 '''
                    if e[-1]==-1:
                        pop_list.append(e[:])
                    elif e[-1]==1:
                        pop_list.append(pre[:])
                        pre = e
                    elif e[-1]==2:
                        pop_list.append(e[:])
                else:
                    ''' 上一个为临时时段 '''
                    if pre[-1]==1:
                        ''' 三种情况均pop '''
                        pop_list.append(e[:])
                    elif pre[-1]==2:
                        if e[-1]==-1:
                            pop_list.append(pre[:])
                            pre = e
                        else:
                            pop_list.append(e[:])
    
    for p in  pop_list:
        run_time_all.remove(p)
    return run_time_all