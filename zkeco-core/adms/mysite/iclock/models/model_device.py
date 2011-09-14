# -*- coding: utf-8 -*-
from django.db import models, connection
import datetime
import sched, time
import os
from django.conf import settings
from dbapp.utils import *
from django.utils.translation import ugettext_lazy as _
from base.models import CachingModel, Operation, ModelOperation
from mysite.personnel.models.model_dept import DeptForeignKey, DEPT_NAME
from mysite.personnel.models.model_area import AreaForeignKey
from redis.server import queqe_server
from dbapp import data_edit
from traceback import print_exc
from django import forms
from mysite.utils import printf
from threading import Event, Semaphore
from base.crypt import encrypt,decrypt
import re
from model_dstime import DSTime
try:
    import cPickle as pickle
except:
    import pickle
s=Semaphore()
MAX_COMMAND_TIMEOUT_SECOND  = 30
#MAX_ACPANEL_COUNT = 50#最大支持50台门禁控制器

DEV_STATUS_OK=1
DEV_STATUS_TRANS=2
DEV_STATUS_OFFLINE=3
DEV_STATUS_PAUSE=0
CMD_OK=200

DEVOPT="DEV_OPERATE"
DeviceAdvField=['com_address','device_type', 'acpanel_type']
init_settings = []
if settings.APP_CONFIG["remove_permision"]:
    init_settings = [ k.split(".")[1] for k,v in settings.APP_CONFIG["remove_permision"].items() if v=="False" and k.split(".")[0]=="Device"]

if settings.APP_CONFIG["iclock"]:
    if settings.APP_CONFIG["iclock"].has_key('DeviceAdvField'):
        DeviceAdvField=[]
    
def encodetime():
    dt = datetime.datetime.now()
    tt = ((dt.year-2000)*12*31 + (dt.month-1)*31 + (dt.day-1))*(24*60*60) + dt.hour*60*60 + dt.minute*60 + dt.second
    return tt

def format_time(tmstart, tmend):
    u"""
    时间格式转换
    """
    st=tmstart.hour*100+tmstart.minute
    et=tmend.hour*100+tmend.minute
    return (st<<16)+(et&(0xFFFF))

class ReadData(object):
    def __init__(id, timeout):
        self.id=id
        self.returndata=""    
        s=sched.scheduler(time.time, time.sleep)
        for i in range(0, timeout, 2):
            s.enter(i, 1, self.read_data(), ())
        s.run()
    def read_data():
        from mysite.iclock.models.model_devcmd import DevCmd
        devcmd=DevCmd.objects.filter(id=self.id)
        if len(devcmd.CmdReturnContent)>0:
            self.returndata=devcmd.CmdReturnContent

def decode_holiday(holidayset):
    line=""
    g=[]
    for hol in holidayset:
        start = hol.start_date
        end = hol.end_date
        delta = (end-start).days+1
        for index in range(delta):
            date = start + datetime.timedelta(index)
            date = date.year*10000 + date.month*100 + date.day
            linestr={}
            linestr["HolidayType"]=hol.holiday_type
            linestr["Holiday"]=date
            if linestr not in g:
                g.append(linestr.copy())
                line += ("\r\n" if line else "") +"Holiday=%d\tHolidayType=%d\tLoop=%d"%(linestr["Holiday"], linestr["HolidayType"], hol.loop_by_year)
    return line

def decode_timeseg(segmentset):
    line=""
    for settime in segmentset:
        print settime
        retbuf = ""
        retbuf += "TimezoneId=%d\t"%settime.id
        retbuf += "SunTime1=%d\t"%format_time(settime.sunday_start1,settime.sunday_end1)
        retbuf += "SunTime2=%d\t"%format_time(settime.sunday_start2,settime.sunday_end2)
        retbuf += "SunTime3=%d\t"%format_time(settime.sunday_start3,settime.sunday_end3)
        retbuf += "MonTime1=%d\t"%format_time(settime.monday_start1,settime.monday_end1)
        retbuf += "MonTime2=%d\t"%format_time(settime.monday_start2,settime.monday_end2)
        retbuf += "MonTime3=%d\t"%format_time(settime.monday_start3,settime.monday_end3)
        retbuf += "TueTime1=%d\t"%format_time(settime.tuesday_start1,settime.tuesday_end1)
        retbuf += "TueTime2=%d\t"%format_time(settime.tuesday_start2,settime.tuesday_end2)
        retbuf += "TueTime3=%d\t"%format_time(settime.tuesday_start3,settime.tuesday_end3)
        retbuf += "WedTime1=%d\t"%format_time(settime.wednesday_start1,settime.wednesday_end1)
        retbuf += "WedTime2=%d\t"%format_time(settime.wednesday_start2,settime.wednesday_end2)
        retbuf += "WedTime3=%d\t"%format_time(settime.wednesday_start3,settime.wednesday_end3)
        retbuf += "ThuTime1=%d\t"%format_time(settime.thursday_start1,settime.thursday_end1)
        retbuf += "ThuTime2=%d\t"%format_time(settime.thursday_start2,settime.thursday_end2)
        retbuf += "ThuTime3=%d\t"%format_time(settime.thursday_start3,settime.thursday_end3)
        retbuf += "FriTime1=%d\t"%format_time(settime.friday_start1,settime.friday_end1)
        retbuf += "FriTime2=%d\t"%format_time(settime.friday_start2,settime.friday_end2)
        retbuf += "FriTime3=%d\t"%format_time(settime.friday_start3,settime.friday_end3)
        retbuf += "SatTime1=%d\t"%format_time(settime.saturday_start1,settime.saturday_end1)
        retbuf += "SatTime2=%d\t"%format_time(settime.saturday_start2,settime.saturday_end2)
        retbuf += "SatTime3=%d\t"%format_time(settime.saturday_start3,settime.saturday_end3)
        retbuf += "Hol1Time1=%d\t"%format_time(settime.holidaytype1_start1,settime.holidaytype1_end1)
        retbuf += "Hol1Time2=%d\t"%format_time(settime.holidaytype1_start2,settime.holidaytype1_end2)
        retbuf += "Hol1Time3=%d\t"%format_time(settime.holidaytype1_start3,settime.holidaytype1_end3)
        retbuf += "Hol2Time1=%d\t"%format_time(settime.holidaytype2_start1,settime.holidaytype2_end1)
        retbuf += "Hol2Time2=%d\t"%format_time(settime.holidaytype2_start2,settime.holidaytype2_end2)
        retbuf += "Hol2Time3=%d\t"%format_time(settime.holidaytype2_start3,settime.holidaytype2_end3)
        retbuf += "Hol3Time1=%d\t"%format_time(settime.holidaytype3_start1,settime.holidaytype3_end1)
        retbuf += "Hol3Time2=%d\t"%format_time(settime.holidaytype3_start2,settime.holidaytype3_end2)
        retbuf += "Hol3Time3=%d"%format_time(settime.holidaytype3_start3,settime.holidaytype3_end3)
        line += ("\r\n" if line else "") +"%s"%(retbuf)
    return line

def device_cmd(device):
    q_server=queqe_server()
    try:
        ret=q_server.llen(device.new_command_list_name())
        return ret
    except:
        traceback.print_exc()
    finally:
        q_server.connection.disconnect()
    return 0

TIMEZONE_CHOICES=(
    (-12,'Etc/GMT-12'),
    (-11,'Etc/GMT-11'),
    (-10,'Etc/GMT-10'),
    (-9,'Etc/GMT-9'),
    (-8,'Etc/GMT-8'),
    (-7,'Etc/GMT-7'),
    (-6,'Etc/GMT-6'),
    (-5,'Etc/GMT-5'),
    (-4,'Etc/GMT-4'),
    (-3,'Etc/GMT-3'),
    (-2,'Etc/GMT-2'),
    (-1,'Etc/GMT-1'),
    (0,'Etc/GMT'),
    (1,'Etc/GMT+1'),
    (2,'Etc/GMT+2'),
    (3,'Etc/GMT+3'),
    (4,'Etc/GMT+4'),
    (5,'Etc/GMT+5'),
    (330,'Etc/GMT+0530 India'),
    (6,'Etc/GMT+6'),
    (7,'Etc/GMT+7'),
    (8,'Etc/GMT+8'),
    (9,'Etc/GMT+9'),
    (10,'Etc/GMT+10'),
    (11,'Etc/GMT+11'),
    (12,'Etc/GMT+12'),
    (13,'Etc/GMT+13'),
)

#COMPORT_CHOICES=(
#    (1,_('COM1')),(2,_('COM2')),(3,_('COM3')),(4,_('COM4')),(5,_('COM5')),
#    (6,_('COM6')),(7,_('COM7')),(8,_('COM8')),(9,_('COM9')),(10,_('COM10')),
#)
COMPORT_CHOICES = tuple([(i, 'COM'+str(i)) for i in range(1, 255)])#1-254

CONNECTTYPE_CHOICES = (
    (0, _(u'内容类型')),
    (1, _(u'无线局域网')), 
    (2, _(u'GPRS')), 
    (3, _(u'3G适配器')),
    (4, _(u'232')),
    (5, _(u'485')),
)

BAUDRATE_CHOICES=(
    (0,'9600'),(1,'19200'),(2,'38400'),(3,'57600'),(4,'115200'),
)

COMMU_MODE_PULL_TCPIP = 1
COMMU_MODE_PULL_RS485 = 2
COMMU_MODE_PUSH_HTTP = 3

COMMU_MODE_CHOICES=(
    (COMMU_MODE_PULL_TCPIP,_('TCP/IP')),
    (COMMU_MODE_PULL_RS485,_('RS485')),
    (COMMU_MODE_PUSH_HTTP, _('HTTP')), 
)

DEVICE_TIME_RECORDER = 1
DEVICE_ACCESS_CONTROL_PANEL = 2
DEVICE_ACCESS_CONTROL_DEVICE = 3
DEVICE_VIDEO_SERVER =4
DEVICE_TYPE=(
    (DEVICE_TIME_RECORDER,_(u'考勤机')),
    (DEVICE_ACCESS_CONTROL_PANEL,_(u'门禁控制器')),
    (DEVICE_VIDEO_SERVER,_(u'视频服务器')),
)

ACPANEL_1_DOOR = 1
ACPANEL_2_DOOR = 2
ACPANEL_4_DOOR = 4

ACPANEL_TYPE_CHOICES=(
    (ACPANEL_1_DOOR,_(u'单门控制器')),
    (ACPANEL_2_DOOR,_(u'两门控制器')),
    (ACPANEL_4_DOOR,_(u'四门控制器')),
)
FPVERSION=(
    ('9',_(u'9.0算法')),
    ('10',_(u'10.0算法')),
)

class Device(CachingModel):
    '''
    设备表模型
    '''
