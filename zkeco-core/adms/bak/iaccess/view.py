#! /usr/bin/env python
#coding=utf-8
from django.http import HttpResponse
from dbapp.utils import getJSResponse
from django.contrib.auth.decorators import login_required
from django.utils.encoding import smart_str
from models import AccFirstOpen, AccMoreCardSet, AccLevelSet, AccMoreCardGroup, AccDoor
from mysite.iclock.iutils import dumps
from mysite.personnel.models import Employee, Department, AccMoreCardEmpGroup
from mysite.iclock.models.model_device import Device, COMMU_MODE_PULL_RS485, ACPANEL_4_DOOR
from mysite.personnel.models import Area
from mysite.iaccess.devcomm import TDevComm
from mysite.iclock.models.dev_comm_operate import sync_set_firstcard, sync_delete_user_privilege, sync_set_user_privilege, sync_set_userinfo, sync_set_output, sync_control_no
from traceback import print_exc
from ctypes import *
from django.utils import simplejson 
import time
from base.cached_model import SAVETYPE_NEW,SAVETYPE_EDIT
from dbapp.datautils import filterdata_by_user
from django.utils.translation import ugettext_lazy as _
from django.db import connection

#检查表AccDevice,该表只在第一次连接成功后写入参数（部分默认值除外）
#devcom:设备连接类的对象
#该函数为设备连接成功后的回调函数
from django.conf import settings
db_type = settings.DATABASES["default"]["ENGINE"];
def check_acpanel_args(dev, devcomm, save=True):#dev.comm
    qret = devcomm.get_options("~SerialNumber,FirmVer,~DeviceName,LockCount,ReaderCount,AuxInCount,AuxOutCount,MachineType,~IsOnlyRFMachine,~MaxUserCount,~MaxAttLogCount,~MaxUserFingerCount,MThreshold")
    if qret["result"] == 0:#等于0即成功获取到数据
        try:
            datdic = {}
            optlist = qret["data"].split(',')
            for opt in optlist:
                opt1=opt.split('=')
                datdic[opt1[0]] = opt1[1] or None
            #print "dic=",datdic
            #print "dev.accdevice=",dev.devobj.accdevice.door_count
            if save and not dev.devobj.accdevice.door_count:#添加设备时accdevice以及其他参数没有写入
                #print "repeat save dev option"
                if dev.devobj.acpanel_type == int(datdic['LockCount']):
                    dev.devobj.sn = datdic['~SerialNumber']
                    dev.devobj.fw_version = datdic['FirmVer']
                    dev.devobj.device_name = datdic['~DeviceName']
                    #新增获取三个容量参数--add by darcy 20101122
                    #dev.devobj.max_user_count = datdic.has_key("~MaxUserCount") and int(datdic["~MaxUserCount"])*100 or 0   
                    #dev.devobj.max_attlog_count = datdic.has_key("~MaxAttLogCount") and int(datdic["~MaxAttLogCount"])*10000 or 0
                    #dev.devobj.max_finger_count = datdic.has_key("~MaxUserFingerCount") and int(datdic["~MaxUserFingerCount"]) or 0 
                    dev.devobj.fp_mthreshold = datdic.has_key("MThreshold") and int(datdic["MThreshold"]) or 0 
                    dev.devobj.save(force_update=True)
                    
                    dev.devobj.accdevice.door_count = int(datdic['LockCount'])
                    dev.devobj.accdevice.reader_count = int(datdic['ReaderCount'])
                    dev.devobj.accdevice.aux_in_count = int(datdic['AuxInCount'])
                    dev.devobj.accdevice.aux_out_count = int(datdic['AuxOutCount'])
                    dev.devobj.accdevice.machine_type = int(datdic['MachineType'])
                    dev.devobj.accdevice.IsOnlyRFMachine = int(datdic['~IsOnlyRFMachine'])

                    dev.devobj.accdevice.save(force_update=True)
                else:
                    dev.devobj.enabled = False
                    dev.devobj.save(force_update=True, log_msg=_(u"控制器类型错误，设备被禁用"))
            elif dev.devobj.fw_version != datdic['FirmVer']:#主要用于升级固件后重新获取固件版本号
                dev.devobj.fw_version = datdic['FirmVer']
                try:
                    dev.devobj.save(force_update=True)
                except:
                    print_exc()
        except:
            print_exc()

