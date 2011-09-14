# -*- coding: utf-8 -*-
#! /usr/bin/env python
#
#设备通讯进程池
#
# Changelog :
#
# 2010.3.19 Zhang Honggen
#   create at zk park Dongguan

from multiprocessing import Pool, Process, Manager#pool tcp/ip---proess 485
import threading
import time
import datetime
from time import sleep, ctime 
from django.utils.translation import ugettext_lazy as _
from django.utils import simplejson
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.encoding import smart_str
from django.db import models, connection
import os, re
import redis
import dict4ini
from redis.server import queqe_server
from mysite.iaccess.devcomm import TDevComm
#from mysite.iaccess.video import TDevVideo
from mysite.iaccess.devcomm import *
from traceback import print_exc
from mysite.utils import printf, deletelog
from ctypes import *
from django.contrib.auth.decorators import login_required
from mysite.iclock.models.model_device import Device, DEVICE_ACCESS_CONTROL_PANEL, COMMU_MODE_PULL_RS485, COMMU_MODE_PULL_TCPIP, DEVICE_VIDEO_SERVER
from mysite.personnel.models.model_emp import format_pin
from dbapp.datautils import filterdata_by_user
try:
    import cPickle as pickle
except:
    import pickle

MAX_TRY_COMM_TIME   = 5
MAX_CONNECT_COUNT   = 60*24*30   #重连一个月失败后禁用
MAX_INTERVAL_CONNTECT_TIME = 60
PAUSE_TIMEOUT   =   60      #485暂停超时60秒

g_devcenter=None
g_video_server={}

G_DEVICE_CONNECT  = "CONNECT"
G_DEVICE_DISCONNECT  = "DISCONNECT"
G_DEVICE_UPDATE_DATA = "DATA UPDATE"
G_DEVICE_QUERY_DATA = "DATA QUERY"
G_DEVICE_DELETE_DATA = "DATA DELETE"
G_DEVICE_GET_DATA="DEVICE GET"
G_DEVICE_SET_DATA="DEVICE SET"
G_DEVICE_CANCEL_ALARM = "CANCEL ALARM"
G_DEVICE_CONTROL_NO = "CONTROL NO"
G_DEVICE_UPGRADE_FIRMWARE = "UPGRADE FIRMWARE"
G_DEVICE_GET_OPTION = "OPTION GET"
G_DEVICE_SET_OPTION = "OPTION SET"
G_REAL_LOG = "REAL_LOG"
G_DOWN_NEWLOG = "DOWN_NEWLOG"
G_QUEUE_ERROR = "QUEUE_ERROR"
G_CHECK_SERVICE = "CHECK_SERVICE"
               
GR_RETURN_OK =  200
FORMAT_DATE =   "%Y-%m-%d %H:%M:%S"

ALAEM_ID_START    = 100#20
ALAEM_ID_END      = 200 

DOOR_STATE_ID   =   255
EVENT_DOORSENSOROPEN = 200  #门磁开
EVENT_DOORSENSORCLOSE = 201     #门磁关

EVENT_LINKCONTROL       = 6     #联动事件
EVENT_UNREGISTERCARD    = 27 #卡未注册
INOUT_SEVER             = 220
INOUT_SHORT             = 221
MAX_RTLOG               = 5000 #实时事件最大缓存

DEVOPT="DEV_OPERATE"        #设备操作缓存, 新增、修改、删除设备操作
#CENTER_PROCE_HEART="CENTER_HEART_%s"
CENTER_PROCE_LIST="CENTER_PROCE_LIST"
CENTER_MAIN_PID="CENTER_MAIN_PID"

OPERAT_ADD  =1
OPERAT_EDIT =2
OPERAT_DEL  =3

PROCESS_NORMAL      = 0
PROCESS_WAIT_PAUSE  = 1
PROCESS_PAUSE       = 2 

DEVICE_COMMAND_TABLE = [
    _(u'用户信息'), 
    _(u'门禁权限信息'), 
    _(u'假日设置'), 
    _(u'时间段设置'), 
    _(u'首卡常开设置'),  
    _(u'多卡开门设置'),  
    _(u'事件记录')
]
DEVICE_MONITOR_CONTENT = [
    _(u'更新数据:'), 
    _(u'查询数据:'), 
    _(u'删除数据:'), 
    _(u'获取设备状态'), 
    _(u'设置设备状态'), 
    _(u'获取设备参数:'),  
    _(u'设置设备参数:'), 
    _(u'连接设备'), 
    _(u'获取实时事件'), 
    _(u'获取新记录'), 
    _(u'连接断开'), 
    _(u'取消报警'),
    _(u'命令队列检测'),
    _(u'数据中心服务检测')
]

#执行失败:
DEVICE_COMMAND_RETURN = {               
    '0': _(u'正常'),
    '-1': _(u'命令发送失败'),
    '-2': _(u'命令超时'), 
    '-3': _(u'需要的缓存不足'),
    '-4': _(u'解压失败'),
    '-5': _(u'读取数据长度错误'),
    '-6': _(u'通讯错误'), #解压的长度和期望的长度不一致
    '-7': _(u'命令重复'),
    '-8': _(u'连接尚未授权'),
    '-9': _(u'数据错误，CRC校验失败'), 
    '-10': _(u'数据错误，SDK无法解析'),#数据错误，PullSDK无法解析
    '-11': _(u'数据参数错误'),
    '-12': _(u'命令执行错误'),
    '-13': _(u'命令错误，没有此命令'),
    '-14': _(u'通讯密码错误'), 
    '-15': _(u'写文件失败'),#固件将文件写到本地时失败
    '-16': _(u'读文件失败'),
    '-17': _(u'文件不存在'),#读取时找不到文件
    '-18': _(u'存储空间已满'),
    '-19': _(u'校验和出错'),
    '-20': _(u'数据长度错误'),#接受到的数据长度与给出的数据长度不一致
    '-21': _(u'没有设置平台参数'),
    '-22': _(u'固件平台不一致'),#固件升级，传来的固件的平台与本地的平台不一致
    '-23': _(u'升级的固件版本过旧'),#升级的固件版本比设备中的固件版本老
    '-24': _(u'升级文件标识出错'),#升级的文件标识出错
    '-25': _(u'文件名错误'),#固件升级，传来的文件名不对，即不是emfw.cfg
    '-99': _(u'未知错误'),
    '-100': _(u'表结构不存在'), 
    '-101': _(u'表结构中，条件字段不存在'), 
    '-102': _(u'字段总数不一致'),
    '-103': _(u'字段排序不一致'),
    '-104': _(u'实时事件数据错误'),
    '-105': _(u'解析数据时，数据错误'),
    '-106': _(u'数据溢出，下发数据超出4M'),
    '-107': _(u'获取表结构失败'),
    '-108': _(u'无效OPTIONS选项'),
    '-201': _(u'库文件不存在'), #LoadLibrary失败
    '-202': _(u'调用接口失败'),
    '-203': _(u'通讯初始化失败'),
    '-301': _(u'获取TCP/IP版本失败'),#？？？？？？？？？？？？？？
    '-302': _(u'错误的TCP/IP版本号'),
    '-303': _(u'获取协议类型失败'),
    '-304': _(u'无效SOCKET'),
    '-305': _(u'SOCKET错误'),
    '-306': _(u'HOST错误'),

    '-1001': _(u'连接断开'),
    '-1002':_(u'禁用'),
    '-1003':_(u'服务未启动'),#数据中心服务未启动
    '-1100':_(u'队列异常! 请取消队列后重新同步数据'),#

    '1000': _(u'获取新记录'),
}


#视频连动录像线程
class TThreadComm(object):
    def __init__(self,func,args):
        self.func = func
        self.args = args

    def __call__(self):
        apply(self.func, self.args)

def video_record(linkageio, fstr, video_log):
    from django.conf import settings
#    from mysite.iaccess.video import TDevVideo
    #print "-----", linkageio.video_linkageio.ipaddress, linkageio.video_linkageio.ip_port, linkageio.video_linkageio.video_login, linkageio.video_linkageio.comm_pwd
    global g_video_server
    #print "g_video_server=", g_video_server
    video = g_video_server[linkageio.video_linkageio.ipaddress]
    if video is None:
        return
    filepath = "%s\\tmp\\OCXRecordFiles\\"%settings.APP_HOME
    #print "filepath=", filepath, "  fstr=", fstr, "video_delay_time=", linkageio.video_delay_time
    if video.record_file[linkageio.lchannel_num] == "":
        video.record_v23(filepath, fstr, linkageio.lchannel_num, linkageio.video_delay_time)
    video_log.f_video=video.record_file[linkageio.lchannel_num]+".mp4"
    video_log.save(force_update=True)

    return

#-201 调用库文件失败
#-202 库接口调用失败
#-203 通讯初始化失败
#-204 连接失败，其它错误
#-301-304   底层连接初始化失败
def strtodatetime(timestr): #1111-11-11 11:11:11
    dt=timestr.split(' ')
    if len(dt)>1:
        dtime=dt[0].split('-')+dt[1].split(':')
        try:
            tt=datetime.datetime(int(dtime[0]),int(dtime[1]),int(dtime[2]),int(dtime[3]),int(dtime[4]),int(dtime[5]))
        except:
            tt=datetime.datetime(1900,1,1,0,0,0)
        return tt
    else:
        return None

def FmtTTime(ttime):
    try:
        t=int(ttime)
    except:
        t=0
    sec=t % 60
    t/=60
    min=t % 60
    t/=60
    hour=t % 24
    t/=24
    mday=t % 31+1
    t/=31
    mon=t % 12
    t/=12
    year=t+2000
    try:
        tt=datetime.datetime(year, mon+1, mday, hour, min, sec)
        return tt
    except:
        return None

def customSql(sql,action=True):
    cursor = connection.cursor()
    cursor.execute(sql)
    if action:
            connection._commit()
    return cursor