#    id = models.AutoField(db_column="devid", primary_key=True, null=False, editable=False)
    sn = models.CharField(_(u'序列号'), max_length=20, null=True, blank=True)# unique=True
    device_type = models.IntegerField(_(u'设备类型'), editable=True, choices=DEVICE_TYPE, default=1)
    last_activity = models.DateTimeField(_(u'最近联机时间'), null=True, blank=True, editable=False)
    trans_times = models.CharField(_(u'定时传送时间'), max_length=50, null=True, blank=True, default="00:00;14:05")#, help_text=_('Setting device for a moment from the plane started to send checks to the new data server. Hh: mm (hours: minutes) format, with a number of time between the semicolon (;) separately')
    trans_interval = models.IntegerField(_(u'刷新间隔时间(分钟)'), db_column="TransInterval", default=1, null=True, blank=True)#, help_text=_('Device set for each interval to check how many minutes to send new data server')
    log_stamp = models.CharField(_(u'传送签到记录标记'), max_length=20, null=True, blank=True)#, help_text=_('Logo for the latest device to the server send the transactions timestamps')
    oplog_stamp = models.CharField(_(u'传送用户数据标记'), max_length=20, null=True, blank=True)#, help_text=_('Marking device for the server to the employee data transfer as timestamps')
    photo_stamp = models.CharField(_(u'传送图片标记'), max_length=20, null=True, blank=True)#, help_text=_('Marking device for the server to the picture transfer as timestamps')
    alias = models.CharField(_(u'设备名称'), max_length=20)
    update_db = models.CharField(_(u'数据更新标志'), db_column="UpdateDB", max_length=10, null=True, default="1111101000", blank=True, editable=True)#, help_text=_('To identify what kind of data should be transfered to the server')
    fw_version = models.CharField(_(u'固件版本'), max_length=30, null=True, blank=True, editable=False)
    device_name = models.CharField(_(u'设备型号'), max_length=30, null=True, blank=True, editable=False)
    fp_count = models.IntegerField(_(u'指纹数'), null=True, blank=True, editable=False)
    transaction_count = models.IntegerField(_(u'记录数'), null=True, blank=True, editable=False)
    user_count = models.IntegerField(_(u'用户数'), null=True, blank=True, editable=False)
    main_time = models.CharField(_(u'动作时间'), max_length=20, null=True, blank=True, editable=False)
    max_user_count = models.IntegerField(_(u'最大用户容量'), null=True, blank=True, editable=False)
    max_finger_count = models.IntegerField(_(u'最大指纹容量'), null=True, blank=True, editable=False)
    max_attlog_count = models.IntegerField(_(u'最大记录容量'), null=True, blank=True, editable=False)
    alg_ver = models.CharField(_(u'算法版本'), max_length=30, null=True, blank=True, editable=False)
    flash_size = models.CharField(_(u'总Flash容量'), max_length=10, null=True, blank=True, editable=False)
    free_flash_size = models.CharField(_(u'剩余Flash容量'), max_length=10, null=True, blank=True, editable=False)
    language = models.CharField(_(u'语言'), max_length=30, null=True, blank=True, editable=False)
    lng_encode = models.CharField(_(u'语言编码'), max_length=10, null=True, blank=True, editable=False, default="gb2312")
    volume = models.CharField(_(u'容量'), max_length=10, null=True, blank=True, editable=False)
    dt_fmt = models.CharField(_(u'日期格式'), max_length=10, null=True, blank=True, editable=False)
    is_tft = models.CharField(_(u'是否为彩屏'), max_length=5, null=True, blank=True, editable=False)
    platform = models.CharField(_(u'系统平台'), max_length=20, null=True, blank=True, editable=False)
    brightness = models.CharField(_(u'分辨率'), max_length=5, null=True, blank=True, editable=False)
    oem_vendor = models.CharField(_(u'制造商'), max_length=30, null=True, blank=True, editable=False)
    city = models.CharField(_(u'所在城市'), max_length=50, null=True, blank=True)#, help_text=_('City of the location')
    lockfun_on = models.SmallIntegerField(db_column='AccFun', default=0, blank=True, editable=False)#, help_text=_('Access Function')
    tz_adj = models.SmallIntegerField(_(u'时区'), db_column="TZAdj", default=8, null=True, blank=True, editable=True, choices=TIMEZONE_CHOICES)#help_text=_('Timezone of the location'), 
    #add as follows by darcy
    comm_type = models.SmallIntegerField(_(u'通信方式'), default=3, editable=True, choices=COMMU_MODE_CHOICES)#通讯类型null=True, 
    #agent_ipaddress = models.IPAddressField(_(u'通信中'), max_length=20, null=True, blank=True, editable=True, default="")
    agent_ipaddress = models.CharField(_(u'通信中'), max_length=20, null=True, blank=True, editable=True, default="")
    ipaddress = models.IPAddressField(_(u'IP地址'), max_length=20, null=True, blank=True, editable=True)
    ip_port = models.IntegerField(_(u'IP端口号'),null=True, blank=True, editable=True,default=4370)
    com_port = models.SmallIntegerField(_(u'串口号'), default=1, null=True, blank=True, editable=True, choices=COMPORT_CHOICES)#串口号
    baudrate = models.SmallIntegerField(_(u'波特率'), default=2, null=True, blank=True, editable=True, choices=BAUDRATE_CHOICES)#波特率
    com_address = models.SmallIntegerField(_(u'485地址'), blank=True, null=True,default=1)
    area = AreaForeignKey(verbose_name=_(u'所属区域'), editable=True, null=True)# default=1, 
    #comm_pwd = models.CharField(_(u'通讯密码'), max_length=16, null=True, blank=True, editable=True)#仅门禁用，表单在新增时显示
    comm_pwd = models.CharField(_(u'通讯密码'), max_length=32, null=True, blank=True, editable=True)#仅门禁用，表单在新增时显示 加密后需增加长度
    acpanel_type = models.IntegerField(_(u'门禁控制器类型'), choices=ACPANEL_TYPE_CHOICES, default=2, null=True, blank=True, editable=True,)
    sync_time = models.BooleanField(_(u'自动同步设备时间'), null=False, default=True, blank=True, editable=True)
    four_to_two = models.BooleanField(_(u'切换为两门双向'), null=False, default=False, blank=True, editable=True) #C4-400,C3-400help_text=_(u" (四门单向与两门双向之间切换)"),
    video_login = models.CharField(_(u'用户名'), max_length=20, null=True, blank=True, editable=True)    
    fp_mthreshold = models.IntegerField(_(u'指纹比对阀值'), null=True, blank=True, editable=False)
    Fpversion = models.CharField(verbose_name=_(u'设备指纹识别版本'), max_length=10, null=True, blank=False, editable=False,default='9',choices=FPVERSION)
    enabled = models.BooleanField(_(u'是否启用'), null=False, default=True, blank=True, editable=False)#启用True(1)-禁用False(0)-默认为1
    
    max_comm_size = models.IntegerField(_(u'和服务器通讯的最大数据包长度(KB)'), default=40, null=True, blank=True, editable=True)
    max_comm_count = models.IntegerField(_(u'和服务器通讯的最大命令个数'), default=20, null=True, blank=True, editable=True)
    realtime = models.BooleanField(_(u'实时上传数据'), null=False, default=False, blank=True, editable=True)
    delay = models.IntegerField(_(u'查询记录时间(秒)'), default=10, null=True, blank=True, editable=True)
    encrypt = models.BooleanField(_(u'加密传输数据'), null=False, default=False, blank=True, editable=True)
    dstime = models.ForeignKey(DSTime, verbose_name=_(u'夏令时'),editable=False, null=True, blank=True)
    
    def data_valid(self, sendtype):
        #print "sendtype:%s",sendtype