#获取数据返回给前端
@login_required
def get_data(request):
    fun_mode = request.REQUEST.get("func", "")

    #获取已有的权限组
    if fun_mode == "level":
        key = request.REQUEST.get("key", 0)#当前的人id（only one）
        qs = AccLevelSet.limit_acclevelset_to(AccLevelSet(), AccLevelSet.objects.all(),request.user)#根据用户权限中的区域和部门过滤
        #print '---qs=',qs
        objs = qs.exclude(emp=int(key)).order_by('id').values_list('id','level_name')
        #print '--------objs=',objs
        return getJSResponse(smart_str(dumps([obj for obj in objs])))

    #特定人所属的权限组
    if fun_mode == "selected_level":
        key = request.REQUEST.get("key", "")#单个对象操作时才会默认已选择的权限组(多个getlist)
        #objs = AccLevelSet.objects.filter(emp = key).values('id')
        objs = AccLevelSet.objects.filter(emp__PIN = key).values('id')
        return getJSResponse(smart_str(dumps([item["id"] for item in objs])))

    #特定权限组或者多卡开门人员组已经选中的人
    if fun_mode == "selected_emp":
        type = request.REQUEST.get("type", "")
        key = request.REQUEST.get("key", "")#单个对象操作时才会默认已选择的人(多个getlist)
        if type == "acclevelset":
            objs = Employee.objects.filter(acclevelset=key)
        elif type == "accmorecardempgroup":
            objs = Employee.objects.filter(morecard_group=key)
        objs = objs.values_list('id', 'PIN', 'EName', 'DeptID', 'Gender', 'Title')
        results = []
        for obj in objs:
            dept = unicode(Department.objects.get(pk = obj[3])) #获取的数据中置换掉部门id
            list_obj = list(obj)
            list_obj.append(dept)
            results.append(tuple(list_obj))
        return getJSResponse(smart_str(dumps([result for result in results])))

    #获取多卡开门人员组列表
    if fun_mode == "morecardempgroup":
        user = request.user
        da = user.deptadmin_set.all()
        limit_empgroups = []#所有有效的多卡开门人员组（即有效人所属的组）
        empgroups_all = AccMoreCardEmpGroup.objects.all()#所有多卡开 门人员组
        if not user.is_superuser and da:#非超级用户如果a不为空则默认全部区域
            d_limit = [int(d.dept_id) for d in da]
            emps = Employee.objects.filter(DeptID__in=d_limit)#范围内的人
            for emp in emps:
                group = emp.morecard_group
                if group:
                    limit_empgroups.append(group)
            null_empgroups = empgroups_all.filter(employee__isnull=True)
            for ne in null_empgroups:
                limit_empgroups.append(ne)
            limit_empgroups = empgroups_all.filter(pk__in=[e.pk for e in limit_empgroups])
                
            #d_limit = [int(d.dept_id) for d in da]
            #emps = Employee.objects.exclude(DeptID__in=d_limit)
            #print '-----emps=',emps
            #limit_empgroups = limit_empgroups.exclude(employee__in=emps)
        if not limit_empgroups:#超级用户
            limit_empgroups = empgroups_all
        
        empgroup_objs = limit_empgroups.order_by('id').values_list("id","group_name")
        key = request.GET.get("key", 0)#key=0表示新增(新增时返回组名称，number均为0),key!=0表示编辑
        
        selected_morecardgroup = AccMoreCardGroup.objects.filter(comb=key)
        
        #print selected_morecardgroup

        list_group =  [s.group_id for s in selected_morecardgroup]
        list_number = [s.opener_number for s in selected_morecardgroup]

        results = []
        for obj in empgroup_objs:
            list_obj = list(obj)
            #加入用户设置的人数
            if list_obj[0] in list_group:#如果是编辑，那么对应组的人数返回
                list_obj.append(list_number[list_group.index(list_obj[0])])
            else:#否则添加0
                list_obj.append(0)
            #加入当前组内的实际人数
            cur_obj = AccMoreCardEmpGroup.objects.filter(pk=list_obj[0])
            list_obj.append(cur_obj and cur_obj[0].employee_set.count() or 0)
            results.append(tuple(list_obj))
        return getJSResponse(smart_str(dumps([obj for obj in results])))

    #获取人事表中已经分配多卡开门人员组的人的id
    if fun_mode == "emps_have_morecardgroup":
        emps = Employee.objects.filter(morecard_group__in = [group.id for group in AccMoreCardEmpGroup.objects.all()])
        return HttpResponse(smart_str({'emps_id_list': [emp.id for emp in emps]}))

    #获取数据库中当前所有的门
    if fun_mode == "doors":
        type = request.GET.get("type", "")
        u = request.user
        aa = u.areaadmin_set.all()
        a_limit = aa and [int(a.area_id) for a in aa] or [int(area.pk) for area in Area.objects.all()]#非超级管理员且没有配置有效区域（默认全部）的有效区域id列表（即用户手动配置过用户区域的）
        
        if type == 'all':
            areas = Area.objects.filter(pk__in=a_limit).order_by('id').values_list('id', 'areaname')
            devices = Device.objects.filter(area__pk__in=a_limit).filter(device_type=2).order_by('id').values_list('id', 'alias')
            doors = AccDoor.objects.filter(device__area__pk__in=a_limit).order_by('id').values_list('id', 'device__alias', 'door_no', 'door_name')
            
            #print 'doors=',doors
            doors = [door for door in doors]
            #print 'doors=',doors
            return getJSResponse(smart_str(simplejson.dumps({ 'type': 'all', 'doors': doors, 'areas': [area for area in areas], 'devices': [device for device in devices] })))
        
        if type == 'area':
            area_id = int(request.GET.get("area_id", 0))
            #print 'area_id=',area_id

            if area_id:
                area_ids = [area_id] + [a.id for a in Area.objects.get(id=area_id).area_set.all()]#处理区域的上下级
                area_ids = [ai for ai in area_ids if ai in a_limit]#权限过滤
                dev_list = Device.objects.filter(area__in=area_ids)
                devs = dev_list.order_by('id').values_list('id', 'alias')
                dev_list_id = [d.id for d in dev_list]
                doors_objs = dev_list and AccDoor.objects.filter(device__in=dev_list_id) or []
            else:#0,取权限范围内全部的
                devs = Device.objects.filter(area__pk__in=a_limit).filter(device_type=2).order_by('id').values_list('id', 'alias')
                doors_objs = AccDoor.objects.filter(device__area__pk__in=a_limit)

            #print 'doors_objs=',doors_objs
            doors = doors_objs and doors_objs.order_by('id').values_list('id', 'device__alias', 'door_no', 'door_name') or []
            #print 'doors=',doors
            return getJSResponse(smart_str(simplejson.dumps({ 'type': 'area', 'doors': [door for door in doors], 'areas': '', 'devices': [dev for dev in devs] })))            

        if type == 'device':
            device_id = request.GET.get("device_id", 0)
            doors_objs = device_id and AccDoor.objects.filter(device__area__pk__in=a_limit).filter(device=int(device_id)) or AccDoor.objects.filter(device__area__pk__in=a_limit)
            doors = doors_objs.order_by('id').values_list('id', 'device__alias', 'door_no', 'door_name')
            return getJSResponse(smart_str(simplejson.dumps({ 'type': 'device', 'doors': [door for door in doors], 'areas': '', 'devices': '' })))            

        if type == 'door':
            door_id = request.GET.get("door_id", 0)
            doors_objs = door_id and AccDoor.objects.filter(device__area__pk__in=a_limit).filter(id=int(door_id)) or AccDoor.objects.filter(device__area__pk__in=a_limit)
            doors = doors_objs.order_by('id').values_list('id', 'device__alias', 'door_no', 'door_name')
            return getJSResponse(smart_str(simplejson.dumps({ 'type': 'door', 'doors': [door for door in doors], 'areas': '', 'devices': '' })))            