def strtoint(str):
    try:
        ret=int(str)
    except:
        ret=0
    return ret

def process_test(line):
    redis_Cach_table="dev2"
    redis_Cach = queqe_server()
    cmdline=redis_Cach.lrange(redis_Cach_table, line, line)
    if cmdline != None:
        process_comm_task(None, cmdline[0])

def get_cmd_table(cmd_str):
    retstr=""
    if (cmd_str.startswith('user')):
        retstr=unicode(DEVICE_COMMAND_TABLE[0])  
    elif (cmd_str.startswith('userauthorize')):
        retstr=unicode(DEVICE_COMMAND_TABLE[1])
    elif(cmd_str.startswith('holiday')):
        retstr=unicode(DEVICE_COMMAND_TABLE[2])
    elif(cmd_str.startswith('timezone')):
        retstr=unicode(DEVICE_COMMAND_TABLE[3])
    elif(cmd_str.startswith('firstcard')):
        retstr=unicode(DEVICE_COMMAND_TABLE[4])
    elif(cmd_str.startswith('multimcard')):
        retstr=unicode(DEVICE_COMMAND_TABLE[5])
    elif(cmd_str.startswith('transaction')):
        retstr=unicode(DEVICE_COMMAND_TABLE[6])
    return retstr

def get_cmd_content(cmd_str):
    comm_param=cmd_str.strip()
    retstr=""
    if (comm_param.startswith(G_QUEUE_ERROR)):
        retstr=unicode(DEVICE_MONITOR_CONTENT[12])
    if (comm_param.startswith(G_DEVICE_CONNECT)):
        retstr=unicode(DEVICE_MONITOR_CONTENT[7])
    elif (comm_param.startswith(G_REAL_LOG)):
        retstr=unicode(DEVICE_MONITOR_CONTENT[8])
    elif (comm_param.startswith(G_DOWN_NEWLOG)):
        retstr=unicode(DEVICE_MONITOR_CONTENT[9])
    elif (comm_param.startswith(G_DEVICE_DISCONNECT)):
        retstr=unicode(DEVICE_MONITOR_CONTENT[10])
    elif (comm_param.startswith(G_DEVICE_UPDATE_DATA)):        
        strs = comm_param.split(" ", 3)
        table = strs[2]
        retstr=unicode(DEVICE_MONITOR_CONTENT[0])+get_cmd_table(table)
    elif (comm_param.startswith(G_DEVICE_QUERY_DATA)):
        strs = comm_param.split(" ", 4)
        table = strs[2]
        retstr=unicode(DEVICE_MONITOR_CONTENT[1])+get_cmd_table(table)
    elif(comm_param.startswith(G_DEVICE_DELETE_DATA)):
        strs = comm_param.split(" ", 3)
        table = strs[2]
        retstr=unicode(DEVICE_MONITOR_CONTENT[2])+get_cmd_table(table)
    elif(comm_param.startswith(G_DEVICE_GET_DATA)):
        retstr=unicode(DEVICE_MONITOR_CONTENT[3])
    elif(comm_param.startswith(G_DEVICE_SET_DATA)):
        strs = comm_param.split(" ", 5)
        retstr=unicode(DEVICE_MONITOR_CONTENT[4])
    elif(comm_param.startswith(G_DEVICE_GET_OPTION)):
        strs = comm_param.split(" ", 2)
        opt=strs[2]
        retstr=unicode(DEVICE_MONITOR_CONTENT[5])+opt
    elif(comm_param.startswith(G_DEVICE_SET_OPTION)):
        strs = comm_param.split(" ", 3)
        opt=strs[2]
        retstr=unicode(DEVICE_MONITOR_CONTENT[6])+opt
    elif comm_param.startswith(G_DEVICE_CANCEL_ALARM):
        strs = comm_param.split(" ")
        opt = strs[2]
        retstr = unicode(DEVICE_MONITOR_CONTENT[7]) + opt
    elif comm_param.startswith(G_CHECK_SERVICE):
        retstr = unicode(DEVICE_MONITOR_CONTENT[13])
        
    return retstr

@login_required
def downdata_progress(request): #进度条后台控制
    cdatas = []
    skey=request.session.session_key
    #print "downdata_progress=", skey
    q_server=queqe_server()
    cur_gress=q_server.get("DEV_COMM_PROGRESS_%s"%skey)
    tol_gress=q_server.get("DEV_COMM_SYNC_%s"%skey)
    if cur_gress and tol_gress:
        cur_strs=cur_gress.split(",", 2)
        tol_gress=tol_gress.split(",", 2)
        try:
            icur=int(cur_strs[1])
        except:
            icur=0
        try:
            itol=(int(tol_gress[1])*100)/int(tol_gress[0])
        except:
            itol=0
        cdata={
            'dev': cur_strs[0].decode("gb18030"),
            'progress':icur,
            'tolprogress':itol,
        }
        cdatas.append(cdata)
        q_server.connection.disconnect()
        cc={
            'index': 1,
            'data': cdatas,
        }
    else:
        cdata={
            'dev': "",
            'progress':0,
            'tolprogress':0,
        }
        cdatas.append(cdata)
        q_server.connection.disconnect()
        cc={
            'index': 0,
            'data': cdatas,
        }            
    rtdata=simplejson.dumps(cc)
    return HttpResponse(smart_str(rtdata))

#检查服务是否启动 True启动，False未启动
def check_service_commcenter():
    #return True
    s = os.popen("sc.exe query ZKECODataCommCenterService").read()
    if ": 1  STOPPED" in s:
        return False
    return True

#进行设备监控--iclock
@login_required
def get_device_monitor(request):
    service_enable = check_service_commcenter()
    from mysite.iclock.models import Device, DevCmd
    from mysite.personnel.models import Area
    q_server=queqe_server()
    u = request.user
    aa = u.areaadmin_set.all()
    a_limit = aa and [int(a.area_id) for a in aa] or [int(area.pk) for area in Area.objects.all()]#非超级管理员且没有配置有效区域（默认全部）的有效区域id列表（即用户手动配置过用户区域的）
    
    dev_list = Device.objects.filter(area__pk__in=a_limit).filter(device_type=DEVICE_ACCESS_CONTROL_PANEL).order_by('id')#当前用户授权范围内的门禁控制器
    cdatas = []
    for dev in dev_list:
        ret = 0
        op_type = ""
        op_state = ""
        if not service_enable:
            op_type = get_cmd_content("CHECK_SERVICE")
            ret = '-1003' #警告 <-1000
            op_state = unicode(DEVICE_COMMAND_RETURN[ret])
        
        key=dev.command_temp_list_name()#ICLOCK_%s_TMP
        ucmd=q_server.get(key)
        cmdcount=q_server.llen(dev.new_command_list_name())#NEWCMDS_%s
        cntkey=dev.command_count_key()#ICLOCK_%s_CMD
        cnt=q_server.get(cntkey)#命令条数
        if cmdcount is None:
            cmdcount="0"
        if cnt is None:
            cnt="0"
        if cnt.find('\x00'):
            cnt=cnt.strip('\x00')
        try:
            cnt=int(cnt)
        except:
            cnt=0
        try:
            cmdcount=int(cmdcount)
        except:
            cmdcount=0       
        if int(cnt)>0:
            if int(cmdcount)==0:
                q_server.set(cntkey, "0")
                cnt=q_server.get(cntkey)
        if int(cnt)>0:
            pp=(int(cnt)-int(cmdcount))*100/int(cnt)
            if pp < 0:
                pp=0
            percent="%d%%"%pp
        else:
            percent="100%"

        if ucmd is None:
            if service_enable:#服务启动时默认第一个操作为获取实时事件（一闪即过）
                op_type = get_cmd_content("REAL_LOG")#
                ret = '0' #警告 <-1000
                op_state = unicode(DEVICE_COMMAND_RETURN[ret])
                
            cdata={
                'id':dev.id,
                'devname':dev.alias,
                'sn':dev.sn,
                'op_type': op_type,
                'op_state':op_state,
                'retmemo': u"",
                'ret':ret,
                'percent':percent,
                'CmdCount':cmdcount,
            }
            cdatas.append(cdata)
            continue
        try:
            acmd=pickle.loads(ucmd)
        except: 
            print_exc()
            acmd=None

        if acmd is None:
            cdata={
                'id':dev.id,
                'devname':dev.alias,
                'sn':dev.sn,
                'op_type': op_type,
                'op_state': op_state,
                'retmemo': "",
                'ret': ret,
                'percent':percent,
                'CmdCount':cmdcount,
            }
            cdatas.append(cdata)
            continue
        if service_enable:
            ret = acmd.CmdReturn
            op_type = get_cmd_content(acmd.CmdContent)
            if acmd.CmdReturn >= 0:
                op_state = unicode(DEVICE_COMMAND_RETURN["0"])
            else:
                try:
                    op_state = unicode(DEVICE_COMMAND_RETURN[str(acmd.CmdReturn)])
                except:
                    op_state = _(u"%(f)s:错误代码%(ff)d")%{"f":DEVICE_COMMAND_RETURN["-1001"], "ff":acmd.CmdReturn}

        reason=""
        cdata = {
            'id':dev.id,
            'devname':dev.alias,
            'sn':dev.sn,
            'op_type':op_type,#操作类型
            'op_state':op_state,#当前操作状态
            'retmemo': reason,
            'ret': ret,
            'percent':percent,
            'CmdCount':cmdcount,
        }
        cdatas.append(cdata)
    cc = {
        'data':cdatas
    }
    q_server.connection.disconnect()
    rtdata=simplejson.dumps(cc)
    return HttpResponse(smart_str(rtdata))

