# coding=utf-8

#获取考勤计算项    
def getcalcitem():
    from mysite.att.models.model_leaveclass1 import LeaveClass1
    calcitem=LeaveClass1.objects.all().order_by('LeaveID')
    return calcitem

def get_item_content():
    '''
    计算项目信息整理
    '''
    from mysite.att.models.model_leaveclass1 import LeaveClass1
    calcitem=LeaveClass1.objects.all().order_by('LeaveID')
    itemcontent=[]
    for item in calcitem:
       if item.LeaveID in [1000,1001,1002,1003,1004,1005,1008,1009,1013]:
          tempitem={'MinUnit':item.MinUnit,'Unit':item.Unit,'RemaindProc':item.RemaindProc,'ReportSymbol':item.ReportSymbol}
          itemcontent.append(tempitem)        