#! /usr/bin/env python
#coding=utf-8
from django.db import models
from base.models import CachingModel
from django.utils.translation import ugettext_lazy as _
from mysite.iclock.models.model_device import Device, DEVICE_ACCESS_CONTROL_PANEL, DEVICE_VIDEO_SERVER
from mysite.iclock.models.dev_comm_operate import sync_set_define_io, sync_delete_define_io
from accmonitorlog import EVENT_CHOICES
from accdoor import LCHANNEL_CHOICES, DEVICE_C3_100, DEVICE_C3_200, DEVICE_C3_400, DEVICE_C3_400_TO_200, DEVICE_C4_200, DEVICE_C4_400, DEVICE_C4_400_TO_200
from dbapp.datautils import filterdata_by_user
from base.middleware import threadlocals

TRIGGEROPT_CHOICES = EVENT_CHOICES
DISABLED_TRIGGEROPT_CHOICES = [6, 7, 11, 12, 13]#事件中不能用来触发联动事件的事件列表

#输入点
INADDRESS_CHOICES = (
    (0, _(u'任意')),
    (1, _(u'门1')),#wiegand+in1+in2
    (2, _(u'门2')),
    (3, _(u'门3')),
    (4, _(u'门4')),
    #C3 C3-100: 无    C3-200: 1,2  C3-400:1,2,3,4
    (301, _(u'辅助输入1')),
    (302, _(u'辅助输入2')),
    (303, _(u'辅助输入3')),
    (304, _(u'辅助输入4')),
    #C4 C4-200: C4-400 : 9,10,11,12
    (409, _(u'辅助输入9')),
    (410, _(u'辅助输入10')),
    (411, _(u'辅助输入11')),
    (412, _(u'辅助输入12')),
)
#输出点
OUTADDRESS_CHOICES = (
    #lockcount
    (1, _(u'门锁1')),
    (2, _(u'门锁2')),
    (3, _(u'门锁3')),
    (4, _(u'门锁4')),
    #C3  C3-100: 1  C3-200: 1,2 C3-400:1,2,3,4 C3-400_to_200:1,2,3,4
    (301, _(u'辅助输出1')),
    (302, _(u'辅助输出2')),
    (303, _(u'辅助输出3')),
    (304, _(u'辅助输出4')),
    #C4  C4-200: 2,4,9,10 C4-400:2,4,6,8,9,10 C4-400_to_200:2,4,6,8,9,10
    (402, _(u'辅助输出2')),
    (404, _(u'辅助输出4')),
    (406, _(u'辅助输出6')),
    (408, _(u'辅助输出8')),
    (409, _(u'辅助输出9')),
    (410, _(u'辅助输出10')),
)

#根据设备型号获取辅助输出
def get_device_auxout(dev):
    auxout_list = []
    index_list = []#特定的index
    out_all = dict(OUTADDRESS_CHOICES)
    
    if dev.accdevice.machine_type == DEVICE_C3_100:
        index_list = [301]
    elif dev.accdevice.machine_type == DEVICE_C3_200:
        index_list = [301, 302]
    elif dev.accdevice.machine_type in [DEVICE_C3_400, DEVICE_C3_400_TO_200]:
        index_list = [301, 302, 303, 304]
    elif dev.accdevice.machine_type == DEVICE_C4_200:
        index_list = [402, 404, 409, 410]
    elif dev.accdevice.machine_type in [DEVICE_C4_400 or DEVICE_C4_400_TO_200]:
        index_list = [402, 404, 406, 408, 409, 410]
        
    for index in index_list:
        if index > 400:
            auxout_list.append((index-400, unicode(out_all[index])))
        else:
            auxout_list.append((index-300, unicode(out_all[index])))
    return auxout_list#tuple(auxout_list)
        

ACTION_CLOSE = 0
ACTION_OPEN = 1
ACTION_LONGOPEN = 255
ACTIONTYPE_CHOICES = (
    (ACTION_CLOSE, _(u'关闭')),
    (ACTION_OPEN, _(u'打开')),#只有打开时才需要设置延时时间
    (ACTION_LONGOPEN, _(u'常开')),
)


