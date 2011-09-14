#! /usr/bin/env python
#coding=utf-8
from django.db import models
from django.utils import simplejson
from django.http import HttpResponse
from django.utils.encoding import smart_str
from base.models import CachingModel
from base.operation import ModelOperation
from base.middleware import threadlocals
from django.utils.translation import ugettext_lazy as _
from accdoor import AccDoor
from mysite.iclock.models import Device 
from mysite.personnel.models import Employee, Area
from redis.server import check_and_start_queqe_server
from django.contrib.auth.decorators import login_required
import redis, re, os, dict4ini, datetime
import re
from traceback import print_exc
from mysite.iaccess.dev_comm_center import door_state_monitor
from mysite.personnel.models.model_emp import format_pin
from django.db.models import Q  
from mysite.iclock.models.model_device import DEVICE_ACCESS_CONTROL_PANEL
from base.crypt import encrypt,decrypt
try:
    import cPickle as pickle
except:
    import pickle

FIRSTVISIT_OR_DELBACKEND = -1 #初始为-1代表为第一次请求（初始化）， 不能为0，否则可能与rtid_all产生冲突   redis最小为1
LOCKED_OR_NOTHING = -1 #文件缓存被锁住时以及文件缓存为空时9实际为0）都返回-1

#验证方式
VERIFIED_CHOICES = (
    (1, _(u'仅指纹')),
    (3, _(u'仅密码')),
    (4, _(u'仅卡')),
    (6, _(u'卡或指纹')),
    (10, _(u'卡加指纹')),
    (11, _(u'卡加密码')),
    (200, _(u'其他'))
)

IN_ADDRESS_CHOICES = (
    (1, _(u'辅助输入1')),
    (2, _(u'辅助输入2')),
    (3, _(u'辅助输入3')),
    (4, _(u'辅助输入4')),
    (9, _(u'辅助输入9')),
    (10, _(u'辅助输入10')),
    (11, _(u'辅助输入11')),
    (12, _(u'辅助输入12')),
)

#出入状态-单向时都为入
STATE_CHOICES = (
    (0, _(u'入')),
    (1, _(u'出')),
    (2, _(u'无')),
    #(2, _(u'未知或无或其他')),#即其他
)

#if ((strtoint(str[4]) >= 0) and (strtoint(str[4]) <=2)) or ((strtoint(str[4]) >= 21) and (strtoint(str[4]) <=23)) or (strtoint(str[4]) == 5):
EVENT_LOG_AS_ATT = [0, 1, 2, 14, 16, 17, 18, 19, 21, 22, 23, 35]#用来作为考勤用的实时监控记录。

#事件选项
EVENT_CHOICES = (
    (0, _(u'正常刷卡开门')),
    (1, _(u'常开时间段内刷卡')),#含门常开时段和首卡常开设置的开门时段 （开门后）
    (2, _(u'首卡开门(刷卡)')),
    (3, _(u'多卡开门(刷卡)')),#门打开
    (4, _(u'紧急状态密码开门')),
    (5, _(u'常开时间段开门')),
    (6, _(u'触发联动事件')),
    (7, _(u'取消报警')),#远程开关门与扩展输出   ，至于远程开关门与扩展输出等动作执行后还有相应事件记录
    (8, _(u'远程开门')),
    (9, _(u'远程关门')),
    (10, _(u'禁用当天常开时间段')),#
    (11, _(u'启用当天常开时间段')),#
    (12, _(u'开启辅助输出')),#
    (13, _(u'关闭辅助输出')),#
    (14, _(u'正常按指纹开门')),#
    (15, _(u'多卡开门(按指纹)')),#
    (16, _(u'常开时间段内按指纹')),#
    (17, _(u'卡加指纹开门')),#
    (18, _(u'首卡开门(按指纹)')),#
    (19, _(u'首卡开门(卡加指纹)')),#
    
    (20, _(u'刷卡间隔太短')),#5
    (21, _(u'门非有效时间段(卡)')),
    (22, _(u'非法时间段')),#！！！有权限但是时间段不对。当前时段无合法权限
    (23, _(u'非法访问')),#当前时段无此门权限----卡已注册，但是没有该门的权限
    (24, _(u'反潜')),
    (25, _(u'互锁')),
    (26, _(u'多卡验证(刷卡)')),#刷卡
    (27, _(u'卡未注册')),#10
    (28, _(u'门开超时')),
    (29, _(u'卡已过有效期')),
    (30, _(u'密码错误')),
    (31, _(u'按指纹间隔太短')),
    (32, _(u'多卡验证(按指纹)')),
    (33, _(u'指纹已过有效期')),
    (34, _(u'指纹未注册')),
    (35, _(u'门非有效时间段(指纹)')),
    (36, _(u'门非有效时间段(出门按钮)')),
    (37, _(u'常开时间段无法关门')),
    #(100, _(u'防拆报警')),
    (101, _(u'胁迫密码开门')),
    (102, _(u'门被意外打开')),
    (103, _(u'胁迫指纹开门')),
    (200, _(u'门已打开')),#16
    (201, _(u'门已关闭')),
    (202, _(u'出门按钮开门')),
    (203, _(u'多卡加指纹开门')),
    (204, _(u'常开时间段结束')),
    (205, _(u'远程开门常开')),
    
    (220, _(u'辅助输入点断开')),
    (221, _(u'辅助输入点短路')), 
)

