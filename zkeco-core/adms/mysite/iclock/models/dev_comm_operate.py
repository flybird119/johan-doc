# -*- coding: utf-8 -*-
#! /usr/bin/env python
import datetime
from traceback import print_exc
from base.middleware.threadlocals import get_current_user
from mysite.iclock.models.model_device import Device, DEVICE_ACCESS_CONTROL_PANEL
from mysite.iclock.models.model_devoperate import OperateCmd

def Get_Author():
    auth=get_current_user()
    if auth and auth.is_anonymous(): auth=None
    return auth

def save_operate_cmd(cmd_content):
    try:
        Op=OperateCmd(Author=Get_Author(), CmdContent=cmd_content, CmdCommitTime=datetime.datetime.now())
        Op.save(force_insert=True)
    except:
        print_exc()
        Op=None 
    return Op

def sync_delete_all_data(dev_obj):
    dev_obj.delete_all_data(save_operate_cmd("DATA DELETE ALL"))

def sync_set_all_data(dev_obj):
    dev_obj.set_all_data(save_operate_cmd("DATA UPDATE all"))

def sync_set_door_options(door_obj):
    door_obj.device.set_dooroptions(save_operate_cmd("DATA UPDATE options"), [door_obj])
 
def sync_set_output(doorobj, addr, state):
    return doorobj.device.set_device_state(doorobj.door_no, addr, state, save_operate_cmd("DATA SET output")) 

def sync_cancel_alarm(dev_obj):#取消报警
    return dev_obj.cancel_alarm(save_operate_cmd("DATA SET output"))

def sync_control_no(doorobj, state):#控制常开时间段
    return doorobj.device.control_door_no(doorobj.door_no, state, save_operate_cmd("DATA SET output"))

def sync_get_input(doorobj, addr):
    return doorobj.device.get_device_state(doorobj.door_no, addr, save_operate_cmd("DATA GET input")) 

def sync_acctimeseg(timeseg_obj):
    Devset=Device.objects.filter(device_type=DEVICE_ACCESS_CONTROL_PANEL)
    for dev in Devset:
        dev.set_data("timezone", [timeseg_obj], save_operate_cmd("DATA UPDATE timezone"))

def sync_accholiday():
    Devset=Device.objects.filter(device_type=DEVICE_ACCESS_CONTROL_PANEL)
    for dev in Devset:
        dev.set_holiday(save_operate_cmd("DATA UPDATE holiday"))

def sync_set_define_io(define_obj):
    define_obj.device.set_define_io(save_operate_cmd("DATA UPDATE defineio"), define_obj)

def sync_delete_define_io(define_obj):
    define_obj.device.delete_define_io(save_operate_cmd("DATA DELETE defineio"), define_obj)

def sync_set_antipassback(device):
    device.set_antipassback(save_operate_cmd("DATA SET antipassback"))
    
def sync_clear_antipassback(device):
    device.clear_antipassback(save_operate_cmd("DATA DELETE antipassback"))

def sync_set_interlock(device):
    device.set_interlock(save_operate_cmd("DATA SET interlock"))

def sync_clear_interlock(device):
    device.clear_interlock(save_operate_cmd("DATA DELETE interlock"))
    
def sync_set_userinfo(devset, empset):
    Op=save_operate_cmd("DATA SET user")
    for dev in devset:
        dev.set_user(empset, Op, "")

def sync_set_user(devset, empset, session_key=""):  #session_key进度条使用
    Op=save_operate_cmd("DATA SET user")
    for dev in devset:
        dev.set_user(empset, Op, session_key)
        dev.set_user_fingerprint(empset, Op)
        
def sync_set_user_fingerprint(devset, empset,FID=""):   #修改可以下载指定指纹到设备
    Op=save_operate_cmd("DATA SET fingerprint")
    for dev in devset:
        dev.set_user_fingerprint(empset, Op,FID)
    
def sync_delete_user(devset, empset):
    Op=save_operate_cmd("DATA DELETE user")
    for dev in devset:
        dev.delete_user(empset, Op)
        dev.delete_user_privilege(empset, Op)

def sync_delete_user_finger(devset, table, empfp):
    Op = save_operate_cmd("DATA DELETE userfinger")
    for dev in devset:
        dev.delete_user_finger(table, empfp, Op)


def sync_set_user_privilege(devset, empset, session_key=""):
    Op=save_operate_cmd("DATA SET userauthorize")
    for dev in devset:
        dev.set_user_privilege(empset, Op, session_key)

def sync_delete_user_privilege(devset, empset):
    Op=save_operate_cmd("DATA DELETE userauthorize")
    for dev in devset:
        dev.delete_user_privilege(empset, Op)

def sync_set_firstcard(door):
    door.device.set_firstcard(save_operate_cmd("DATA SET firstcard"), door)

def sync_delete_firstcard(door):
    door.device.delete_firstcard(save_operate_cmd("DATA DELETE firstcard"), door)

def sync_del_multicard(morecard):
    morecard.door.device.del_multicard(save_operate_cmd("DATA DELETE multicard"), morecard.door)

def sync_set_multicard(morecard):
    morecard.door.device.set_multicard(save_operate_cmd("DATA SET multicard"), morecard.door)