@login_required
def ClearCmdCache(request):
    from mysite.iclock.models import Device
    dev_id = request.GET.get("devid", 0)
    if dev_id:
        dev=Device.objects.get(id=dev_id)
        q_server=queqe_server()
        q_server.delete(dev.new_command_list_name())
        q_server.delete(dev.command_temp_list_name())
        q_server.delete(dev.command_count_key())
        q_server.connection.disconnect()
        return HttpResponse(smart_str({'ret':1}))
    else:
        return HttpResponse(smart_str({'ret':0}))

@login_required
def comm_error_msg(request):
    from mysite.iclock.models import Device, DevCmd
    from mysite.iclock.models.model_device import DEVICE_ACCESS_CONTROL_PANEL
    q_server=queqe_server()
    cdatas = []
    cc={}
    dev_list = filterdata_by_user(Device.objects.filter(device_type=DEVICE_ACCESS_CONTROL_PANEL),request.user)
    #print '-----dev_list=', dev_list
    icount=0
    for dev in dev_list:
        key=dev.command_temp_list_name()
        ucmd=q_server.get(key)
        if ucmd is None:
            continue
        try:
           acmd=pickle.loads(ucmd)
        except: 
           acmd=None
        if acmd is None:
            continue
        if acmd.CmdReturn <= 0:    
            icount+=1
            cdata={
                'devname':acmd.SN.alias,
            }
            cdatas.append(cdata)
    cc={
        'cnt':icount,
        'data':cdatas,
    }
    q_server.connection.disconnect()
    rtdata=simplejson.dumps(cc)
    return HttpResponse(smart_str(rtdata))

def get_door_state(val, doorno):
    if doorno==1:
        return  (val & 0x000000FF)
    elif doorno==2:
        return (val & 0x0000FF00) >> 8
    elif doorno == 3:
        return (val & 0x00FF0000) >> 16
    elif doorno == 4:
        return (val & 0xFF000000) >> 24

#将门状态写入缓存中
def set_door_connect(device, vcom):
    q_server=queqe_server()
    doorstate=q_server.get(device.get_doorstate_cache_key())
#    print "doorstate=",doorstate 
    if doorstate is None:
        doorstate="0,0,0"
    doorstr=doorstate.split(",", 3)
    if vcom > 0:#"DEVICE_DOOR_%s"%self.id
        q_server.set(device.get_doorstate_cache_key(), "%s,%s,%d"%(doorstr[0],doorstr[1], vcom))
    else:
        q_server.set(device.get_doorstate_cache_key(), "0,0,0")#没连接上
    q_server.connection.disconnect()

#门状态监控
# state（0无门磁，1门关,2门开） alarm（1报警 2门开超时）connect(0不在线，1在线)
def door_state_monitor(dev_list):#dev_list为QuerySet---devids需为list
    from mysite.iclock.models import Device
    service_enable = check_service_commcenter()
    q_server = queqe_server()
    
#    if devids==0:#all
#        dev_list = Device.objects.all()
#    else:
#        dev_list = Device.objects.filter(id__in=devids)#type(devids)!=list and Device.objects.filter(id__in=[devids]) or Device.objects.filter(id__in=[devids])
    cdatas = []
#    print '--------dev_list=',dev_list
    for dev in dev_list:
        key = dev.get_doorstate_cache_key()
        doorstate = q_server.get(key)
        #print 'doorstate=',doorstate
        if doorstate and service_enable:#服务没有启动（含手动），前端门显示不在线
            val=doorstate.split(",", 3)
            try:
                vdoor = int(val[0])#设备中所有门的开关状态
            except:
                print_exc()
                vdoor = 0
            try:
                valarm = int(val[1])#设备中所有门的 报警 门开超时
            except:
                print_exc()
                valarm = 0
            try:
                vcon = int(val[2])#是否在线
            except:
                print_exc()
                vcon = 0
        else:
            vdoor = 0
            valarm = 0
            vcon = 0
        door = dev.accdoor_set.all()
        for d in door:
            state = get_door_state(vdoor, d.door_no)
            alarm = get_door_state(valarm, d.door_no)
            cdata = {
                'id': int(d.id),
                'state': int(state),
                'alarm': int(alarm),
                'connect': int(vcon),
            }
            cdatas.append(cdata)
    cc={
        'data':cdatas,
    }
    q_server.connection.disconnect()
    #print cc
    #rtdata=simplejson.dumps(cc)
    return cc
    #return HttpResponse(smart_str(rtdata))

def checkdevice_and_savecache(q, devobj):
    from mysite.iclock.models import Device
    last_activity_time=q.get(devobj.get_last_activity())
    #修改最后连接时间
    if last_activity_time:
        now_t=time.mktime(datetime.datetime.now().timetuple())
        if float(last_activity_time) > now_t:
            q.set(devobj.get_last_activity(), "1")
        elif now_t - float(last_activity_time) > 120:
            try:
                dev=Device.objects.get(id = devobj.id)
                dev.last_activity = datetime.datetime.now()
                dev.save(force_update=True, log_msg=False)
                q.set(devobj.get_last_activity(), str(now_t))
            except:
                print_exc()
    else:
        q.set(devobj.get_last_activity(), "1")

def set_doorstr(istr, val, doorid): #设置某个门的状态
    dest=[0,0,0,0]
    for i in range(0, 4, 1):
        dest[i]=istr>>(i*8)&0xFF
    dest[doorid-1]=val
    return dest[0] | (dest[1]<<8) | (dest[2]<<16) | (dest[3]<<24)

#time, Pin, cardno, doorID, even_type, reserved, verified
def save_event_log(str, doorobj, devobj=None):
    from mysite.iaccess.models import AccRTMonitor, AccDoor
    from mysite.iclock.models import Device
    devid=0
    devname=""
    doorid=0
    doorname=""

    if devobj:
        try:
            dev=Device.objects.get(id=devobj.id)
            devid=dev.id
            devname=dev.alias
        except:
            print_exc()
    if doorobj:
        try:
            door=AccDoor.objects.get(id=doorobj[0].id)
            doorid=door.id
            doorname=door.door_name
        except:
            print_exc()
    
    if (strtoint(str[4]) == INOUT_SEVER) or (strtoint(str[4]) == INOUT_SHORT):
        try:
            rtlog=AccRTMonitor(device_id=devid, device_name=devname, time=strtodatetime(str[0]), pin = int(str[1]) and format_pin(str[1]) or "--",\
                    event_type=(len(str[4])>0) and str[4] or 0,state=(len(str[5])>0) and str[5] or 0, \
                    in_address=(len(str[3])>0) and str[3] or 0, card_no = int(str[2]) and str[2] or "--")
            rtlog.save(force_insert=True)
        except:
            print_exc()
    elif strtoint(str[4]) == EVENT_LINKCONTROL:
        if (strtoint(str[6] == INOUT_SEVER)) or (strtoint(str[6] == INOUT_SHORT)):
            try:
                rtlog=AccRTMonitor(device_id=devid, device_name=devname, time=strtodatetime(str[0]), pin = int(str[1]) and format_pin(str[1]) or "--",\
                        event_type=(len(str[4])>0) and str[4] or 0,state=(len(str[5])>0) and str[5] or 0, \
                        trigger_opt=(len(str[6])>0) and str[6] or 0,in_address=(len(str[3])>0) and str[3] or 0, card_no = "--")
                rtlog.save(force_insert=True)
            except:
                print_exc()
        else:
            try:
                rtlog=AccRTMonitor(device_id=devid, device_name=devname, time=strtodatetime(str[0]), pin = int(str[1]) and format_pin(str[1]) or "--", door_id=doorid, door_name=doorname, \
                        event_type=(len(str[4])>0) and str[4] or 0,state=(len(str[5])>0) and str[5] or 0, \
                        trigger_opt=(len(str[6])>0) and str[6] or 0, card_no = "--")
                rtlog.save(force_insert=True)
            except:
                print_exc()
    else:
        try:
            rtlog=AccRTMonitor(device_id=devid, device_name=devname, time=strtodatetime(str[0]), pin = int(str[1]) and format_pin(str[1]) or "--", door_id=doorid, door_name=doorname, \
                    event_type=(len(str[4])>0) and str[4] or 0,state=(len(str[5])>0) and str[5] or 0, \
                    verified=(len(str[6])>0) and str[6] or 0, card_no = int(str[2]) and str[2] or "--")
            rtlog.save(force_insert=True)
        except:
            print_exc()

def appendrtlog(q_server, devobj, rtlog):
    from mysite.iaccess.models import AccRTMonitor,AccDoor
    from mysite.iclock.models import Transaction
    from mysite.personnel.models import Employee
    try:
        rtlog=rtlog.split("\r\n", 1)[0]
        #print '---rtlog=',rtlog
        str = rtlog.split(",",7)
        #print '---str=',str
        doorstr=""
        if len(str) < 7:      #不合规范数据
            return 0
        if strtoint(str[4]) == DOOR_STATE_ID:#0时间+1门开关状态+2报警或门开超时+3没用+4（255标明该事件为门状态，否则为事件）+5 没用+6验证方式（200其他）
            #q_server.set(devobj.get_doorstate_cache_key(), "%s,%s,1"%(str[1],str[2]))
            #dev_doorstatus[devobj.get_doorstate_cache_key()] = "%s,%s,1" % (str[1], str[2])
            printf("rtlog ---- %s %s"%(str[1],str[2]))
            return
        if strtoint(str[4])==EVENT_DOORSENSOROPEN:
            doorstate=q_server.get(devobj.get_doorstate_cache_key())