#        if self.comm_type == COMMU_MODE_PULL_RS485:#rs485通讯
#            tmp_dev = Device.objects.filter(com_port=self.com_port, com_address=self.com_address)
#            if tmp_dev and tmp_dev[0].id != self.id:#
#                raise Exception(_(u'串口 %(f)s 的485地址 %(ff)s 已存在')%{"f":dict(COMPORT_CHOICES)[self.com_port], "ff":self.com_address})                   
            
        if self.comm_type in [COMMU_MODE_PULL_TCPIP, COMMU_MODE_PUSH_HTTP]:
            #if self.ipaddress:#当通讯方式为485时ip地址为空
            tmp_ip = Device.objects.filter(ipaddress__exact = self.ipaddress.strip())
            if (self.comm_type==COMMU_MODE_PULL_TCPIP) and len(tmp_ip)>0 and tmp_ip[0].id != self.id:   #编辑状态
                raise Exception(_(u'IP地址为:%s 的设备已存在')%self.ipaddress)
        self.__class__.page_input=True              #当修改设备信息时需要下发指令，增加此属性
        
    def save(self, **args):
        from django.conf import settings
        if self.comm_pwd:
            dev = Device.objects.filter(pk=self.pk)
            if len(dev)!=0:
                if dev[0].comm_pwd == self.comm_pwd and not dev[0].comm_pwd.isdigit():
                    pass
                else:
                    self.comm_pwd = encrypt(self.comm_pwd)
            else:
                self.comm_pwd = encrypt(self.comm_pwd)
        if self.comm_type == COMMU_MODE_PULL_RS485:#rs485通讯
            self.ipaddress = None
            self.ip_port = None
        elif self.comm_type in [COMMU_MODE_PULL_TCPIP, COMMU_MODE_PUSH_HTTP]:
            self.com_address = None
            self.com_port = None
            self.baudrate = None
        try:
            if self.device_type == DEVICE_TIME_RECORDER: 
                #新增、修改时考勤的序列号不为空(考勤)，门禁新增时为'',修改时可能为空可能不为空(用户不可见)
                tmp_sn = Device.objects.filter(sn__exact=self.sn.strip())
                if len(tmp_sn) > 0 and tmp_sn[0].id != self.id:   #编辑状态
                    raise Exception(_(u'序列号：%s 已存在') % self.sn)

                s.acquire()
                count=Device.objects.filter(device_type=DEVICE_TIME_RECORDER).count()
                try:
                    if (count < settings.ATT_DEVICE_LIMIT) or (count == settings.ATT_DEVICE_LIMIT and self.pk):
                        self.acpanel_type = None
                        super(Device, self).save(**args)
                    elif settings.ZKECO_DEVICE_LIMIT != 0:
                        count=Device.objects.filter(device_type__in = [DEVICE_TIME_RECORDER, DEVICE_ACCESS_CONTROL_PANEL]).count()
                        if (count < settings.ZKECO_DEVICE_LIMIT) or (count == settings.ZKECO_DEVICE_LIMIT and self.pk):
                            self.acpanel_type = None
                            super(Device, self).save(**args)
                        else:
                            raise Exception(_(u"登记的设备总数%(d1)s，已经达到系统限制%(d2)s！")%{"d1":count,"d2":settings.ZKECO_DEVICE_LIMIT});
                    else:                        
                        raise Exception(_(u"登记的考勤机数%(d1)s，已经达到系统限制%(d2)s！")%{"d1":count,"d2":settings.ATT_DEVICE_LIMIT});
                finally:
                        s.release()
                if hasattr(self.__class__,"page_input"):
                    if self.__class__.page_input:                                    
                        from mysite.iclock.dataprocaction import append_dev_cmd
                        append_dev_cmd(self,"CHECK")      #修改或新增都需要对机器下发CHECK指令
                        self.__class__.page_input=False
                
            else:
                #force_insert = 'force_insert' in args.keys() and args['force_insert'] or False#update时为False不判断最大数量
                tmp_alias = Device.objects.filter(device_type__in = [DEVICE_ACCESS_CONTROL_PANEL, DEVICE_VIDEO_SERVER]).filter(alias__exact = self.alias.strip())
                if len(tmp_alias)>0 and tmp_alias[0] != self:   #编辑状态
                    raise Exception(_(u'设备名称：%s 已存在') % self.alias)
                
                if self.device_type == DEVICE_ACCESS_CONTROL_PANEL:
                    s.acquire()
                    acc_limit = Device.objects.filter(device_type=DEVICE_ACCESS_CONTROL_PANEL).count()
                    try:
                        if (acc_limit < settings.MAX_ACPANEL_COUNT) or (acc_limit == settings.MAX_ACPANEL_COUNT and self.pk):
                            self.TZAdj = None
                            self.max_comm_count = None
                            self.max_comm_size = None
                            self.delay = None
                            #self.Fpversion = 10
                            super(Device, self).save(**args)
                        elif settings.ZKECO_DEVICE_LIMIT != 0:
                            count = Device.objects.filter(device_type__in = [DEVICE_TIME_RECORDER, DEVICE_ACCESS_CONTROL_PANEL]).count()
                            if (count < settings.ZKECO_DEVICE_LIMIT) or (count == settings.ZKECO_DEVICE_LIMIT and self.pk):
                                self.TZAdj = None
                                self.max_comm_count = None
                                self.max_comm_size = None
                                self.delay = None
                                #self.Fpversion = 10
                                super(Device, self).save(**args)
                            else:
                                raise Exception(_(u"登记的设备总数，已经达到系统限制！"));
                        else:                        
                            raise Exception(_(u'系统最大支持%s台门禁控制器') % settings.MAX_ACPANEL_COUNT)
                    finally:
                            s.release()
                elif self.device_type == DEVICE_VIDEO_SERVER:
                    self.acpanel_type = None
                    self.Fpversion = None
                    print "save video server"
                    super(Device, self).save(**args)           
                
        except Exception, e:
            print_exc()
            raise e
    def delete(self):
        try:
            devinfo=self.getdevinfo()
            #删除相关缓存
            self.clear_device_cache()
            
            q_server=queqe_server()
            if self.device_type==DEVICE_ACCESS_CONTROL_PANEL:
                from mysite.iaccess.dev_comm_center import OPERAT_DEL
                devinfo["operatstate"] = OPERAT_DEL
                minfo=True      #没有相同操作
                len=q_server.llen(DEVOPT)   #设备操作列表
                for i in range(0, len, -1): #查询是否有同样操作，没有相同的操作就加, 
                    info=q_server.lrange(DEVOPT, i, i)
                    try:
                        dinfo=pickle.loads(info[0])
                        if dinfo["id"] == devinfo["id"]:
                            minfo=False
                            break;
                    except:
                        dinfo=None                        
                if minfo:
                    #print "add operate delete"
                    q_server.rpush(DEVOPT, pickle.dumps(devinfo))
            q_server.connection.disconnect()
            super(Device, self).delete()
        except Exception, e:
            print_exc()
            raise e

    def clear_device_cache(self):
        q_server=queqe_server()
        q_server.delete(self.new_command_list_name())
        q_server.delete(self.processing_command_set_name())
        q_server.delete(self.cache_key())
        q_server.delete(self.command_temp_list_name())
        q_server.delete(self.command_count_key())
        q_server.delete(self.get_doorstate_cache_key())
        q_server.delete(self.get_last_activity())
        q_server.connection.disconnect()
        
    def get_std_fw_version(self):
        return ""
    
    def cache_key(self):
        return "ICLOCK_%s"%self.id
    
    def new_command_list_name(self):
        ''' 
        命令队列的名称格式  NEWCMDS_设备ID
        每个设备对应一个name
        '''
        return "NEWCMDS_%s"%self.id

    #命令执行
    def processing_command_set_name(self):
        return "PROCCMDS_%s"%self.id
    
    #当前执行命令缓存
    def command_temp_list_name(self):
        return "ICLOCK_%s_TMP"%self.id

    def command_count_key(self):
        ''' 命令统计数目 key 名称 '''
        return "ICLOCK_%s_CMD"%self.id
    
    #设备状态-解析为门状态
    def get_doorstate_cache_key(self):
        '''
        门状态key名称
        '''
        return "DEVICE_DOOR_%s"%self.id
        #return "DEVICE_%s_DOORSTATUS" % self.id

    #最后连接时间
    def get_last_activity(self):
        return "ICLOCK_%d_LAST_ACTIVEITY"%self.id
    
    #下载新记录标记
    def get_transaction_cache(self):
        return "ICLOCK_%d_TRANS_CACHE"%self.id
    
    def set_fquere_progress(self, gress, session_key):
        q_server=queqe_server()
        q_server.set("DEV_COMM_PROGRESS_%s"%session_key, "%s,%d"%(self.alias.encode("gb18030"), gress))
        q_server.connection.disconnect()
        return 0
        
    def set_current_cmd(self, devcmd_obj):
        q_server=queqe_server()
        q_server.set(self.command_temp_list_name(), pickle.dumps(devcmd_obj))
        q_server.connection.disconnect()

    def get_dyn_state(self):
        try:
            if self.state==DEV_STATUS_PAUSE:
                return DEV_STATUS_PAUSE
            if not self.last_activity:
                return DEV_STATUS_OFFLINE
            d=datetime.datetime.now()-self.last_activity
            if d>datetime.timedelta(0,5*60):
                return DEV_STATUS_OFFLINE
            #如果有命令等待执行，返回“通讯中”
            if device_cmd(self)>0:  #if DevCmd.objects.filter(SN=self,CmdOverTime__isnull=True).count()>0:
                return DEV_STATUS_TRANS
            return DEV_STATUS_OK
        except:
            errorLog()
            
    def check_dev_enabled(self):
        return self.enabled
    
    def set_dev_disabled(self):
        self.enabled = False
        self.save(force_update=True)
    
    def set_dev_enabled(self):
        self.enabled = True
        self.save(force_update=True)
        
    def get_img_url(self):
        if self.DeviceName:
            imgUrl=settings.MEDIA_ROOT+'img/device/'+self.DeviceName+'.png'
            if os.path.exists(imgUrl):
                return settings.MEDIA_URL+'/img/device/'+self.DeviceName+'.png'
        return settings.MEDIA_URL+'/img/device/noImg.png'
    
    def get_thumbnail_url(self):
        return self.get_img_url()
    
    def set_mthreshold(self, threshold):
        from mysite.iclock.dataprocaction import appendDevCmdReturn
        CMD = "OPTION SET MThreshold=%d" % threshold   #同步指纹阀值
        #return self.appendcmdreturn(CMD, MAX_COMMAND_TIMEOUT_SECOND)#appendcmdreturn
        return appendDevCmdReturn(self, CMD)

    
    def __unicode__(self):
        if self.device_type in [DEVICE_ACCESS_CONTROL_PANEL, DEVICE_VIDEO_SERVER]:
            return self.alias
        return self.sn+(self.alias and "("+self.alias+")" or "")

    class Syncdata(Operation):
        help_text = _(u"""同步所有数据""")
        verbose_name = _(u"""同步所有数据""")
        def action(self):
            self.object.set_all_data()#考勤门禁通用
            
    class SyncACPanelTime(Operation):
        verbose_name = _(u"""同步时间""")
        help_text = _(u"""同步设备时间为服务器时间。""")

        def action(self):
            if self.object.device_type==DEVICE_ACCESS_CONTROL_PANEL:
                self.object.set_time()
            #else:
                #raise Exception(_(u"设备：%s 并非门禁控制器，该操作只能同步门禁控制器时间")%self.object.alias)
    
    class OpChangeMThreshold(Operation):
        verbose_name = _(u"""修改指纹比对阀值""")
        help_text = _(u"""修改设备中进行指纹比对时的阀值。默认阀值为55。""")
        
        params = (
            ('threshold', models.IntegerField(_(u"指纹比对阀值"), null=True, blank=False, max_length=3, help_text=_(u'(范围35-100)'))),
        )
        #非紧急命令
        def action(self, threshold):
            if self.object.device_type == DEVICE_ACCESS_CONTROL_PANEL:
                if threshold > 100 or threshold < 35:
                    raise Exception(_(u"指纹比对阀值范围为1-100！"))
                if threshold != self.object.fp_mthreshold:#相等直接返回，不重复下
                    self.object.fp_mthreshold = threshold
                    self.object.save(force_update=True)
                    self.object.set_mthreshold(threshold)

    class OpCloseAuxOut(Operation):
        verbose_name = _(u"""关闭辅助输出""")
        help_text = _(u"""该操作只对当前打开的辅助输出点有效，如果选择的辅助输出点是关闭的，那么该操作无效。""")
        only_one_object = True
    
        def action(self):
            if self.object.device_type == DEVICE_ACCESS_CONTROL_PANEL:
                from dev_comm_operate import save_operate_cmd
                save_operate_cmd("DATA SET output")#写入操作日志
                auxout = self.request.POST.getlist("auxout")#选择全部时，该值为空
                #print '---auxout=',auxout

                for aux in auxout:
                    CMD = "DEVICE SET %d 2 0" % int(aux)#最后一个0表示关  ControlDevice(self.hcommpro, 1, doorid, index, state, 0 , "")
                    self.object.appendcmdreturn(CMD, MAX_COMMAND_TIMEOUT_SECOND)
    
    class OpUpgradeFirmware(Operation):
        verbose_name = _(u"""升级固件""")
        help_text = _(u"""升级设备中的固件。""")
        only_one_object = True
        params = (
            ('firmware_file', models.FileField(verbose_name=_(u"选择目标文件"), blank=True, null=True)),#, max_length=80  forms
        )
    
        def action(self, firmware_file):
            if self.object.device_type == DEVICE_ACCESS_CONTROL_PANEL:#门禁               
                file = self.request.FILES['firmware_file']
                if not file:
                    raise Exception(_(u"目标文件不存在"))
                if file.name != "emfw.cfg":
                    raise Exception(_(u"目标文件名错误"))
                #for chunk in file.chunks():
                    #buffer.write(chunk)
                buffer = file.read()
                from mysite.iaccess.devcomm import TDevComm
                devcomm = TDevComm(self.object.getcomminfo())
                cret = devcomm.connect()
                #devcomm.disconnect()
                if cret['result'] > 0:
                    ret = devcomm.upgrade_firmware(file.name, buffer, file.size)
                    if ret['result'] >= 0:#
                        devcomm.reboot()
                        devcomm.disconnect()
                        #raise Exception(_(u"升级固件成功"))
                    else:
                        devcomm.disconnect()
                        raise Exception(_(u"升级固件失败，错误码：%d") % ret['result'])
                else:
                    from mysite.iaccess.dev_comm_center import DEVICE_COMMAND_RETURN
                    try:
                        reason = unicode(dict(DEVICE_COMMAND_RETURN)[str(cret["result"])])
                        raise Exception(_(u"连接设备失败（原因：%s），无法升级固件。") % reason)
                    except:
                        raise Exception(_(u"设备连接失败（错误码：%d），无法升级固件。") % cret['result'])
                    
    class UploadLogs(Operation):
        verbose_name = _(u"""获取事件记录""")
        help_text = _(u"""获取设备中的事件记录到服务器中。""")

        def action(self):
            if self.object.device_type == DEVICE_ACCESS_CONTROL_PANEL:
                ret = self.object.upload_acclog()
                if ret >= 0:
                    raise Exception(_(u"获取事件记录成功，共 %d 条") % ret)
                else:
                    raise Exception(_(u"获取事件记录失败"))
    