#门状态可以具体到某个或某几个控制器（不具体到门），事件则具体到门
#控制服务器只将符合当前用户条件的门状态信息发送给前端
@login_required
def obtain_valid_devices(request):
    u = request.user
    aa = u.areaadmin_set.all()#如果新增用户时设定区域，那么aa不为空，否则为空代表全部（包含普通用户和超级管理员）
    a_limit = aa and [int(a.area_id) for a in aa] or [int(area.pk) for area in Area.objects.all()]#非超级管理员且没有配置有效区域（默认全部）的有效区域id列表（即用户手动配置过用户区域的）    
    
    area_id = int(request.GET.get("area_id", 0))#不为0.前端随已经过过滤，但是考虑用户可以手动修改url
    #print '----area_id=',area_id
    if area_id and area_id in a_limit:
        #devices = Device.objects.filter(area__pk=area_id)#权限范围内的全部
        devices = Device.objects.filter(Q(area__pk=area_id)|Q(area__in=Area.objects.get(id=area_id).area_set.all()))#权限范围内的全部,且要处理区域的上下级
    else:
        device_id = int(request.GET.get("device_id", 0))
        #print '----device_id=',device_id
        dev_limit = [int(d.pk) for d in Device.objects.filter(area__pk__in=a_limit)]#权限范围内的设备
        if device_id and device_id in dev_limit:
            devices = Device.objects.filter(pk=device_id)
        else:
            door_limit = [int(door.id) for door in AccDoor.objects.filter(device__area__pk__in=a_limit)]#所有有效的
            doors_id = request.GET.get("door_id", 0)
            #print '--first--doors_id=',doors_id
            if doors_id:
                doors_id = doors_id.split(",")#默认0，取全部
                #print '----doors_id=',doors_id
                doors_id_left = [int(id) for id in doors_id if int(id) in door_limit]#当前需要的---不过滤也可以
                devices = Device.objects.filter(accdoor__pk__in=doors_id_left).distinct()
                #print '---devices=',devices
            else:#没有area_id,device_id,door_id的请求--door_id实际不可能为0
                #print '----none----'
                devices = Device.objects.filter(area__pk__in=a_limit)
    
    return devices.filter(device_type=DEVICE_ACCESS_CONTROL_PANEL)

def obtain_valid_doors(request, devices):
    doors = AccDoor.objects.filter(device__in=devices)
    doors_id = request.GET.get("door_id", 0)
    if doors_id:
        doors_id = doors_id.split(",")#默认0，取全部
        return [int(id) for id in doors_id]
    return [int(d.id) for d in doors]

