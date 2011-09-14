# coding=utf-8

from leave_utils import getleaveReportSymbol,getleaveCalcUnit
from att_utils import intdata,decquan

def calcleave(acttime,ef,currentday,eLeave,empsh):
   #
   '''计算请假 取当前时段的所有有效请假数据
       
   acttime: 当天的取卡结果    
   ef: 当日时段    
   currentday: 当日    
   eLeave: 人员请假数据    
   empsh: 班次ID
   '''
   empleavetime = []    #---请假时长
   starttime=[] #---请假开始时间
   endtime = [] #---请假结束时间
   leavename= []    #---请假类型pk
   alreadyleave = False
   for eleave in eLeave:#---循环请假数据 
      alreadyleave = False         
      if empsh!=1:#------------------------------------------非弹性班次
         #---------------被包含
         if eleave.start>acttime['bccheckin'] and eleave.end<acttime['bccheckout']:
            if acttime['endrest1']!=datetime.datetime(1900,1,1,0,0,0) and acttime['startrest1']!=datetime.datetime(1900,1,1,0,0,0): #---包含段中休息时间
               if eleave.start<=acttime['startrest1'] and eleave.end>acttime['endrest1'] and acttime['endrest1']!=datetime.datetime(1900,1,1,0,0,0) and eleave.end<acttime['endrest2']:
                  empleavetime.append((dtconvertint(eleave.end) - dtconvertint(eleave.start)) - acttime['rest1'])
                  alreadyleave = True
               if eleave.start<=acttime['startrest1'] and eleave.end>acttime['endrest1'] and acttime['endrest1']!=datetime.datetime(1900,1,1,0,0,0) and acttime['endrest2'].year==1900 and alreadyleave==False:
                  empleavetime.append((dtconvertint(eleave.end) - dtconvertint(eleave.start)) - acttime['rest1']) 
                  alreadyleave = True
               if eleave.start>acttime['startrest1'] and eleave.end<acttime['bccheckout'] and eleave.end>acttime['endrest1'] and alreadyleave==False:
                  if dtconvertint(eleave.start)>dtconvertint(acttime['endrest1']):
                     empleavetime.append((dtconvertint(eleave.end) - dtconvertint(eleave.start)))
                  else:
                     empleavetime.append((dtconvertint(eleave.end) - dtconvertint(acttime['endrest1'])))                     
                  alreadyleave = True
               if (eleave.end<acttime['startrest1'] and alreadyleave==False) or (eleave.start>acttime['endrest1'] and alreadyleave==False):
                  empleavetime.append((dtconvertint(eleave.end) - dtconvertint(eleave.start)))
                  alreadyleave = True
               if (eleave.end<=acttime['startrest1'] and alreadyleave==False):
                  empleavetime.append((dtconvertint(eleave.end) - dtconvertint(eleave.start)))               
            else:
               empleavetime.append((dtconvertint(eleave.end) - dtconvertint(eleave.start)))
            starttime.append(eleave.start)
            endtime.append(eleave.end)
            leavename.append(eleave.leaveclass.pk)             
         #----------------------前部分重叠          
         if eleave.start<=acttime['bccheckin'] and eleave.end<acttime['bccheckout'] and eleave.end>=acttime['bccheckin']:
            if acttime['endrest2']!=datetime.datetime(1900,1,1,0,0,0):
               if eleave.end>=acttime['endrest2']:               
                  empleavetime.append((dtconvertint(eleave.end) - dtconvertint(acttime['bccheckin'])) - acttime['rest1'] - acttime['rest2'])
                  endtime.append(eleave.end)
                  alreadyleave = True
               if eleave.end<acttime['endrest2']:
                  empleavetime.append((dtconvertint(acttime['startrest2']) - dtconvertint(acttime['bccheckin'])) - acttime['rest1']) #- acttime['rest2'])
                  endtime.append(acttime['startrest2'])
                  alreadyleave = True               
            else:
               if eleave.end>=acttime['bccheckin'] and acttime['startrest1'].year==1900:               
                  empleavetime.append((dtconvertint(eleave.end) - dtconvertint(acttime['bccheckin']))) 
                  endtime.append(eleave.end)
                  alreadyleave = True
            if alreadyleave==False and eleave.end>=acttime['endrest1'] and acttime['endrest1']!=datetime.datetime(1900,1,1,0,0,0) and (eleave.end<acttime['startrest2'] or acttime['startrest2'].year==1900):
               empleavetime.append((dtconvertint(eleave.end) - dtconvertint(acttime['bccheckin'])) - acttime['rest1'])
               endtime.append(eleave.end)
               alreadyleave =True
            if alreadyleave==False and eleave.end<=acttime['endrest1'] and eleave.end>=acttime['startrest1'] and acttime['endrest1']!=datetime.datetime(1900,1,1,0,0,0) and (eleave.end<acttime['startrest2'] or acttime['startrest2'].year==1900):
               empleavetime.append((dtconvertint(acttime['startrest1']) - dtconvertint(acttime['bccheckin'])))
               endtime.append(acttime['startrest1'])
            if alreadyleave==False and eleave.end<acttime['startrest1'] and acttime['endrest1']!=datetime.datetime(1900,1,1,0,0,0) and (eleave.end<acttime['startrest2'] or acttime['startrest2'].year==1900):
               empleavetime.append((dtconvertint(eleave.end) - dtconvertint(acttime['bccheckin'])))
               endtime.append(eleave.end)                
            starttime.append(acttime['bccheckin'])
            #endtime.append(eleave.end)
            leavename.append(eleave.leaveclass.pk)        
         #-----------------包含
         if eleave.start<=acttime['bccheckin'] and eleave.end>=acttime['bccheckout']:
            if (dtconvertint(acttime['bccheckout']) - dtconvertint(acttime['bccheckin']))>ef.shiftworktime:
               empleavetime.append((dtconvertint(acttime['bccheckout']) - dtconvertint(acttime['bccheckin'])) - acttime['rest1'] - acttime['rest2'])
            else:
               empleavetime.append((dtconvertint(acttime['bccheckout']) - dtconvertint(acttime['bccheckin'])))                
            starttime.append(acttime['bccheckin'])
            leavename.append(eleave.leaveclass.pk)
            endtime.append(acttime['bccheckout'])
         #-----------------后部门重叠
         if eleave.start>acttime['bccheckin'] and eleave.end>=acttime['bccheckout'] and eleave.start<=acttime['bccheckout']:
            if acttime['startrest1']!=datetime.datetime(1900,1,1,0,0,0):
               if eleave.start<=acttime['startrest1']:
                  empleavetime.append((dtconvertint(acttime['bccheckout']) - dtconvertint(eleave.start)) - acttime['rest1'])# - acttime['rest2']
                  starttime.append(eleave.start)
                  alreadyleave = True                                     
            else:
               if eleave.start<=acttime['bccheckout'] and acttime['endrest1']==datetime.datetime(1900,1,1,0,0,0):
                  empleavetime.append((dtconvertint(acttime['bccheckout']) - dtconvertint(eleave.start)))
                  starttime.append(eleave.start)
                  alreadyleave = True 
            if alreadyleave==False and acttime['endrest1']!=datetime.datetime(1900,1,1,0,0,0):
               if eleave.start>acttime['endrest1']  and eleave.start>acttime['startrest2'] and acttime['endrest2']!=datetime.datetime(1900,1,1,0,0,0):             
                  if eleave.start>acttime['endrest1'] and eleave.start<acttime['startrest2'] and eleave.start<acttime['bccheckout']:
                     empleavetime.append((dtconvertint(acttime['bccheckout']) - dtconvertint(eleave.start)) - acttime['rest2'])
                     starttime.append(eleave.start)
               else:
                  if eleave.start>acttime['startrest1'] and eleave.start<acttime['bccheckout']:
                     if dtconvertint(eleave.start)>dtconvertint(acttime['endrest1']):
                        empleavetime.append((dtconvertint(acttime['bccheckout']) - dtconvertint(eleave.start)))
                        starttime.append(eleave.start)
                     else:
                        empleavetime.append((dtconvertint(acttime['bccheckout']) - dtconvertint(acttime['endrest1'])))
                        starttime.append(acttime['endrest1']) 
            endtime.append(acttime['bccheckout'])
            leavename.append(eleave.leaveclass.pk)        
      else:#------------------------------------------弹性班次
         #本段段中请假
         if eleave.start>acttime['bccheckin'] and eleave.end<acttime['bccheckout']:
            if acttime['endrest1']!=datetime.datetime(1900,1,1,0,0,0) and acttime['startrest1']!=datetime.datetime(1900,1,1,0,0,0):
               if eleave.start<=acttime['startrest1'] and eleave.end>acttime['endrest1'] and acttime['endrest1']!=datetime.datetime(1900,1,1,0,0,0) and eleave.end<acttime['endrest2']:
                  empleavetime.append(eleave.end - eleave.start - acttime['rest1'])
                  alreadyleave = True
               if alreadyleave==False and eleave.start>acttime['startrest1'] and eleave.end<acttime['bccheckout'] and eleave.end>acttime['endrest1']:
                  empleavetime.append(eleave.end - acttime['endrest1'])
                  alreadyleave = True
               if alreadyleave==False and eleave.end<acttime['startrest1'] or eleave.start>acttime['endrest1']:
                  empleavetime.append(dtconvertint(eleave.end) - dtconvertint(eleave.start))
            else:
               empleavetime.append(dtconvertint(eleave.end) - dtconvertint(eleave.start))
            starttime.append(eleave.start)
            endtime.append(eleave.end)
            leavename.append(eleave.leaveclass.pk)          
         if alreadyleave==False and (eleave.start<=currentday and eleave.end>(currentday + datetime.timedelta(minutes=1440))):
            if acttime['endrest2']!=datetime.datetime(1900,1,1,0,0,0):
               if eleave.end>=acttime['endrest2']:              
                  empleavetime.append((dtconvertint(acttime['bccheckout']) - dtconvertint(acttime['bccheckin'])) - acttime['rest1'] - acttime['rest2'])
                  alreadyleave = True
            else:
               if eleave.end>=acttime['bccheckout']:              
                  empleavetime.append((dtconvertint(acttime['bccheckout']) - dtconvertint(acttime['bccheckin'])))
                  alreadyleave = True               
            if alreadyleave==False and eleave.end>=acttime['endrest1']and acttime['endrest1']!=datetime.datetime(1900,1,1,0,0,0) and (eleave.end<acttime['startrest2'] or acttime['startrest2'].year==1900):
               empleavetime.append((dtconvertint(acttime['bccheckout']) - dtconvertint(acttime['bccheckin'])) - acttime['rest1'])                
            starttime.append(acttime['bccheckin'])
            leavename.append(eleave.leaveclass.pk)
            endtime.append(acttime['bccheckout'])             
         if alreadyleave==False and (eleave.start>currentday and eleave.start<(currentday + datetime.timedelta(minutes=1440)) and eleave.end>(currentday + datetime.timedelta(minutes=1440))):
            empleavetime.append((dtconvertint(eleave.start) - dtconvertint(acttime['bccheckin'])) - acttime['rest1'] - acttime['rest2'])
            starttime.append(acttime['bccheckin'])
            leavename.append(eleave.leaveclass.pk)
            endtime.append(eleave.start)             
         if alreadyleave==False and (eleave.start<=currentday and eleave.end>=currentday and eleave.end<=currentday+datetime.timedelta(minutes=1440)):
            if acttime['endrest2']!=datetime.datetime(1900,1,1,0,0,0):
               if eleave.end>=acttime['endrest2']: 
                  empleavetime.append((dtconvertint(acttime['bccheckin']) - dtconvertint(eleave.end)) - acttime['rest1'] - acttime['rest2'])
                  alreadyleave = True
            else:
               if eleave.end>=acttime['bccheckin']: 
                  empleavetime.append((dtconvertint(acttime['bccheckin']) - dtconvertint(eleave.end)) - acttime['rest1'] - acttime['rest2'])
                  alreadyleave = True                
            if alreadyleave==False and eleave.end>=acttime['endrest1'] and acttime['endrest1']!=datetime.datetime(1900,1,1,0,0,0) and (eleave.end<acttime['startrest2'] or acttime['startrest2'].year==1900):
               empleavetime.append((dtconvertint(acttime['bccheckin']) - dtconvertint(eleave.end)) - acttime['rest1'])
            starttime.append(eleave.start)
            leavename.append(eleave.leaveclass.pk)
            endtime.append(acttime['bccheckout'])                 
         if alreadyleave==False and (eleave.start>=currentday and eleave.start<=(currentday + datetime.timedelta(minutes=1440)) and eleave.end>=currentday and eleave.end<=(currentday+datetime.timedelta(minutes=1440))):
            if acttime['startrest1']!=datetime.datetime(1900,1,1,0,0,0):             
               if eleave.start<=acttime['startrest1']: 
                  empleavetime.append((dtconvertint(eleave.end) - dtconvertint(eleave.start)) - acttime['rest1']) #- acttime['rest2'])
                  alreadyleave = True
            else:
               if eleave.start<=eleave.end: 
                  empleavetime.append((dtconvertint(eleave.end) - dtconvertint(eleave.start)) - acttime['rest1'] - acttime['rest2'])
                  alreadyleave = True
            if alreadyleave==False and acttime['endrest1']!=datetime.datetime(1900,1,1,0,0,0) and acttime['startrest2']!=datetime.datetime(1900,1,1,0,0,0):
               if eleave.start>acttime['endrest1'] and eleave.start<acttime['startrest2']:
                  empleavetime.append((dtconvertint(eleave.end) - dtconvertint(eleave.start)) - acttime['rest2'])
            starttime.append(eleave.start)
            leavename.append(eleave.leaveclass.pk)
            endtime.append(eleave.end)
   return [(empleavetime[i],starttime[i],endtime[i],leavename[i]) for i in range(0,len(empleavetime))]  #---以元祖的结构形式返回