#    #暂只有门禁使用
#    class OpGetMoreOptions(Operation):
#        verbose_name = _(u"""获取更多参数""")
#        help_text = _(u"""获取设备中的更多参数。""")
#        only_one_object = True
#    
#        def action(self):
#            pass
        
    class OpReloadData(Operation):
        help_text = _(u"重新上传数据")
        verbose_name = _(u"重新上传数据")
        
        def action(self):
            self.object.oplog_stamp='0'
            self.object.log_stamp='0'
            self.photo_stamp='0'
            self.object.save(force_update=True)
            #print "self.object.oplog_stamp",self.object.oplog_stamp
            self.object.appendcmd("CHECK")
            
#    class OpReloadLogData(Operation):
#        help_text=_("upload transactions again from device")
#        verbose_name = u"重新上传记录"
#        def action(self):
#            from mysite.iclock.dataprocaction import reloadLogDataCmd
#            reloadLogDataCmd(self.object)
            
    class RefreshDeviceInfo(Operation):
        help_text = _(u"""获取设备信息""")
        verbose_name = _(u"""获取设备信息""")

        def action(self):
            if self.object.device_type!=DEVICE_ACCESS_CONTROL_PANEL:
                self.object.appendcmd("INFO")
                
    class Reboot(Operation):
        verbose_name = _(u"""重启设备""")
        help_text = _(u"""重启设备""")

        def action(self):
            if self.object.device_type!=DEVICE_ACCESS_CONTROL_PANEL:
                self.object.appendcmd("REBOOT")
                
    class ClearData(Operation):
        verbose_name = _(u"清除全部数据")
        help_text = _(u"清除全部数据")

        def action(self):
            self.object.appendcmd("CLEAR DATA")
            
    class ClearTransaction(Operation):
        verbose_name = _(u"清除考勤记录")
        help_text = _(u"清除考勤记录")

        def action(self):
            self.object.appendcmd("CLEAR LOG")

    class ClearPicture(Operation):
        verbose_name = _(u"清除考勤图片")
        help_text = _(u"清除考勤图片")
        
        def action(self):
            self.object.appendcmd("CLEAR PHOTO")