#            print "doorstate=",doorstate 
            if doorstate is None:
                doorstate="0,0,0"
            doorstr=doorstate.split(",", 3)
            try:
                val=set_doorstr(int(doorstr[0]), 0x02, int(str[3]))
            except:
                val=0
            q_server.set(devobj.get_doorstate_cache_key(), "%d,%s,1"%(val,doorstr[1]))
        
        if strtoint(str[4])== EVENT_DOORSENSORCLOSE:
            doorstate=q_server.get(devobj.get_doorstate_cache_key())
            #print "doorstate=",doorstate 
            if doorstate is None:
                doorstate="0,0,0"
            doorstr=doorstate.split(",", 3)
            try:
                val=set_doorstr(int(doorstr[0]), 0x01, int(str[3]))
            except:
                val=0
            q_server.set(devobj.get_doorstate_cache_key(), "%d,%s,1"%(val,doorstr[1]))

        if (strtoint(str[4]) >= ALAEM_ID_START) and (strtoint(str[4]) < ALAEM_ID_END):
            doorstate=q_server.get(devobj.get_doorstate_cache_key())
            #print "doorstate=",doorstate 
            if doorstate is None:
                doorstate="0,0,0"
            doorstr=doorstate.split(",", 3)
            try:
                val=set_doorstr(int(doorstr[1]), int(str[4]), int(str[3]))
            except:
                val=0
            q_server.set(devobj.get_doorstate_cache_key(), "%s,%d,1"%(doorstr[0], val))
        #print " end doorstate=", doorstr
        
        try:
            doorobj=None
            if (strtoint(str[4]) == INOUT_SEVER) or (strtoint(str[4]) == INOUT_SHORT):  #辅助事件
                pass
                #print str[3]
            elif (strtoint(str[4]) == EVENT_LINKCONTROL) and (strtoint(str[6]) == INOUT_SEVER):  #连动事件
                pass
                #print str[3]
            elif (strtoint(str[4]) == EVENT_LINKCONTROL) and (strtoint(str[6]) == INOUT_SHORT):  #连动事件
                pass
                #print str[3]
            else:
                doorobj=AccDoor.objects.filter(device=devobj).filter(door_no=str[3])
                if doorobj is not None:
                    str[3]=doorobj and doorobj[0].id or 0
        except:
            print_exc()
        
        #if q_server.llen("MONITOR_RT")<MAX_RTLOG:
        try:
            log="%s,%s,%s,%s,%s,%s,%s,%d"%(str[0],str[1],str[3],str[4],str[5], str[6], str[2], devobj and devobj.id or 0)
            q_server.rpush("MONITOR_RT", log)
        except:
            print_exc()

        if (strtoint(str[4]) >= ALAEM_ID_START) and (strtoint(str[4]) < ALAEM_ID_END):
            q_server.rpush("ALARM_RT", log)
        #time, Pin, cardno, doorID, even_type, reserved, verified    
        save_event_log(str, doorobj, devobj)

        if doorobj:
            if doorobj[0].is_att:
                from  models.accmonitorlog import EVENT_LOG_AS_ATT
                #if ((strtoint(str[4]) >= 0) and (strtoint(str[4]) <=2)) or ((strtoint(str[4]) >= 21) and (strtoint(str[4]) <=23)) or (strtoint(str[4]) == 5):
                if strtoint(str[4]) in EVENT_LOG_AS_ATT:
                    try:
                        pin1=(len(str[1])>0) and str[1] or 0
                        user=Employee.objects.filter(PIN=format_pin(pin1))
                        if user:
                            trans=Transaction(UserID=user[0], SN=doorobj[0].device, TTime=strtodatetime(str[0]))
                            trans.save(force_insert=True)
                    except:
                        print_exc()
    except:
        print_exc()

def appendDevCmdOld(sn, cmdStr, cmdTime=None):
        from mysite.iclock.models import DevCmd
        cmd=DevCmd(SN=dObj, CmdContent=cmdStr, CmdCommitTime=(cmdTime or datetime.datetime.now()))
        cmd.save(force_insert=True)
        return cmd.id
#Cardno,Pin,Verified,DoorID,EventType,InOutState,Time_second  记录
#time, Pin, cardno, doorID, even_type, reserved, verified   事件
def process_comm_task(devs, comm_param):#dev指DevComm的实例，而非Device的实例--comment by darcy
    ret=0
    dev=devs.comm
    if (comm_param.startswith(G_DEVICE_CONNECT)):
        qret = dev.connect()
        return {"ret":qret["result"], "retdata":qret["data"]}
    elif (comm_param.startswith(G_DEVICE_DISCONNECT)):
        return dev.disconnect()
    elif (comm_param.startswith(G_DEVICE_UPDATE_DATA)):        
        strs = comm_param.split(" ",3)
        table = strs[2]
        if(len(table)>0):
            data=comm_param[comm_param.find(table)+len(table)+1:]
            data=re.sub(ur'\\', '\r', data)
            qret = dev.update_data(table.strip(),data.strip(),"")
        else:
            pass
            #print "command error"
        return {"ret":qret["result"], "retdata":qret["data"]}
    elif (comm_param.startswith(G_DEVICE_QUERY_DATA)):
        if (comm_param.find("transaction")>0):#下载全部刷卡事件   
            from mysite.iaccess.models import AccRTMonitor, AccDoor
            qret=dev.get_transaction(False)
            printf("24. user down all transaction rec=%d"%qret['result'])
            if qret['result']>0:
                for i in range(1, qret['result'], 1):
                    log = qret['data'][i]
                    str = log.split(",",7)
                    doorobj=None
                    try:
                        if (strtoint(str[4]) == INOUT_SEVER) or (strtoint(str[4]) == INOUT_SHORT):  #辅助事件
                            pass
                            #print str[3]
                        elif (strtoint(str[4]) == EVENT_LINKCONTROL) and (strtoint(str[6]) == INOUT_SEVER):  #连动事件
                            pass
                            #print str[3]
                        elif (strtoint(str[4]) == EVENT_LINKCONTROL) and (strtoint(str[6]) == INOUT_SHORT):  #连动事件
                            pass
                            #print str[3]
                        else:
                            doorobj=AccDoor.objects.filter(device=devs.devobj).filter(door_no=str[3])
                            if doorobj is not None:
                                str[3]=doorobj and doorobj[0].id or 0
                    except:
                        print_exc()
                    try:
                        restr="%s,%s,%s,%s,%s,%s,%s"%(FmtTTime(str[6]),str[1],str[0],str[3],str[4],str[5],str[2])
                        save_event_log(restr.split(",",7), doorobj, devs.devobj)
                    except:
                        print_exc()
                        continue
                return {"ret":qret['result'], "retdata":""}
            else:
                return {"ret":-1, "retdata":""}
        else:
            str = ""
            strs = comm_param.split(" ",4)
            table = strs[2]
            field_names = strs[3]
            if(len(table)>0):
                filter=comm_param[comm_param.find(field_names)+len(field_names)+1:]
                qret = dev.query_data(table.strip(),fields.strip(),filter.strip(), "")
            else:
                pass
                #printf "command error"
            return {"ret":qret["result"],"retdata":qret["data"]}
    elif(comm_param.startswith(G_DEVICE_DELETE_DATA)):
        strs = comm_param.split(" ",3)
        table = strs[2]
        if(len(table)>0):
            qret = dev.delete_data(table,comm_param[comm_param.find(table)+len(table)+1:],)
        else:
            pass
            #print "command error"
        return {"ret":qret["result"],"retdata":qret["data"]}
    elif(comm_param.startswith(G_DEVICE_GET_DATA)):
        return 
    elif(comm_param.startswith(G_DEVICE_SET_DATA)):
        try:
            comm_param=comm_param.strip()
            strs = comm_param.split(" ", 5)
            door=int(strs[2])
            index=int(strs[3])
            state=int(strs[4])
            qret=dev.controldevice(door, index, state)
            return {"ret":qret["result"],"retdata":qret["data"]}
        except:
            print_exc()
            return 
    elif(comm_param.startswith(G_DEVICE_CONTROL_NO)):#
        try:
            comm_param = comm_param.strip()
            strs = comm_param.split(" ", 5)
            door = int(strs[2])#门编号
            state = int(strs[3])#启用（1）或禁用（0）
            qret = dev.control_normal_open(door, state)#控制常开
            #print '---qret=',qret,'-----',door,'---',state
            return {"ret": qret["result"], "retdata": qret["data"]}
        except:
            print_exc()
            return
    elif(comm_param.startswith(G_DEVICE_CANCEL_ALARM)):
        try:
            qret = dev.cancel_alarm()#取消报警
            return {"ret": qret["result"], "retdata": qret["data"]}
        except:
            print_exc()
            return
#    elif(comm_param.startswith(G_DEVICE_UPGRADE_FIRMWARE)):
#        try:
#            comm_param = comm_param.strip()
#            strs = comm_param.split(" ", 5)
#            file_name = strs[2]
#            import struct
#            (buffer,) = struct.unpack("s", strs[3])
#            buff_len = strs[4]
#            qret = dev.update_firmware(file_name, buffer, buff_len)#升级固件
#        except:
#            print_exc()
#            return
    elif(comm_param.startswith(G_DEVICE_GET_OPTION)):
        strs = comm_param.split(" ",2)
        opt=strs[2]
        if len(opt)>0:
            optitem=re.sub(ur'\t', ',', opt)
            qret=dev.get_options(optitem.strip())
        return {"ret":qret["result"],"retdata":qret["data"]}
    elif(comm_param.startswith(G_DEVICE_SET_OPTION)):
        strs = comm_param.split(" ",3)
        opt=strs[2]
        if len(opt)>0:
            optitem=re.sub(ur'\t', ',', opt)
            qret=dev.set_options(optitem.strip())
        return {"ret":qret["result"],"retdata":qret["data"]}
    else:
        return {"ret":0, "retdata":"unknown command"}

class DeviceMonitor(object):
    def __init__(self):
        self.id = 0
        self.comm_tmp=""
        self.cln = ""
        self.devobj = None
        self.comm = None
        self.try_failed_time = 0
        self.try_connect_count = 0
        self.try_connect_delay = 0

