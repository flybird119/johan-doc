# coding=utf-8

from django.utils.translation import ugettext_lazy as _
from django.db import models
from base.models import CachingModel, Operation, ModelOperation
from mysite.iclock.models.model_device import DeviceMultForeignKey,DevicePoPForeignKey,Device
from mysite.personnel.models.model_emp import EmpPoPForeignKey
verbose_name=_(u"研究")
_menu_index=5

class model_1(CachingModel):
#    emp=EmpPoPForeignKey(verbose_name=_(u'人员'),db_column='UserID', null=False, blank=False)
#    device = DevicePoPForeignKey(verbose_name=_(u'设备'),db_column='DeviceID',null=False, blank=False)
    username = models.CharField(_(u'用户名'), db_column="name", null=True, max_length=24, blank=True, default="")
    password = models.CharField(_(u'密码'), max_length=16, null=True, blank=True, editable=True)
    
    class _add(ModelOperation):
        visible=False
        help_text=_(u"新增记录") #新增记录
        verbose_name=_(u"新增")
        def action(self):
            pass
    class OpAddManyUserID(ModelOperation):
        help_text=_(u'''新增模型一''')
        verbose_name=_(u"新增")
        params=(
            ('device',DeviceMultForeignKey(verbose_name=_(u'设备'),db_column='DeviceID',null=False, blank=False)),
            ('username',models.CharField(_(u'用户名'), db_column="name", null=True, max_length=24, blank=True, default="")),
            ('password',models.CharField(_(u'密码'), max_length=16, null=True, blank=True, editable=True)),
#            ('UserID', EmpMultForeignKey(verbose_name=_(u'人员'),blank=False,null=False)),          
#            ('start',models.DateTimeField(_(u'开始时间'))),
#            ('end',models.DateTimeField(_(u'结束时间'))),
#            ('leaveclass',models.ForeignKey(LeaveClass, verbose_name=_(u'假类'))),
#            ('reson',models.CharField(_(u'请假原因'),blank=True,null=True,max_length=100)),
#            ('apply',models.DateTimeField(_(u'填写时间'), default=datetime.datetime.now(), blank=True)),
        )
        def action(self, **args):
            devices=args.pop('device')   
            if self.request:
                   if not devices:
                       depts=self.request.POST.getlist('deptIDs')
                       devices=Device.objects.filter(area__in=depts)
            if not devices:
                raise Exception(_(u'请选择人员'))
            
            for device in devices: 
                model_1(device=device, **args).save()
    
    class Operation1(Operation):
            help_text = _(u'''操作一说明''')
            verbose_name = _(u"操作一")
#            visible = False # 是否显示，默认为True
            # 二元元祖 注意","不能少，元素一：参数名 元素二：供django from渲染的模型字段
            params = (('username',models.CharField(_(u'用户名'), db_column="name", null=True, max_length=24, blank=True, default="")),)
            def action(self,username):
                '''
                做相关数据处理
                '''
                print username
    class Operation2(ModelOperation):
            help_text = _(u'''操作二说明''')
            verbose_name = _(u"操作二")
            def action(self):
                pass
    class Admin(CachingModel.Admin):
        query_fields = ['username', 'password']
#        visible = False
        help_text = _(u'''模型添加的说明''')
        menu_index=101
    class Meta:
#        app_label = 'johan'
        verbose_name = _(u"模型一")
        db_table = 'table1'
class model_2(models.Model):
    username = models.CharField(_(u'用户名'), db_column="name", null=True, max_length=24, blank=True, default="")
    password = models.CharField(_(u'密码'), max_length=16, null=True, blank=True, editable=True)
    class Admin:
        query_fields = ['username', 'password']
        visible = False
    class Meta:
#        app_label = 'johan'
        verbose_name = _(u"模型二")
        db_table = 'table2'