#从缓存中获取实时事件的记录，数据经过组织后返回客户端
@login_required
def get_redis_rtlog(request):
    logid = int(request.GET.get('logid', FIRSTVISIT_OR_DELBACKEND))
    step = int(request.GET.get('step', 0))#步长：即要log的最大条数
    rt_type = request.GET.get('type', '')#all alarm 
    devid = request.REQUEST.get("devid", 0)#默认为0，表示监控所有设备的所有门的状态
    
    #再获取实时监控记录
    q_server = check_and_start_queqe_server()
    #print "--",logid+step
#    cfg = dict4ini.DictIni(os.getcwd()+"/appconfig.ini",values={"iaccess": {"down_newlog": 0}}) #默认0点定时下载新记录,定时删除缓存
#    now_hour = datetime.datetime.now().hour
#    if now_hour == cfg.iaccess.down_newlog:
#        q_server.delete("MONITOR_RT")
#        q_server.delete("ALARM_RT")
#        logid = -1#重新取
    
    rtid_all = 0#缓存里所有的记录条数
    rtid_alarm = 0#缓存里所有的报警事件记录
    log_count = 0#返回的有效记录条数
    valid_devices = [] 
    if rt_type == "all":
        rtid_all = q_server.lock_rlen("MONITOR_RT")#被锁住时以及文件缓存为空时都返回-1，即该值不可能为0 此时前端继续使用原来的logid取数据

        if (rtid_all != LOCKED_OR_NOTHING) and (rtid_all < logid):#主要用于后台服务0时定时删除监控缓存时可能导致的不一致，故重新取，当数据量少时未必准确。
            logid = FIRSTVISIT_OR_DELBACKEND#重新取
        #获取门状态door_states
        valid_devices = obtain_valid_devices(request)
        #print '---valid_devices=',valid_devices
        door_states = door_state_monitor(valid_devices)#门状态不涉及辅助输入点，故不需调整
        if logid == FIRSTVISIT_OR_DELBACKEND:#监控全部时获取报警记录的初始id值
            rtid_alarm = q_server.llen("ALARM_RT")
        rtlog = q_server.lrange("MONITOR_RT", logid, logid + step)
        
    elif rt_type == "alarm":
        rtid_alarm = q_server.lock_rlen("ALARM_RT")
        if (rtid_alarm != LOCKED_OR_NOTHING) and (rtid_alarm < logid):#主要用于后台服务0时定时删除监控缓存时可能导致的不一致，故重新取，当数据量少时未必准确。--包含发现报警事件的按钮如果被删除，那么跳转后直接重新开始
            logid = FIRSTVISIT_OR_DELBACKEND#重新取
        
        door_states = { "data": []}
        rtlog = q_server.lrange("ALARM_RT", logid, logid + step)
    
    #rtlog数据格式如下“0-时间 + 1-PIN号 + 2-门id + 3-事件类型 + 4-出入状态 +5-验证方式 +6-卡号+7-设备号”
    #rtlog = ['2010-03-07 09:53:51,370,4,6,0,221,36656656']
    #print 'door_states=',door_states
    #print "----------------------rtlog=", rtlog
    
    q_server.connection.disconnect()
    
    cdatas = []
    a_logids = []
    #如下代码测试时请注释掉
    if logid == FIRSTVISIT_OR_DELBACKEND:
        cc={
            'log_id': logid,
            'all_id': (rtid_all != LOCKED_OR_NOTHING) and rtid_all or 0,#redis中所有记录条数
            'alarm_id': rtid_alarm,
            'log_count': log_count,#返回的记录条数
            'data': cdatas,
            'door_states': door_states["data"],
        }
        rtdata = simplejson.dumps(cc)
        return HttpResponse(smart_str(rtdata))

    if not valid_devices:#如果之前没有进入“all”则需要重新获取有效设备（主要是避免重新获取，每次请求只获取一次即可）
        valid_devices = obtain_valid_devices(request)#通过设备找到对应的门以及辅助输入，作为事件点
    
    for alog in rtlog:
        log = alog.strip()
        #print "log=", log
        #验证数据合法性，保证了除了时间之外的数据都是数字字符，从而可以使用int()而不会出错
        p1 = re.compile(r'(((^((1[8-9]\d{2})|([2-9]\d{3}))([-\/\._])(10|12|0?[13578])([-\/\._])(3[01]|[12][0-9]|0?[1-9]))|(^((1[8-9]\d{2})|([2-9]\d{3}))([-\/\._])(11|0?[469])([-\/\._])(30|[12][0-9]|0?[1-9]))|(^((1[8-9]\d{2})|([2-9]\d{3}))([-\/\._])(0?2)([-\/\._])(2[0-8]|1[0-9]|0?[1-9]))|(^([2468][048]00)([-\/\._])(0?2)([-\/\._])(29))|(^([3579][26]00)([-\/\._])(0?2)([-\/\._])(29))|(^([1][89][0][48])([-\/\._])(0?2)([-\/\._])(29))|(^([2-9][0-9][0][48])([-\/\._])(0?2)([-\/\._])(29))|(^([1][89][2468][048])([-\/\._])(0?2)([-\/\._])(29))|(^([2-9][0-9][2468][048])([-\/\._])(0?2)([-\/\._])(29))|(^([1][89][13579][26])([-\/\._])(0?2)([-\/\._])(29))|(^([2-9][0-9][13579][26])([-\/\._])(0?2)([-\/\._])(29)))((\s+(0?[1-9]|1[012])(:[0-5]\d){0,2}(\s[AP]M))?$|(\s+([01]\d|2[0-3])(:[0-5]\d){0,2})?$))')
        p2 = re.compile(r'^,(((\d+),){6}\d+)$')#r'^,(((\d+),){4}\d+)?$'  5-6
        if p1.match(log[0:19]) and p2.match(log[19:]):
            log_count += 1
            str = log.split(",",8)#0-7 共8部分
            #print "accmonitorlog=", str
            
            #设备名称
            dev_id = int(str[7])
            dev = Device.objects.filter(pk=dev_id)
            alias = dev and unicode(dev[0].alias) or ""
            if dev and dev[0] not in valid_devices:#设备级别的过滤--辅助输入（含联动中触发条件为辅助输入点的）
                break
            
            #事件类型
            event = int(str[3])
            
            #验证方式（或源事件类型）,但是当事件为联动事件时为联动事件的原事件
            veri_event = int(str[5])
            #卡号-联动时复用为联动id号（pk）
            card_no = int(str[6]) and str[6] or ''
            
            door_id = 0
            link_video = []
            #print '---vari_event=',veri_event,'  event=',event,'  door_id',door_id,
            
            if event == 220 or event == 221:#辅助输入点的事件
                #事件点
                in_address_id = int(str[2])#辅助输入点，如1,2,3,4  9，10,11,12
                event_point = unicode(dict(IN_ADDRESS_CHOICES)[in_address_id])
                
                #验证方式
                try:
                    verified = unicode(dict(VERIFIED_CHOICES)[veri_event])#the true verified method("others" included)
                except:
                    verified = unicode(_(u"数据异常"))
                
            else:#与门相关
                door_id_limit = obtain_valid_doors(request, valid_devices)#可控的ip地址，不包含辅助输入点
                
                if event == 6:#事件类型为联动事件
                    #print '----------------event=',event
                    #verified = ''#联动事件验证方式为空-固件字段复用--触发的原事件
                    verified = unicode(dict(VERIFIED_CHOICES)[200])#其他

                    if veri_event == 220 or veri_event == 221:
                        number = int(str[2]) #如C4 9，10,11,12
                        event_point = unicode(dict(IN_ADDRESS_CHOICES)[number])
                        #linkage = AccLinkageIO.objects.filter(Q(device__id=dev_id), Q(trigger_opt=veri_event), Q(in_address_hide=number)|Q(in_address_hide=0))#输入点inout或0只能居其一
                    else:
                        door_id = int(str[2])#门id（不同于门编号）
                        if door_id not in door_id_limit:#门级别的过滤
                            break #跳出for循环，该记录无效
                        #事件点
                        doors = AccDoor.objects.filter(id=door_id)
                        event_point = doors and unicode(doors[0]) or ""
                    #视频联动处理
                    try:
                        link_id = int(card_no) or 0#联动时卡号复用为联动id号
                    except:
                        link_id = 1
                    card_no = ''#联动时不需要显示卡号
                    #print "link_id=", link_id
                    from mysite.iaccess.models import AccLinkageIO
                    try:
                        linkage = AccLinkageIO.objects.filter(id = link_id)
                        if linkage:
                            pwd = linkage[0].video_linkageio.comm_pwd
                            link_video.append(linkage[0].video_linkageio.ipaddress)
                            link_video.append(linkage[0].video_linkageio.ip_port)
                            link_video.append(linkage[0].video_linkageio.video_login)
                            link_video.append(pwd and decrypt(pwd) or "")
                            link_video.append(linkage[0].lchannel_num)
                    except:
                        print_exc()
                    

                else:#其他事件--门相关或设备相关
                    door_id = int(str[2])#门id--如果为0,指的是事件点为设备（如取消报警事件）
                    if door_id:#不为0
                        if door_id not in door_id_limit:#门级别的过滤
                            break #跳出for循环，该记录无效
                        #事件点
                        doors = AccDoor.objects.filter(id=door_id)
                        event_point = doors and unicode(doors[0]) or ""
                    else:
                        event_point = ""#如取消报警事件
                    
                    try:
                        verified = unicode(dict(VERIFIED_CHOICES)[veri_event])#the true verified method("others" included)
                    except:
                        verified = unicode(_(u"数据异常"))
                        
            try:
                event_content = unicode(dict(EVENT_CHOICES)[event])#description of the triggered event
            except:
                event_content = unicode(_(u"数据异常"))
 
            #print 'str[1]=',str[1]
            pin_str = int(str[1]) and unicode(format_pin(str[1])) or ''
            #print '---pin_str=',pin_str
            emps = pin_str and Employee.objects.filter(PIN = pin_str) or ''
            
            #print 'emps=',emps
            if emps:
                empname = emps[0].EName and u"%s(%s)"%(str[1], emps[0].EName) or u"%s"%(str[1])
                photo = emps[0].photo and '/file/' + unicode(emps[0].photo) or ''
            else:
                empname = ''
                photo = ''
            #print '--str[6]=',str[6]
            
            #state = int(str[4])!=2 and unicode(dict(STATE_CHOICES)[int(str[4])]) or ''#2直接显示空
            #连动视频

            #print "link_video=", link_video
            #print '---photo=',photo
            cdata={
                'time': str[0],
                'card': card_no,
                #'door': doorname,#输入点，包含门名称或者辅助输入点
                'device': alias,#设备名称
                'event_point': event_point,#输入点，包含门名称或者辅助输入点
                'door_id': door_id,#doorid
                'event_type': int(str[3]),
                'content': event_content,
                'state': unicode(dict(STATE_CHOICES)[int(str[4])]),#0出，1入
                'verified': verified,
                'emp': empname,#用户名(包含用户编号)
                'photo': photo,#有人员照片的要显示,如/file/photo/000000121.jpg 空代表无照片（或无此人）
                'link_video': link_video,
            }
            cdatas.append(cdata)
        else:
            print "DATA ERROR"
    
    cc={
        'log_id': logid,
        'all_id': rtid_all,#无效
        'alarm_id': rtid_alarm,
        'log_count': log_count,#返回的有效的记录条数，用于改变logid
        'data':cdatas,
        'door_states':door_states["data"],#门状态数据
    }

    #print "**########**cc=",cc
    rtdata = simplejson.dumps(cc)
    return HttpResponse(smart_str(rtdata))

