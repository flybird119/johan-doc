# -*- coding: utf-8 -*-

from django.db import models
from base.cached_model import CachingModel
from base.operation import Operation

from mysite.personnel.models import Employee, EmpForeignKey

StatusType_enum = (
        (0, _(u'未知')),
        (1, _(u'上班签到')),
        (2, _(u'下班签退')),
)

class att_record(CachingModel):
    ID = models.AutoField(primary_key=True,null=False, editable=False)
    EmpID = EmpForeignKey(verbose_name=_(u'人员'),null=False)
    SchID = models.ForeignKey("SchClass", verbose_name=_(u'时段名称') , null=True,default=-1,blank=True)
    SetTime = models.DateTimeField(_(u'设定时间'))
    AttTime = models.DateTimeField(_(u'考勤时间'))
    StatusType = models.SmallIntegerField(_(u'上班签到'), null=True, blank=True, editable=True, default=0, choices=StatusType_enum)
    
    
    class Meta:
        app_label='att'
        db_table='att_record'
        verbose_name=_(u'考勤记录表')
        unique_together = (("EmpID","AttTime"),)