#    #检查当前控制器下属们的数量及门编号、门名称
#    if fun_mode == "device_doors_info":
#        device_id = int(request.GET.get("device_id", 0))#肯定不为0
#        dev_obj = Device.objects.filter(pk=device_id)
#        #if dev_obj:
#        doors_count = dev_obj[0].acpanel_type
#        doors_name = dev_obj[0].accdoor_set.order_by('id').values_list('door_no','door_name')
#        return HttpResponse(smart_str(simplejson.dumps({'doors_name': list(doors_name), 'doors_count': int(doors_count)})))#因acpanel-type null=true所以一定不为None

    #返回设备参数表中的信息（需已连接的设备才有，否则返回0）联动设置时调用 检查当前控制器下属们的数量及门编号、门名称
    if fun_mode == "machine_args":
        device_id = request.GET.get("device_id", 0)
        dev = Device.objects.filter(id=int(device_id))
        #dev = device and device[0] or None
        doors_name = dev[0].accdoor_set.order_by('id').values_list('door_no','door_name')

        try:
            count = dev[0].accdevice.door_count
            door_count = count and int(count) or 0 #如果没有连接成功过为0or obj.acpanel_type
            r_count = dev[0].accdevice.reader_count
            reader_count = r_count and int(r_count) or 0
            inc = dev[0].accdevice.aux_in_count
            in_count = inc and int(inc) or 0 #默认为4,0说明设备没有连接成功过
            outc = dev[0].accdevice.aux_out_count
            out_count = outc and int(outc) or 0 #注释同上
            m_type = dev[0].accdevice.machine_type
            machine_type = m_type and int(m_type) or 0 
        except:#因为异常导致设备参数表没有生成dev.accdevice
            door_count = -1
            reader_count = -1
            in_count = -1
            out_count = -1

        return HttpResponse(smart_str(simplejson.dumps({'doors_name': list(doors_name), 'door_count': door_count, 'reader_count': reader_count, 'in_count': in_count, 'out_count': out_count, 'machine_type': machine_type})))
    
    #用于新增门禁控制器时与设备连接获取机器的options
    if fun_mode == "connect_dev":
        comm_type = int(request.GET.get("comm_type", "0"))
        comm_pwd = request.GET.get("comm_pwd", "")#最多16位字符串  未加密
        device_sn = request.GET.get("device_sn", "")
        ip = request.GET.get("ip", "")
        ip_port = int(request.GET.get("ip_port", '4370'))
        com_address = int(request.GET.get("com_address", '1'))
        com_port = int(request.GET.get("com_port", '1'))
        baudrate = request.GET.get("baudrate", "38400")
        acpanel_type = int(request.GET.get("acpanel_type", '0'))#1 2 4
        four_to_two = request.GET.get("four_to_two", "")
        comminfo = {
            'sn': device_sn,
            'comm_type': comm_type,
            'ipaddress': ip,
            'ip_port': ip_port,
            'com_port': "COM" + str(com_port),
            'com_address': com_address,
            'baudrate': baudrate,
            'password': comm_pwd,
        }     
        #print comminfo   
        devcom = TDevComm(comminfo)
        if comm_type == COMMU_MODE_PULL_RS485:
            tmp_dev = Device.objects.filter(com_port=com_port, com_address=com_address)
            if tmp_dev:#该串口已存在相同485地址的设备
                return HttpResponse(smart_str({"result": '485repeat', "data": ""}))    
                       
            from dev_comm_center import wait_com_pause
            if wait_com_pause(com_port, 60) == False: #等待后台停止进程
                return HttpResponse(smart_str({"result": '485busy', "data": ""}))
            
        try:
            cret = devcom.connect()
        except:
            if comm_type == COMMU_MODE_PULL_RS485:
                from dev_comm_center import set_comm_run
                set_comm_run(com_port) #后台进程继续
                return #以下不执行，前端直接显示-615错误
            
        #print cret
        if cret["result"] > 0:#连接成功
            ret = {}
            if acpanel_type == ACPANEL_4_DOOR:#仅限前端显示了四门控制器之后
                switch = int(devcom.get_options("Door4ToDoor2")['data'].split("=")[1])
                if four_to_two == 'true':#切换为两门双向
                    if switch == 0:
                        ret = devcom.set_options("Door4ToDoor2=1")
                        ret = devcom.reboot()#大概需要10-15s
                        time.sleep(12)
                        devcom.disconnect()
                        cret = devcom.connect()#重连

                else:#不切换，如果是两门双向则改回四门单向
                    if switch == 1:
                        ret = devcom.set_options("Door4ToDoor2=0")
                        ret = devcom.reboot()
                        time.sleep(12)
                        devcom.disconnect()
                        cret = devcom.connect()
  
            #print '---ret=',ret
            
            if (ret and ret["result"] >= 0) or not ret: # or not ret:#four_to_two设置成功或者未设置four_to_two
                qret = devcom.get_options("~SerialNumber,FirmVer,~DeviceName,LockCount,ReaderCount,AuxInCount,AuxOutCount,MachineType,~IsOnlyRFMachine,~MaxUserCount,~MaxAttLogCount,~MaxUserFingerCount,~ZKFPVersion")
                if qret["result"] >= 0:
                    try:
                        datdic = {}
                        optlist = qret["data"].split(',')
                        for opt in optlist:
                            opt1 = opt.split('=')
                            datdic[opt1[0]] = opt1[1]
                        #print "dic=", datdic
                    except:
                        print_exc()
                        
            devcom.disconnect()
            if comm_type == COMMU_MODE_PULL_RS485:
                from dev_comm_center import set_comm_run
                set_comm_run(com_port) #后台进程继续
                
            return HttpResponse(smart_str({"result": cret["result"], "data": datdic}))#返回获取的控制器参数，用于前端判断
        else:#连接失败
            from mysite.iaccess.dev_comm_center import DEVICE_COMMAND_RETURN
            try:
#                if cret["result"] == 0:
#                    cret["result"] = -99#未知错误
                reason = unicode(dict(DEVICE_COMMAND_RETURN)[str(cret["result"])])
            except:
                print_exc()
                reason = ""
            if comm_type == COMMU_MODE_PULL_RS485:
                from dev_comm_center import set_comm_run
                set_comm_run(com_port) #后台进程继续
            return HttpResponse(smart_str(simplejson.dumps({"result": cret["result"], "reason": reason, "data": ""})))

    #首卡开门、多卡开门等获取当前门名称
    if fun_mode == "get_doorname":
        door_id = request.GET.get("door_id", 0)
        #print '----door_id=',door_id
        door_name = AccDoor.objects.filter(id=int(door_id))[0].door_name

        #return getJSResponse(door_name) simplejson.dumps
        return getJSResponse(smart_str(simplejson.dumps(door_name)))
        #return getJSResponse(smart_str({ 'name':door_name })) 

    #获取当前数据库中存在的ip地址和序列号。用于搜索控制器时用ip地址以及显示已经新增过的设备做判断
    if fun_mode == "get_all_ip_sn":
        devs = Device.objects.all()
        return HttpResponse(smart_str(simplejson.dumps({ 'ipaddress': [d.ipaddress for d in devs if d.ipaddress], 'sn': [d.sn for d in devs if d.sn]})))

    #获取当前AccLinkageIO中的输入输出信息的选项，避免之前前端也需要维护该信息情况出现
    if fun_mode == "linkageio_info":
        from models.acclinkageio import INADDRESS_CHOICES, OUTADDRESS_CHOICES, DISABLED_TRIGGEROPT_CHOICES
        from models.accmonitorlog import EVENT_CHOICES
        in_info = dict(INADDRESS_CHOICES)
        out_info = dict(OUTADDRESS_CHOICES)
        event_info = dict(EVENT_CHOICES)

        for ini in in_info.keys():
            in_info[ini] = unicode(in_info[ini])
        for outi in out_info.keys():
            out_info[outi] = unicode(out_info[outi])
        for eventi in event_info.keys():
            if eventi not in DISABLED_TRIGGEROPT_CHOICES:
                event_info[eventi] = unicode(event_info[eventi])
            else:
                event_info.pop(eventi)
        return HttpResponse(smart_str(simplejson.dumps({'in_info': in_info, 'out_info': out_info, 'event_info': event_info})))
    
    #获取设备的辅助输出点信息（用于关闭辅助输出点）
    if fun_mode == "get_device_auxout":
        dev_id = int(request.REQUEST.get("dev_id", 0))
        devs = Device.objects.filter(pk=dev_id)
        
        if devs:           
            from models.acclinkageio import get_device_auxout            
            return HttpResponse(smart_str(simplejson.dumps({"auxout_info": get_device_auxout(devs[0])})))        #else 如果不存在前端执行error
        
    if fun_mode == 'get_doors_tree':#just like acclevelset
        from dbapp.widgets import queryset_render_multiple
        u = request.user
        aa = u.areaadmin_set.all()
        if u.is_superuser or not aa:#为超级管理员或者没有配置区域（默认全部区域）
           doors = AccDoor.objects.all()
        else:
           areas = [a.area for a in aa]
           doors = AccDoor.objects.filter(device__area__in=areas)

        tree_html = queryset_render_multiple(doors, 'door', "class='wZBaseZManyToManyField' name='door' id='id_door'", None, 'id_door', parent=None)
        return HttpResponse(tree_html)

