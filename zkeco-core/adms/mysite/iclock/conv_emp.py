# coding=utf-8
from django.conf import settings
import datetime
from models import  Template
from mysite.personnel.models.model_emp import Employee,format_pin
from dataprocaction import append_dev_cmd
from django.core.exceptions import ObjectDoesNotExist

def line_to_emp(cursor, device, line, Op,event=True):
    '''
    解析设备命令    
    line：设备post过来的命令字符串
    device：传送命令的设备
    '''
    from mysite import settings
    import os
    try:    #---行数据以空格分割标志名和键值对数据
        if line.find("\tName=") > 0:
            ops = unicode(line.decode("gb18030")).split(" ", 1)
        else:
            ops = line.split(" ", 1)
    except:
        ops = line.split(" ", 1)

    if ops[0] == 'OPLOG':   #-------------管理员操作记录        ops[0] 为标志名
        from conv_device import line_to_oplog
        return line_to_oplog(cursor, device, ops[1], event)
    
    flds = {};  #-----------行数据中包含的所以键值对
    for item in ops[1].split("\t"):
        index = item.find("=")
        if index > 0: flds[item[:index]] = item[index + 1:]
        
    try:
        pin = str(int(flds["PIN"])) #---得到用户编号
        if int(pin) in settings.DISABLED_PINS or len(pin)>settings.PIN_WIDTH: #----用户编号有效性验证
            return
    except:
        return
    
    e = get_employee(pin, device)   #--- 得到命令对应的人员对象  必须有
    
    if str(ops[0]).strip() == "USER":   #----------用户基本信息
        try:
            ename = unicode(flds["Name"])[:40]
        except:
            ename = ' '
        passwd = flds.get("Passwd","")
        card = flds.get("Card", "")
        agrp = flds.get("Grp", "")
        tz = flds.get("TZ","")
        priv = flds.get('Pri', 0)
        fldNames = ['SN', 'utime']
        values = [device.id, str(datetime.datetime.now())[:19]]
        if ename and (ename != e.EName):
            fldNames.append('name')
            values.append(ename)
            e.EName = ename
        if passwd and (passwd != e.Password):
            fldNames.append('password')
            values.append(passwd)
            e.Password = passwd
        if priv != e.Privilege:
            fldNames.append('privilege')
            values.append(priv)
            e.Privilege = priv
        if card and (card_to_num(card) != e.Card):
            if str(card_to_num(card)).strip()!="0":
                vcard=card_to_num(card)
            else:
                vcard=""
            fldNames.append('Card')
            values.append(vcard)
            e.Card = vcard
        if agrp != e.AccGroup:
            fldNames.append('AccGroup')
            values.append(agrp)
            e.AccGroup = agrp
        if tz != e.TimeZones:
            fldNames.append('TimeZones')
            values.append(tz)
            e.TimeZones = tz
        try:
            e.IsNewEmp
        except:
            e.IsNewEmp = False
        if e.IsNewEmp:    #新增用户
            e.IsNewEmp = False     
            e.DeptID_id=1       
            e.attarea=(device.area,)
            e.save()
            devs=set(e.search_device_byuser()) 
            if devs:
                try:
                    devs.remove(device)
                except:
                    pass
            for dev in devs:
                dev.set_user([e], Op,"")
                dev.set_user_fingerprint([e], Op)
                time.sleep(0.01)    
            sql = ''
        elif len(fldNames) > 2: #有新的用户信息
            devs=set(e.search_device_byuser()) 
            e.save()
            if devs:
                try:
                    devs.remove(device)
                except:
                    pass
            for dev in devs:
                dev.set_user([e], Op,"")
                dev.set_user_fingerprint([e], Op)
                time.sleep(0.01)
        else:
            pass
        return e
    
    elif str(ops[0]).strip() == "FP":   #----------------用户的指纹模板
        if e.IsNewEmp:    #新增用户               
            e.DeptID_id=1       
            e.attarea=(device.area,)
            e.save()
        emps=e
        try:
            size=flds["Size"]            
            fp = flds["TMP"]    
            d_len=len(fp.decode("base64"))
            if fp and (len(fp)==int(size) or d_len==int(size) ):
                devs=set(e.search_device_byuser())
                if devs:
                    try:
                        devs.remove(device)
                    except:
                        pass
                e = Template.objects.filter(UserID=e.id, FingerID=int(flds["FID"]),Fpversion=device.Fpversion)
                if len(e)>0:
                    e=e[0]
                    if fp[:100] == e.Template[:100]:
                        pass # Template is same
                    else:                        #指纹有修改
                        e.Template=fp
                        e.Fpversion=device.Fpversion
                        e.UTime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        e.save()
                        for dev in devs:
                            dev.set_user_fingerprint([emps], Op, int(flds["FID"]))
                            time.sleep(0.01)
                else:     #新增指纹
                    e=Template()
                    e.UserID=emps
                    e.Template=fp
                    e.UTime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    e.FingerID=int(flds["FID"])
                    e.Fpversion=device.Fpversion
                    e.Valid=1
                    e.save()
                    for dev in devs:
                        dev.set_user_fingerprint([emps], Op, int(flds["FID"]))
                        time.sleep(0.01)
                return True
            else:
                print "size:%s   TMP size:%s"%(size,len(fp))
                print "template length error"
        except:
            import traceback; traceback.print_exc();            
        else:
            return False
        
def cdata_get_pin(request, device):
    '''
    请求中 带人员PIN参数时的处理 返回人员基本信息和指纹模板信息 
    涉及 http参数：pin、save 
    '''
    resp=""
    #---是否保存  设备请求参数"save"
    save = request.REQUEST.has_key('save') and (request.REQUEST['save'] in ['1', 'Y', 'y', 'yes', 'YES']) or False
    try:    #---根据人员PIN得到人员对象
        pin = request.REQUEST['PIN']
        emp = Employee.objects.get(PIN=format_pin(pin))
    except ObjectDoesNotExist:
        resp += "NONE"
    else:
        #---人员信息数据
        cc = u"DATA USER PIN=%s\tName=%s\tPasswd=%s\tGrp=%d\tCard=%s\tTZ=%s\tPri=%s\n" % (emp.pin(), emp.EName or "", emp.Password or "", emp.AccGroup or 1, get_normal_card(emp.Card), emp.TimeZones or "", save and emp.Privilege or 0)
        for fp in Template.objects.filter(UserID=emp):
            try:
                #---人员指纹信息
                cc += u"DATA FP PIN=%s\tFID=%d\tTMP=%s\n" % (emp.pin(), fp.FingerID, fp.temp())
            except:pass
        try:
            resp += cc.encode("gb18030")
        except:
            resp += cc.decode("utf-8").encode("gb18030")
        if not save:    #---如果没有请求参数"save"
            endTime = datetime.datetime.now() + datetime.timedelta(0, 5 * 60)
            append_dev_cmd(device, "DATA DEL_USER PIN=%s" % emp.pin(), None, endTime)   #---保存设备删除用户请求记录
    return resp
