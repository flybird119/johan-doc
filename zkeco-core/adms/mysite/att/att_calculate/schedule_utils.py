# coding=utf-8
from mysite.att.models import NUM_RUN

#获取员工某天的班次ID和时段ID。#暂时不考虑自动排班
def getshift_byuserdate(u,currentday,wd,usersch):
    '''
    获取人员某天的班次ID和时段ID列表  当天只能有一个班次
    '''
    num_run_all = list(NUM_RUN.objects.all())      #---所有班次   
        
    ushift=None #---当前日期班次
    ushclass=[] #---班次时段
    ushiftunits=1   #---班次周期单位
    ushiftcycle=1   #---班次周期数
    for u in usersch:
        if todatetime(u[1])<=todatetime(currentday) and todatetime(u[2])>=todatetime(currentday):   #---当前时间在班次时间段内 多次则以第一次为准
           ushift=u
           break         
    if ushift:
       for s in num_run_all:
           if s.pk==ushift[0]:
              ushiftunits=s.Units   #---周期单位
              ushiftcycle=s.Cycle   #---周期数
              break
       from mysite.att.models.num_run_deil import NUM_RUN_DEIL    
       shclass = list(NUM_RUN_DEIL.objects.filter(Num_runID=ushift[0]).order_by('Num_runID','id').values_list('SchclassID','Sdays','Num_runID'))          
       if ushiftunits==1:   #---周
          for uc in shclass:    #--- uc 班次详细 ( 时段ID , 星期数(开始日期), 班次ID)
              if uc[2]==ushift[0] and uc[1]==wd:
                 ushclass.append(uc[0]) #---得到该班次当天的时段
       if ushiftunits==0:   #---天
          cdays = (todatetime(currentday) - todatetime(ushift[1])).days
          if (cdays+1)>(ushiftcycle):
             cdays = (cdays+1)%(ushiftcycle) -1
          for uc in shclass:
              if uc[2]==ushift[0] and uc[1]==cdays:
                 ushclass.append(uc[0]) 
       if ushiftunits==2:   #---月
          cdays = currentday.day -1
          for uc in shclass:
              if uc[2]==ushift[0] and uc[1]==cdays:
                 ushclass.append(uc[0])
    else:
       ushclass = []       
    if ushclass:
       return ushift[0],ushclass    #---返回 班次ID 和 该班次当天时段ID
    else:
       return None,ushclass