#该方法主要用于远程开关门（包括开部分门)               废弃：开所有门）
@login_required
def send_doors_data(request):
    fun_mode = request.GET.get("func", "")
    type = request.GET.get("type", "")
    door = request.GET.get("data", "")
    
    if type == 'part':
        doors = AccDoor.objects.filter(id__in=door.split(','))
            
    datas = []
    if fun_mode in ["cancelalarm", "cancelall"]:#单个门对应控制器的取消报警
        devs = Device.objects.filter(accdoor__in=doors)#sure to exist
        for dev in devs:
            ret = dev.cancel_alarm()#>=0成功，否则失败  None??????????????//////
            datas.append({ "device_name": dev.alias, "ret": ret == None and -1 or ret })
        return getJSResponse(smart_str(simplejson.dumps({'result': datas})))
    elif fun_mode in ["opendoor", "openpart"]:#, "openall"]:
        interval = request.GET.get("open_interval", 0)#1-254
        enable = request.GET.get("enable_no_tzs", False)
        #print '----------interval=',interval
        #print '------enable=',enable
        if enable == "true":#仅启用常开时间段，不开门
            for door_obj in doors:
                ret = sync_control_no(door_obj, 1)#重新启用常开时间段
                #ret = sync_set_output(door_obj, 1, int(interval))#ret为None代表固件没有返回值，成功还是失败？  door_obj.lock_delay
                datas.append({ "door_name": door_obj.door_name, "ret": ret == None and -1 or ret })
        else:
            for door_obj in doors:
                ret = sync_set_output(door_obj, 1, int(interval))#ret为None代表固件没有返回值，成功还是失败？  door_obj.lock_delay
                datas.append({ "door_name": door_obj.door_name, "ret": ret == None and -1 or ret })
        return getJSResponse(smart_str(simplejson.dumps({'result': datas})))
    elif fun_mode in ["closedoor", "closepart"]:# "closeall",:
        disable = request.GET.get("disable_no_tzs", False)
        #print '----disable=',disable
        if disable == "true":
            for door_obj in doors:  
                ret = sync_control_no(door_obj, 0)#仅禁用门常开时间段              
                #ret = sync_set_output(door_obj, 1, 0)
                datas.append({ "door_name": door_obj.door_name, "ret": ret == None and -1 or ret}) 
        else:
            #print '---in'
            for door_obj in doors:  
                ret = sync_set_output(door_obj, 1, 0)
                datas.append({ "door_name": door_obj.door_name, "ret": ret == None and -1 or ret})        
        return getJSResponse(smart_str(simplejson.dumps({'result': datas})))

#取消报警（原确认报警）----all
@login_required
def cancel_alarm(request):
    data =request.GET.get("data", "")#前端已做了不能为空的判断,故正常情况下data！=''
    datas = []
    if data:
        #doors = set(data.split(','))#去掉重复的门id
        doors_ids = [int(d) for d in data.split(',')]
        devs = Device.objects.filter(accdoor__pk__in=door_ids)
        for dev in devs:
            ret = dev.cancel_alarm()
            datas.append({ "dev_name": dev.alias, "ret": ret == None and -1 or ret})
    return getJSResponse(smart_str(simplejson.dumps({'result': datas})))

