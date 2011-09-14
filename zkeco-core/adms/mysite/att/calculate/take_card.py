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

        
def get_initial_record(emp,start_date=None,end_date=None):
    '''
    功能: 获取人员某期间的原始签卡记录
    返回: ((id, userid, checktime, checktype,counter),)
    '''
    sql = '''
    select id,userid, checktime, checktype, 0 as counter 
    from checkinout 
    where userid=14 and checktime>='2011-06-01 00:00:00' and checktime<='2011-07-01 23:59:59' 
    order by checktime
    '''
    cursor = custom_sql(sql)
    return cursor.fetchall()

def get_att_record(initial_record_origin,initial_record,start_date=None,end_date=None):
    '''
    功能: 从签卡记录集合中取出某个考勤区的签卡记录
    返回: [index1, index2, index3,...]
    '''
    att_record = []
    pop_list = []
    len_ = len(initial_record)
#    print 'lennnnnnnnnnnnnnnnnnnnn',len_
    for r in initial_record:
        e = initial_record_origin[r[-1]]
        if e[2]<start_date:
            pop_list.append(r)
            continue
        else:
            if e[2]<=end_date:
                att_record.append(r[-1])
                e[4] +=1
            else:
                break
    for e in pop_list:
        initial_record.remove(e)
    return att_record

def get_run_att(initial_record_origin,run_att_record,set_time,type):
    '''
    功能: 从考勤区间的签卡集合中取出考勤记录(即取卡)    type　０:上下班　1:上班　2:下班
    '''
    type=0
    pre = None
    if type==0:
        ''' 上下班 '''
        len_ = len(run_att_record)
        for i in range(len_):
            data = initial_record_origin[run_att_record[i]]
            if data[4]==-1:
                '''此签卡被上一个区间取了'''
#                done = initial_record.pop(run_att_record[i])
                continue
            if data[4]==1:
                ''' 区间正常签卡'''
#                data = initial_record.pop(run_att_record[i])
                pre = data
            else:
                '多区间公用签卡'
                if data[4]>10:
                    '''此公共签卡未被被上一个区间取'''
#                        done = initial_record.pop(run_att_record[i])
                    pass
                else:
                    '''此公共签卡第一次处理'''
                    pass
                if pre:
                    initial_record_origin[run_att_record[i]][4] += 10
                else:
                    pre = data
                    initial_record_origin[run_att_record[i]][4] = -1
    if pre:
        return pre[0],pre[2]
    else:
        return None,None

def get_run_att_flex(initial_record_origin,run_att_record,in_time,out_time):
    '''
    功能: 弹性时段取卡
    '''
    pre = None
    in_list = []
    out_list = []
    len_ = len(run_att_record)
    for i  in range(len_):
        e = run_att_record[i]
        data = initial_record_origin[e]
        if data[4]==-1:
            '''此签卡被上一个区间或上一次取了'''
            continue
        if data[4]>=2:
            ''' 区间正常签卡(包括多区间共用卡)'''
            result = (data[0],data[2])
            initial_record_origin[e][4] = -1
            if pre==1:
                if i !=len_-1:
                    initial_record_origin[e][4] = -1
                    in_list.append(result)
                    pre = 2
            elif pre==2:
                initial_record_origin[e][4] = -1
                out_list.append(result)
                pre = 1
            else:
                '''首次'''
                if i !=len_-1:
                    initial_record_origin[e][4] = -1
                    in_list.append(result)
                    pre = 2
        else:
            ''' 不合理的签卡 '''
            pass
    ret = []
    count = min((len(in_list),len(out_list)))
    for i in range(count):
        ret.append((in_list[i],out_list[i])) 
    return ret


def take_card(emp=14,start_date=None,end_date=None):
    '''
    功能: 计算出人员某期间的考勤记录列表
    返回: ((empID, SchclassID, set_time, att_time, att_ID, type),...............) 按 set_time 先后顺序排列
    '''
    start_date = datetime.datetime(2011,6,1,0,0,0)
    end_date = datetime.datetime(2011,7,1,23,59,59)
#    from schedul_calculate import get_emp_run_time
#    run_time = get_emp_run_time(emp,start_date,end_date)
    from deal_temp import get_run_time,get_temp_flex_id
    run_time = get_run_time(emp,start_date,end_date)
    temp_flex_id = get_temp_flex_id(emp,start_date,end_date)
    initial_record_origin = get_initial_record(emp,run_time[0][3],run_time[-1][6])
    initial_record_origin = [list(e) for e in initial_record_origin]
    initial_record = []
    count = 0
    for e in  initial_record_origin:
        data = e[:]
        data.append(count)
        initial_record.append(data)
        count +=1
 
    att_result = []
    len_ = len(run_time)
    att_record_in_next = []
    att_record_out_next = []
    for i in range(len_):########### 循环所有时段
        e = run_time[i]
        if i==0:
            att_record_in = get_att_record(initial_record_origin,initial_record,e[3],e[4])
            att_record_out = get_att_record(initial_record_origin,initial_record,e[5],e[6])
        else:
            att_record_in = att_record_in_next
            att_record_out = att_record_out_next
        if i<len_-1:
            e_next = run_time[i+1]
            att_record_in_next = get_att_record(initial_record_origin,initial_record,e_next[3],e_next[4])
            att_record_out_next = get_att_record(initial_record_origin,initial_record,e_next[5],e_next[6])

        if e[2]==1 or e[2] in temp_flex_id:
            ''' 弹性时段 '''
            att_record_flex = att_record_in + att_record_out
            att_record_flex.sort()
            flex_result = get_run_att_flex(initial_record_origin,att_record_flex,e[0],e[1])
            for ret in flex_result:
                att_result.append([emp,e[2],e[0],ret[0][1],ret[0][0],1,e[-1]])
                att_result.append([emp,e[2],e[1],ret[1][1],ret[1][0],2,e[-1]])
        else:
            run_att__in = get_run_att(initial_record_origin,att_record_in,e[0],'in')
            run_att__out = get_run_att(initial_record_origin,att_record_out,e[1],'out')
            att_result.append([emp,e[2],e[0],run_att__in[1],run_att__in[0],1,e[-1]])
            att_result.append([emp,e[2],e[1],run_att__out[1],run_att__out[0],2,e[-1]])
    return att_result
    for e in att_result:
        print e 