#命令处理
def process_general_cmd(dev,q_server):
    cmd_ret=False
    try:
        acmd=q_server.getrpop(dev.cln)  #防意外掉电，命令丢失, 先取出执行，成功再删除
        if (acmd!=None) and (acmd.startswith(G_QUEUE_ERROR)):
            cmd_ret=True
            acmd=None
            try:
                from mysite.iclock.models.model_devcmd import DevCmd
                acmd=DevCmd(SN=dev.devobj, CmdContent=G_QUEUE_ERROR, CmdReturn=-1100)
                q_server.set(dev.comm_tmp, pickle.dumps(acmd))
                print "add queue error"
            except:
                print_exc()
                acmd=None
    except:
        printf("error 2 zzz")
        print_exc()
		
    try:
        if(acmd != None):
            acmd=pickle.loads(acmd)
    except: 
        acmd=None
		
    if acmd is not None:
        try:
            from mysite.iclock.models.model_device import MAX_COMMAND_TIMEOUT_SECOND
            cmdline=str(acmd.CmdContent)
            if acmd.CmdImmediately:
                now_t=datetime.datetime.now()
                if (now_t - acmd.CmdCommitTime).seconds > MAX_COMMAND_TIMEOUT_SECOND:
                    q_server.rpop(dev.cln)
                    return False
            #print "general====", cmdline,"==="
        except:
            printf("check cmd error")
            print_exc()
			
        if cmdline != None:
            try:
                cmd_ret = True
                try:
                    ret=process_comm_task(dev, cmdline)
                except:
                    printf("%s *********process_comm_task error"%dev.devobj.alias.encode("gb18030"), True)
                printf("8.%s -- process_general_cmd cmd=%s, ret=%d"%(dev.devobj.alias.encode("gb18030"), cmdline, ret["ret"]))
                if (ret["ret"] >= 0): #执行成功, 写入数据库
                    q_server.rpop(dev.cln)
                    acmd.CmdReturn=ret["ret"]
                    acmd.CmdReturnContent=ret["retdata"]
                    acmd.CmdTransTime=datetime.datetime.now()
                    acmd.save()
                    checkdevice_and_savecache(q_server, dev.devobj)
                else:
                    if acmd.CmdImmediately == 1:    #立即执行的命令，只执行一次，包括失败
                        q_server.rpop(dev.cln)
                    if ret["ret"] == -18:
                        q_server.deletemore(dev.cln)    #存贮空间不足，清空命令缓存
                    
                    acmd.CmdReturn=ret["ret"]
                    cmd_ret=False
                q_server.set(dev.comm_tmp, pickle.dumps(acmd))
            except:
                print_exc()
                printf("process_comm_task defail....")
                cmd_ret=False
    return cmd_ret


def add_dev_dict(devdic,devobj):
    try:
        devdic[devobj.id] = DeviceMonitor()
        devdic[devobj.id].id = devobj.id
        devdic[devobj.id].cln =devobj.new_command_list_name()
        devdic[devobj.id].comm_tmp= devobj.command_temp_list_name()
        devdic[devobj.id].devobj = devobj
        devdic[devobj.id].comm= TDevComm(devobj.getcomminfo())
        devdic[devobj.id].comm.connect()
        devdic[devobj.id].try_connect_count=0
        if devdic[devobj.id].comm.hcommpro>0:
            devdic[devobj.id].try_connect_delay=time.mktime(datetime.datetime.now().timetuple())
            set_door_connect(devdic[devobj.id].devobj, 1)#在线
            if devdic[devobj.id].devobj.sync_time:
                devdic[devobj.id].devobj.set_time(False)
        else:
            set_door_connect(devdic[devobj.id].devobj, 0)#离线
            devdic[devobj.id].try_connect_delay=0
    except:
        printf("15. add_dev_dict id=%d error"%devobj.id)

def is_comm_io_error(errorid):
    return ((errorid < ERROR_COMM_OK) and (errorid > ERROR_COMM_PARAM))

def check_and_down_log(dev):    #下载新记录
    from mysite.iaccess.models import AccRTMonitor, AccDoor
    from mysite.iclock.models.model_devcmd import DevCmd
    try:
        cfg=dict4ini.DictIni(os.getcwd()+"/appconfig.ini",values={"iaccess":{"down_newlog":0}}) #默认0点定时下载新记录
        now_hour=datetime.datetime.now().hour
        if now_hour != cfg.iaccess.down_newlog:
            return 
        q_server = queqe_server()
        trans_key=dev.devobj.get_transaction_cache()
        mday=q_server.get(trans_key)
        if mday is None:
            q_server.set(dev.devobj.get_transaction_cache(), "0")
            return 
        now_day=datetime.datetime.now().day
        if int(mday) == now_day:
            return 
        else:
            q_server.set(trans_key, "%d"%now_day)

        acmd=DevCmd(SN=dev.devobj, CmdContent="DOWN_NEWLOG", CmdReturn=1000)   #正在执行下载新记录
        q_server.set(dev.comm_tmp, pickle.dumps(acmd))  
        q_server.connection.disconnect()
    except:
        print_exc()

    printf("22. %s check_and_down_log "%dev.devobj.alias.encode("gb18030"), True)
    try:
        ret = dev.comm.get_transaction(True)
    except:
        printf("%s *********get_transaction error"%dev.devobj.alias.encode("gb18030"), True)
    printf("23. %s ---check_and_down_log rec=%d"%(dev.devobj.alias.encode("gb18030"), ret['result']), True)
    if ret['result']>0:
        for i in range(1, ret['result']+1, 1):
            try:
                doorobj=None
                log = ret['data'][i]
                str = log.split(",",7)
                if (strtoint(str[4]) == INOUT_SEVER) or (strtoint(str[4]) == INOUT_SHORT):  #辅助事件
                    pass
                    #print str[3]
                elif (strtoint(str[4]) == EVENT_LINKCONTROL) and (strtoint(str[6]) == INOUT_SEVER):  #连动事件
                    pass
                    #print str[3]
                elif (strtoint(str[4]) == EVENT_LINKCONTROL) and (strtoint(str[6]) == INOUT_SHORT):  #连动事件
                    pass
                    #print str[3]
                else:
                    doorobj=AccDoor.objects.filter(device=dev.devobj).filter(door_no=str[3])
                    if doorobj is not None:
                        str[3]=doorobj and doorobj[0].id or 0

                restr="%s,%s,%s,%s,%s,%s,%s"%(FmtTTime(str[6]),str[1],str[0],str[3],str[4],str[5],str[2])
                save_event_log(restr.split(",",7), doorobj, dev.devobj)
            except:
                print_exc()
                continue
    return ret['result']

def check_server_stop(procename, pid, devs):
    #服务停止进程退出
    try:
        ret=False
        q_server=queqe_server()
        proce_server_key="%s_SERVER"%procename   
        proce_stop=q_server.get(proce_server_key)
        q_server.connection.disconnect()
        if proce_stop == "STOP":
            q_server=queqe_server()
            q_server.delete(proce_server_key)
            #q_server.deletemore("CENTER_HEART_*")
            printf("%s servers return "%procename, True)
            for devsn in devs:
                dev = devs[devsn]
                try:
                    acmd=DevCmd(SN=dev.devobj, CmdContent="DISCONNECT", CmdReturn=-1001)   #设备监控显示设备断开
                    q_server.set(dev.comm_tmp, pickle.dumps(acmd))
                except:
                    print_exc()
            ret=True
            q_server.connection.disconnect()
    except:
        print_exc()
        printf("stop server error")   
    return ret
    
def wait_com_pause(com, timeout):     #COM_1_CHANNELS    PROCESS_WAIT_PAUSE
    q_server=queqe_server()
    channel_key="COM_%d_CHANNELS"%com   #COM_1_CHANNELS
    com_key="COM_%d_PID"%com
    com_pid=q_server.get(com_key)
    if com_pid is None:     #串口不存在
        return True
    q_server.set(channel_key, "%d"%PROCESS_WAIT_PAUSE)
    for i in range(0, timeout, 1):
        mchan=q_server.get(channel_key)
        if mchan is None:
            time.sleep(1)
            continue
        try:
            mchan=int(mchan)
        except:
            mchan=0
        if int(mchan) > PROCESS_WAIT_PAUSE:
            return True
        time.sleep(1)
    q_server.connection.disconnect()
    return False

def set_comm_run(com):  #删除暂停通道
    q_server=queqe_server()
    channel_key="COM_%d_CHANNELS"%com   #COM_1_CHANNELS
    channel_timeout_key="COM_%d_CHANNELS_TIMEOUT"%com
    q_server.delete(channel_key)
    q_server.delete(channel_timeout_key)
    q_server.connection.disconnect()
    
#实时任务处理函数，用于进程调用
def net_task_process(devobjs, devcount, procename="", process_heart={}, children_pid={}):
    from mysite.iclock.models.model_device import Device, COMMU_MODE_PULL_RS485
    from mysite.iaccess.view import check_acpanel_args
    from mysite.iclock.models.model_devcmd import DevCmd
    q_server=queqe_server()
    tt = q_server.get("CENTER_RUNING")    #主服务ID
    pid = os.getpid()#子进程pid
    children_pid[procename] = pid
    #print '------child process=',pid
    #print '-------net_tast_process process_heart =',process_heart