@login_required
def search_acpanel(request):
    fun_mode = request.GET.get("func", '')

    #搜索门禁控制器
    #result为返回的条数（即设备数量）    
    if fun_mode == "search_tcpip":
        devcomm = TDevComm(None)
        #{'data': 'MAC=00:17:62:01:36:F7,IPAddress=192.168.1.226\r\n', 'result'
        ret = devcomm.SearchDevice()
        #print 'ret=',ret
        devs = ret['data'].split('\r\n', ret['result'])
        datas = []
        for dev in devs:
            data = {}
            if dev:
                arg = dev.split(',')
                #print arg
                for s in arg:
                    #print 's=',s
                    record = s.split('=')
                    #print 'record=',record
                    data[record[0]] = record[1] or ''
                datas.append(data)
        #print datas      
        #{'datas': [{'MAC': '00:17:62:01:36:F7', 'IPAddress': '192.168.1.226'}, {'MAC': '00:17:62:01:36:F7', 'IPAddress': '192.168.1.226'}, {'MAC': '(null)', 'IPAddress': '192.168.1.2052.168.1.226'}, {'MAC': '(null)', 'IPAddress': '192.168.1.2052.168.1.226'}]}
        return HttpResponse(smart_str({'datas': datas}))   
    
    #将控制器添加到设备表时检查该ip地址和sn是否已经存在
    if fun_mode == "check_and_save":
        ip = request.GET.get("ip", '')
        sn = request.GET.get("sn", '')
        alias = request.GET.get("alias", '')
        
        #先检测ip,后检测序列号,_existed 为1表示存在 0表示不存在
        ip_existed = 0
        sn_existed = 0
        if ip and ip in [d.ipaddress for d in [dev for dev in Device.objects.all()]]:
            ip_existed = 1#ip地址已存在
        #搜索上来的序列号不为空，故sn不为空，数据库中当前可能存在多个sn为空的记录
        if sn and sn in [d.sn for d in [dev for dev in Device.objects.all()]]:
            sn_existed = 1
            
        if not ip_existed and not sn_existed:#均不存在 可以保存
            #需先连接设备获取设备的参数
            comminfo = {
                'sn': sn,
                'comm_type': 1, #int(comm_type),1为tcp/ip 2为rs485
                'ipaddress': ip,
                'ip_port': 4370,
                'password': '',
            }     
            #print "comminfo====",comminfo   
            devcom = TDevComm(comminfo)
            cret = devcom.connect()
            if cret["result"] > 0:#连接成功
                qret = devcom.get_options("~SerialNumber,FirmVer,~DeviceName,LockCount,ReaderCount,AuxInCount,AuxOutCount,MachineType,~IsOnlyRFMachine,~MaxUserCount,~MaxAttLogCount,~MaxUserFingerCount,MThreshold,~ZKFPVersion")               
                devcom.disconnect()
                if qret["result"] >= 0:#有数据返回
                    datdic = {}
                    optlist = qret["data"].split(',')
                    for opt in optlist:
                        opt1 = opt.split('=')
                        #print "opt1===",opt1
                        #datdic[opt1[0]] = opt1[1] and int(opt1[1]) or None
                        datdic[opt1[0]] = opt1[1] #or 0#None
                    #print "dic=",datdic
                    try:
                        dev_obj = Device()
                        dev_obj.alias = alias#ip.split(".")[-1]#默认以ip地址一部分为alias
                        dev_obj.sn = datdic['~SerialNumber'] #or ''
                        dev_obj.Fpversion = datdic['~ZKFPVersion']
                        dev_obj.fw_version = datdic['FirmVer'] #or ''
                        dev_obj.device_name = datdic['~DeviceName'] #or ''
                        dev_obj.device_type = 2
                        dev_obj.ipaddress = ip
                        dev_obj.ip_port = 4370
                        dev_obj.comm_type = 1
                        dev_obj.comm_pwd = ""#默认通讯密码为空
                        dev_obj.acpanel_type = int(datdic['LockCount'])
                        #新增获取三个容量参数--add by darcy 20101122                        dev_obj.max_user_count = datdic.has_key("~MaxUserCount") and int(datdic["~MaxUserCount"])*100 or 0                        dev_obj.max_attlog_count = datdic.has_key("~MaxAttLogCount") and int(datdic["~MaxAttLogCount"])*10000 or 0                        dev_obj.max_finger_count = datdic.has_key("~MaxUserFingerCount") and int(datdic["~MaxUserFingerCount"]) or 0                        dev_obj.fp_mthreshold = datdic.has_key("MThreshold") and int(datdic["MThreshold"]) or 0                                                dev_obj.data_valid(SAVETYPE_NEW)#验证业务逻辑
                        aa = request.user.areaadmin_set.all()
                        if aa:#给用户设置过授权区域
                            dev_obj.area = aa[0].area
                        else:#没设置的话默认全部区域
                            dev_obj.area = Area.objects.get(pk=1)
                        dev_obj.save(force_insert=True)
                        from mysite.iclock.models.dev_comm_operate import sync_set_all_data
                        dev_obj.delete_transaction()
                        sync_set_all_data(dev_obj)
                    except Exception, e:
                        print_exc()
                        return HttpResponse(smart_str(simplejson.dumps({ "ret": -1, "reason": unicode(e) })))#添加设备失败
                    
                    try:
                        from mysite.iaccess.dev_comm_center import OPERAT_ADD    
                        dev_obj.add_comm_center(None, OPERAT_ADD)
                    except:
                        print_exc()
                        return HttpResponse(smart_str({ "ret": -5 }))#添加设备异常
                        
                    try:
                        #dev_obj.accdevice.machine_type = int(datdic['ACPanelFunOn'])
                        dev_obj.accdevice.door_count = int(datdic['LockCount'])
                        dev_obj.accdevice.reader_count = int(datdic['ReaderCount'])
                        dev_obj.accdevice.aux_in_count = int(datdic['AuxInCount'])
                        dev_obj.accdevice.aux_out_count = int(datdic['AuxOutCount'])
                        dev_obj.accdevice.machine_type = int(datdic['MachineType'])
                        dev_obj.accdevice.IsOnlyRFMachine = int(datdic['~IsOnlyRFMachine'])
                        dev_obj.accdevice.save(force_update=True)

                        return HttpResponse(smart_str({ "ret": 1, "result": qret["result"], "data": datdic }))#返回的字节数qret["result"]大于等于0
                    except:
                        print_exc()
                        return HttpResponse(smart_str({ "ret": -2, "result": qret["result"]}))#设备表保存成功，但是设备参数表保存失败，下次连接成功时将写入----是否存在？？
                else:#0
                    return HttpResponse(smart_str({ "ret": -3, "result": qret["result"]}))#无数据返回
               
            else:#连接失败
                from mysite.iaccess.dev_comm_center import DEVICE_COMMAND_RETURN
                try:
                    reason = unicode(dict(DEVICE_COMMAND_RETURN)[str(cret["result"])])
                except:
                    print_exc()
                    reason = ""
                return HttpResponse(smart_str(simplejson.dumps({ "ret": -4, "result": cret["result"], "reason": reason, "data": ""})))
        else:
              return HttpResponse(smart_str({'ret': 0, 'ip_existed':ip_existed, 'sn_existed':sn_existed }))#sn已存在
            
    #搜索控制器时tcp/ip通讯方式下修改搜索出来的设备的ip地址
    if fun_mode == "change_ip":
        newip = request.GET.get("newip", '')
        gateway = request.GET.get("gateway", "")
        subnet_mask = request.GET.get("subnet_mask", "")
        mac = request.GET.get("mac", '')
        #调用修改ip地址的接口---广播方式
        devcomm = TDevComm(None)
        cret = devcomm.ModifyIPAddress("MAC=%s,IPAddress=%s,GATEIPAddress=%s,NetMask=%s"%(mac, newip, gateway, subnet_mask))
        from mysite.iaccess.dev_comm_center import DEVICE_COMMAND_RETURN
        try:
        #  if cret["result"] == 0:
             # cret["result"] = -99#未知错误            
            reason = unicode(dict(DEVICE_COMMAND_RETURN)[str(cret["result"])])
        except:
            print_exc()
            reason = ""

        return HttpResponse(smart_str(simplejson.dumps({ 'ret': cret["result"], 'reason': reason })))#>=0success 小于0fail   0？


