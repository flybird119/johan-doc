# coding=utf-8

def getleaveitem():
    '''
    获取所有假类
    '''
    from mysite.att.models.model_leaveclass import LeaveClass
    calcitem=LeaveClass.objects.all().order_by('LeaveID')
    return calcitem

def getleaveReportSymbol(leaveid):
    '''
    获取假类的报表符号
    '''
    for item in getleaveitem():
        if item.LeaveID==leaveid:
           return item.ReportSymbol
    return ''


def getleaveCalcUnit(leaveid):
    '''
    获取假类的计算单位
    '''
    for item in getleaveitem():
        if item.LeaveID==leaveid:
           return item.Unit,item.MinUnit,item.RemaindProc
    return 1,1,0