#    if procename.find("COM") >= 0:
#        com_pid=q_server.get("%s_PID"%procename)
#        if com_pid:
#            pid=int(com_pid)
#        else:
#            pid=0
#        print "com pid=", pid
#    else:
#        pid=os.getpid()
#视频服务器初始化

    q_server.rpush(CENTER_PROCE_LIST, "%s"%procename)
    devs = {}
    for devobj in devobjs:
        try:
            add_dev_dict(devs, devobj)
            q_server.delete(devs[devobj.id].comm_tmp)#清除原有命令
            acmd=DevCmd(SN=devobj, CmdContent="CONNECT", CmdReturn=devs[devobj.id].comm.hcommpro)
            q_server.set(devs[devobj.id].comm_tmp, pickle.dumps(acmd))
        except:
            printf("add_dev_dict %d error"%devobj.id, True)
            #print "add_dev_dict %d error"%devobj.id 
        if check_server_stop(procename, pid, devs):  #启动时检测停止服务
            return 0
    printf("%s :parent process: %d"%(procename, os.getpid()))
    #print "%s :parent process: %d"%(procename, os.getpid())

    while(1):
        #服务停止进程退出
        proce_server_key="%s_SERVER"%procename   
        proce_stop=q_server.get(proce_server_key)
        if proce_stop == "STOP":
            try:
                q_server.delete(proce_server_key)
                #q_server.deletemore("CENTER_HEART_*")
                printf("%s servers return "%procename, True)
                #print "%s servers return "%procename
                for devsn in devs:
                    dev = devs[devsn]
                    try:
                        acmd=DevCmd(SN=dev.devobj, CmdContent="DISCONNECT", CmdReturn=-1001)   #设备监控显示设备断开
                        q_server.set(dev.comm_tmp, pickle.dumps(acmd))
                    except:
                        print_exc()
                q_server.connection.disconnect()
            except:
                print_exc()
                printf("stop server error ", True)
            return 0

        pid_t=time.mktime(datetime.datetime.now().timetuple())
        #print '-----pid_t=',pid_t
        process_heart[procename] = pid_t
        #q_server.set(CENTER_PROCE_HEART%procename, str(pid_t))
        
        #主服务ID不一致退出
        if tt != q_server.get("CENTER_RUNING"):
            try:
                printf("%s servers id error return "%procename, True)
                for devsn in devs:
                    dev = devs[devsn]
                    try:
                        acmd=DevCmd(SN=dev.devobj, CmdContent="DISCONNECT", CmdReturn=-1001)   #设备监控显示设备断开
                        q_server.set(dev.comm_tmp, pickle.dumps(acmd))
                    except:
                        print_exc()
                q_server.connection.disconnect()
            except:
                print_exc()
                printf("stop server error ", True)
            return 0           
        
        #线程与缓存中的设备同步
        proce_cache_devset=[]   #前台缓存表
        proce_thread_devset=[]  #线程表
        for i in range(0, q_server.llen(procename)):
            try:
                proc_cache=q_server.lindex(procename, i)
                proce_dev=pickle.loads(proc_cache)
            except:
                proce_dev=None
            try:
                if proce_dev:
                    proce_cache_devset.append(proce_dev)
            except:
                printf("proce_cache_devset append device error")
        #print procename, "proce_cache_devset=" , proce_cache_devset
        del_dev={}
        for devsn in devs:
            try:
                thread_dev = devs[devsn].devobj.getdevinfo()
                proce_thread_devset.append(thread_dev)
            except:
                printf("proce_thread_devset append device error")
            #删除设备
            if thread_dev not in proce_cache_devset:
                try:
                    devs[devsn].comm.disconnect()
                    #devs.__delitem__(devsn)
                    del_dev[devsn] = devs[devsn]
                    #print "1. %s delete device %d"%(procename, thread_dev["id"])
                    printf("1. %s delete device %d"%(procename, thread_dev["id"]), True)
                except:
                    print_exc()
                    printf("16. %s delete device error id=%d"%(procename, thread_dev["id"]), True)
        try:
            for del_d in del_dev:   #解决运行期
                del devs[del_d]
        except:
            printf("procecache delete device error", True)
            
        #print procename, "proce_thread_devset=" , proce_thread_devset
        #增加设备(缓存中的设备不在进程中)
        for proce_cache in proce_cache_devset:
            if proce_cache not in proce_thread_devset:
                try:
                    cdev=Device.objects.filter(id=proce_cache["id"])
                    if cdev:
                        add_dev_dict(devs, cdev[0])
                        q_server.delete(devs[cdev[0].id].comm_tmp)
                        acmd=DevCmd(SN=cdev[0], CmdContent="CONNECT", CmdReturn=devs[cdev[0].id].comm.hcommpro)
                        q_server.set(devs[cdev[0].id].comm_tmp, pickle.dumps(acmd))
                        #print "22. %s add device %s"%(procename, proce_cache["id"])
                        printf("22. %s add device %s"%(procename, proce_cache["id"]), True)
                except:
                    print_exc()
                    printf("add device error", True) 
                    continue

        printf("3. %s proce_thread_devset=%s, proce_cache_devset=%s"%(procename, proce_thread_devset, proce_cache_devset))
        if procename.find("COM") >= 0:
            try:
                if devs.__len__()==0:#串口进程设备为空时自动中止进程
#                    q_server.deletemore("CENTER_HEART_*")
#                    q_server.deletemore("COM_1_*")
#                    q_server.connection.disconnect()
##                    return 0

                    #用于新增485设备, 线程暂停
                    channel_key="%s_CHANNELS"%procename   #COM_1_CHANNELS
                    channel_timeout_key="%s_CHANNELS_TIMEOUT"%procename
                    
                    channel_t=time.mktime(datetime.datetime.now().timetuple())
                    mchan_t=q_server.get(channel_timeout_key)
                    if mchan_t: 
                        try:
                            mchan_t=int(mchan_t)
                        except:
                            mchan_t=0
                        if channel_t - int(mchan_t) > PAUSE_TIMEOUT:#暂停超时，取消暂停
                            q_server.delete(channel_key)
                            q_server.delete(channel_timeout_key)
                    mchan=q_server.get(channel_key)
                    if mchan is None:
                        mchan = 0
                    try:
                        mchan=int(mchan)
                    except:
                        mchan=0                    
                    if int(mchan) == PROCESS_WAIT_PAUSE:
                        q_server.set(channel_key, "%d"%PROCESS_PAUSE)
                        q_server.set(channel_timeout_key, "%d"%(int(channel_t)))
                    if int(mchan) > PROCESS_NORMAL:
                        continue
            except:
                printf("proccache device empty return error", True)
        #设备通讯
        for devsn in devs:
            #服务停止进程退出
            proce_server_key="%s_SERVER"%procename   
            proce_stop=q_server.get(proce_server_key)
            if proce_stop == "STOP":
                try:                   
                    q_server.delete(proce_server_key)
                    #q_server.deletemore("CENTER_HEART_*")
                    printf("%s servers return "%procename, True)
                    for devsn in devs:
                        dev = devs[devsn]
                        try:
                            acmd=DevCmd(SN=dev.devobj, CmdContent="DISCONNECT", CmdReturn=-1001)   #设备监控显示设备断开
                            q_server.set(dev.comm_tmp, pickle.dumps(acmd))
                        except:
                            print_exc()
                    q_server.connection.disconnect()
                except:
                    print_exc()
                    printf("stop server error ", True)                
                return 0

            #主服务ID不一致退出
            if tt != q_server.get("CENTER_RUNING"):
                try:
                    printf("%s servers id error return "%procename, True)
                    for devsn in devs:
                        dev = devs[devsn]
                        try:
                            acmd=DevCmd(SN=dev.devobj, CmdContent="DISCONNECT", CmdReturn=-1001)   #设备监控显示设备断开
                            q_server.set(dev.comm_tmp, pickle.dumps(acmd))
                        except:
                            print_exc()
                    q_server.connection.disconnect()
                except:
                    print_exc()
                    printf("stop server error ", True)
                return 0           
            
            if procename.find("COM") >= 0:
                try:
                    #用于新增485设备, 线程暂停
                    channel_key="%s_CHANNELS"%procename   #COM_1_CHANNELS
                    channel_timeout_key="%s_CHANNELS_TIMEOUT"%procename
                    
                    channel_t=time.mktime(datetime.datetime.now().timetuple())
                    mchan_t=q_server.get(channel_timeout_key)
                    if mchan_t: 
                        try:
                            mchan_t=int(mchan_t)
                        except:
                            mchan_t=0
                        if channel_t - int(mchan_t) > PAUSE_TIMEOUT:#暂停超时，取消暂停
                            q_server.delete(channel_key)
                            q_server.delete(channel_timeout_key)
                    mchan=q_server.get(channel_key)
                    if mchan is None:
                        mchan = 0
                    try:
                        mchan=int(mchan)
                    except:
                        mchan=0                    
                    if int(mchan) == PROCESS_WAIT_PAUSE:
                        q_server.set(channel_key, "%d"%PROCESS_PAUSE)
                        q_server.set(channel_timeout_key, "%d"%(int(channel_t)))
                    if int(mchan) > PROCESS_NORMAL:
                        continue
                except:
                    printf("485 pause error", True)
                    
            dev = devs[devsn]
            #设备被禁用
            try:
                cdev=Device.objects.filter(id=dev.devobj.id)
                if cdev:
                    if not cdev[0].check_dev_enabled():
                        acmd=DevCmd(SN=dev.devobj, CmdContent="DISABLED", CmdReturn=-1002)
                        q_server.set(dev.comm_tmp, pickle.dumps(acmd))                       
                        if dev.comm.hcommpro > 0:
                            dev.comm.disconnect()
                        now_t=time.mktime(datetime.datetime.now().timetuple())
                        if now_t - dev.try_connect_delay < MAX_INTERVAL_CONNTECT_TIME:
                            dev.try_connect_delay = now_t - MAX_INTERVAL_CONNTECT_TIME      #启用设备立即重连
                        continue
                else:
                    printf("14. check_dev_enabled not find device", True)
                    continue    #设备不存在，已被删除
            except:
                printf("4. check_dev_enabled error", True)

            printf("5. %s -- dev.comm.hcommpro=%d"%(dev.devobj.alias.encode("gb18030"), dev.comm.hcommpro))
            if dev.comm.hcommpro <= 0:
                now_t=time.mktime(datetime.datetime.now().timetuple())
                if now_t - dev.try_connect_delay > MAX_INTERVAL_CONNTECT_TIME:  #未连接设备, 60秒重连一次
                    try:
                        dev.try_connect_count += 1
                        dev.try_connect_delay=time.mktime(datetime.datetime.now().timetuple())
                        printf("5. %s -- try connect device"%dev.devobj.alias.encode("gb18030"))
                        dev.comm.disconnect()
                        dev.comm.connect()
                        acmd=DevCmd(SN=dev.devobj, CmdContent="CONNECT", CmdReturn=dev.comm.hcommpro)
                        q_server.set(dev.comm_tmp, pickle.dumps(acmd))
                    except:
                        print_exc()                   
                    if dev.comm.hcommpro>0: #重试连接成功
                        try:
                            dev.try_connect_count = 0
                            set_door_connect(dev.devobj, 1)
                            if dev.devobj.sync_time:
                                dev.devobj.set_time(False)
                            check_acpanel_args(dev, dev.comm)#关于门禁控制器设备参数的回调函数
                        except:
                            print_exc()
                    else:
                        try:
                            set_door_connect(dev.devobj, 0)
                            if dev.try_connect_count > MAX_CONNECT_COUNT:   #禁用设备
                                printf("6. %s -- set dev disabled"%(dev.devobj.alias.encode("gb18030")))
                                dev.try_connect_count = 0
                                dev.devobj.set_dev_disabled()
                        except:
                            print_exc()
                continue

            try:
                if process_general_cmd(dev,q_server):    #下载命令
                    continue
            except:
                printf("process_general_cmd error", True)

            try:
                rtlog = dev.comm.get_rtlog()
                #print dev.devobj.alias," rtlog result:",rtlog["data"]#实时事件
                printf("7.%s -- rtlog result:%s"%(dev.devobj.alias.encode("gb18030"), rtlog["data"]))#固件最原始数据
                if(is_comm_io_error(rtlog["result"])):
                    printf("7. %s -- get rtlog return failed result=%d"%(dev.devobj.alias.encode("gb18030"), rtlog["result"]), True)
                    acmd=DevCmd(SN=dev.devobj, CmdContent="REAL_LOG", CmdReturn=rtlog["result"])
                    q_server.set(dev.comm_tmp, pickle.dumps(acmd))
                    dev.try_failed_time +=1
                    if(dev.try_failed_time>MAX_TRY_COMM_TIME):
                        try:
                            dev.comm.disconnect()
                            dev.try_connect_delay=time.mktime(datetime.datetime.now().timetuple())
                            set_door_connect(dev.devobj, 0)
                            dev.try_failed_time = 0
                            acmd=DevCmd(SN=dev.devobj, CmdContent="DISCONNECT", CmdReturn=-1001)
                            q_server.set(dev.comm_tmp, pickle.dumps(acmd))
                        except:
                            print_exc()
                    continue
                else:
                    try:
                        acmd=DevCmd(SN=dev.devobj, CmdContent="REAL_LOG", CmdReturn=1)
                        q_server.set(dev.comm_tmp, pickle.dumps(acmd))
                        checkdevice_and_savecache(q_server, dev.devobj)
                    except:
                        print_exc()
                    if (rtlog["result"] >0):
                        appendrtlog(q_server, dev.devobj, rtlog["data"])
            except:
                print_exc()
                printf("get rtlog error", True)
                
            try:
                ret_log=check_and_down_log(dev)    #检查定时下载记录
                if ret_log>0:
                    printf("check_and_down_log end .... ret_log=%d"%ret_log, True)
                    #print "check_and_down_log end .... ret_log=%d"%ret_log
                    pid_t=time.mktime(datetime.datetime.now().timetuple())
                    #print '---pid_t2=',pid_t
                    process_heart[procename] = pid_t
                    #g_devcenter.process_heart[procename] = pid_t
                    #q_server.set(CENTER_PROCE_HEART%procename, str(pid_t))                   
            except:
                print_exc()
                printf("check_and_down_log error", True)
                        
        delaytime=(1200-150*devs.__len__())/1000.0
        if delaytime > 0.50:
            time.sleep(delaytime)
        else:
            time.sleep(0.50)
    q_server.connection.disconnect()
    return 0

