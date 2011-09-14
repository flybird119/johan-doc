# coding=utf-8

import datetime
from datetime_utils import todatetime,todatetime2,dtconvertint
from att_rule import LoadAttRule
AttRule = LoadAttRule()

#取每个段的刷卡时间、迟到、早退时间、提前加班时间、延迟加班时间。
def getchecktime(ef,empcheckdata,currentday,lasttime,recordstate,empsh,firststarttime,iii,lenef):
    '''
    ef                             当前时段
    empcheckdata         签卡数据
    currentday               当前日期
    lasttime                   前面最后的取卡数据 1900-01-01 00:00:00
    recordstate              ['I','O','0','1']    签卡状态
    empsh                     班次ID  3
    firststarttime            该班次第一个时段的上班时间   用于判断前跨天 后跨天的参数  09:00:00 
    iii                             该时段在该班次时段列表中的序号
    lenef                        0    时段数目-1
    '''    
    ####################取卡有效时间段初始化####################
    if ef.CheckInTime1 == None:
       ef.CheckInTime1 = todatetime2(ef.StartTime) + datetime.timedelta(minutes = -30)
    if ef.CheckInTime2 == None:
       ef.CheckInTime2 = todatetime2(ef.StartTime) + datetime.timedelta(minutes = 30) 
    if ef.CheckOutTime1 ==None:
       ef.CheckOutTime1 = todatetime2(ef.EndTime) + datetime.timedelta(minutes = -30)
    if ef.CheckOutTime2 == None:
       ef.CheckOutTime2 = todatetime2(ef.EndTime) + datetime.timedelta(minutes = 30)
    actcheckin = datetime.datetime(1900,1,1,0,0,0)
    actcheckout = datetime.datetime(1900,1,1,0,0,0)
    startrest1 = datetime.datetime(1900,1,1,0,0,0)
    endrest1 = datetime.datetime(1900,1,1,0,0,0)
    startrest2 = datetime.datetime(1900,1,1,0,0,0)
    endrest2 = datetime.datetime(1900,1,1,0,0,0) 
    rest1=0
    rest2=0   
    istate=''
    ostate=''
    ######################### 签到相关数据处理 #############################
    checkintqTime = datetime.datetime(currentday.year,currentday.month,currentday.day,# 签到起始时间
                               ef.CheckInTime1.hour,ef.CheckInTime1.minute,ef.CheckInTime1.second)
    checkinycTime = datetime.datetime(currentday.year,currentday.month,currentday.day, # 签到结束时间
                              ef.CheckInTime2.hour,ef.CheckInTime2.minute,ef.CheckInTime2.second)
    checkInTime = datetime.datetime(currentday.year,currentday.month,currentday.day,    #---上班时间
                              ef.StartTime.hour,ef.StartTime.minute,ef.StartTime.second)
    if todatetime2(firststarttime)>todatetime2(ef.StartTime):     #如果第一段的上班时间大于该段的上班时间则说明后跨天
       checkInTime = checkInTime + datetime.timedelta(days=1)
    if todatetime2(ef.CheckInTime1)>todatetime2(ef.StartTime) and todatetime2(firststarttime)==todatetime2(ef.StartTime):   #如果提前时间大于上班时间说明是前跨天
        checkintqTime= checkintqTime - datetime.timedelta(days=1)
    if todatetime2(ef.CheckInTime2)<todatetime2(ef.StartTime) or todatetime2(firststarttime)>todatetime2(ef.StartTime):   #如果延迟时间小于上班时间说明是后跨天
        checkinycTime= checkinycTime + datetime.timedelta(days=1)
    if ef.StartRestTime!=None and ef.EndRestTime!=None and ef.StartRestTime!=startrest1 and ef.EndRestTime!=endrest1:   #---段中休息时间
       if ef.StartRestTime>ef.StartTime:
          startrest1 = datetime.datetime(currentday.year,currentday.month,currentday.day,ef.StartRestTime.hour,
                                         ef.StartRestTime.minute,0)
       if ef.StartRestTime<=ef.StartTime:
          startrest1 = datetime.datetime(currentday.year,currentday.month,(currentday.day+1),ef.StartRestTime.hour,
                                         ef.StartRestTime.minute,0)
       if ef.EndRestTime>ef.StartRestTime:
          endrest1 = datetime.datetime(currentday.year,currentday.month,currentday.day,ef.EndRestTime.hour,
                                       ef.EndRestTime.minute,0)
       if ef.EndRestTime<=ef.StartRestTime:
          endrest1 = datetime.datetime(currentday.year,currentday.month,(currentday.day+1),ef.EndRestTime.hour,
                                       ef.EndRestTime.minute,0)
    if ef.StartRestTime1!=None and ef.EndRestTime1!=None and ef.EndRestTime!=None and ef.StartRestTime1!=startrest2 and ef.StartRestTime1!=endrest2: 
       if ef.StartRestTime1>ef.EndRestTime:
          startrest2 = datetime.datetime(currentday.year,currentday.month,currentday.day,ef.StartRestTime1.hour,
                                         ef.StartRestTime1.minute,0)
       if ef.StartRestTime1<=ef.EndRestTime:
          startrest2 = datetime.datetime(currentday.year,currentday.month,(currentday.day+1),ef.StartRestTime1.hour,
                                         ef.StartRestTime1.minute,0)
       if ef.EndRestTime1>ef.StartRestTime1:
          endrest2 = datetime.datetime(currentday.year,currentday.month,currentday.day,ef.EndRestTime1.hour,
                                       ef.EndRestTime1.minute,0)
       if ef.EndRestTime1<=ef.StartRestTime1:
          endrest2 = datetime.datetime(currentday.year,currentday.month,(currentday.day+1),ef.EndRestTime1.hour,
                                       ef.EndRestTime1.minute,0) 
    ######################## 签退相关数据处理 #############################
    checkouttqTime = datetime.datetime(currentday.year,currentday.month,currentday.day, # 签退起始时间
                               ef.CheckOutTime1.hour,ef.CheckOutTime1.minute,ef.CheckOutTime1.second)
    checkoutycTime = datetime.datetime(currentday.year,currentday.month,currentday.day,# 签退结束时间
                               ef.CheckOutTime2.hour,ef.CheckOutTime2.minute,ef.CheckOutTime2.second)
    CheckOutTime = datetime.datetime(currentday.year,currentday.month,currentday.day, # 签退时间
                              ef.EndTime.hour,ef.EndTime.minute,ef.EndTime.second)                            
    #if todatetime2(ef.CheckOutTime1)>todatetime2(ef.EndTime)or (ef.StartTime>ef.EndTime and todatetime2(ef.CheckOutTime1)>todatetime2(ef.EndTime)):    #如果提前时间大于下班时间说明是前跨天
    #    checkouttqTime = checkouttqTime - datetime.timedelta(days=1)
    if ef.StartTime>ef.EndTime and ef.CheckOutTime1<ef.EndTime or todatetime2(firststarttime)>todatetime2(ef.StartTime):
        checkouttqTime = checkouttqTime + datetime.timedelta(days=1)
    if todatetime2(ef.CheckOutTime2)<todatetime2(ef.EndTime) or todatetime2(firststarttime)>todatetime2(ef.StartTime) or (ef.StartTime>ef.EndTime and todatetime2(ef.CheckOutTime2)>todatetime2(ef.EndTime)):    #如果延迟时间小于下班时间说明是后跨天
        checkoutycTime = checkoutycTime + datetime.timedelta(days=1)       
    if ef.StartTime>ef.EndTime or todatetime2(firststarttime)>todatetime2(ef.StartTime):     #如果上班时间大于下班时间则说明后跨天。
       CheckOutTime = CheckOutTime + datetime.timedelta(days=1)
    ######################### 取上班卡 ########################
    intervalTime=9999    # 上个签卡时间和签到时间的绝对差值
    actcheckin =None    #----签到时间
    for itimein in empcheckdata:
       if actcheckin != None and (dtconvertint(itimein.TTime) - dtconvertint(actcheckin))<=AttRule['MinRecordInterval']:
         continue          #重复记录要过滤掉。
       if itimein.TTime<checkintqTime or itimein.TTime>checkinycTime:
         continue
       #if itimein.State!=2 and itimein.State!=3 and AttRule['OutCheckRecType']==1: #外出记录被剔除。
       if itimein.State not in recordstate and AttRule['OutCheckRecType']==1:  #外出记录被剔除。
         continue
       if itimein.TTime <=lasttime: #小于上一段的时间的卡被过滤出。
         continue
       if itimein.TTime<=currentday and empsh==1:  #弹性班次不支持跨天。
          continue
       if itimein.TTime>(currentday + datetime.timedelta(minutes=1440)) and empsh==1: #弹性班次不支持跨天。
          continue
       if AttRule['TakeCardIn'] == 2:
           i_min =(abs(dtconvertint(itimein.TTime) - dtconvertint(checkintqTime)))
       else: 
           i_min =(abs(dtconvertint(itimein.TTime) - dtconvertint(checkInTime)))       # 当前签卡时间和签到时间的绝对差值 ------------------------checkintqTime
       if empsh!=1:         
          if i_min<intervalTime:
             if AttRule['TakeCardIn'] == 2:
                 if actcheckin!= None and actcheckin !=datetime.datetime(1900,1,1,0,0,0) and itimein.TTime < checkintqTime:   #----------------<checkintqTime
                    continue
             else:
                 if actcheckin!= None and actcheckin !=datetime.datetime(1900,1,1,0,0,0) and itimein.TTime > checkInTime:   #----------------<checkintqTime
                    continue                    
             actcheckin = itimein.TTime
             intervalTime = i_min   #------------------------------
             istate = itimein.State
       else:  #弹性班次取卡
          actcheckin = itimein.TTime
          intervalTime = i_min
          istate = itimein.State 
          break 
     #########          
    if (actcheckin==None or intervalTime==9999) and ef.CheckIn==0 and empsh!=1:   #不需要签到时，需要产生一个随机的卡。
        actcheckin = checkInTime+datetime.timedelta(minutes=-int(random()*10))
    ######################### 取下班卡 ########################
    intervalTime = 9999
    actcheckout = None   #----签退时间
    for itimeout in empcheckdata:
        if actcheckin != None:
           if itimeout.TTime<=actcheckin: #下班时间必须大于上班时间
              continue
        if itimeout.TTime<checkouttqTime or itimeout.TTime>checkoutycTime:  #小于提前大于延迟的卡被过滤。
           continue    
        if actcheckout != None and (dtconvertint(itimeout.TTime) - dtconvertint(actcheckout))<=AttRule['MinRecordInterval']:
           continue           #重复记录要剔除   
        if actcheckin!= None and (dtconvertint(itimeout.TTime) - dtconvertint(actcheckin))<=AttRule['MinRecordInterval']:
           continue     #与上班卡相比，如果小于重复卡时间，也被过滤。
        #if itimeout.State!=2 and itimeout.State!=3 and AttRule['OutCheckRecType']==1: #外出记录被剔除。
        if itimeout.State not in recordstate and AttRule['OutCheckRecType']==1:   #外出记录被剔除。
           continue    
        if itimeout.TTime<=lasttime: #小于上一段的时间卡被过滤出。
           continue
        if itimeout.TTime<=currentday and empsh==1:  #弹性班次不支持跨天。
           continue
        if itimeout.TTime>(currentday + datetime.timedelta(minutes=1440)) and empsh==1: #弹性班次不支持跨天。
           continue       
        if actcheckin==None and lasttime.year ==1900 and ef.StartTime==firststarttime and iii==0 and lenef>0 and (abs(dtconvertint(itimeout.TTime) - dtconvertint(CheckOutTime)))>=20:     
           continue    #去掉本段是第一段并且不止一段并且无签到时占用第二段的上班时间的BUG。！！！！！！！！！！！！慎用
        if AttRule['TakeCardOut'] == 2:
            i_min = (abs(dtconvertint(itimeout.TTime) - dtconvertint(checkoutycTime)))   
        else:       
            i_min = (abs(dtconvertint(itimeout.TTime) - dtconvertint(CheckOutTime)))   
        if empsh!=1:
           if AttRule['TakeCardOut'] == 2:
               if i_min<intervalTime or (itimeout.TTime<=checkoutycTime and actcheckout!=None and actcheckout<checkoutycTime):
                  actcheckout = itimeout.TTime
                  intervalTime = i_min
                  ostate = itimeout.State
           else:  
               if i_min<intervalTime or (itimeout.TTime>=CheckOutTime and actcheckout!=None and actcheckout<CheckOutTime):
                  actcheckout = itimeout.TTime
                  intervalTime = i_min
                  ostate = itimeout.State
        else:   #弹性班次取卡
           actcheckout = itimeout.TTime
           intervalTime = i_min
           ostate = itimeout.State           
           break
    ######        
    if (actcheckout==None or intervalTime==9999) and ef.CheckOut==0 and empsh!=1:   #不需要签退时，需要产生一个随机的卡。
        actcheckout = CheckOutTime + datetime.timedelta(minutes=int(random()*10))
    ##################### 计算提前签卡时间 #####################
    tqtime =0   #提前签到时间
    yctime =0   #提前签退时间 
    if actcheckin !=None and actcheckin<checkInTime:
       tqtime = (dtconvertint(checkInTime) - dtconvertint(actcheckin))
    if actcheckout !=None and actcheckout>CheckOutTime:
       yctime = (dtconvertint(actcheckout) - dtconvertint(CheckOutTime))
    ##################### 计算迟到早退时间 #####################   
    if actcheckin != None:
       if actcheckin>checkInTime and ((dtconvertint(actcheckin) - dtconvertint(checkInTime)))>=ef.LateMinutes:
          latetime = (dtconvertint(actcheckin) - dtconvertint(checkInTime))
       else:
          latetime =0
    else:
        latetime =0
    if actcheckout != None:
       if actcheckout<CheckOutTime and ((dtconvertint(CheckOutTime) -dtconvertint(actcheckout)))>=ef.EarlyMinutes:
          earlytime = (dtconvertint(CheckOutTime) - dtconvertint(actcheckout))
       else:
          earlytime = 0
    else:
        earlytime =0
        
    if actcheckout!=None:
       lasttime = actcheckout #---签退时间
    else:
       if actcheckin!=None:
          lasttime = actcheckin   #---签到时间
       else:
          lasttime = datetime.datetime(1900,1,1,0,0,0) #---初始则为 原始时间

     ##################### 汇总所有计算数据 #####################    
     # startrest1 段中休息开始时间   startrest2 段中休息开始时间2
    acttime = {'actcheckin':actcheckin,'actcheckout':actcheckout,'tqtime':tqtime,'yctime':yctime,
               'latetime':latetime,'earlytime':earlytime,'bccheckin':checkInTime,'bccheckout':CheckOutTime,'istate':istate,'ostate':ostate,
               'startrest1':startrest1,'endrest1':endrest1,'startrest2':startrest2,'endrest2':endrest2,
               'rest1':(endrest1-startrest1).seconds/60,'rest2':(endrest2-startrest2).seconds/60,
               'lasttime':lasttime}
    return acttime