#    class PowerSuspend(Operation):
#        help_text=u"""设置自动关机"""
#        verbose_name=u"""设置自动关机"""
#        def action(self):
#            return setOpt(self.object,params)
        
    class OpSearchACPanel(ModelOperation):
        verbose_name = _(u'''搜索门禁控制器''')
        help_text = _(u"搜索局域网内存在的门禁控制器。")

        def action(self, **kwargs):
            pass
    
    class OpDisableDevice(Operation):
        verbose_name = _(u'''禁用''')
        help_text = _(u"设备禁用后在重新启用前将无法使用。")
    
        def action(self, **kwargs):
           self.object.set_dev_disabled()

    class OpEnableDevice(Operation):
        verbose_name = _(u'''启用''')
        help_text = _(u"启用设备后设备将恢复正常的使用状态。")

        def action(self, **kwargs):
            self.object.set_dev_enabled()
    
    class ResetPassword(Operation):
        verbose_name = _(u"""修改通讯密码""")#门禁控制器设备
        help_text = _(u"""最多15位字符，空值代表取消通讯密码。修改成功后服务器将会自动将软件中的密码同步为新的密码。""")
        params=(
            ('commkey', forms.CharField(label=_(u"新通讯密码"), required=False, widget=forms.PasswordInput, max_length=15)),
            ('commkey_again', forms.CharField(label=_(u"确认通讯密码"), required=False, widget=forms.PasswordInput, max_length=15)),
        )
        only_one_object=True

        def action(self, commkey, commkey_again):
            for key in commkey:
                if key == ' ':
                    return Exception(_(u'设备通讯密码不能包含空格！'))
            
            if commkey != commkey_again:  
                raise Exception(_(u'两次输入密码不一致,请重新输入！'))

            ret = self.object.set_commkey(commkey)
            if ret >= 0:#?
                dev_info = self.object.getdevinfo()
                self.object.comm_pwd = commkey
                self.object.save(force_update=True)
                from mysite.iaccess.dev_comm_center import OPERAT_EDIT   
                self.object.add_comm_center(dev_info, OPERAT_EDIT)
                raise Exception(_(u'修改通讯密码成功！'))
            else:
                raise Exception(_(u'修改通讯密码失败！'))
            
    class OpChangeIPOfACPanel(Operation):
        verbose_name = _(u"""修改IP地址""")
        help_text = _(u"""修改设备IP地址，每次只能修改一台设备。修改成功后服务器将会自动将软件中的设备IP地址同步为新的IP地址。""")#门禁控制器设备

        params=(
            ('newip', forms.CharField(label=_(u"输入新的IP地址"), widget=forms.TextInput, max_length=20)),
            ('subnet_mask', forms.CharField(label=_(u"输入子网掩码"), widget=forms.TextInput, max_length=20, initial="255.255.255.0")),#, default="255.255.255.0"
            ('gateway', forms.CharField(label=_(u"输入网关地址"), widget=forms.TextInput, max_length=20)),
        )
        only_one_object=True
        
        def action(self, newip, gateway, subnet_mask):
            #print 'newip=',newip
            #print 'ip=',self.object.ipaddress
            #print 'ip=',self.object.ipaddress
            ret = self.object.set_ipaddress(newip, gateway, subnet_mask, 10)#发送指令10秒后使用新IP试连接
            
            if ret >= 0:
                dev_info = self.object.getdevinfo()
                self.object.alias = newip
                self.object.ipaddress = newip
                self.object.save(force_update=True)
                from mysite.iaccess.dev_comm_center import OPERAT_EDIT
                self.object.add_comm_center(dev_info, OPERAT_EDIT)
                #raise Exception(_(u'修改IP地址成功！'))
            else:
                raise Exception(_(u'修改IP地址失败！'))
    
    class OpSetDSTime(Operation):    #仅门禁使用
        verbose_name = _(u"""启用夏令时""")
        help_text = _(u"""给设备设置夏令时，每次可以同时对多台设备进行设置，修改成功后服务器将会自动同步到选中设备当中。""")
        
        params = (
            ('dstime', models.ForeignKey(DSTime, verbose_name=_(u"夏令时"))),
        )
        def action(self, dstime):
            ret = self.object.set_dstime(dstime)
            if ret >= 0:
                dev_info = self.object.getdevinfo()
                self.object.dstime = dstime
                self.object.save(force_update=True)
                from mysite.iaccess.dev_comm_center import OPERAT_EDIT
                self.object.add_comm_center(dev_info, OPERAT_EDIT)
                raise Exception(_(u'夏令时设置成功！'))
            else:
                raise Exception(_(u'夏令时设置失败！'))
            
        
    class OpRemoveDSTime(Operation):    #仅门禁使用
        verbose_name = _(u'''禁用夏令时''')
        help_text = _(u'''禁用夏令时''')
        
        def action(self, **kwargs):
            if self.object.dstime == None:
                raise Exception(_(u'该设备未设置夏令时！'))
            ret = self.object.set_dstime_disable()
            if ret >= 0:
                dev_info = self.object.getdevinfo()
                self.object.dstime = None
                self.object.save(force_update=True)
                from mysite.iaccess.dev_comm_center import OPERAT_EDIT
                self.object.add_comm_center(dev_info, OPERAT_EDIT)
                raise Exception(_(u'夏令时已禁用！'))
            else:
                raise Exception(_(u'夏令时禁用失败！'))
   
    def getdevinfo(self):
        comminfo={
            'id': self.id,
            'comm_type':self.comm_type,
            'ipaddress':self.ipaddress,
            'ip_port':self.ip_port,
            'com_port':self.com_port,
            'com_address':self.com_address,
            'baudrate':self.baudrate and Device._meta.get_field('baudrate').choices[self.baudrate][1] or '',
            'operatstate':0,
            'commstate':0,
            'password': self.comm_pwd and decrypt(self.comm_pwd) or "",
        }
        return comminfo

    #数据同步相关命令
    def appendcmd(self, cmd, Op=None):
        from mysite.iclock.dataprocaction import append_dev_cmd
        append_dev_cmd(self, cmd, Op)
        
    def appendcmdreturn(self, cmd, timeout):
        '''
        执行设备信息查询命令
        '''
        from mysite.iclock.dataprocaction import appendDevCmdReturn
        from mysite.iclock.models.model_devcmd import DevCmd
        cmdid = appendDevCmdReturn(self, cmd)
        returncmd = None
        for i in range(0, timeout, 1):
            devcmd = DevCmd.objects.filter(id=cmdid)
            if devcmd:
                returncmd = devcmd[0].CmdReturn
            if returncmd is not None:#返回大于等于0表示成功
                break
            time.sleep(1)
        return returncmd#返回None说明固件没有返回值。返回0说明成功，负数说明失败。如果是获取记录大于零表示记录条数--comment by darcy
    
    def getcomminfo(self):
        comminfo={
            'id': self.id,
            'comm_type':self.comm_type,
            'ipaddress':self.ipaddress,
            'ip_port':self.ip_port,
            'com_port':"COM"+str(self.com_port),
            'com_address':self.com_address,
            'baudrate':self.baudrate and Device._meta.get_field('baudrate').choices[self.baudrate][1] or '',
            'password': self.comm_pwd and decrypt(self.comm_pwd) or "",
        }
        return comminfo
    
    def search_user_bydevice(self): #查找设备关联员工 返回empobjects
        return self.area.employee_set.all()
    
    def search_accuser_bydevice(self):
        sql="select distinct employee_id from acc_levelset_emp where acclevelset_id in ( select distinct acclevelset_id from acc_levelset_door_group  where accdoor_id in (select id from acc_door where device_id=%d))"%self.id
        cursor = connection.cursor()
        cursor.execute(sql)
        fet=set(cursor.fetchall())
        emp=[]
        ss=[emp.append(int(f[0])) for f in fet]
        from mysite.personnel.models import Employee
        empset=Employee.objects.filter(id__in=emp)
        return empset
    
    def set_data(self, table, objectset, Op=None, session_key="", immediate=False, timeout=0):
        from mysite.personnel.models.model_emp import device_pin
        from mysite.iclock.models.modelproc import get_normal_card
        CMD=""
        if (table.upper() == "USER"):
            line=""
            if self.comm_type==COMMU_MODE_PUSH_HTTP:
                print "len(object)=",len(objectset)#注意不能屏蔽删除，处理sqlserver 查询的问题
                #print datetime.datetime.now()
                #pk_lst=objectset.values_list('Card','EName','PIN','Password','AccGroup')
                for u in objectset:
                    line="CardNo=%s\tName=%s\tPin=%s\tPassword=%s\tGroup=%s\tPri=%s"%(get_normal_card(u.Card),u.EName,
                        device_pin(u.PIN), decrypt(u.Password) or "", u.AccGroup and u.AccGroup or 0,u.Privilege and u.Privilege or 0)
                    CMD="DATA UPDATE user %s"%(line)
                    self.appendcmd(CMD, Op)

            else:
                i=0
                for u in objectset:
                    i+=1
                    if i%200 == 0:
                        time.sleep(0.1)
                        self.set_fquere_progress((i*100)/len(objectset), session_key)
                    if (u.acc_startdate is None):
                        sdate=0
                    else:
                        sdate = u.acc_startdate.year*10000 + u.acc_startdate.month*100 + u.acc_startdate.day
                    if (u.acc_enddate is None):
                        edate=0
                    else:
                        edate = u.acc_enddate.year*10000 + u.acc_enddate.month*100 + u.acc_enddate.day
                    if self.device_type==DEVICE_ACCESS_CONTROL_PANEL:
                        line += ("\r\n" if line else "") + "CardNo=%s\tPin=%s\tPassword=%s\tGroup=%d\tStartTime=%d\tEndTime=%d"%(u.Card,
                            u.PIN, decrypt(u.Password) or "", u.morecard_group and u.morecard_group.id or 0, sdate, edate)
                    else:
                        line += ("\r\n" if line else "") + "CardNo=%s\tName=%s\tPin=%s\tPassword=%s\tGroup=%d\tStartTime=%d\tEndTime=%d"%(u.Card,u.EName,
                            device_pin(u.PIN), decrypt(u.Password) or "", u.morecard_group and u.morecard_group.id or 0, sdate, edate)
                if len(objectset)>0:
                    self.set_fquere_progress(100, session_key)                    
                if len(line)>0:
                    CMD="DATA UPDATE user %s"%(line)
                    self.appendcmd(CMD, Op)
        elif (table.upper() == "FINGERPRINT"):
            line=""
            if self.comm_type==COMMU_MODE_PUSH_HTTP:
                for template in objectset:
                    if len(template.Template)>0:
                        line = "Pin=%s\tFingerID=%d\tTemplate=%s"%(device_pin(template.UserID.PIN), template.FingerID, template.Template)
                        CMD="DATA UPDATE fingerprint %s"%(line)
                        self.appendcmd(CMD, Op)
            else:
                for template in objectset:
                    if len(template.Template)>0:
                        line += ("\r\n" if line else "") + "Pin=%s\tFingerID=%d\tTemplate=%s"%(template.UserID.PIN, template.FingerID, template.Template)
                if len(line)>0:
                    CMD="DATA UPDATE fingerprint %s"%(line)
                    self.appendcmd(CMD, Op)
        elif (table.upper() == "TEMPLATEV10"):
            line=""
            count = 0
            for template in objectset:
                if len(template.Template)>0:
                    line += ("\r\n" if line else "") + "PIN=%s\tFingerID=%d\tValid=%d\tTemplate=%s"%(template.UserID.PIN, template.FingerID, template.Valid, template.Template)
                    count += 1
                if count == 1000:
                    CMD="DATA UPDATE templatev10 %s"%(line)
                    self.appendcmd(CMD, Op) 
                    count = 0
                    line = ""
            if len(line)>0:
                CMD="DATA UPDATE templatev10 %s"%(line)
                self.appendcmd(CMD, Op)           
        elif (table.upper()=="USERAUTHORIZE"):
            line=""
            for level in objectset:
                line += ("\r\n" if line else "") + "Pin=%s\tAuthorizeTimezoneId=%d\tAuthorizeDoorId=%d"%(level['PIN'],level['leveltimeseg'],level['tAuthorizeDoorId'])
            if len(line)>0:
                CMD="DATA UPDATE userauthorize %s"%(line)
                self.appendcmd(CMD, Op)
        elif (table.upper() == "HOLIDAY"):
            line=decode_holiday(objectset)
            if len(line)>0:
                CMD="DATA UPDATE holiday %s"%(line)
                self.appendcmd(CMD, Op)
        elif (table.upper() == "TIMEZONE"):
            #print "settime", objectset
            line=decode_timeseg(objectset)
            if len(line)>0:
                CMD="DATA UPDATE timezone %s"%(line)
                self.appendcmd(CMD, Op)
        elif (table.upper() == "FIRSTCARD"):
            line=""
            for fo in objectset:
                if fo.door.device.id==self.id:
                    for emp in fo.emp.all():
                        line += ("\r\n" if line else "") + "DoorID=%d\tTimezoneID=%d\tPin=%s"%(fo.door.door_no,fo.timeseg.id,emp.PIN)
            if len(line)>0:
                CMD="DATA UPDATE firstcard %s"%(line)
                self.appendcmd(CMD, Op)
        elif (table.upper() == "MULTIMCARD"):
            line=""
            for moreopen in objectset:
                gc=[]
                for groupcard in moreopen.accmorecardgroup_set.all():
                    for num in range(groupcard.opener_number):
                            gc.append(groupcard.group.id)
                while len(gc)<5:
                    gc.append(0)
                line += ("\r\n" if line else "") + "Index=%d\tDoorId=%d\tGroup1=%d\tGroup2=%d\tGroup3=%d\tGroup4=%d\tGroup5=%d"%(moreopen.id,moreopen.door.door_no,gc[0],gc[1],gc[2],gc[3],gc[4])    
            if len(line)>0:
                CMD="DATA UPDATE multimcard %s"%line
                self.appendcmd(CMD, Op)
        elif (table.upper() == "INOUTFUN"):
            line=""
            for define in objectset:
                line += ("\r\n" if line else "") + "Index=%d\tEventType=%d\tInAddr=%d\tOutType=%d\tOutAddr=%d\tOutTime=%d"%(define.id,define.trigger_opt,define.in_address_hide, define.out_type_hide, define.out_address_hide, define.get_action_type())    
            if len(line)>0:
                CMD="DATA UPDATE inoutfun %s"%line
                self.appendcmd(CMD, Op) 
        else:
            pass
            
    def get_data(self, table, data, filter, Op, immediate=True, timeout=30):
        CMD="DATA QUERY %s %s %s"%(table.lower(), data, filter)
        self.appendcmd(CMD, Op)
        
    def delete_data(self, table, filter, Op=None,immediate=False, timeout=0):
        CMD="DATA DELETE %s %s"%(table.lower(), filter)
        self.appendcmd(CMD, Op)
    
    #如远程开关门
    def set_device_state(self, door, index, state, Op, immediate=False, timeout=0):    #输入输出为紧急命令
        CMD="DEVICE SET %d %d %d"%(door, index, state)
        return self.appendcmdreturn(CMD, MAX_COMMAND_TIMEOUT_SECOND)
    
    #取消报警（准备某个控制器）
    def cancel_alarm(self):
        CMD = "CANCEL ALARM"
        return self.appendcmdreturn(CMD, MAX_COMMAND_TIMEOUT_SECOND)
    
    #控制门的常开状态no--normal open
    def control_door_no(self, door, state, Op, immediate=False, timeout=0):    #输入输出为紧急命令
        CMD = "CONTROL NO %d %d" % (door, state)
        return self.appendcmdreturn(CMD, MAX_COMMAND_TIMEOUT_SECOND)
    
    def get_device_state(self, door, index, Op, immediate=True, timeout=30):
        CMD="DEVICE GET %d %d"%(door, index)
        self.appendcmd(CMD)
        
    def set_options(self, items, Op=None, immediate=False, timeout=0):
        CMD="OPTION SET %s"%items
        self.appendcmd(CMD, Op)
        
    def get_optins(self, items, Op=None, immediate=True, timeout=30):
        CMD="OPTION GET %s"%items
        return self.appendcmdreturn(CMD, MAX_COMMAND_TIMEOUT_SECOND)
        
    def connect(self, save=True, immediate=True, timeout=30):
        from mysite.iaccess.devcomm import TDevComm
        from mysite.iaccess.models.accdoor import AccDevice
        devcom = TDevComm(self.getcomminfo())
        cret = devcom.connect()
        if cret["result"] > 0:
            #连接成功取设备参数，序列号写入设备表，其他参数写入accdevice表
            qret = devcom.get_options("~SerialNumber,FirmVer,~DeviceName,LockCount,ReaderCount,AuxInCount,AuxOutCount,MachineType,~IsOnlyRFMachine,MThreshold,~ZKFPVersion")#SerialNumber, 
            if qret["result"] > 0:
                try:
                    datdic = {}
                    optlist = qret["data"].split(',')
                    for opt in optlist:
                        opt1=opt.split('=')
                        datdic[opt1[0]] = opt1[1] or None
                    #print "dic=",datdic
                    #print "self=",self
                    #self._accdevice_cache.save()
                    #print "self.accdevice=",self.accdevice
                    
                    #print save
                    #print self.accdevice.door_count
                    if save and not self.accdevice.door_count:#搜索控制器后手动添加设备时，Device->AccDevice两表会先后保存，故此处的判断可以保证不重复添加
                        #print self.acpanel_type
                        #print datdic['LockCount']
                        if self.acpanel_type == int(datdic['LockCount']):
                            self.sn = datdic['~SerialNumber']
                            self.Fpversion = datdic['~ZKFPVersion']
                            self.fw_version = datdic['FirmVer']
                            self.device_name = datdic['~DeviceName']
                            #新增获取三个容量参数--add by darcy 20101122
                            self.max_user_count = datdic.has_key("~MaxUserCount") and int(datdic["~MaxUserCount"])*100 or 0
                            self.max_attlog_count = datdic.has_key("~MaxAttLogCount") and int(datdic["~MaxAttLogCount"])*10000 or 0
                            self.max_finger_count = datdic.has_key("~MaxUserFingerCount") and int(datdic["~MaxUserFingerCount"]) or 0
                            self.fp_mthreshold = datdic.has_key("MThreshold") and int(datdic["MThreshold"]) or 0
                            
                            self.save(force_update=True)
                            #print '---Device has been updated,SN FWVersion.....'

                            #self.accdevice.machine_type = int(datdic['ACPanelFunOn'])
                            self.accdevice.door_count = int(datdic['LockCount'])
                            self.accdevice.reader_count = int(datdic['ReaderCount'])
                            self.accdevice.aux_in_count = int(datdic['AuxInCount'])
                            self.accdevice.aux_out_count = int(datdic['AuxOutCount'])
                            self.accdevice.machine_type = int(datdic['MachineType'])
                            self.accdevice.IsOnlyRFMachine = int(datdic['~IsOnlyRFMachine'])

                            self.accdevice.save(force_update=True)
                            #print '---AccDevice has been updated,LockCount AuxInCount AuxOutCount....'
                        else:
                            try:
                                q_server=queqe_server()
                                acmd=DevCmd(SN=self, CmdContent="DOOR_DIFFER", CmdReturn=0)
                                q_server.set(devs[devobj.id].comm_tmp, pickle.dumps(acmd))                            
                                q_server.connection.disconnect()
                            except:
                                print_exc()
                except:
                    print_exc()
            return {"result":qret["result"], "data":datdic}
        return {"result":cret["result"], "data":""}
    
       
    def set_user(self, empobjs, Op, session_key=""):    #同步设备员工信息
        self.set_data("user", empobjs, Op, session_key)
        if self.device_type==2:
            self.set_acc_user_fingerprint(empobjs, Op)
    def set_acc_user_fingerprint(self, empobjs, Op):
        from mysite.iclock.models.model_bio import Template
        if self.accdevice.IsOnlyRFMachine>0: #不持指纹
            return
        else:
            u = [int(user.id) for user in empobjs]
            temps = Template.objects.filter(UserID__in=u).filter(Fpversion=10)
            self.set_data("templatev10", temps, Op)

    def set_user_fingerprint(self, empobjs, Op,FID=""):    #同步设备员工指纹
        from mysite.iclock.models.model_bio import Template
        if self.device_type==1:
            for user in empobjs:
                if len(str(FID).strip())>0:
                    temp=Template.objects.filter(UserID=user.id,FingerID=int(FID)).filter(Fpversion=self.Fpversion)
                else:
                    temp=Template.objects.filter(UserID=user.id).filter(Fpversion=self.Fpversion)
                if len(temp)>0:
                    self.set_data("fingerprint", temp, Op)

    def set_user_privilege(self, empobjs, Op, session_key=""):    #同步设备员工门禁权限
        from mysite.personnel.models import Employee
        from mysite.iaccess.models import AccLevelSet
        if empobjs is None:
            empobjs = Employee.objects.all()
        emplevel=[]
        i=0
        for emp in empobjs:
            i += 1
            if i%200 == 0:
                self.set_fquere_progress((i*100)/len(empobjs), session_key)
                time.sleep(0.1)
            sql="select acc_levelset_door_group.acclevelset_id,acc_door.door_no  from acc_levelset_door_group left join acc_door on acc_door.id=acc_levelset_door_group.accdoor_id where (accdoor_id in (select id from acc_door where device_id=%d)) and (acclevelset_id in (select acclevelset_id from acc_levelset_emp where acc_levelset_emp.employee_id=%d))"%(self.id, emp.id)
            cursor = connection.cursor()
            cursor.execute(sql)
            fet=cursor.fetchall()
            for d in dict(fet).keys():
                line={}
                line['PIN']=emp.PIN
