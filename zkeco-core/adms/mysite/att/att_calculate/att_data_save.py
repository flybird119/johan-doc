# coding=utf-8
from leave_utils import getleaveReportSymbol,getleaveCalcUnit
from calculate_cleave import calcleave,leave_data_SchClass

def calcitemandsave(acttime,ef,currentday,u,eLeave,worktype,empsh,itemn):
    '''
    acttime：取卡结果
    ef：时段
    currentday：当前日期
    u：人员ID
    eLeave：请假数据
    worktype：当前日期类型
    empsh：班次ID
    itemn,    循环计算时的序号 
    leavetype：所有假类
    itemcontent：计算项目内容
    返回
    '''
    from model_data_utils import get_item_content
    itemcontent=get_item_content        
    
    #先保存请假
    from mysite.att.models import AttException,LeaveClass,attRecAbnormite  
    if ef.shiftworktime==0 and worktype==0: #--- 平日且工作时间=0 则为平日加班
       worktype=1
       
    empexcept = []  #---请假数据计算结果
    if worktype==0: #---平日工作
       try:
          empexcept = calcleave(acttime,ef,currentday,eLeave,empsh) #---请假计算
       except:
          import traceback;traceback.print_exc()
          
    eactleave =0    #---时段请假时长
    ssymbol=''  #---请假情况符号表示
    exceptid =[] #---请假ID集合
    
    nocheckin = 0   #---是否有签到
    nocheckout =0   #---是否有签退
    present = 0 #----工作分钟数
    absent = 0  #---缺勤时长
    absenttr = 0
    late =0
    early = 0
    tqycov = 0
    ov =0
    xxov =0    
    jjov =0
    check =0
    gdov =0
  
    if itemn==1:    #-------只第一此计算该时段的请假数据
        leave_cal_result = leave_data_SchClass(empexcept)
        eactleave = leave_cal_result[0]
        ssymbol = leave_cal_result[1]
        exceptid = leave_cal_result[2]           
    if eactleave>ef.shiftworktime:  #---时段请假时长不能超过时段工作时间
       eactleave=ef.shiftworktime
    from data_save_utils import save_attRecAbnormite
    save_attRecAbnormite(u,acttime,currentday)

    if empsh!=1:  #-------非弹性班次。           
       #计算出勤
       if acttime['actcheckin'] != None and acttime['actcheckout'] !=None:   #两次卡都有的情况
          check = (dtconvertint(acttime['actcheckout']) - dtconvertint(acttime['actcheckin']))  #-----出勤时长
          actworktime = (dtconvertint(acttime['actcheckout']) - dtconvertint(acttime['actcheckin']))            #---上班时间    下班时间
          intime=(acttime['actcheckin'] - datetime.timedelta(minutes=ef.LateMinutes))<=acttime['bccheckin'] and acttime['bccheckin'] or acttime['actcheckin']
          if intime>acttime['startrest1'] and intime<acttime['endrest1'] and acttime['startrest1'].year!=1900:
             intime=acttime['endrest1']
          if intime>acttime['startrest2'] and intime<acttime['endrest2'] and acttime['startrest2'].year!=1900:
             intime=acttime['endrest2']             
          outtime=(acttime['actcheckout']+datetime.timedelta(minutes=ef.EarlyMinutes))>=acttime['bccheckout'] and acttime['bccheckout'] or acttime['actcheckout']         
          if outtime>acttime['startrest1'] and outtime<acttime['endrest1'] and acttime['startrest1'].year!=1900: 
             outtime = acttime['startrest1']
          if outtime>acttime['startrest2'] and outtime<acttime['endrest2'] and acttime['startrest2'].year!=1900: 
             outtime = acttime['startrest2']                      
          ############################ 没有迟到早退、缺勤则工作时间是班次规定的工作时间###################
          if acttime['actcheckin']<=acttime['bccheckin'] and acttime['actcheckout']>=acttime['bccheckout']:
             if eactleave==0:   #---请假时长为0
                if worktype!=1: #---平日正常上班
                   if ef.shiftworktime>0:
                      present = ef.shiftworktime
                   else:
                      present = dtconvertint(outtime) - dtconvertint(intime) - acttime['rest1']
                else: #-------平日加班
                   if dtconvertint(acttime['actcheckout'])>=dtconvertint(acttime['bccheckout']) and acttime['rest1']>0 and ((dtconvertint(acttime['bccheckout']) - dtconvertint(acttime['bccheckin']))!=ef.shiftworktime):
                      if ef.shiftworktime>0:    #----如果设置了时段工作时间则以设置的值为准
                         present = ef.shiftworktime#actworktime - acttime['rest1']
                      else:
                         if acttime['actcheckin']<acttime['startrest1']:    #----去除段中休息时间
                            present = actworktime - acttime['rest1']
                         else:
                            present = acttime #----????????????????????????????????
                   else:
                      present = actworktime
             else:
                if ef.shiftworktime>0:
                   present = ef.shiftworktime - eactleave
                else:
                   present = dtconvertint(outtime) - dtconvertint(intime) - eactleave - acttime['rest1']
          else:    #---有迟到早退或缺勤
             if intime<=acttime['startrest1'] and outtime>acttime['endrest2'] and acttime['endrest2'].year!=1900:
                if worktype!=1: #---非平日加班要去除中间休息时间
                   present = (dtconvertint(outtime) - dtconvertint(intime)) - acttime['rest1'] - acttime['rest2']
                else:   #---平日加班
                   present = actworktime
             else: #----当段中休息时间越界了时
                if intime<=acttime['startrest1'] and outtime>=acttime['endrest1'] and acttime['endrest1'].year!=1900:
                   if eactleave==0:
                      if worktype!=1:
                         if dtconvertint(acttime['bccheckout']) - dtconvertint(acttime['bccheckin'])==ef.shiftworktime or dtconvertint(acttime['bccheckout']) - dtconvertint(acttime['bccheckin'])==(ef.shiftworktime - 1440):
                            present = (dtconvertint(outtime) - dtconvertint(intime)) 
                         else: 
                            present = (dtconvertint(outtime) - dtconvertint(intime)) - acttime['rest1'] #- eactleave
                      else:
                         if dtconvertint(acttime['actcheckout'])>=dtconvertint(acttime['bccheckout']) and acttime['rest1']>0 and ((dtconvertint(acttime['bccheckout']) - dtconvertint(acttime['bccheckin']))>ef.shiftworktime):
                            present = actworktime - acttime['rest1']
                         else:
                            present = actworktime
                   else:
                      if ef.shiftworktime>0:
                         present = ef.shiftworktime - eactleave#(dtconvertint(acttime['bccheckout']) - dtconvertint(acttime['bccheckin'])) - acttime['rest1'] - eactleave
                      else:
                         present = dtconvertint(outtime) - dtconvertint(intime) - eactleave - acttime['rest1']
                else:
                   if eactleave==0:
                      if worktype!=1:
                         present = (dtconvertint(outtime) - dtconvertint(intime)) #- eactleave
                      else:
                         if dtconvertint(acttime['actcheckout'])>=dtconvertint(acttime['bccheckout']) and acttime['rest1']>0 and ((dtconvertint(acttime['bccheckout']) - dtconvertint(acttime['bccheckin']))>ef.shiftworktime):
                            present = actworktime - acttime['rest1']
                         else:
                            present = actworktime
                   else:
                      present = ef.shiftworktime - eactleave#(dtconvertint(acttime['bccheckout']) - dtconvertint(acttime['bccheckin'])) - eactleave 
             if (present+ef.LateMinutes + ef.EarlyMinutes)>ef.shiftworktime and worktype==0:  #消除有迟到、早退的情况下，出勤时间不够的问题。
                if ef.shiftworktime>0:
                   present = ef.shiftworktime
          ################################### 计算迟到、早退、旷工 ##################################3          
          if present<ef.shiftworktime and eactleave==0:  #出勤不满规定时间的情况
             if eactleave==0: 
                absent = ef.shiftworktime - present
             else:
                if (present + eactleave)<ef.shiftworktime:
                   absent = ef.shiftworktime - present - eactleave
                if (eactleave + present)>=ef.shiftworktime:
                   present = ef.shiftworktime - eactleave
                   absent = 0
             if absent<=(ef.LateMinutes + ef.EarlyMinutes) and worktype==0:
                absent = 0
          else:
             absent = 0
             
             #eactleave = 0  #有出勤的时候先默认为自动销假。
          if acttime['latetime']>ef.LateMinutes and worktype!=1:   #一次迟到超过多少分种开始计算为旷工。
             if eactleave==0:
                if acttime['latetime']>AttRule['MinsLateAbsent'] and AttRule['LateAbsent']==1 :
                   if absent==0:
                      absent = acttime['latetime']
                else:
                   late = acttime['latetime']
                   if worktype==0:
                      absent =0
             else:
                late =0
                if worktype==0:
                   absent =0             
          else:
             late =0
             
          if acttime['earlytime']>ef.EarlyMinutes and worktype!=1:  #一次早退超过多少分种开始计算为旷工。
             if eactleave==0:
                if acttime['earlytime']>AttRule['MinsEarlyAbsent'] and AttRule['EarlyAbsent']==1:
                   if absent==0:
                      absent = acttime['earlytime']
                else:
                   early=acttime['earlytime']
                   if absent==early and worktype==0:
                      absent =0
             else:
                early =0
                if worktype==0:
                   absent =0
          else:
             early =0
             
       if late>0 and present<ef.shiftworktime and eactleave==0 and present>0 and absent==0:
          present = ef.shiftworktime
       if early>0 and present<ef.shiftworktime and eactleave==0 and present>0 and absent==0:
          present = ef.shiftworktime
                    
       if acttime['actcheckin'] == None and acttime['actcheckout'] !=None: #-----------------------------------缺上班卡
          nocheckin = 1
          if acttime['earlytime']>ef.EarlyMinutes and AttRule['EarlyAbsent']==1:  #一次早退超过多少分种开始计算为旷工。
             if eactleave==0:
                if acttime['earlytime']>AttRule['MinsEarlyAbsent']:
                   absent = ef.shiftworktime#absent + acttime['earlytime']
                else:
                   early=acttime['earlytime']
             else:
                early =0
                absent =0
          else:
              if acttime['earlytime']>ef.EarlyMinutes:
                 early = acttime['earlytime']
          #   early =0          
          if AttRule['NoInAbsent']==2:
             if eactleave == 0:
                absent = ef.shiftworktime
             else:
                absent = ef.shiftworktime - eactleave
             if absent<0:
                absent =0
             present = 0
          else:
             if acttime['actcheckout'] >=acttime['bccheckin']:
                if absent==0:
                   present = ef.shiftworktime - eactleave #- AttRule['MinsNoIn']
                else:
                   present = 0
                if present<0:
                   present = 0
                if worktype!=1:
                   late = AttRule['MinsNoIn']
             else:
                if absent==0:
                   present = ef.shiftworktime - eactleave#(dtconvertint(acttime['actcheckout']) - dtconvertint(acttime['bccheckin'])) - AttRule['MinsNoIn']
                else:
                   present =0
                if present<0:
                   present =0
                if worktype!=1:
                   early = acttime['earlytime']   #这里暂时不考虑旷工的情况。
             late = AttRule['MinsNoIn']
                         
       if acttime['actcheckin'] !=None and acttime['actcheckout'] == None: #-----------------------------------------缺下班卡
          nocheckout = 1
          if acttime['latetime']>ef.LateMinutes and AttRule['LateAbsent']==1:   #一次迟到超过多少分种开始计算为旷工。
             if eactleave==0:
                if acttime['latetime']>AttRule['MinsLateAbsent']:
                   absent = ef.shiftworktime#acttime['latetime']
                else:
                   late = acttime['latetime']
                   absent =0
             else:
                late =0
                absent =0  
          else:
              if acttime['latetime']>ef.LateMinutes:
                 late = acttime['latetime']         
          if AttRule['NoOutAbsent']==2:
             if eactleave ==0:
                absent = ef.shiftworktime            
             else:
                absent = ef.shiftworktime - eactleave
                nocheckout =0
             if absent <0:
                absent = 0
             present =0                 
          else:
             if acttime['actcheckin']<acttime['bccheckin']:
                if absent ==0:
                   present = ef.shiftworktime - eactleave #- AttRule['MinsNoOut']
                else:
                   present = 0
                if present<0:
                   present =0
             else:
                if absent==0:
                   present = ef.shiftworktime - eactleave#(dtconvertint(acttime['bccheckout']) - dtconvertint(acttime['bccheckin'])) - AttRule['MinsNoOut']
                else:
                   present =0
                if present<0:
                   present =0
                #late=acttime['latetime']
             early = AttRule['MinsNoOut']   # 这里暂时不考虑旷工的情况
                         
       if acttime['actcheckin'] ==None and acttime['actcheckout'] == None:  #-----------------------------------缺两次卡
          nocheckin = 1
          nocheckout = 1
          if eactleave==0:
             absent = ef.shiftworktime
             present =0
          else: # 有请假时 
             if ef.shiftworktime>eactleave:
                absent = ef.shiftworktime - eactleave   #-----将缺勤中的请假部分除去           
             else:
                absent = 0
                eactleave = ef.shiftworktime
             if worktype ==3:   #节假日时自动设置为正常
                present =ef.shiftworktime
                absent =0
             else:
                present =0 #---没有设置缺勤时长
       #加班 , 本应该要加上提前加班，目前暂时不考虑
       if acttime['yctime']>AttRule['MinsOutOverTime'] and ef.IsOverTime>0 and  AttRule['OutOverTime']==1 and worktype!=1:
          tqycov = acttime['yctime']
       #如果既存在旷工，又存在迟到早退的情况，应该要消除旷工时间及迟到早退，此处存在风险。 慎用

       #如果旷工时间=应工作时间，则应该不存在迟到早退。
       if absent >=ef.shiftworktime and ef.shiftworktime>0:
          late =0
          early=0
       if worktype == 1 or (ef.shiftworktime==0 and worktype==0):     #如果工作时间等于0，则本段为加班时间段。
          ov = present
          present =0
          absent =0
          late =0
          early =0          
    if empsh==1:    #------------------------------------------------------------------------弹性班次时
       if acttime['actcheckin']!=None and acttime['actcheckout']!=None:
          present =(dtconvertint(acttime['actcheckout']) - dtconvertint(acttime['actcheckin'])) - acttime['rest1']
          check = (dtconvertint(acttime['actcheckout']) - dtconvertint(acttime['actcheckin']))                      
          late =0
          early =0
          absent =0
    if worktype in [2,3]:
       late =0
       early =0
       absent =0
    if absent>ef.shiftworktime:
       absent = ef.shiftworktime
    #根据考勤参数进行单位换算。
    ############################### 实到的计算 ##############################
    yd =0
    if absent<ef.shiftworktime or ef.shiftworktime==0:
       if eactleave==0:
          if worktype!=1:
             sd =present+late+early
          else:
             sd = ov + late + early
       else:
          sd = present
    else:
       sd =0
    if itemcontent[0]['Unit']==1:
       sd=decquan(Decimal(str(sd))/60)      #lehman 2010-08-27日        
    if itemcontent[0]['Unit']==3:
       if ef.shiftworktime!=0:
          sd = decquan((Decimal(str(sd))/ef.shiftworktime) * (Decimal(str(ef.WorkDay)))) #leman 2010-08-27日
       else:
          if ov>0:
             sd = ef.WorkDay
          else:
             sd =0  
       if sd>1:
          sd=1   
    if sd <0:
       sd =0
    if present<0:
       present=0
    if absent<0:
       absent =0
    ################################### 应到的计算 ####################################
    if worktype in [0,1]: #---为平日
       if empsh!=1: #---非弹性时段
          if itemcontent[0]['Unit']==3: #---单位     (1小时    2分钟    3天)
             if worktype==1:#平日加班
                if ef.shiftworktime>0:
                   yd = decquan(Decimal(str(ov)))/ef.shiftworktime*decquan(Decimal(str(ef.WorkDay)))
                else:
                    if acttime['rest1']>0 and acttime['rest1']==0: 
                       yd = decquan(Decimal(str(ov)))/(dtconvertint(acttime['bccheckout']) - dtconvertint(acttime['bccheckin'] - acttime['rest1']))*decquan(Decimal(str(ef.WorkDay)))
                    else:
                       yd = decquan(Decimal(str(ov)))/(dtconvertint(acttime['bccheckout']) - dtconvertint(acttime['bccheckin'] - acttime['rest1'] - acttime['rest2']))*decquan(Decimal(str(ef.WorkDay)))                                                
                if yd>decquan(Decimal(str(ef.WorkDay))):
                   yd=ef.WorkDay
             else:
                yd = ef.WorkDay 
          if itemcontent[0]['Unit']==1:
             if worktype!=1:
                yd = decquan(Decimal(str(ef.shiftworktime))/60)
             else:
                if ef.shiftworktime==0:
                   yd = decquan(Decimal(str(ov))/60)
                else:
                   yd = decquan(Decimal(str(ef.shiftworktime))/60)
          if itemcontent[0]['Unit']==2:
             if worktype !=1:
                yd = ef.shiftworktime
             else:
                if ef.shiftworktime==0:
                   yd = ov
                else:
                   yd = ef.shiftworktime
       else:  #---弹性时段
          if itemcontent[0]['Unit']==3:
             yd = ef.WorkDay 
          if itemcontent[0]['Unit']==1:
             yd = decquan(Decimal(str(ef.shiftworktime))/60)
          if itemcontent[0]['Unit']==2:
             yd = ef.shiftworktime
    else: #---为休息日或节假日
       yd = 0
    yd = intdata(yd,itemcontent[0]['MinUnit'],itemcontent[0]['RemaindProc'])
    sd = intdata(sd,itemcontent[0]['MinUnit'],itemcontent[0]['RemaindProc'])       
    if sd>yd:
       sd =yd
    ##################################### 平日加班 ################################
    if ov>0:
       if itemcontent[5]['Unit']==1:
          ov = decquan(Decimal(str(ov))/60)
       if itemcontent[5]['Unit']==3:
          ov = decquan(Decimal(str(ov))/60)          
       ov=intdata(ov,itemcontent[5]['MinUnit'],itemcontent[5]['RemaindProc'])       
    ###################################### 迟到 #################################
    if itemcontent[1]['Unit']==1:
       late=decquan(Decimal(str(late))/60)
    if itemcontent[1]['Unit']==3:
       if ef.shiftworktime!=0:
          late =decquan(Decimal(str(late))/ef.shiftworktime)*decquan(ef.WorkDay)
       else:
          late =decquan(Decimal(str(late))/480)*decquan(ef.WorkDay)         
    late = intdata(late,itemcontent[1]['MinUnit'],itemcontent[1]['RemaindProc'])
    ##################################### 早退 ###################################
    if itemcontent[2]['Unit']==1:
       early = decquan(Decimal(str(early))/60)
    if itemcontent[2]['Unit']==3:
       if ef.shiftworktime!=0:
          early = decquan(Decimal(str(early))/ef.shiftworktime)*decquan(ef.WorkDay)
       else:
          early = decquan(Decimal(str(early))/480)*decquan(ef.WorkDay) 
    early =intdata(early,itemcontent[2]['MinUnit'],itemcontent[2]['RemaindProc'])
    ##################################### 请假 ###################################
    if itemcontent[3]['Unit']==1:
       eactleave = decquan(Decimal(str(eactleave))/60)
    if itemcontent[3]['Unit']==3:
       if ef.shiftworktime!=0:
          eactleave = decquan(Decimal(str(eactleave))/ef.shiftworktime)*decquan(ef.WorkDay)
       else:
          eactleave = decquan(Decimal(str(eactleave))/480)*decquan(ef.WorkDay)  
    eactleave = intdata(eactleave,itemcontent[3]['MinUnit'],itemcontent[3]['RemaindProc'])
    ##################################### 旷工 ###################################
    absenttr = absent
    if itemcontent[4]['Unit'] ==1:
       absenttr = decquan(Decimal(str(absent))/60)
    
    if itemcontent[4]['Unit'] ==3:
       if ef.shiftworktime!=0:
          absenttr = decquan(Decimal(str(absent))/ef.shiftworktime)*decquan(ef.WorkDay)
       else:
          absenttr = decquan(Decimal(str(absent))/480)*decquan(ef.WorkDay) 
    absenttr = intdata(absenttr,itemcontent[4]['MinUnit'],itemcontent[4]['RemaindProc'])
    if itemcontent[5]['Unit'] ==1:
       tqycov = decquan(Decimal(str(tqycov))/60)
    if itemcontent[5]['Unit'] ==3:
       if ef.shiftworktime!=0:
          tqycov = decquan(Decimal(str(tqycov))/ef.shiftworktime)*decquan(ef.WorkDay)
       else:
          tqycov = decquan(Decimal(str(tqycov))/480)*decquan(ef.WorkDay) 
    tqycov = intdata(tqycov,itemcontent[5]['MinUnit'],itemcontent[5]['RemaindProc'])       
    #if worktype in [0,1]:
    if ef.OverTime>0 and absent==0 and eactleave==0 and acttime['actcheckin']!=None and acttime['actcheckout']!=None and acttime['actcheckin']<=acttime['bccheckin'] and acttime['actcheckout']>=acttime['bccheckout']:
       gdov = ef.OverTime
       if itemcontent[5]['Unit'] ==1:
           gdov = decquan(Decimal(str(gdov))/60)
       if itemcontent[5]['Unit'] ==3:
          if ef.shiftworktime!=0:
             gdov = decquan(Decimal(str(gdov))/ef.shiftworktime)*decquan(ef.WorkDay)
          else:
             gdov = decquan(Decimal(str(gdov))/480)*decquan(ef.WorkDay)
       gdov = intdata(gdov,itemcontent[5]['MinUnit'],itemcontent[5]['RemaindProc'])

    #加班应该要加上延时加班
    ov = ov + tqycov + gdov
    #休息加班
    if worktype ==2:
       xxov = present
       if itemcontent[5]['Unit']==1:
          xxov =  decquan(Decimal(str(present))/60)
       if itemcontent[5]['Unit']==3:
          if ef.shiftworktime!=0:
             xxov=decquan(Decimal(str(present))/ef.shiftworktime)*decquan(ef.WorkDay)
          else:
             xxov = decquan(Decimal(str(present))/8)*decquan(ef.WorkDay)
       xxov = intdata(xxov,itemcontent[5]['MinUnit'],itemcontent[5]['RemaindProc'])
       xxov = xxov + tqycov + gdov
    #加班应该加上延时加班  
    if worktype ==3:
       jjov = present
       if itemcontent[5]['Unit']==1:
          jjov =  decquan(Decimal(str(present))/60)
       if itemcontent[5]['Unit']==3:
          if ef.shiftworktime!=0:
             jjov = decquan(Decimal(str(present))/ef.shiftworktime)*decquan(ef.WorkDay)
          else:
             jjov = decquan(Decimal(str(present))/480)*decquan(ef.WorkDay) 
       jjov = intdata(jjov,itemcontent[5]['MinUnit'],itemcontent[5]['RemaindProc'])
       jjov = jjov + tqycov + gdov
    #加班应该加上延时加班
    if xxov>0 or jjov>0:
       if present>0:
          present =0
       if absent>0:
          absent =0
       if late >0:
          late =0
       if early>0:
          early =0
    if xxov>0:
       ov =0
    if jjov>0:
       ov =0
       xxov =0    
    if late>0 and worktype==0:
       ssymbol = ssymbol + itemcontent[1]['ReportSymbol']
    if early>0 and worktype==0:
       ssymbol = ssymbol + itemcontent[2]['ReportSymbol'] 
    if absent>0 and worktype==0:
       ssymbol = ssymbol + itemcontent[4]['ReportSymbol']+str(absenttr)
    if ov>0 or xxov or jjov>0:
       ssymbol = ssymbol + itemcontent[5]['ReportSymbol']
    if late==0 and early==0 and absent==0 and eactleave==0 and worktype in [0,1]:
       ssymbol = ssymbol + itemcontent[0]['ReportSymbol']  
    cin = [nocheckin,nocheckin,0,0]  
    cout =[nocheckout,nocheckout,0,0]
    muin =[ef.CheckIn,ef.CheckIn,0,0] 
    muout =[ef.CheckOut,ef.CheckOut,0,0]    
    bctime =0
    if worktype in [2,3]:
       bctime =0
    else:
       if empsh==1:
          bctime = present
       else:
          bctime = ef.shiftworktime              
    if cin[worktype]!=0:
       ssymbol = ssymbol + itemcontent[6]['ReportSymbol']
    if cout[worktype]!=0:
       ssymbol = ssymbol + itemcontent[7]['ReportSymbol']                       
    try:
        attdays = attShifts()
        attdays.UserID_id = u
        attdays.AttDate = currentday    #---日期
        attdays.ClockInTime = acttime['bccheckin']  #---上班时间
        attdays.ClockOutTime = acttime['bccheckout'] #---下班时间
        attdays.StartTime = acttime['actcheckin']   #---签到时间
        attdays.EndTime = acttime['actcheckout']    #---签退时间
        attdays.WorkDay=yd  #---应到
        attdays.SchIndex = ef.SchclassID    #---考勤时段编号
        attdays.AutoSch = 0 #---是否自动班次
        attdays.SchId_id = ef.SchclassID
        attdays.RealWorkDay=sd  #---实到
        attdays.NoIn=cin[worktype]  #---未签到
        attdays.NoOut=cout[worktype]    #---未签退
        attdays.Late = late #---迟到
        attdays.Early = early   #---早退
        attdays.Absent = absenttr   #---旷工
        attdays.OverTime = ov + xxov + jjov #---加班时间
        attdays.WorkTime = check    #---出勤时长
        attdays.ExceptionID=eactleave   #---例外情况ID
        attdays.Symbol = ssymbol    #---符号
        attdays.Exception=",".join(exceptid)    #---例外情况明细
        attdays.MustIn= muin[worktype]  #---应签到
        attdays.MustOut= muout[worktype]    #---应签退
        attdays.OverTime1= ((ov+xxov+jjov)>0 and 1 or 0)    #---加班签到
        attdays.WorkMins = present  #---工作分钟
        attdays.SSpeDayNormal= (worktype in [0,1] and 1 or 0)   #---平日    休息日    节假日
        attdays.SSpeDayWeekend= (worktype==2 and 1 or 0)
        attdays.SSpeDayHoliday= (worktype==3 and 1 or 0)        
        attdays.AttTime = bctime    #---时段时间
        attdays.SSpeDayNormalOT=ov  #---平日加班    休息日加班    节假日加班
        attdays.SSpeDayWeekendOT= xxov
        attdays.SSpeDayHolidayOT= jjov
        attdays.AbsentMins= absent  #---旷工时间
        attdays.AttChkTime = (empsh!=1 and ef.shiftworktime or present) #---AttChkTime ????????
        attdays.AbsentR= absenttr   #---旷工
        attdays.ScheduleName = ef.SchName
        attdays.IsConfirm= 0    #----??
        attdays.IsRead= 0
        attdays.save()  #----------------------------------------------------保存考勤明细表
        return 1
    except:
        import traceback;traceback.print_exc()
        return -1
####终于结束