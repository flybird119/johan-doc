# coding=utf-8

def save_attRecAbnormite(u,acttime,currentday):
    ############################# 写入统计结果详情表 ##########################
    if acttime['actcheckin'] and acttime['actcheckin']>datetime.datetime(1900,1,1,0,0,0):
       attrecord = attRecAbnormite()        #---写入统计结果详情表 签入和签出
       attrecord.UserID_id = u
       attrecord.checktime = acttime['actcheckin']  #---签卡时间
       attrecord.CheckType = acttime['istate']        #----考勤状态类型
       attrecord.NewType = 'I'      #---更正状态
       attrecord.AbNormiteID=0      #----？？？
       attrecord.SchID=0    #---时段
       attrecord.OP=0   #---操作
       attrecord.AttDate=currentday     #---日期'
       attrecord.save() #--------------------------------保存统计结果详情表
    if acttime['actcheckout'] and acttime['actcheckout']>datetime.datetime(1900,1,1,0,0,0):
       attrecord = attRecAbnormite()        
       attrecord.UserID_id = u
       attrecord.checktime = acttime['actcheckout']
       attrecord.CheckType = acttime['ostate']
       attrecord.NewType = 'O' 
       attrecord.AbNormiteID=0
       attrecord.SchID=0
       attrecord.OP=0
       attrecord.AttDate=currentday
       attrecord.save()             