class TThreadMonitor(object):
    def __init__(self,func,args):
        self.func = func
        self.args = args

    def __call__(self):
        apply(self.func, self.args)

class TDevDataCommCenter(object):
    def __init__(self, process_heart, children_pid):
        #from mysite.iclock.models.model_device import Device, DEVICE_ACCESS_CONTROL_PANEL, COMMU_MODE_PULL_RS485, COMMU_MODE_PULL_TCPIP
        #print '----process_heart=',process_heart
        cfg=dict4ini.DictIni(os.getcwd()+"/appconfig.ini",values={"iaccess":{"max_thread":5}})
        self.max_thread = cfg.iaccess.max_thread

        self.pool = Pool(processes = self.max_thread)#进程池
        self.comport_set={}
        self.NetDev=Device.objects.filter(device_type=DEVICE_ACCESS_CONTROL_PANEL).filter(comm_type=COMMU_MODE_PULL_TCPIP)
        self.ComDev=Device.objects.filter(device_type=DEVICE_ACCESS_CONTROL_PANEL).filter(comm_type=COMMU_MODE_PULL_RS485)
        printf("self.NetDev=%s"%self.NetDev)
        self.net_dev_set=self.set_thread_dev(self.NetDev)   #将设备平均分配 生成设备列表
        printf("self.net_dev_set=%s"%self.net_dev_set)
        self.killRsagent()
        self.pid=os.getpid()
        #print '----self.pid=',self.pid主进程pid
        
        q_server=queqe_server()
        q_server.set(CENTER_MAIN_PID, "%d"%(self.pid))#主进程--darcy
        
        #print "net_dev_set=", self.net_dev_set
        for i in range(0, self.max_thread):
            devs = self.net_dev_set[i]
            tName = "Net%d" % i
            process_heart[tName] = time.mktime(datetime.datetime.now().timetuple())#子进程心跳#self.pid
            #t = threading.Thread(target = TThreadMonitor(net_task_process,(devs, len(devs), tName)))
            q_server.delete(tName)
            for dev in devs:
                q_server.rpush(tName, pickle.dumps(dev.getdevinfo()))
            self.pool.apply_async(net_task_process, [devs, len(devs), tName, process_heart, children_pid])#net_task_process进程调用--tcp/ip
            
        self.comports =Device.objects.filter(device_type=DEVICE_ACCESS_CONTROL_PANEL,comm_type=COMMU_MODE_PULL_RS485).values('com_port').distinct()
        for comport in self.comports:
            comdevs = Device.objects.filter(device_type=DEVICE_ACCESS_CONTROL_PANEL,comm_type=COMMU_MODE_PULL_RS485,com_port=comport['com_port'])
            tName="COM_%d"%comport["com_port"]
            devs=[]
            q_server.delete(tName)
            for comdev in comdevs:
                devs.append(comdev)
                q_server.rpush(tName, pickle.dumps(comdev.getdevinfo()))
            p = Process(target=net_task_process, args=(devs, len(devs), tName, process_heart, children_pid))#net_task_process进程调用--485
            q_server.set("%s_PID"%tName, "%d"%(p._parent_pid))
            p.start()
            #t = threading.Thread(target = TThreadMonitor(net_task_process,(devs, len(devs), tName)))
        q_server.save()
        q_server.connection.disconnect()
        
    def killRsagent(self):
        return os.system("taskkill /im plrscagent.* /f")
    
    def set_thread_dev(self, devset):
        devs=[]
        for i in range(0, self.max_thread):
            devs.append([])#
        for i in range(0, len(devset)):
            devs[i%self.max_thread].append(devset[i])
        return devs

    def refushcomport(self):
        from mysite.iclock.models.model_device import Device, DEVICE_ACCESS_CONTROL_PANEL, COMMU_MODE_PULL_RS485, COMMU_MODE_PULL_TCPIP
        self.comports =Device.objects.filter(device_type=DEVICE_ACCESS_CONTROL_PANEL,comm_type=COMMU_MODE_PULL_RS485).values('com_port').distinct()
        self.NetDev=Device.objects.filter(device_type=DEVICE_ACCESS_CONTROL_PANEL).filter(comm_type=COMMU_MODE_PULL_TCPIP)

    #同步前台后台设备
    def delete_device(self, devinfo):
        from mysite.iclock.models.model_device import Device, DEVICE_ACCESS_CONTROL_PANEL, COMMU_MODE_PULL_RS485, COMMU_MODE_PULL_TCPIP
        q_server=queqe_server()
        if devinfo["comm_type"]==COMMU_MODE_PULL_TCPIP:
            for i in range(0, len(self.net_dev_set)):
                for net_dev in self.net_dev_set[i]:
                    if net_dev.id== devinfo["id"]:
                        self.net_dev_set[i].remove(net_dev)
                        tName="Net%d"%i
                        q_server.delete(tName)
                        for dev in self.net_dev_set[i]:
                            q_server.rpush(tName, pickle.dumps(dev.getdevinfo()))
        elif devinfo["comm_type"]==COMMU_MODE_PULL_RS485:
            comdevs = Device.objects.filter(device_type=DEVICE_ACCESS_CONTROL_PANEL,comm_type=COMMU_MODE_PULL_RS485,com_port=devinfo["com_port"])
            tName="COM_%d"%devinfo["com_port"]
            q_server.delete(tName)
            for dev in comdevs:
                q_server.rpush(tName, pickle.dumps(dev.getdevinfo()))
        q_server.save()
        q_server.connection.disconnect()

    def edit_device(self, dev):
        from mysite.iclock.models.model_device import Device, DEVICE_ACCESS_CONTROL_PANEL, COMMU_MODE_PULL_RS485, COMMU_MODE_PULL_TCPIP
        q_server=queqe_server()
        if dev.comm_type==COMMU_MODE_PULL_TCPIP:
            for i in range(0, len(self.net_dev_set)):
                for net_dev in net_dev_set[i]:
                    if net_dev.id == dev.id:
                        ii=net_dev_set[i].index(net_dev)
                        net_dev_set[i][ii]=dev
                        #修改缓存设备信息
                        tName="Net%d"%i
                        q_server.delete(tName)
                        dev=[]
                        for dev0 in self.net_dev_set[i]:
                            try:
                                dev=Devivce.objects.filter(id=dev0.id)
                                q_server.rpush(tName, pickle.dumps(dev[0].getdevinfo()))
                            except:
                                printf("edit_device error")
        elif dev.comm_type==COMMU_MODE_PULL_RS485:
            comdevs = Device.objects.filter(device_type=DEVICE_ACCESS_CONTROL_PANEL,comm_type=COMMU_MODE_PULL_RS485,com_port=dev.com_port)
            tName="COM_%d"%dev.com_port
            devs=[]
            q_server.delete(tName)
            for comdev in comdevs:
                devs.append(comdev)
                q_server.rpush(tName, pickle.dumps(comdev.getdevinfo()))
        q_server.save()
        q_server.connection.disconnect()

    def adddevice(self,dev):
        from mysite.iclock.models.model_device import Device, DEVICE_ACCESS_CONTROL_PANEL, COMMU_MODE_PULL_RS485, COMMU_MODE_PULL_TCPIP
        self.NetDev=Device.objects.filter(device_type=DEVICE_ACCESS_CONTROL_PANEL).filter(comm_type=COMMU_MODE_PULL_TCPIP)
        q_server=queqe_server()
        if dev.comm_type==COMMU_MODE_PULL_TCPIP:
            new_dev=True    
            for dev_set in self.net_dev_set:
                if dev in dev_set:
                    new_dev=False
            if new_dev:     #设备不在线程中
                for i in range(0, self.max_thread):
                    if len(self.net_dev_set[i]) <= len(self.NetDev)/self.max_thread:    #分配至后台进程
                        self.net_dev_set[i].append(dev)
                        tName="Net%d"%i
                        q_server.rpush(tName, pickle.dumps(dev.getdevinfo()))
                        break
        elif dev.comm_type==COMMU_MODE_PULL_RS485:
            comdevs = Device.objects.filter(device_type=DEVICE_ACCESS_CONTROL_PANEL,comm_type=COMMU_MODE_PULL_RS485,com_port=dev.com_port)
            tName="COM_%d"%dev.com_port
            devs=[]
            q_server.delete(tName)
            for comdev in comdevs:
                devs.append(comdev)
                q_server.rpush(tName, pickle.dumps(comdev.getdevinfo()))
            com_list=[]
            for v in self.comports:
                com_list.append(v.values()[0])
            if dev.com_port not in com_list:
                #t = threading.Thread(target = TThreadMonitor(net_task_process,(devs, len(devs), tName)))
                self.comports =Device.objects.filter(device_type=DEVICE_ACCESS_CONTROL_PANEL,comm_type=COMMU_MODE_PULL_RS485).values('com_port').distinct()
                p = Process(target=net_task_process, args=(devs, len(devs), tName))
                q_server.set("%s_PID"%tName, "%d"%(p._parent_pid))
                p.start()
        q_server.save()
        q_server.connection.disconnect()