#处理人员门禁权限设置
@login_required
def emp_level_op(request):
    mode = request.GET.get("func", '')
    
    #删除某个权限组中某个或某些人员
    if mode == "level":
        level_id = request.GET.get("data", 0)
        emps = request.GET.get("emps" ,'')
        emps = emps.split(',')
        level = AccLevelSet.objects.filter(pk = int(level_id))
        level_obj = level and level[0] or None
        #level_obj实际不为空
        if level_obj:
            for e in emps:
                level_obj.emp.remove(int(e))
            dev=[]
            level_door=level_obj.door_group.all()
            for door in level_door:
                if door.device not in dev:
                    dev.append(door.device)
            emp_set=Employee.objects.filter(pk__in = emps)
            sync_delete_user_privilege(dev, emp_set)
            sync_set_user_privilege(dev, emp_set)
            return HttpResponse(smart_str({ 'ret': 1 }))
        else:
            return HttpResponse(smart_str({ 'ret': 0 }))
        
    #删除某个人员中某个或某些权限组
    if mode == "emp":
        emp = request.GET.get("data", 0)
        levels = request.GET.get("levels", '')
        levels = levels.split(',')
        emps = Employee.objects.filter(pk = int(emp))
        emp_obj = emps and emps[0] or None
        #emp_obj实际不为空
        #print levels
        if emp_obj:
            for level in levels:
                emp_obj.acclevelset_set.remove(int(level))
            level_set=emp_obj.acclevelset_set.filter(pk__in = levels)
            dev=[]
            for level in level_set:
                for door in level.door_group.all():
                    if door.device not in dev:
                        dev.append(door.device)
            sync_delete_user_privilege(dev, [emp_obj])
            sync_set_user_privilege(dev, [emp_obj])#删除设备权限后需重新同步设备人员权限
            return HttpResponse(smart_str({ 'ret': 1 }))
        else:
            return HttpResponse(smart_str({ 'ret': 0 }))

