# coding=utf-8

from take_card import getchecktime

def attcalc_oneemp_oneday(u,currentday,empcheckdata,empleavedata,emptx,usersch,etempsch,holidays):
    '''
    #计算每个人每天的考勤
    usersch 人员的班次列表
    '''
    weekday = (currentday.weekday()+1)%7    #---得到星期数
    from schedule_utils import getshift_byuserdate
    empshift,schclassdetail = getshift_byuserdate(u,currentday,weekday,usersch) #---当天班次ID 和 该班次当天时段ID列表(可能有多个)
    ################################# 得到 班次、时段、是否弹性等信息 ######################
    empshiftschclass = None    #--- 正常班次时段对象  
    try:
       temp = []    #---------当天[临时排班的时段]对象
       tempworktype=[]  #---当天[临时排班的工作类型]
       tempflag=0   #---是否追加在排班之后
       if etempsch: #---有临时排班
          for e in etempsch:    #---每个临时排班    'SchclassID','WorkType','ComeTime','LeaveTime','Flag'
              if e[2]<=(currentday+datetime.timedelta(minutes=1439)) and e[3]>=currentday:  #---当天在排班日期范围内 (若当天存在多个临时排班则'当天存在员工排班'以最后一次为准)
                 for elem in schclass_all:  #---所有时段
                     if elem.pk==e[0]:
                        temp.append(elem)
                        tempworktype.append(e[1])   #---排班(次)的工作类型
                        tempflag=e[4]   #---排班(次)当天存在员工排班时(是否追加在排班之后)
       emptempsch = temp    #---当天临时排班的时段
    except:
       import traceback;traceback.print_exc()
       pass    
    if len(schclassdetail)==0 and not empshift and not emptempsch:  #如果没有排班及时段也没有临时排班时段(总之，没有时段)，则为弹性班次。
       schclassdetail =[(1,),]  #---正常时段初始化
       empshift=1   #---正常排班初始化 为弹性班次(ID)    是否弹性班次的依据
    
    if len(schclassdetail)>0:
       empshiftschclass = [e for e in schclass_all if e.pk in schclassdetail] #----正常班次时段或者弹性班次时段
       
    if empshift==1:
        empworktype = getworktype_byuserdate(currentday,True,holidays) #---得到当前日期类型  0平日,2休息日,3节假日。
    else:
        empworktype = getworktype_byuserdate(currentday,False,holidays)

    ############################## 正常班次时段或弹性班次时段  时的处理 ##############################    
    if empshiftschclass != None:
       try:
         ############################## 非弹性班次 ##############################         
         if empshift!=1: #---非弹性班次
            lasttime = datetime.datetime(1900,1,1,0,0,0) #---签到与签退的后一次  
            ###################无临时排班，或，有临时排班且临时排班是追加在排班之后。           
            if not emptempsch or len(emptempsch)==0 or (len(emptempsch)>0 and tempflag==2):             
               iii=0    #---正常班次时段计数
               for ef in empshiftschclass:  #---正常班次时段循环           
                   acttime = getchecktime(ef,empcheckdata,currentday,lasttime,['I','O','0','1'],empshift,empshiftschclass[0].StartTime,iii,len(empshiftschclass) -1)  #---取签卡
                   if emptx:   #存在调休
                      calcresult = calcitemandsave(acttime,ef,currentday,u,empleavedata,calctx(ef,currentday,emptx,empworktype,empshiftschclass[0].StartTime),empshift,1)  #计算实际的项目并保存。
                   else:
                      calcresult = calcitemandsave(acttime,ef,currentday,u,empleavedata,empworktype,empshift,1)  #计算实际的项目并保存。
                   lasttime = acttime['lasttime']   
                   iii = iii+1
                   
            ######################有临时排班，且类型为"仅临时排班有效"
            else:
                iii=0
                for ef in emptempsch: #---临时班次时段循环
                    acttime = getchecktime(ef,empcheckdata,currentday,lasttime,['8,9'],empshift,emptempsch[0].StartTime,iii,len(emptempsch) -1)
                    if emptx: 
                       calcresult = calcitemandsave(acttime,ef,currentday,u,empleavedata,calctx(ef,currentday,emptx,tempworktype[iii],empshiftschclass[0].StartTime),0,1)
                    else:
                       calcresult = calcitemandsave(acttime,ef,currentday,u,empleavedata,tempworktype[iii],0,1)
                    lasttime = acttime['lasttime'] 
                    iii=iii+1
         ################################# 弹性班次 ##############################            
         else: #---弹性班次
             try:
                lasttime = datetime.datetime(1900,1,1,0,0,0)
                empshiftschclass =  filter(lambda f:f.pk in (1,),schclass_all)  #---得到弹性时段对象
                #----构造循环次数  
                if len(empcheckdata)>=2: #---签卡次数2次以上
                   ii = len([e for e in empcheckdata if (e.TTime).day == currentday.day]) #---本日签卡次数
                   if ii in [0,1]:
                      ii = 2
                      forlist = range(ii/2)
                else:
                   forlist = [0]
                #----循环计算开始   
                iii=0  
                for i  in forlist:             
                    acttime = getchecktime(empshiftschclass[0],empcheckdata,currentday,lasttime,['I','O','0','1','8','9'],empshift,empshiftschclass[0].StartTime,iii,(ii/2) -1)  #取刷卡时间并对应签到签退
                    if emptx:                       
                       calcresult = calcitemandsave(acttime,empshiftschclass[0],currentday,u,empleavedata,calctx(empshiftschclass[0],currentday,emptx,empworktype,empshiftschclass[0].StartTime),empshift,(i+1))  #计算实际的项目并保存。
                    else:
                       calcresult = calcitemandsave(acttime,empshiftschclass[0],currentday,u,empleavedata,empworktype,empshift,(i+1))  #计算实际的项目并保存。
                    lasttime = acttime['lasttime'] 
                    iii = iii +1                    
             except:
                import traceback;traceback.print_exc()
                pass
       except:
         import traceback;traceback.print_exc()
         pass
    ############################### 没有正常班次时段时的处理 #################################                                        
    else:
        #没有排班，但是有临时排班的情况。
        if emptempsch :
           try: 
              lasttime = datetime.datetime(1900,1,1,0,0,0)   
              iii =0    
              nworktype=0        
              for ef in emptempsch:
                  acttime = getchecktime(ef,empcheckdata,currentday,lasttime,['I','o','1','0','8,9'],empshift,emptempsch[0].StartTime,iii,len(emptempsch) -1)
                  if emptx:
                     calcresult = calcitemandsave(acttime,ef,currentday,u,empleavedata,calctx(ef,currentday,emptx,tempworktype[nworktype],emptempsch[0].StartTime),empshift,1)  #工作类型、班次代码(未知)、第几段
                  else:
                     calcresult = calcitemandsave(acttime,ef,currentday,u,empleavedata,tempworktype[nworktype],0,1)  #工作类型、班次代码(未知)、第几段
                  lasttime = acttime['lasttime'] 
                  iii = iii +1
                  nworktype = nworktype+1
           except:       
              import traceback;traceback.print_exc()
              pass
        else:  #既没有排班，也没有临时排班的情况,视为弹性班次(第二次做默认处理)。
           try:
              empshiftschclass =  filter(lambda f: f.pk in (1,),schclass_all)
              lasttime = datetime.datetime(1900,1,1,0,0,0) 
              ii = filattercord(currentday,empcheckdata)
              if ii in [0,1]:
                 ii = 2                  
              if ii>=2:   
                 iii =0       
                 for i  in range(ii/2):             
                     acttime = getchecktime(empshiftschclass[0],empcheckdata,currentday,lasttime,['I','O','0','1','8','9'],empshift,empshiftschclass[0].StartTime,iii,ii/2)  #取刷卡时间并对应签到签退
                     if emptx:
                        calcresult = calcitemandsave(acttime,empshiftschclass[0],currentday,u,empleavedata,calctx(empshiftschclass[0],currentday,emptx,empworktype,empshiftschclass[0].StartTime),empshift,i)  #计算实际的项目并保存。                                                 
                     else:
                        calcresult = calcitemandsave(acttime,empshiftschclass[0],currentday,u,empleavedata,empworktype,empshift,i)  #计算实际的项目并保存。
                     lasttime = acttime['lasttime'] 
                     iii = iii +1
              else:
                 iii =0
                 for i  in [0]:             
                     acttime = getchecktime(empshiftschclass[0],empcheckdata,currentday,lasttime,['I','O','0','1','8','9'],empshift,empshiftschclass[0].StartTimem,iii,0)  #取刷卡时间并对应签到签退
                     if emptx:
                        calcresult = calcitemandsave(acttime,empshiftschclass[0],currentday,u,empleavedata,calctx(empshiftschclass[0],currentday,emptx,empworktype,empshiftschclass[0].StartTime),empshift,i)  #计算实际的项目并保存。                                                
                     else:
                        calcresult = calcitemandsave(acttime,empshiftschclass[0],currentday,u,empleavedata,empworktype,empshift,i)  #计算实际的项目并保存。
                     lasttime = acttime['lasttime'] 
                     iii = iii +1
           except:
              import traceback;traceback.print_exc()
              pass