def check_sync_db_cachel():
    from mysite.iclock.models.model_device import Device, DEVICE_ACCESS_CONTROL_PANEL
    from mysite.iclock.models.model_devcmd import DevCmd, trigger_cmd_device
    device=Device.objects.filter(device_type=DEVICE_ACCESS_CONTROL_PANEL)

    for dev in device:
        q_server=queqe_server()
        q_server.delete(dev.new_command_list_name())
        q_server.connection.disconnect()
        devcmd=DevCmd.objects.filter(CmdReturn=None).filter(CmdImmediately=0).filter(SN=dev).order_by('id')
        for cmd in devcmd:
            trigger_cmd_device(cmd)

#某个进程异常，杀掉子进程，然后重启所有进程
def killall_pid(children_pid=None):
    try:
        q_server = queqe_server()
        if children_pid:#只杀子进程，避免“自杀”
            for pid in children_pid.values:
                os.system("taskkill /PID %s /F /T" % pid)
        else:
            main_pid = q_server.get(CENTER_MAIN_PID)
            os.system("taskkill /PID %s /F /T" % main_pid)
        q_server.connection.disconnect()
    except:
        pass
    
def clear_file_cache(q_server):
    #q_server.deletemore("CENTER_HEART_*")  #删除所有进程ID
    q_server.deletemore("ICLOCK_*_LAST_ACTIVEITY")  #最后连接时间
    q_server.deletemore("DEV_COMM_PROGRESS_*")  #进度条缓存
    q_server.deletemore("DEV_COMM_SYNC_*")  #进度条缓存
    q_server.deletemore("*_CHANNELS")   #清除485暂停通道  
    q_server.deletemore("*_CHANNELS_TIMEOUT")
    q_server.deletemore("*_PID")   #清除485暂停通道
    q_server.deletemore("ICLOCK_*_TMP")   #清除当前命令缓存
    q_server.deletemore("DEVICE_DOOR_*")   #门状态缓存
    q_server.deletemore("MONITOR_RT")   #清除实时监控数据
    q_server.delete(CENTER_PROCE_LIST)
    q_server.delete(DEVOPT)
    q_server.deletemore("*_SERVER")
    tt="{0:%Y-%m-%d %X}".format(datetime.datetime.now())
    q_server.set("CENTER_RUNING", tt)
    

def rundatacommcenter():
    from mysite.iclock.models.model_device import Device, COMMU_MODE_PULL_RS485
    global g_devcenter
    manager = Manager()
    printf("1.--rundatacenter--")
    process_heart = manager.dict()#子进程心跳
    children_pid = manager.dict()#总进程pid（用于杀僵尸进程）
    #dev_doorstatus = manager.dict()#实时监控门状态时。保存设备状态（未解析前）
#    check_sync_db_cachel()  #同步数据库与缓存数据
    try:
        deletelog()
    except:
        pass

    killall_pid()#缓存中记录了之前的主进程pid，杀掉
    #print '---current_pid=',os.getpid()
    try:
        q_server=queqe_server()
        clear_file_cache(q_server)
        g_devcenter = TDevDataCommCenter(process_heart, children_pid)
    except:
        print_exc();
#    global g_video_server
#    VidDev=Device.objects.filter(device_type=DEVICE_VIDEO_SERVER)
#    for vid in VidDev:
#        vidcom = TDevVideo()
#        vidcom.login(vid.ipaddress, vid.ip_port, vid.video_login, vid.comm_pwd)
#        g_video_server[vid.ipaddress]=vidcom
#    print "aaaa  g_video_server", g_video_server

    while True:
        #print '---while true-----'
        try:
            len=q_server.llen(DEVOPT)
            if len > 0:
                acmd=q_server.lpop(DEVOPT)
                if acmd is None:
                    continue
                try:
                    devinfo=pickle.loads(acmd)
                except:
                    devinfo=None
                if devinfo is not None:
                    try:
                        #print "2. add com device %s operate=%s"%(devinfo["id"], devinfo["operatstate"])
                        printf("2. add com device %s operate=%s"%(devinfo["id"], devinfo["operatstate"]), True)
                        if (devinfo["operatstate"]==OPERAT_ADD):   #新增设备
                            dev=Device.objects.filter(id = devinfo["id"])
                            if dev:
                                g_devcenter.adddevice(dev[0])
                            else:
                                q_server.lpush(DEVOPT, pickle.dumps(devinfo))   #设备还未save进数据库
                                time.sleep(10)
                        elif (devinfo["operatstate"]==OPERAT_EDIT):  #修改设备时，先删除后增加设备
                            g_devcenter.delete_device(devinfo)
                            dev=Device.objects.filter(id = devinfo["id"])
                            if dev:
                                g_devcenter.adddevice(dev[0])
                            else:
                                q_server.lpush(DEVOPT, pickle.dumps(devinfo))   #设备还未save进数据库
                                time.sleep(10)                           
                        elif (devinfo["operatstate"]==OPERAT_DEL):
                                g_devcenter.delete_device(devinfo)
                    except:
                        printf("device opreater error", True)
                continue
            else:
                time.sleep(5)
            if (q_server.llen("MONITOR_RT")>MAX_RTLOG):
                q_server.lock_delete("MONITOR_RT")
                q_server.lock_delete("ALARM_RT")
            #僵尸进程检测
            pid_set=q_server.lrange(CENTER_PROCE_LIST, 0, -1)
            #print '-----pid_set=',pid_set
            for p in pid_set:
                #pid_time = q_server.get(CENTER_PROCE_HEART%p)
                #pid_time = g_devcenter.process_heart[p]
                #print '-----here  process_heart=',process_heart
                pid_time = process_heart[p] 
                #print '----new pid_time=',pid_time
                #print '---!!!!!!!-children_pid=',children_pid
                if pid_time:
                    now_t = time.mktime(datetime.datetime.now().timetuple())
                    #print '-----now_t-float(pid_time)=',now_t - float(pid_time)
                    
                    if now_t - pid_time > 60*60*1:#     #now_t - float(pid_time)#1小时没心跳, 杀掉所有进程，重新启动
                        printf("PID die**********", True)
                        #print '---PID die--'
                        try:
                            killall_pid()#杀掉后服务会自动重启
                            print '****kill pid finished'
                            #time.sleep(60*5)#60*5
                        except:
                            print '-----killall pid error'
                        break;

        except:
            continue
        time.sleep(1)
    q_server.connection.disconnect()

if __name__ == '__main__':
    print 'start at:', ctime()

    rundatacenter()
    print 'finish'