class AccLinkageIO(CachingModel):
        u"""
        联动设置-当前只支持单控制器的联动设置.输入点根据事件判断是门还是辅助输入。输出点则是根据out_type_hide来判断是锁还是辅助输出
        """
        linkage_name = models.CharField(_(u'联动设置名称'), null=False, max_length=30, blank=False, unique=True)
        device = models.ForeignKey(Device, verbose_name=_(u'设备'), null=True, blank=False, editable=True)#控制器id
        trigger_opt = models.SmallIntegerField(_(u'触发条件'), default=0, null=True, blank=False, editable=True, choices=TRIGGEROPT_CHOICES)
        in_address_hide = models.SmallIntegerField(_(u'输入点地址'), null=True, blank=False, editable=False)        
        in_address = models.SmallIntegerField(_(u'输入点地址'), default=0, null=True, blank=False, editable=True, choices=INADDRESS_CHOICES)
        out_type_hide = models.SmallIntegerField(_(u'输出类型'), null=True, blank=False, editable=False)
        out_address_hide = models.SmallIntegerField(_(u'输出点地址'), null=True, blank=False, editable=False) 
        out_address = models.SmallIntegerField(_(u'输出点地址'), default=0, null=True, blank=False, editable=True, choices=OUTADDRESS_CHOICES)
        action_type = models.SmallIntegerField(_(u'动作类型'), default=0, null=True, blank=False, editable=True, choices=ACTIONTYPE_CHOICES)#联动动作类型，非复位动作类型
        delay_time = models.PositiveSmallIntegerField(_(u'延时'), default=20, help_text=_(u'秒 (范围:1-254)'), null=True, blank=False, editable=True)#延时（复位时间）
        video_linkageio = models.ForeignKey(Device, verbose_name=_(u'视频服务器'), related_name='video_set', null=True, blank=True, editable=True)
        lchannel_num = models.SmallIntegerField(_(u'绑定通道'), default=0, null=True, blank=True, editable=True, choices=LCHANNEL_CHOICES)
        #video_delay_time = models.PositiveSmallIntegerField(_(u'录像延时'), default=20, help_text=_(u'秒 (范围:1-254)'), null=True, blank=True, editable=True)#延时（复位时间）
        
        def limit_device_to(self, queryset):
            print '--------------------------queryset=',queryset
            return filterdata_by_user(queryset.filter(device_type = DEVICE_ACCESS_CONTROL_PANEL), threadlocals.get_current_user()) #只要门禁控制器
        
        def limit_video_linkageio_to(self, queryset):
            print '-----------------------', filterdata_by_user(queryset.filter(device_type = DEVICE_VIDEO_SERVER), threadlocals.get_current_user()) #只要门禁控制器
            return filterdata_by_user(queryset.filter(device_type = DEVICE_VIDEO_SERVER), threadlocals.get_current_user()) #只要门禁控制器
        
        def __unicode__(self):
            return u'%s'%self.linkage_name
        
        def delete(self):
            sync_delete_define_io(self)
            super(AccLinkageIO, self).delete()
        
        def get_action_type(self):
            return self.delay_time if self.action_type == ACTION_OPEN else self.action_type

        def data_valid(self, sendtype):
            tmp = AccLinkageIO.objects.filter(linkage_name=self.linkage_name.strip())
            if tmp and tmp[0] != self:   #新增时不能重复。
                raise Exception(_(u'联动设置名称设置重复'))

#            tmp_a = AccLinkageIO.objects.filter(device=self.device, trigger_opt=self.trigger_opt, in_address=self.in_address)
#            if tmp_a and tmp_a[0] != self:
#                raise Exception(_(u'系统中已存在该设备在该触发条件下输入点相同的联动设置'))
            
            if self.in_address == 0:
                tmp_b = AccLinkageIO.objects.filter(device=self.device, trigger_opt=self.trigger_opt, in_address__gt=0)#id_address不为0
                if tmp_b and tmp_b[0] != self:
                    raise Exception(_(u'系统中已存在该设备在该触发条件下输入点不为“任意”的联动设置'))
            else:
                tmp_c = AccLinkageIO.objects.filter(device=self.device, trigger_opt=self.trigger_opt, in_address=0)
                if tmp_c and tmp_c[0] != self:
                    raise Exception(_(u'系统中已存在该设备在该触发条件下输入点为“任意”的联动设置'))
                
            tmp_c = AccLinkageIO.objects.filter(device=self.device, trigger_opt=self.trigger_opt, in_address=self.in_address, out_address=self.out_address)
            if tmp_c and tmp_c[0] != self:
                raise Exception(_(u'系统中已存在该设备在该触发条件下输入点和输出点都相同的联动设置'))
            
            #动作类型为打开时
            if self.action_type != ACTION_LONGOPEN and self.action_type != ACTION_CLOSE and (self.delay_time < 1 or self.delay_time > 254):
                raise Exception(_(u'延时时间的设置范围为 1-254(秒)'))
            
        def save(self, *args, **kwargs):
            if self.out_address < 300:#门锁
                self.out_type_hide = 0
                self.out_address_hide = self.out_address
            else:#辅助输出
                self.out_type_hide = 1
                if self.out_address < 400:#300 < a <400  C3
                    self.out_address_hide = self.out_address - 300
                else:#>400 C4
                    self.out_address_hide = self.out_address - 400

                
            if self.in_address < 300:
                self.in_address_hide = self.in_address
            else:
                if self.out_address < 400:#200 < a <400 C3
                    self.in_address_hide = self.in_address - 300
                else:#C4
                    self.in_address_hide = self.in_address - 400
                    
            super(AccLinkageIO, self).save()#log_msg=False
            sync_set_define_io(self)

        class Admin(CachingModel.Admin):
            parent_model = 'DoorSetPage'
            menu_group = 'acc_doorset'
            disabled_perms = ['clear_acclinkageio', 'dataimport_acclinkageio', 'dataexport_acclinkageio', 'view_acclinkageio']
            menu_focus = 'DoorSetPage'
            menu_index = 100025
            position = _(u'门禁系统 -> 门设置 -> 联动设置')
            list_display = ('linkage_name', 'device', 'trigger_opt', 'in_address', 'out_address', 'action_type')
            query_fields =('linkage_name', 'device', 'trigger_opt', 'action_type') #list_filter
            help_text = _(u'请先输入联动设置名称再选择要设置的设备。每台设备可进行多次联动设置。')

        class Meta:
            app_label='iaccess'
            db_table = 'acc_linkageio'
            verbose_name = _(u'联动设置')
            verbose_name_plural=verbose_name