def leave_data_SchClass(empexcept):
    '''
    保存指定的时段请假数据到数据库
    '''
    eactleave =0    #---时段请假时长
    ssymbol=''  #---请假情况符号表示
    exceptid =[] #---请假ID集合
    start_old=datetime.datetime(1900,01,01,0,0,0)
    end_old=datetime.datetime(1900,01,01,0,0,0)
    for etime,start,end,leavename in empexcept:  #--- 循环请假计算的结果 (请假时间,开始时间,结束时间,假类名称)
        if start_old==start: #---两个请假的开始时间不能相同
           continue
        att_exp = AttException()
        att_exp.StartTime=start  #---开始时间
        att_exp.EndTime = end  #---结束时间
        att_exp.UserID_id =u #---人员编号
        att_exp.ExceptionID = leavename  #---请假类型
        if etime>ef.shiftworktime:
           etime = ef.shiftworktime           
        k1,k2,k3 = getleaveCalcUnit(leavename)
        if k1==1:     
           if k3==1:      
              ssymbol = ssymbol + getleaveReportSymbol(leavename)+str(intdata(decquan(decquan(etime,3)/60),k2,k3))
           else:
              ssymbol = ssymbol + getleaveReportSymbol(leavename)+str(decquan(decquan(etime,3)/60,1,1))
           att_exp.TimeLong = intdata(etime/60,k2,k3)    #---总时长              
        if k1==2:
           ssymbol = ssymbol + getleaveReportSymbol(leavename)+str(etime)
           att_exp.TimeLong = etime#intdata(etime,k2,k3)            
        if k1==3:
           if ef.shiftworktime!=0: 
              if k3==1:                
                 ssymbol = ssymbol + getleaveReportSymbol(leavename)+str(decquan(intdata((decquan(etime,3)/60)/(decquan(ef.shiftworktime,3)/60),k2,k3))*decquan(ef.WorkDay))
              else:
                 ssymbol = ssymbol + getleaveReportSymbol(leavename)+str(decquan(decquan(etime,3)/60/(decquan(ef.shiftworktime,3)/60),1,1)*decquan(ef.WorkDay))
              att_exp.TimeLong = intdata(etime/60/ef.shiftworktime,k2,k3)                 
           else:  
              if k3==1:               
                 ssymbol = ssymbol + getleaveReportSymbol(leavename)+str(intdata(decquan(decquan(etime,3)/60/(480/60)),k2,k3)*decquan(ef.WorkDay))
              else:
                 ssymbol = ssymbol + getleaveReportSymbol(leavename)+str(decquan(decquan(etime,3)/60/(480/60),1,1)*decquan(ef.WorkDay))
              att_exp.TimeLong = intdata(etime/60/480,k2,k3)
        att_exp.InScopeTime =  etime #---有效时长               
        att_exp.AttDate = currentday  #---日期
        att_exp.OverlapWorkDayTail = 1
        att_exp.save() #----------------------------------------------------保存异常记录表
        exceptid.append(str(att_exp.pk))
        eactleave = eactleave + etime    #----累加请假时长
        start_old=start
        end_old = end
        return eactleave,ssymbol,exceptid