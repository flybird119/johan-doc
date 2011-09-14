# coding=utf-8

#始化过程变量
def InitData():
    global Schedules
    global SchDetail
    global schClass
    global UserSchPlan
    global AttAbnomiteRptItems
    global AbnomiteRptItems
    global LeaveClasses
    global LClasses1
    global qryLeaveClass1
    global tHoliday
    tHoliday=None
    Schedules=None
    SchDetail=None
    schClass=None
    qryLeaveClass1=None
    UserSchPlan={}
    ExceptionIDs=[]
    rmdattexception=[]
    AttAbnomiteRptItems=[]
    LeaveClasses=[]
    LClasses1=[]
    AbnomiteRptItems=[]
    calcitem=None 
    leavetype=None

def MainCalc_new(UserIDList,DeptIDList,d1,d2,isForce=0):
    '''
    考勤统计计算 UserIDList like [1,2,3,4]
    返回计算的人数
    '''
    from mysite.att.models import attShifts,attRecAbnormite,AttException,attCalcLog
    from mysite.att.models import NUM_RUN  ,SchClass ,AttException #考勤班次,考勤时段,请假明细
    from mysite.personnel.models import Employee
    global isCalcing
    d1=trunc(d1)
    d2=trunc(d2)
    ############################# 一些常规的验证 ########################
    if d1>d2:   #---起始时间不能大于中止时间
        return -1
    if d2>trunc(datetime.datetime.now()): #---中止时间不能大于现在
        return -3
    if not allowAction(d1,1,d2):    #----是否运行动作
        return -4
    if isCalcing==1:    #---同时只能有一个计算实例
        return -5
    isCalcing=1
    
    StartDate=datetime.datetime(d1.year,d1.month,d1.day,0,0,0)  #---处理起止时间为日期0点到24点
    EndDate=datetime.datetime(d2.year,d2.month,d2.day,23,59,59)
    
    
    global LeaveClasses,AttRule
    global AttAbnomiteRptItems
    global StartDate,EndDate
    global UserSchPlan
    global AttRule
    global schclass
    global NUM_RUN
    global schclass_all
    global empleavedata
    global calcitem 
    global leavetype   
    empleavedata = None
    schclass_all = list(SchClass.objects.all())    #---所有考勤时段

    ############################# 部门ID列表或人员ID列表的处理 ########################
    userids=[]
    if DeptIDList:  #---部门ID列表时的处理
        calcDepts=[]
        for t in DeptIDList:
            calcDepts.append(t)
            if len(calcDepts)>300:
               ues=Employee.objects.filter(DeptID__in=calcDepts,OffDuty__lt=1 ).values_list('id', flat=True).order_by('id')
               for u in ues:
                   userids.append(u)
               calcDepts=[]
        if len(calcDepts)>0:
            ues=Employee.objects.filter(DeptID__in=calcDepts,OffDuty__lt=1 ).values_list('id', flat=True).order_by('id')
            for u in ues:
                userids.append(u)
    else:
        userids=UserIDList  #---用户ID列表
    if userids==[]:
        isCalcing=0
        return 0
    if isForce: #---是否强制数据初始化
        InitData()
    ############################# 获取考勤相关的参数规则、假类和计算项目信息 ########################
    try:
#        global rmdattabnormite
#        global rmdRecAbnormite
#        AttRule=LoadAttRule(True)   #---获取考勤参数规则

        ########################### 循环计算每个人员的考勤 ########################
        for u in userids:            
            u=int(u)
            UserSchPlan=LoadSchPlan(u,True,False)   #---员工考勤方面的信息
            valid=bool(UserSchPlan['Valid'])    #---总是为1
            if valid:
                uobj=Employee.objects.filter(pk=u)  #---清空 考勤明细表、考勤计算操作日志表、统计结果详情表、考勤异常记录表 用以重新计算
                attShifts.objects.filter(UserID=uobj,AttDate__gte=StartDate.date(),AttDate__lte=EndDate.date()).delete()
                attCalcLog.objects.filter(UserID=uobj,StartDate__gte=StartDate,EndDate__lte=EndDate).delete()
                attRecAbnormite.objects.filter(UserID=uobj,AttDate__gte=StartDate,AttDate__lte=EndDate).delete()
                AttException.objects.filter(UserID=uobj,StartTime__gte=StartDate,EndTime__lte=EndDate).delete()                
                #---开始计算                                                                                                                                                            
                attcalc_oneemp(u,d1,d2)                                        
                time.sleep(0.1)
    except:
        import traceback;traceback.print_exc()
    isCalcing=0 #---计算结束
    return len(userids) #---返回计算的人数