#                line['Card']=emp.Card
                line['leveltimeseg']=AccLevelSet.objects.get(id=int(d)).level_timeseg.id
                lev=0
                for f in fet:
                    if f[0]==d:
                        lev+=(1<<(int(f[1])-1))
                line['tAuthorizeDoorId']=lev
                emplevel.append(line.copy())
#            levelset=emp.acclevelset_set.all()
#            for level in levelset:
#                line={}
#                line['PIN']=emp.PIN
#                line['Card']=emp.Card
#                line['leveltimeseg']=level.level_timeseg.id
#                doorset=[]
#                lev=0
#                for door in level.door_group.all():
#                    if door.device.id==self.id:
#                        lev+=(1<<(door.door_no-1))
#                line['tAuthorizeDoorId']=lev
#                if line not in emplevel:
#                    emplevel.append(line.copy())
#                print line
        if len(empobjs):
            self.set_fquere_progress(100, session_key)
        if len(emplevel)>0:
            self.set_data("userauthorize", emplevel, Op)

    def set_timezone(self, Op):     #同步设备所有时间段
        from mysite.iaccess.models import AccTimeSeg
        timezoneobjs=AccTimeSeg.objects.all()
        self.delete_data("timezone", "", Op)
        self.set_data("timezone", timezoneobjs, Op)
        
    def del_timezone(self, tzid):
        #print "del timezone %d"%tzid
        if tzid>0:
            self.delete_data("timezone", "TimezoneId=%d"%tzid)
        else:
            self.delete_data("timezone", "")
            
    def set_holiday(self, Op):  #同步设备所有假日
        from mysite.iaccess.models import AccHolidays
        holidayobjs=AccHolidays.objects.all()
        self.delete_data("holiday", "", Op)
        self.set_data("holiday", holidayobjs, Op)

    def set_dooroptions(self, Op, door_set=None):  #同步设备门属性, doorid=0，设备所有门
        from mysite.iaccess.models import AccDoor
        if door_set is None:
            door_set=AccDoor.objects.filter(device=self)
        for d in door_set:
            optstr=""
            if d.door_sensor_status is not None:
                str="Door%dSensorType=%d,"%(d.door_no, d.door_sensor_status)   #门磁类型
            else:
                str="Door%dSensorType=0,"%(d.door_no)
            optstr += str;
            
            if d.lock_delay is not None:
                str="Door%dDrivertime=%d,"%(d.door_no, d.lock_delay)       #锁延时
            else:
                str="Door%dDrivertime=0,"%(d.door_no)
            optstr += str;
            
            if d.sensor_delay is not None:
                str="Door%dDetectortime=%d,"%(d.door_no, d.sensor_delay)   #门磁延时
            else:
                str="Door%dDetectortime=0,"%(d.door_no)
            optstr += str;
            
            if d.back_lock is not None:#一定不为空
                str = "Door%dCloseAndLock=%d," % (d.door_no, d.back_lock)#闭门回锁  1 启用，0不启用，默认1
            else:
                str = "Door%dCloseAndLock=0," % d.door_no
            optstr += str;
                
            if d.opendoor_type is not None:
                str="Door%dVerifyType=%d,"%(d.door_no, d.opendoor_type)      #开门方式
            else:
                str="Door%dVerifyType=0,"%(d.door_no)
            optstr += str;
            
            if d.lock_active is not None:
                str="Door%dValidTZ=%d,"%(d.door_no, d.lock_active.id)   #门激活时区
            else:
                str="Door%dValidTZ=0,"%(d.door_no)
            optstr += str;
            
            if d.long_open is not None:
                str="Door%dKeepOpenTimeZone=%d,"%(d.door_no, d.long_open.id)   #门常开 时区号
            else:
                str="Door%dKeepOpenTimeZone=0,"%(d.door_no)
            optstr += str;
            
            if d.wiegand_fmt is not None:
                str="Reader%dWGType=%d,"%(d.door_no, d.wiegand_fmt.id)    #读头wg格式
            else:
                str="Reader%dWGType=0,"%(d.door_no)
            optstr += str;
            
            if d.card_intervaltime is not None:
                str="Door%dIntertime=%d,"%(d.door_no, d.card_intervaltime)   #双卡间隔
            else:
                str="Door%dIntertime=0,"%(d.door_no)
            optstr += str;
            
            if d.reader_type is not None:
                str="Door%dReaderType=%d,"%(d.door_no, d.reader_type)   #读头类型
            else:
                str="Door%dReaderType=0,"%(d.door_no)
            optstr += str;
            
            if d.force_pwd is not None:
                str="Door%dForcePassWord=%s,"%(d.door_no, decrypt(d.force_pwd)) #协迫密码
            else:
                str="Door%dForcePassWord=0,"%(d.door_no)
            optstr += str;
            
            if d.supper_pwd is not None:
                str="Door%dSupperPassWord=%s"%(d.door_no, decrypt(d.supper_pwd))   #超级密码
            else:
                str="Door%dSupperPassWord=0"%(d.door_no)
            optstr += str;
            
            #print  "optstr=", optstr
            self.set_options(optstr, Op)

    def set_firstcard(self, Op, mdoor):    #同步设备首卡开门
        from mysite.iaccess.models import AccFirstOpen
        if mdoor:
            self.delete_data("firstcard", "DoorID=%d"%(mdoor.door_no), Op)
            firstopen=AccFirstOpen.objects.filter(door=mdoor)
            if firstopen:
                self.set_data("firstcard", firstopen, Op)
                optstr="Door%dFirstCardOpenDoor=1"%mdoor.door_no
                self.set_options(optstr, Op)
            else:
                optstr="Door%dFirstCardOpenDoor=0"%mdoor.door_no
                self.set_options(optstr, Op)
    #检测是否启用首卡开门    
    def check_firstcard_options(self, mdoor):
        from mysite.iaccess.models import AccFirstOpen
        if mdoor:
            firstopen=AccFirstOpen.objects.filter(door=mdoor)
            if firstopen:
                optstr="Door%dFirstCardOpenDoor=1"%mdoor.door_no
            else:
                optstr="Door%dFirstCardOpenDoor=0"%mdoor.door_no
            self.set_options(optstr, None)

    def delete_firstcard(self, Op, mdoor):
        from mysite.iaccess.models import AccFirstOpen
        if mdoor:
            self.delete_data("firstcard", "DoorID=%d"%(mdoor.door_no), Op)
        else:
            self.delete_data("firstcard", "", Op)
        self.check_firstcard_options(mdoor)
                
    def del_multicard(self, Op, mdoor):
        if mdoor:
            self.delete_data("multimcard", "DoorId=%d"%(mdoor.door_no), Op)
        else:
            self.delete_data("multimcard", "", Op)
        self.check_muliticard_options(mdoor)

    def set_multicard(self, Op, mdoor):    #同步设备多卡开门
        from mysite.iaccess.models import AccMoreCardSet
        from mysite.personnel.models import Employee
        filter="DoorId=%d"%mdoor.door_no
        self.delete_data("multimcard", filter, Op)
        morecard=AccMoreCardSet.objects.filter(door=mdoor)
        if morecard:
            self.set_data("multimcard", morecard, Op)
            optstr="Door%dMultiCardOpenDoor=1"%mdoor.door_no
            self.set_options(optstr, Op)
            
            sql="select userid from userinfo where morecard_group_id in (select group_id from acc_morecardgroup where comb_id in (select id from acc_morecardset where door_id=%d))"%mdoor.id
            #print "set_multicard sql=", sql
            cursor = connection.cursor()
            cursor.execute(sql)
            fet=set(cursor.fetchall())
            emp=[]
            ss=[emp.append(int(f[0])) for f in fet]
            #print emp
            empset=Employee.objects.filter(id__in=emp)
            if len(empset):
                self.set_user(empset, Op)
        else:
            optstr="Door%dMultiCardOpenDoor=0"%mdoor.door_no
            self.set_options(optstr, Op)
    #检测是否启用多卡开门    
    def check_muliticard_options(self, mdoor):
        from mysite.iaccess.models import AccMoreCardSet
        if mdoor:
            morecard=AccMoreCardSet.objects.filter(door=mdoor)
            if morecard:
                optstr="Door%dMultiCardOpenDoor=1"%mdoor.door_no
            else:
                optstr="Door%dMultiCardOpenDoor=0"%mdoor.door_no
            self.set_options(optstr, None)

    def set_antipassback(self, Op): #同步设备反潜信息
        anti=0
        if self.accantiback_set.all():
            antibackobj=self.accantiback_set.all()[0]
            anti=antibackobj.getantibackoption()
        optstr="AntiPassback=%d"%anti
        self.set_options(optstr, Op)
        
    def clear_antipassback(self, Op):
        self.set_options("AntiPassback=0", Op)
        
    def set_interlock(self, Op): #同步设备互锁信息
        IntLock=0
        if self.accinterlock_set.all():
            interlock=self.accinterlock_set.all()[0]
            IntLock=interlock.getlockoption()
        optstr="InterLock=%d"%IntLock
        self.set_options(optstr, Op)

    def clear_interlock(self, Op):
        self.set_options("InterLock=0", Op)

    def delete_user_privilege(self, empobjs, Op, session_key=""): #删除员工门禁权限
        if self.device_type==2:     #门禁机
            if empobjs:
                filter = ""
                i=0
                for emp in empobjs:
                    i+=1
                    if i%200 == 0:
                        time.sleep(0.1)
                        self.set_fquere_progress((i*100)/len(empobjs), session_key)
                    filter += ("\r\n" if filter else "") + "Pin=%s"%emp.PIN
                self.set_fquere_progress(100, session_key)
                self.delete_data("userauthorize", filter, Op)
            else:
                self.delete_data("userauthorize", "", Op)

    def delete_user(self, empobjs, Op):     
        """
        删除员工信息,包括指纹信息,
        #判断是否有首卡权限及多卡权限，如果有包括删除首卡权限，多卡权限
        """
        from mysite.personnel.models.model_emp import device_pin
        if self.comm_type==COMMU_MODE_PUSH_HTTP:
            for emp in empobjs:                
                if (self.device_type != 2) or ((self.device_type==2) and (self.accdevice.IsOnlyRFMachine==0)):
                    self.delete_data("fingerprint", "Pin=%s"%device_pin(emp.PIN), Op)
                self.delete_data("user", "Pin=%s"%device_pin(emp.PIN), Op)
        else:
            filter = ""
            for emp in empobjs:
                filter += ("\r\n" if filter else "") + "Pin=%s"%emp.PIN
            self.delete_data("user", filter, Op)

    def delete_user_finger(self, table, empfp, Op):
        if self.comm_type==COMMU_MODE_PUSH_HTTP:
            if (self.device_type != 2) or ((self.device_type==2) and (self.accdevice.IsOnlyRFMachine==0)):
                self.delete_data(table, empfp, Op)
        else:
            self.delete_data(table, empfp, Op)

    def upload_acclog(self):
        CMD="DATA QUERY %s %s %s"%("transaction", "*", "")
        return self.appendcmdreturn(CMD, MAX_COMMAND_TIMEOUT_SECOND*120)
        
    def delete_define_io(self, Op, defobj=None):
        if defobj:
            filter="Index=%d"%defobj.id
            self.delete_data("inoutfun", filter, Op)
        else:
            self.delete_data("inoutfun", "", Op)

    def set_define_io(self, Op, defobj=None):
        if defobj:
            self.set_data("inoutfun", [defobj], Op)
        else:
            defobj_set = self.acclinkageio_set.all()
            self.delete_data("inoutfun", "", Op)
            self.set_data("inoutfun", defobj_set, Op)
    
    def delete_transaction(self, Op=None):
        self.delete_data("transaction", "", Op) 
                        
    #设备替换,设备区域变更手动更新设备后
    def delete_all_data(self, Op=None):        #清除所有数据
        if (self.device_type == DEVICE_TIME_RECORDER) or ((self.device_type==DEVICE_ACCESS_CONTROL_PANEL) and (self.accdevice.IsOnlyRFMachine==0)):
            #self.delete_data("fingerprint", "*", Op)
            #print "Op:%s"%Op
            self.appendcmd("CLEAR DATA",Op)
        if (self.device_type==DEVICE_ACCESS_CONTROL_PANEL):
            self.set_options("Door1ValidTZ=0", Op)
            self.set_options("AntiPassback=0", Op)
            self.set_options("InterLock=0", Op)
            self.delete_data("user", "", Op)
            self.delete_data("userauthorize", "", Op)
            self.delete_data("timezone", "", Op)
            self.delete_data("holiday", "", Op)
            self.delete_data("firstcard", "", Op)
            self.delete_data("multimcard", "", Op)
            self.delete_data("inoutfun", "", Op)
            

    def set_all_data(self, Op=None):       #同步所有数据
        if (self.device_type==DEVICE_ACCESS_CONTROL_PANEL):#门禁控制器
            self.delete_all_data()  #同步所有数据，先清除控制器数据
            empobjs=self.search_accuser_bydevice()
            if empobjs:
                self.set_user(empobjs, Op)
                if (self.accdevice.IsOnlyRFMachine==0):
                    self.set_user_fingerprint(empobjs, Op)
                self.set_user_privilege(empobjs, Op)
            self.set_timezone(Op)
            self.set_holiday(Op)
            self.set_dooroptions(Op)
            for door in self.accdoor_set.all():
                self.set_firstcard(Op, door)
                self.set_multicard(Op, door)
            self.set_define_io(Op)
            self.set_antipassback(Op)
            self.set_interlock(Op)
        else:#考勤
            empobjs=self.search_user_bydevice()
            self.set_user(empobjs, Op)
            self.set_user_fingerprint(empobjs, Op) 

    #输入输出控制
    def set_output (self, doorid, addr, state):
        return self.set_device_state(doorid,addr,state) 
      
    def get_input(self, doorid, addr):
        return self.get_device_state(doorid,addr)  

    def set_ipaddress(self, newip, gateway, subnet_mask, timeout):
        CMD="OPTION SET IPAddress=%s,GATEIPAddress=%s,NetMask=%s" % (newip, gateway, subnet_mask)    #修改设备ip地址
        return self.appendcmdreturn(CMD, timeout)

    def set_time(self, ret=True):
        from mysite.iclock.dataprocaction import appendDevCmdReturn
        dt=encodetime()
        CMD="OPTION SET DateTime=%d"%(dt)   #同步控制器时间
        if ret:
            return self.appendcmdreturn(CMD, MAX_COMMAND_TIMEOUT_SECOND)
        else:
            return appendDevCmdReturn(self, CMD)
      
    def set_commkey(self, new_commkey):
        CMD = "OPTION SET ComPwd=%s" % new_commkey#ComPwd为设备通讯密码，非串口密码
        return self.appendcmdreturn(CMD, MAX_COMMAND_TIMEOUT_SECOND)
    
    def set_dstime(self,dstime, immediately=True):#immediately  为True时只执行一次，失败就直接返回，为False时失败后会在设备下次连接上之后继续执行
        CMD = ""
        if dstime.mode == 0:
            time_st = dstime.start_time
            time_ed = dstime.end_time
            time_st = time_st.split(" ")
            time_st_mon = int(time_st[0].split("-")[0])
            time_st_d = time_st[0].split("-")[1]
            time_st_h = time_st[1].split(":")[0]
            time_st_mun = time_st[1].split(":")[1]
            time_st = ((int(time_st_mon)&0xFF) << 24)|((int(time_st_d)&0xFF)<<16)|((int(time_st_h)&0xFF)<<8)|(int(time_st_mun)&0xFF)
            
            time_ed = time_ed.split(" ")
            time_ed_mon = time_ed[0].split("-")[0]
            time_ed_d = time_ed[0].split("-")[1]
            time_ed_h = time_ed[1].split(":")[0]
            time_ed_mun = time_ed[1].split(":")[1]
            time_ed = ((int(time_ed_mon)&0xFF) << 24)|((int(time_ed_d)&0xFF)<<16)|((int(time_ed_h)&0xFF)<<8)|(int(time_ed_mun)&0xFF)
            
            CMD = "OPTION SET ~DSTF=%s,DaylightSavingTimeOn=%s,CurTimeMode=%s,DLSTMode=%s,DaylightSavingTime=%s,StandardTime=%s"%(1, 1, 0, 0, time_st, time_ed)
        else:
            time_st = dstime.start_time
            time_ed = dstime.end_time
            time_st = time_st.split(" ")
            time_st_mon = time_st[0].split("-")[0]
            time_st_w = time_st[0].split("-")[1]
            time_st_d = time_st[0].split("-")[2]
            time_st_h = time_st[1].split(":")[0]
            time_st_mun = time_st[1].split(":")[1]
            
            time_ed = time_ed.split(" ")
            time_ed_mon = time_ed[0].split("-")[0]
            time_ed_w = time_ed[0].split("-")[1]
            time_ed_d = time_ed[0].split("-")[2]
            time_ed_h = time_ed[1].split(":")[0]
            time_ed_mun = time_ed[1].split(":")[1]
           
            CMD = "OPTION SET ~DSTF=%s,DaylightSavingTimeOn=%s,CurTimeMode=%s,DLSTMode=%s,WeekOfMonth1=%s,WeekOfMonth2=%s,WeekOfMonth3=%s,WeekOfMonth4=%s,WeekOfMonth5=%s,WeekOfMonth6=%s,WeekOfMonth7=%s,WeekOfMonth8=%s,WeekOfMonth9=%s,WeekOfMonth10=%s"%(1, 1, 0, 1, int(time_st_mon), int(time_st_w), int(time_st_d), int(time_st_h), int(time_st_mun), int(time_ed_mon), int(time_ed_w), int(time_ed_d), int(time_ed_h), int(time_ed_mun))
        if immediately:
            return self.appendcmdreturn(CMD, MAX_COMMAND_TIMEOUT_SECOND)
        else:
            return self.appendcmd(CMD)
    
    def set_dstime_disable(self):
        CMD = "OPTION SET ~DSTF=0,DaylightSavingTimeOn=0,CurTimeMode=0"
        return self.appendcmdreturn(CMD, MAX_COMMAND_TIMEOUT_SECOND)
    def show_status(self):
        '''
        设备状态
        '''
        if self.last_activity:
            if (datetime.datetime.now() - self.last_activity).seconds < 60*5:  #小于五分钟之内为联机状态
                return True
            else:
                return False
        else:
            return False
    
    def show_enabled(self):
        if self.enabled:
            return True
        else:
            return False

    #搜索新增设备加入通讯线程 insert operate_cmd=1 update operate_cmd=2
    def add_comm_center(self, old_comm_info, operate_cmd):
        from mysite.iaccess.dev_comm_center import OPERAT_ADD, OPERAT_EDIT, OPERAT_DEL       
        if operate_cmd==OPERAT_ADD:
            try:
                q_server=queqe_server()
                devinfo=self.getdevinfo()
                devinfo["operatstate"]=OPERAT_ADD
                minfo=True
                len=q_server.llen(DEVOPT)
                for i in range(0, len, 1):
                    info=q_server.lindex(DEVOPT, i)
                    try:
                        dinfo=pickle.loads(info)
                    except:
                        dinfo=None                        
                    if (dinfo["id"] == devinfo["id"]) and (dinfo["operatstate"] == devinfo["operatstate"]):
                        minfo=False
                if minfo:
                    q_server.rpush(DEVOPT, pickle.dumps(devinfo))
                    #print devinfo["id"], " operate add"
                q_server.set(self.get_doorstate_cache_key(), "0,0,0")
                q_server.set(self.get_last_activity(), "0")
                q_server.connection.disconnect()
            except:
                print_exc()
        elif operate_cmd==OPERAT_EDIT:  #对设备的新增，删除只能做一次，但修改可做多次操作
            try:                    #删除旧设备
                q_server=queqe_server()
                old_comm_info["operatstate"]=OPERAT_DEL
                q_server.rpush(DEVOPT, pickle.dumps(old_comm_info))
                q_server.connection.disconnect()
                self.add_comm_center(None, OPERAT_ADD)
            except:
                print_exc()
            
    def get_dstime_name(self):
        print self.dstime.dst_name
        return self.dstime.dst_name
    
    def show_last_activity(self):
        return self.last_activity.strftime("%Y-%m-%d %X")
    
    def show_fp_mthreshold(self):#为0时为获取失败（设备问题）
        return self.fp_mthreshold or _(u"获取失败")

    class Admin(CachingModel.Admin):
        from django.forms import RadioSelect
        cache=False
        sort_fields=["last_activity"]
        default_give_perms=["contenttypes.can_AttDeviceDataManage", "contenttypes.can_DoorSetPage"]
        menu_index=9991
        help_text = _(u"请选择设备类型以及对应的通信方式。设备名称、各通信参数以及所属区域为必填项。")
        api_fields = ('alias','sn', 'device_type','comm_type','ipaddress','com_address','area.areaname','Fpversion', 'last_activity', 'acpanel_type')
        list_display = ('alias','sn', 'device_type','comm_type','ipaddress','com_port',
                    'com_address','get_dstime_name','area.areaname','Fpversion','show_status|boolean_icon',
                    'show_enabled|boolean_icon','show_last_activity', 'acpanel_type', 'device_name','user_count','fp_count','transaction_count','show_fp_mthreshold','fw_version')
        adv_fields=['alias','sn', 'ipaddress','area.areaname','last_activity']+DeviceAdvField
        #newadded_column = { 'status':'show_status'}
        query_fields =  ['alias','sn', 'device_type', 'comm_type','area__areaname','device_type']
        query_fields_iaccess = ['alias', 'acpanel_type', 'iaccess:accdoor__door_name']#支持输入门查询设备
        search_fields = ["sn", "alias"]
        default_widgets={'device_type': RadioSelect, 'comm_type': RadioSelect, 'comm_pwd': forms.PasswordInput}
        detail_model = ['iaccess/AccDoor']
        cache=120
        layout_types=["table","photo"]
        #photo_path="photo"#指定图片的路径，如果带了".jpg",就用这个图片，没有带的话就找这个字符串所对应的字段的值
        disabled_perms = ["dataimport_device","resume_device","pause_device","opbrowselog_device"] + init_settings
        opt_perm_menu = { "uploadlogs_device": "iaccess.DoorMngPage", "opdisabledevice_device": "iaccess.DoorMngPage", "openabledevice_device": "iaccess.DoorMngPage", "opchangeipofacpanel_device": "iaccess.DoorMngPage", "syncacpaneltime_device": "iaccess.DoorMngPage", "resetpassword_device": "iaccess.DoorMngPage",  "opupgradefirmware_device": "iaccess.DoorMngPage", "opsetdstime_device": "iaccess.DoorMngPage", "opremovedstime_device": "iaccess.DoorMngPage",\
            "cleartransaction_device": "att.AttDeviceDataManage", "refreshdeviceinfo_device": "att.AttDeviceDataManage" ,"clearpicture_device": "att.AttDeviceDataManage","cleardata_device": "att.AttDeviceDataManage", "opreloaddata_device": "att.AttDeviceDataManage", "opreloaddata_device": "att.AttDeviceDataManage",  "reboot_device": "att.AttDeviceDataManage"}
        hide_perms = ["opchangemthreshold_device","opcloseauxout_device"]

    class Meta:
        app_label='iclock'
        db_table = 'iclock'
        verbose_name = _(u'设备')
        verbose_name_plural=verbose_name
        #unique_together = (('com_port', 'com_address'),)

