# -*- coding: utf-8 -*-
from django.db import models, connection
from django.db.models import Q
import datetime
import os
import string
from django.contrib import auth
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
from dbapp.utils import *
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.forms.models import ModelChoiceIterator
from base.models import CachingModel, Operation
from model_leaveclass import LeaveClass
from django.db.models import Q
from mysite.personnel.models.model_emp import Employee,EmpForeignKey,EmpMultForeignKey,EmpPoPForeignKey
from mysite.personnel.models.empwidget import ZMulPopEmpChoiceWidget
from base.operation import ModelOperation

AUDIT_STATES=(
    (0,_(u'申请')),
    (1,_(u'正在审核')),
    (2,_(u'已接受')),
    (3,_(u'拒绝')),
    (4,_(u'暂停')),
    (5,_(u'重申请')),
    (6,_(u'重新申请')),
    (7,_(u'取消请假'))
)


#员工请假(考勤例外)表##
class EmpSpecDay(CachingModel):
    '''
    请假原始表模型
    '''
    emp=EmpPoPForeignKey(verbose_name=_(u'人员'),db_column='UserID', null=False, blank=False)
    start= models.DateTimeField(_(u'开始时间'), db_column='StartSpecDay', null=False, default=nextDay(), blank=False)
    end = models.DateTimeField(_(u'结束时间'), db_column='EndSpecDay', null=True, default=endOfDay(nextDay()),blank=False)
    leaveclass=models.ForeignKey(LeaveClass, verbose_name=_(u'假类'), db_column='DateID', null=False, blank=False,default=1)
    reson=models.CharField(_(u'请假原因'), db_column='YUANYING', max_length=100,null=True,blank=True)
    apply=models.DateTimeField(_(u'填写时间'), db_column='Date', null=True, default=datetime.datetime.now(), blank=True)
    state=models.CharField(_(u'申请状态'),max_length=2, null=True, db_column="State", default=2, blank=True, choices=AUDIT_STATES, editable=False)
    def save(self, *args, **kwargs):
        if self.start>=self.end:
            raise Exception(_(u'结束时间不能小于开始时间'))
        
        tt=EmpSpecDay.objects.filter(emp=self.emp,start__lte=self.end,end__gte=self.start)
        if tt and tt[0].id !=self.id:
            raise Exception(_(u'请假时间重复'))
#        tmp=EmpSpecDay.objects.filter(Q(emp=self.emp,start__lte=self.start,end__gte=self.end)| Q(emp=self.emp,start__gte=self.start,end__lte=self.end)).exclude(pk=1)
#        if tmp and tmp[0].pk !=self.pk :
#            raise Exception(_(u'已存在相同请假记录！'))
        
        super(EmpSpecDay,self).save()
        from mysite.att.models.__init__ import get_autocalculate_time as gct
        from model_waitforprocessdata import WaitForProcessData as wfpd
        import datetime
        gct_time=gct()
        if self.start<gct_time or self.end<=gct_time:
            wtmp=wfpd()                
            st=self.start
            et=self.end
            wtmp.UserID=self.emp
            wtmp.starttime=st
            wtmp.endtime=et
            #wtmp.customer=self.customer
            wtmp.save()
        
    def __unicode__(self):
        return u"%s: %s, %s"%(self.emp, self.start and self.start.strftime("%m-%d") or "", self.leaveclass)
        #return u"%s: %s, %s"%(self.emp, self.start and self.start.strftime("%m-%d") or "", self.leaveclass)出错
    class _add(ModelOperation):
        visible=False
        help_text=_(u"新增记录") #新增记录
        verbose_name=_(u"新增")
        def action(self):
            pass
    class OpAddManyUserID(ModelOperation):
        help_text=_(u'''新增''')
        verbose_name=_(u"新增请假")
        params=(
            ('UserID', EmpMultForeignKey(verbose_name=_(u'人员'),blank=False,null=False)),          
            ('start',models.DateTimeField(_(u'开始时间'))),
            ('end',models.DateTimeField(_(u'结束时间'))),
            ('leaveclass',models.ForeignKey(LeaveClass, verbose_name=_(u'假类'))),
            ('reson',models.CharField(_(u'请假原因'),blank=True,null=True,max_length=100)),
            ('apply',models.DateTimeField(_(u'填写时间'), default=datetime.datetime.now(), blank=True)),
        )
        def action(self, **args):
            emps=args.pop('UserID')
            if self.request:
                   if not emps:
                       depts=self.request.POST.getlist('deptIDs')
                       emps=Employee.objects.filter(DeptID__in=depts)
            if args['start']>=args['end']:
                raise Exception(_(u'结束时间不能小于开始时间'))
            if not emps:
                raise Exception(_(u'请选择人员'))
            
            for emp in emps: 
                EmpSpecDay(emp=emp, **args).save()

    class Admin(CachingModel.Admin):
        from mysite.personnel.models.empwidget import ZMulPopEmpChoiceWidget
        sort_fields=["emp.PIN","start","end"]
        disabled_perms=['add_empspecday','dataimport_empspecday']
        #default_widgets={"emp":ZMulPopEmpChoiceWidget}
        list_filter =['emp','reson','state','leaveclass']
        query_fields=['emp__PIN','emp__EName','reson','state']
        list_display=['emp.PIN','emp.EName','start','end','reson','leaveclass']
        
        menu_index=1
    class Meta:
        app_label='att'
        db_table = 'user_speday'
        verbose_name = _(u'请假')
        verbose_name_plural=verbose_name
        unique_together = (("emp", "start","leaveclass"),)