class AccRTMonitor(CachingModel):
    u"""
    实时监控记录
    """
    time = models.DateTimeField(_(u'时间'), null=True, blank=True, editable=True)
    pin = models.CharField(_(u'人员编号'), max_length=20, null=True, blank=True, editable=True)
    card_no = models.CharField(_(u'卡号'), max_length=20, null=True, blank=True, editable=True)
    #device = models.ForeignKey(Device, verbose_name=_(u'设备'), null=True, blank=False, editable=True)
    device_id = models.IntegerField(_(u'设备ID'), null=True, blank=True, editable=False)#特殊用途--表征唯一
    device_name = models.CharField(_(u'设备'), max_length=20, null=True, blank=True, editable=True)
    door_id = models.IntegerField(_(u'设备ID'), null=True, blank=True, editable=False)#特殊用途
    door_name = models.CharField(_(u'门事件点'), max_length=30, null=True, blank=True, editable=True)
    #door = models.ForeignKey(AccDoor,verbose_name=_(u'门事件点'), null=True, blank=True, editable=True)
    in_address = models.IntegerField(_(u'辅助输入点'), null=True, blank=True, editable=True, choices=IN_ADDRESS_CHOICES)  
    verified = models.IntegerField(_(u'验证方式'), default=200, null=True, blank=True, editable=True, choices=VERIFIED_CHOICES)#暂时只支持密码验证和卡验证
    state = models.IntegerField(_(u'出入状态'), null=True, blank=True, editable=True, choices=STATE_CHOICES)
    event_type = models.SmallIntegerField(_(u'事件描述'), null=True, blank=True, editable=True, choices=EVENT_CHOICES)
    trigger_opt = models.SmallIntegerField(_(u'联动触发条件'), null=True, blank=True, editable=True, choices=EVENT_CHOICES)
    #f_video=models.CharField(_(u'视频连动文件'), max_length=100, null=True, blank=True, editable=True)
    
