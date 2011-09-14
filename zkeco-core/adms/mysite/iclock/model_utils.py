# coding=utf-8
from mysite.personnel.models.model_emp import Employee,format_pin
from models.model_devcmd import DevCmd
from django.core.exceptions import ObjectDoesNotExist
import datetime
def get_employee(pin, Device=None):
    '''
    根据给定员工PIN查找员工,若不存在就创建改PIN的员工
    '''
    s_pin = format_pin(pin)
    try:
        e=Employee.objects.get(PIN=s_pin)
        if e:
            e.IsNewEmp=False
            return e
        else:
            raise ObjectDoesNotExist
    except ObjectDoesNotExist:
        e = Employee(PIN=s_pin, EName=pin)
        e.save()
        e.IsNewEmp=True
        return e
    
def update_cmd(device, id, ret, q_server=None):
    try:
        cmdobj=DevCmd.objects.get(id=id)
    except ObjectDoesNotExist:
        return None
    if cmdobj.SN_id!=device.id: 
        print u"ERROR: 命令对应的设备与指定设备不一致(%s != %s)"%(cmdobj.SN_id, device.id)
        return None
    cmdobj.CmdOverTime=datetime.datetime.now()
    cmdobj.CmdReturn=ret
    cmdobj.save()
    cmdobj.SN=device
    return cmdobj

def update_cmds(device, rets):
    for id in rets:
        update_cmd(device, id, rets[id],None)