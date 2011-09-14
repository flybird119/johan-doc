# coding=utf-8

AttRule={}
AttRuleStrKeys=('CompanyLogo','CompanyName')

#获取考勤规则
def LoadAttRule(reloadData=False):
    '''
    初始化加载考勤参数数据
    '''
    from mysite.att.models import AttParam
    global AttRule
    if not reloadData and AttRule!={}:
        return AttRule
    AttRule={
        'CompanyLogo':'Our Company',
        'CompanyName' :'Our Company',
        'EarlyAbsent':0,                #一次早退大于   分钟记
        'LateAbsent':0,                 #一次迟到大于   分钟记
        'MaxShiftInterval':660,         #最长的班次时间不超过
        'MinRecordInterval':5,            #最小的记录间隔
        'MinsEarly' : 0,                  #提前多少分钟记早退
        'MinsLateAbsent':100,
        'MinsEarlyAbsent':100,            #早退大于的分钟
        'MinShiftInterval':127,          #最短的班次时段
        'MinsLate' : 0,                  #超过多长时间记迟到
        'MinsNoIn' : 60,                  #无签到时记? 分钟
        'MinsNoOut' : 60,
        'MinsOutOverTime' : 60,
        'MinsWorkDay' : 480,
        'MinsWorkDay1' : 0,            #计算用
        'NoInAbsent':1,                   #上班无签到
        'NoOutAbsent':1,
        
        'TakeCardIn':1,                   #上班签到取卡规则
        'TakeCardOut':1,                #下班签到取卡规则
        
        'OTCheckRecType':2,               #加班状态
        'OutCheckRecType':3,
        'OutOverTime' :1,                 #下班后记加班
        'TwoDay' : '0',
        'WorkMonthStartDay' : 1,
        'WorkWeekStartDay' : 0,
        }
    qryOptions=AttParam.objects.all()
    for qryOpt in qryOptions:
        for k in AttRule.keys():
            if k==qryOpt.ParaName:
                if qryOpt.ParaValue=='on':
                    AttRule[k]=1
                elif k not in AttRuleStrKeys:
                    AttRule[k]=int(qryOpt.ParaValue)
                else:
                    AttRule[k]=qryOpt.ParaValue
                break
    return AttRule

def SaveAttOptions(paraName, paraValue):
    from mysite.att.models import AttParam
    ap=AttParam.objects.filter(ParaName=paraName)
    if ap:
        ap=ap[0]
        if u"%s"%ap.ParaValue!=u"%s"%paraValue:
            ap.ParaValue=paraValue
            ap.save()
    else:
        att=AttParam(ParaName=paraName,ParaValue=paraValue)
        att.save()

def SaveAttRule(AttRules):
    global AttRule
    if AttRule=={}:
        AttRule=LoadAttRule()
    changeflag=0
    k=AttRule.keys()
    for t in k:
        if not t in AttRules:
            AttRule[t]=0
        elif AttRules[t]=='on':
            if AttRule[t]!=1:
                changeflag=1
            AttRule[t]=1
        elif t not in AttRuleStrKeys:
            if AttRule[t]!=int(AttRules[t]):
                changeflag=1
            AttRule[t]=int(AttRules[t])
        else:
            AttRule[t]=AttRules[t]
        if t!='LeaveClass':
            SaveAttOptions(t,AttRule[t])
    if changeflag:
        deleteCalcLog(Type=0)