#    def limit_accrtmonitor_to(self, queryset, user):
#        #需要过滤掉用户权限不能控制的设备对应的门的实时监控记录(列表datalist)
#        aa = user.areaadmin_set.all()
#        if not user.is_superuser and aa:
#            areas = [a.area for a in aa]
#            queryset = queryset.filter(device__area__in=areas)#door__device__area__in
#        return queryset

    @staticmethod
    def clear():
        AccRTMonitor.objects.all().delete()
    
    def save(self, *args, **kwargs):
        super(AccRTMonitor, self).save(log_msg=False)
        
    def get_name_by_PIN(self):
        emp = Employee.objects.filter(PIN=self.pin)
        return emp and emp[0].EName or ''

    class OpClearRTLogs(ModelOperation):
        help_text = _(u"全部事件记录包含了所有的实时监控记录（包含异常事件记录），确认后将会被清空！") #清除该表的全部记录
        tips_text =  _(u"确认要清空全部事件记录")
        verbose_name = _(u"清空全部事件记录")
        def action(self):
            self.model.objects.all().delete()

    class OpClearAbnormityLogs(ModelOperation):
        help_text = _(u"门禁异常事件记录是实时监控记录中存在异常的部分，确认后将会被清空！") #清除该表的全部记录
        tips_text =  _(u"确认要清空异常事件记录")
        verbose_name = _(u"清空异常事件记录")
        def action(self):
            self.model.objects.filter(event_type__gte=20).filter(event_type__lt=200).delete()

#    class OpExportRTLogs(ModelOperation):
#        help_text=_(u"导出全部事件记录")
#        verbose_name=u"导出全部事件记录"
#        def action(self):
#            pass
#
#    class OpExportAbnormityLogs(ModelOperation):
#        help_text=_(u"导出异常事件记录")
#        verbose_name=u"导出异常事件记录"
#        def action(self):
#            pass
        
    class Admin(CachingModel.Admin):
        list_display = ['time','pin','get_name_by_PIN','card_no','device_name','door_name','in_address','verified', 'state', 'event_type', 'trigger_opt']
        query_fields = ('pin', 'card_no', 'device_name','door_name','in_address','verified', 'state', 'event_type')#'time', 只能支持精确查询，模糊查询暂时支持不了，故暂时不开放（可使用高级查询）
        visible = False
        menu_group = "acc_monitor_"

    class Meta:
        app_label = 'iaccess'
        db_table = 'acc_monitor_log'
        verbose_name = _(u'实时监控记录')
        verbose_name_plural = verbose_name