installed_apps = settings.INSTALLED_APPS          
if "mysite.iaccess" in installed_apps and "mysite.att" in installed_apps:
    pass#默认
elif "mysite.iaccess" in installed_apps:#门禁
    Device.Admin.help_text = _(u'设备名称、各通信参数以及所属区域为必填项。<br>系统会验证用户提交的设备是否存在，并判断门禁控制器类型是否正确。')
    Device.Admin.query_fields = ['alias', 'sn', 'comm_type','area__areaname']#Device处的列表
else:#考勤
    Device.Admin.help_text = _(u'设备名称、各通信参数以及所属区域为必填项。')
    Device.Admin.query_fields = ['alias', 'sn', 'area__areaname']#Device处的列表
    
class DeviceForeignKey(models.ForeignKey):
    def __init__(self, verbose_name="", **kwargs):
        super(DeviceForeignKey, self).__init__(Device, verbose_name=verbose_name, **kwargs)

#解析门禁控制器的options参数
def options_split(acp_opts):
    options = {}
    if acp_opts:
        for acp_opt in acp_opts:
            opt = acp_opt.split("=")
            options[opt[0]] = opt[1]
    return options

def data_pre_check(sender, **kwargs):
    model = kwargs['model']
    if model == Device:
        request = sender
        device_type = int(request.POST.get("device_type", -1))
        #print '-----device_type=',device_type
        if device_type == DEVICE_ACCESS_CONTROL_PANEL and not kwargs['oldObj']:#只考虑新增时，编辑时不涉及sn（门禁&&视频服务器）
            try:
                acp_opts = request.POST.get("ACPanelOptions", '').split(",")
                options = options_split(acp_opts)
                sn = options.has_key("~SerialNumber") and options["~SerialNumber"] or ''
                Fpversion = options.has_key("~ZKFPVersion") and options["~ZKFPVersion"] or ''
                #print '----sn=',sn
                #print Device.objects.filter(sn=sn).exists()
                if sn and Device.objects.filter(sn=sn).exists():
                    raise Exception(_(u'该设备的序列号：%s 已存在') % sn)
            except:
                print_exc()
            
