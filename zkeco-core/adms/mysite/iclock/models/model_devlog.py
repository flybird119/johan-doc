# -*- coding: utf-8 -*-
from django.db import models
import datetime
from dbapp.utils import *
from django.utils.translation import ugettext_lazy as _
from model_device import DeviceForeignKey
from base.operation import OperationBase, Operation, ModelOperation
from django.conf import settings
    
class DevLog(models.Model):
    '''
    设备通讯日志表模型
    '''
    SN = DeviceForeignKey(verbose_name=_(u'设备'))
    OP = models.CharField(_(u'数据'),max_length=40, default="TRANSACT",)
    Object = models.CharField(_(u'对象'),max_length=80, null=True, blank=True)
    Cnt = models.IntegerField(_(u'数据记录数'),default=1, blank=True)
    ECnt = models.IntegerField(_(u'错误'),default=0, blank=True)
    OpTime = models.DateTimeField(_(u'上传时间'),default=datetime.datetime.now())
    def Device(self):
        return get_device(self.SN_id)
    @staticmethod    
    def del_old(): return ("OpTime", 30)
    def save(self, **args):
        if not self.id:
            self.OpTime=datetime.datetime.now()
        models.Model.save(self, **args)
    class dataexport(Operation):
        help_text=_(u"数据导出") #导出
        verbose_name=_(u"导出")
        visible=False
        def action(self):
                pass
    
    def __unicode__(self): 
        try:
            return u"%s, %s, %s"%(self.SN, self.OpTime.strftime('%y-%m-%d %H:%M'), self.OP)
        except:
            return u"%s, %s, %s"%(self.SN_id, self.OpTime.strftime('%y-%m-%d %H:%M'), self.OP)

    class Admin:
        visible = "mysite.att" in settings.INSTALLED_APPS#暂只有考勤使用
        list_display=('SN.alias','SN.sn','OpTime','OP','Cnt')
        query_fields=('SN.alias','SN.sn','OP','Cnt')
        list_filter=("SN",'OpTime')
        search_fields = ["OP","Object"]
        disabled_perms=["change_devlog","delete_devlog","add_devlog"]
        hide_perms=["dataexport_devlog",]
    class Meta:
        app_label='iclock'
        verbose_name = _(u"设备通讯日志")
        verbose_name_plural=verbose_name
        db_table = 'devlog'