#多卡开门人员组中人的操作（删除）
@login_required
def mcegroup_emp_op(request):
    #删除某个组中某个或某些人员
    group_id = request.GET.get("data", 0)
    emps = request.GET.get("emps" ,'')
    emps = emps.split(',')

    group = AccMoreCardEmpGroup.objects.filter(pk = int(group_id))
    group_obj = group and group[0] or None
    #level_obj实际不为空
    emp_objs = Employee.objects.filter(pk__in = emps)
    if group_obj:
        for e in emp_objs:
            e.morecard_group = None
            e.save()
            #group_obj.employee_set.remove(e)
        devs = filterdata_by_user(Device.objects.all(), request.user)
        #print '---devs=',devs 
        sync_set_userinfo(devs, emp_objs)    
        return HttpResponse(smart_str({ 'ret': 1 }))
    else:
        return HttpResponse(smart_str({ 'ret': 0 }))

#首卡开门开门的人的操作（删除，不包括人本身）
@login_required
def fcopen_emp_op(request):
    level_id = request.GET.get("data", 0)
    emps = request.GET.get("emps" ,'')
    emps = emps.split(',')
    fo = AccFirstOpen.objects.filter(pk = int(level_id))
    fo_obj = fo and fo[0] or None
    #level_obj实际不为空
    if fo_obj:
        for e in emps:
            fo_obj.emp.remove(int(e))
        sync_set_firstcard(fo_obj.door)
        return HttpResponse(smart_str({ 'ret': 1 }))
    else:
        return HttpResponse(smart_str({ 'ret': 0 }))

#实时获取控制器中未注册的卡
@login_required
def get_card_number(request):
    from django.db import connection
    from django.utils.encoding import smart_str
    from django.utils.simplejson  import dumps 
    import datetime
    doors = request.REQUEST.get("doors")
    if not doors:
        return HttpResponse("")
    doors = doors.split("_")
    door_list = "("
    for i  in doors:
        door_list = door_list+i+','
    door_list = door_list[0:-1]
    door_list = door_list+")"
    log_id = request.REQUEST.get("log_id")
    time_now = request.REQUEST.get("time_now")
    cursor = connection.cursor()
    global db_type
    
    if log_id == 'undefined':
        if time_now == 'undefined':
            time_now = datetime.datetime.now()
            time_now = time_now.strftime("%Y-%m-%d %X")
        if db_type == "django.db.backends.postgresql_psycopg2":
            sql = """select id,card_no from acc_monitor_log where create_time>='%s' and event_type=27 and door_id in %s and card_no not in(select "Card" from userinfo)""" %(time_now, door_list)
        else:
            sql = """select id,card_no from acc_monitor_log where create_time>='%s' and event_type=27 and door_id in %s and card_no not in(select card from userinfo)""" %(time_now, door_list)    
    else:
        if db_type == "django.db.backends.postgresql_psycopg2":
            sql = """select id,card_no from acc_monitor_log where id>%s and event_type=27 and door_id in %s and card_no not in(select "Card" from userinfo)"""%(log_id, door_list)
        else:
            sql = """select id,card_no from acc_monitor_log where id>%s and event_type=27 and door_id in %s and card_no not in(select card from userinfo)"""%(log_id, door_list)
    cursor.execute(sql)
    li = cursor.fetchall()
    try:
        li.append(time_now)
    except:
        li=list(li).append(time_now)
    return HttpResponse(smart_str(dumps(li)))

#验证输入的旧密码是否正确
@login_required
def check_pwd(request):
    from base.crypt import encrypt
    try:
        old_pwd = request.POST.get("old_pwd")
        p_device = request.POST.get("device")
        p_door_no = request.POST.get("door_no")
        field = request.POST.get("field")
        if not p_door_no:  #通讯密码
            device = Device.objects.filter(id=p_device)
            old_pwd = encrypt(old_pwd)
            if device:
                if old_pwd == device[0].comm_pwd:
                    state = True
                else:
                    state = False
        else:
            acc_door = AccDoor.objects.filter(device=p_device,door_no=p_door_no)
            state = acc_door and acc_door[0].check_password(old_pwd,acc_door[0].__getattribute__(field)) or False
            
        if state == True:return HttpResponse("ok")
        else:return HttpResponse("error")
    except:
        import traceback
        traceback.print_exc()
        
    