data_edit.pre_check.connect(data_pre_check)#不同于pre_save

def DataPostCheck(sender, **kwargs):
    oldObj=kwargs['oldObj']
    newObj=kwargs['newObj']
    request=sender
    if isinstance(newObj, Device):
        #此时Device对应的AccDevice记录已经生成
        if newObj.device_type == DEVICE_ACCESS_CONTROL_PANEL:
            #print "device_args_save---door_count=",newObj.accdevice.door_count
            #print "sn=",newObj.accdevice.device.sn
            connected = request.POST.getlist("connect_result")
            #print '------------------------connected=',connected
            #新增时sn肯定为None
            if connected and not newObj.accdevice.door_count:#尚未写入门数量参数.如果sn没写入，说明没有连接成功（新增设备时）或者在大循环中已经连接成功，但设备参数已由check_acpanel_args写入，不需要重复连接设备
                #print "DataPostCheck---now beginning to get device arguments and save them."
                try:
                    acp_opts = request.POST.get("ACPanelOptions", '').split(",")
                    options = options_split(acp_opts)
                except:
                    print_exc()

                newObj.sn = options.has_key("~SerialNumber") and options["~SerialNumber"] or ''
                newObj.Fpversion = options.has_key("~ZKFPVersion") and options["~ZKFPVersion"] or ''
                newObj.fw_version = options.has_key("FirmVer") and options["FirmVer"] or ''
                newObj.device_name = options.has_key("~DeviceName") and options["~DeviceName"] or ''
                #新增获取三个容量参数--add by darcy 20101122
                newObj.max_user_count = options.has_key("~MaxUserCount") and int(options["~MaxUserCount"])*100 or 0
                newObj.max_attlog_count = options.has_key("~MaxAttLogCount") and int(options["~MaxAttLogCount"])*10000 or 0
                newObj.max_finger_count = options.has_key("~MaxUserFingerCount") and int(options["~MaxUserFingerCount"]) or 0
                newObj.fp_mthreshold = options.has_key("MThreshold") and int(datdic["MThreshold"]) or 0
                
                try:
                    newObj.save(force_update=True)
                except:
                    print_exc()
                #print '---Device has been updated,SN FWVersion DeviceName.....'
                newObj.accdevice.door_count = options.has_key("LockCount") and int(options["LockCount"]) or 0
                newObj.accdevice.reader_count = options.has_key("ReaderCount") and int(options["ReaderCount"]) or 0
                newObj.accdevice.aux_in_count = options.has_key("AuxInCount") and int(options["AuxInCount"]) or 0
                newObj.accdevice.aux_out_count = options.has_key("AuxOutCount") and int(options["AuxOutCount"]) or 0
                newObj.accdevice.machine_type = options.has_key("MachineType") and int(options["MachineType"]) or 0
                newObj.accdevice.IsOnlyRFMachine = options.has_key("~IsOnlyRFMachine") and int(options["~IsOnlyRFMachine"]) or 0 

                try:
                    newObj.accdevice.save(force_update=True)
                except:
                    print_exc()
                #print "SN FwVesion door_count......have been updated to Device and AccDevice......"
                    
        from mysite.iclock.models.dev_comm_operate import sync_delete_all_data, sync_set_all_data
        from mysite.iclock.models.model_cmmdata import adj_device_cmmdata
        try:
            if oldObj is None:
                if newObj.device_type==DEVICE_TIME_RECORDER:
                    adj_device_cmmdata(newObj,newObj.area)
                if newObj.device_type==DEVICE_ACCESS_CONTROL_PANEL:
                    newObj.delete_transaction()
                    sync_set_all_data(newObj)
                    from mysite.iaccess.dev_comm_center import OPERAT_ADD
                    newObj.add_comm_center(None, OPERAT_ADD)
            else:         
                if newObj.device_type==DEVICE_TIME_RECORDER:
                    if oldObj.area!=newObj.area or oldObj.Fpversion!=newObj.Fpversion:
                        adj_device_cmmdata(newObj,newObj.area)
                elif newObj.device_type==DEVICE_ACCESS_CONTROL_PANEL:
                    #控制器区域变化时，清空该控制器内所有门所在地图上的信息
                    if newObj.area != oldObj.area:
                        map_doors = newObj.accdoor_set.filter(map__isnull=False)
                        for map_door in map_doors:
                            map_door.accmapdoorpos_set.all().delete()       
                            map_door.map = None
                            map_door.save(force_update=True)
                            
                    from mysite.iaccess.dev_comm_center import OPERAT_EDIT, OPERAT_ADD, OPERAT_DEL
                    if (oldObj.com_port != newObj.com_port):    # 修改串口号
                        try:                    #删除旧设备
                            q_server=queqe_server()
                            devinfo=oldObj.getdevinfo()
                            devinfo["operatstate"]=OPERAT_DEL
                            q_server.rpush(DEVOPT, pickle.dumps(devinfo))
                            q_server.connection.disconnect()
                        except:
                            print_exc()
                        newObj.add_comm_center(None, OPERAT_ADD)  #增新设备
        except:
            import traceback;traceback.print_exc()
data_edit.post_check.connect(DataPostCheck)

class DeviceMultForeignKey(models.ManyToManyField):
    def __init__(self, *args, **kwargs):
            super(DeviceMultForeignKey, self).__init__(Device, *args, **kwargs)

class DevicePoPForeignKey(models.ForeignKey):
    def __init__(self, to_field=None, **kwargs):
            super(DevicePoPForeignKey, self).__init__(Device, to_field=to_field, **kwargs)

def update_device_widgets():
    '''
    添加字段映射的部件
    '''
    from dbapp import widgets
    if DevicePoPForeignKey not in widgets.WIDGET_FOR_DBFIELD_DEFAULTS:
            from device_widget import ZPopDeviceChoiceWidget,ZMulDeviceChoiceWidget
            widgets.WIDGET_FOR_DBFIELD_DEFAULTS[DeviceMultForeignKey] = ZMulDeviceChoiceWidget
            widgets.WIDGET_FOR_DBFIELD_DEFAULTS[DevicePoPForeignKey] = ZPopDeviceChoiceWidget
update_device_widgets()