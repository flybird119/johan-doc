# coding=utf-8

def attcalc_oneemp(u,d1,d2):
    '''
    计算每个人的考勤
    '''
    #人员u在d1,d2期间的签卡记录。一天的日期应该到23:59:59
    from mysite.iclock.models.model_trans import Transaction
    empcheckdata = Transaction.objects.filter(UserID = u,TTime__gte=d1,TTime__lte=d2+datetime.timedelta(days=1,hours=23,minutes=59,seconds=59)).order_by('UserID','TTime')
    
    #人员u的请假记录
    from mysite.att.models.model_empspecday import EmpSpecDay
    empleavedata = EmpSpecDay.objects.filter(emp = u,start__lte=d2+datetime.timedelta(minutes=2879),end__gte=d1).order_by('emp','start')
    
    #人员u的临时调休
    from mysite.att.models.model_setuseratt import SetUserAtt
    emptx = SetUserAtt.objects.filter(UserID = u,endtime__gte=d1,starttime__lte=(d2+datetime.timedelta(minutes=1439))).order_by('UserID','starttime')   
    
    #人员u的排班情况 
    from mysite.att.models import USER_OF_RUN    #---获取人员所有排班记录和班次详细信息
    usersch=[]      #---人员所有排班记录
    usersch=list(USER_OF_RUN.objects.filter(UserID=u,EndDate__gte=d1,StartDate__lte=(d2+datetime.timedelta(minutes=1439))).order_by('-pk').values_list('NUM_OF_RUN_ID','StartDate','EndDate'))
    from mysite.att.models.user_temp_sch import USER_TEMP_SCH #---获取人员所有临时排班记录
    etempsch = list(USER_TEMP_SCH.objects.filter(UserID = u,ComeTime__lte=d2+datetime.timedelta(days=1,hours=23,minutes=59,seconds=59),LeaveTime__gte=d1).order_by('UserID','ComeTime').values_list('SchclassID','WorkType','ComeTime','LeaveTime','Flag'))
    
    global empinfo 
    empinfo = getempinfo(u) #---人员信息
    day_current = d1
    while day_current<=d2:  #---循环计算d1-d2之间的每一天
        if day_current > d2 or day_current <todatetime(empinfo['HireDate']): #---当前日期大于结束日期或者当前日期小于聘用日期则跳出
           day_current = day_current + datetime.timedelta(days=1)            
           continue
        if empinfo['firedate']!= None:   #---是离职人员且当前日期超过了离职日期则跳出
           if day_current > todatetime(empinfo['firedate']):
              day_current = day_current + datetime.timedelta(days=1)            
              continue
                        
        from mysite.att.models import Holiday #---获取计算日期前100天到计算日期的节假日
        holidays=Holiday.objects.filter(start_time__gte=(d1+datetime.timedelta(days=-100))).order_by('start_time').values('name','start_time','duration')
        #计算每天的考勤。
        attcalc_oneemp_oneday(u,day_current,empcheckdata,empleavedata,emptx,usersch,etempsch,holidays)
        day_current = day_current + datetime.timedelta(days=1)      