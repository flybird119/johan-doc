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

def get_emp_run(emp,start_date,end_date):
    '''
    功能: 获取人员在某期间的排班
    返回:  ((14, datetime.date(2011, 6, 1), datetime.date(2012, 10, 1), 22),)
    '''
    sql = '''
select UserID,StartDate,EndDate,NUM_OF_RUN_ID
from user_of_run 
where UserID=14 and (enddate>'2011-06-01 00:00:00' and startdate<'2011-07-01 23:59:59') 
order by user_of_run.StartDate 
    '''
    cursor = custom_sql(sql)
    return cursor.fetchall()

def get_run_detail(num_run_ID):
    '''
    功能: 获取某个班次的班次详细
    返回：
            ((datetime.time(7, 0), datetime.time(15, 0), 0, 15), 
            (datetime.time(23, 0), datetime.time(7, 0), 0, 17), 
            (datetime.time(19, 0), datetime.time(7, 0), 1, 14),
            (datetime.time(19, 0), datetime.time(7, 0), 2, 14),  ...
    '''
#    sql = '''
#select StartTime,EndTime,Sdays,SchclassID 
#from num_run_deil 
#where num_runid = 22
#order by Sdays,StartTime
#    '''
    sql = '''
select d.StartTime,d.EndTime,d.Sdays,d.SchclassID,s.CheckInTime1, s.CheckInTime2,s.CheckOutTime1,s.CheckOutTime2
from num_run_deil as d,schclass as s
where num_runid = 22 and d.SchclassID = s.SchclassID
order by d.Sdays,d.StartTime
    '''
    cursor = custom_sql(sql)
    return cursor.fetchall()

def deal_cross_day(begin,end,e):
    '''
    处理跨天
    '''
    d4 = datetime.datetime(begin.year,begin.month,begin.day,e[4].hour,e[4].minute,e[4].second)    
    if e[4]>e[0]:
        CheckInTime1 = d4+datetime.timedelta(days=-1)
    else:
        CheckInTime1 = d4
    d5 = datetime.datetime(begin.year,begin.month,begin.day,e[5].hour,e[5].minute,e[5].second) 
    if e[5]< e[0]:
        CheckInTime2 = d5+datetime.timedelta(days=1)
    else:
        CheckInTime2 = d5
    
    
    d6 = datetime.datetime(end.year,end.month,end.day,e[6].hour,e[6].minute,e[6].second)    
    if e[6]>e[1]:
        CheckOutTime1 = d6+datetime.timedelta(days=-1)
    else:
        CheckOutTime1 = d6
    d7 = datetime.datetime(end.year,end.month,end.day,e[7].hour,e[7].minute,e[7].second)
    if e[7]< e[1]:
        CheckOutTime2 = d7+datetime.timedelta(days=1)
    else:
        CheckOutTime2 = d7
    return CheckInTime1,CheckInTime2,CheckOutTime1,CheckOutTime2

def get_emp_run_time(emp=None,start_date=None,end_date=None):
    '''
    功能: 获取人员某期间的班次时段列表
    返回: ((begin,    end,    SchclassID,    CheckInTime1,    CheckInTime2,    CheckOutTime1,    CheckOutTime2),)
    '''
#    start_date = datetime.datetime(2011,6,1,0,0,0)
#    end_date = datetime.datetime(2011,7,1,23,59,59)
    emp_run = get_emp_run(emp,start_date,end_date)
    run_time = []
    for e in emp_run:######### 循环该期间的所有排班
        run_detail = get_run_detail(e[3])
        d1 = datetime.datetime(e[1].year,e[1].month,e[1].day,0,0,0) 
        d2 = datetime.datetime(e[2].year,e[2].month,e[2].day,23,59,59) 
        day_current = d1
        while day_current<=d2:
            if day_current< start_date or day_current>end_date:
                day_current = day_current + datetime.timedelta(days=1) 
                continue
            else:
                nday = day_current.day -1
                day_current_sch = [e for e in run_detail if e[2]==nday]
                for e in day_current_sch:
                    begin = datetime.datetime(day_current.year,day_current.month,day_current.day,e[0].hour,e[0].minute,e[0].second)
                    end = datetime.datetime(day_current.year,day_current.month,day_current.day,e[1].hour,e[1].minute,e[1].second)
                    if e[0]>e[1]:
                        end = end+datetime.timedelta(days=1)
                        
                    result = deal_cross_day(begin,end,e)
                    
                    run_time.append((begin,end,e[3],result[0],result[1],result[2],result[3],-1))
#                    run_time.append((begin,end,e[3],CheckInTime1,CheckInTime2,CheckOutTime1,CheckOutTime2))
 
                day_current = day_current + datetime.timedelta(days=1)
    return run_time
    for e in run_time:
        print e