# -*- coding: utf-8 -*-
from django.db import models, connection
from django.db.models import Q
from base.cached_model import CachingModel
from base.operation import Operation

from django.contrib.auth.models import User, Permission, Group
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
from mysite.personnel.models.model_emp import Employee,EmpForeignKey,EmpMultForeignKey,EmpPoPForeignKey,EmpPoPMultForeignKey

from mysite.iclock.models.model_trans   import ATTSTATES,Transaction
from base.operation import ModelOperation

from django import forms
 ##员工考勤修改日志##

class CheckExact(CachingModel):
    '''
    补签表模型
    '''
    UserID = EmpPoPForeignKey(verbose_name=_(u'人员'),db_column='UserID',  editable=True)    
    CHECKTIME = models.DateTimeField(_(u'签卡时间'),null=False, blank=False)
    CHECKTYPE=models.CharField(_(u'考勤状态'),max_length=5, default=0,choices=ATTSTATES)
    ISADD=models.SmallIntegerField(null=True, blank=True,editable=False)
    YUYIN=models.CharField(_(u'签卡原因'),max_length=100, null=True, blank=True)
    ISMODIFY=models.SmallIntegerField(null=True, default=0,blank=True,editable=False)
    ISDELETE=models.SmallIntegerField(null=True,default=0, blank=True,editable=False)
    INCOUNT=models.SmallIntegerField(null=True,default=0, blank=True,editable=False)
    ISCOUNT=models.SmallIntegerField(null=True, default=0,editable=False)
    MODIFYBY = models.CharField(_(u'修改'),max_length=20,null=True, blank=True,editable=False)
    DATE=models.DateTimeField(_(u'员工考勤修改日志日期'),null=True, blank=True,editable=False)
    def save(self,**args):
        
        ce=CheckExact.objects.filter(UserID=self.UserID,CHECKTIME=self.CHECKTIME)
        if ce and ce[0].id!=self.id:
                   raise Exception(_(u'补签记录输入重复'))
        if self.pk!=None:
            ce=CheckExact.objects.get(pk=self.pk)
        old=""
        if ce:
            old=Transaction.objects.filter(UserID=self.UserID,TTime=ce.CHECKTIME)
       
        super(CheckExact,self).save(**args)
        if old:
            t=old[0]
        else:            
            t=Transaction()
        t.UserID=self.UserID
        t.TTime=self.CHECKTIME
        t.State=self.CHECKTYPE
        t.Verify=5
        t.save()    #---添加到签卡原始数据表
        from mysite.att.models.__init__ import get_autocalculate_time as gct
        from model_waitforprocessdata import WaitForProcessData as wfpd
        import datetime
        gct_time=gct()
        if self.CHECKTIME<gct_time:
            wtmp=wfpd()                
            st=datetime.datetime(self.CHECKTIME.year,self.CHECKTIME.month,self.CHECKTIME.day,0,0,0)
            et=datetime.datetime(self.CHECKTIME.year,self.CHECKTIME.month,self.CHECKTIME.day,23,59,59)
            wtmp.UserID=self.UserID
            wtmp.starttime=st
            wtmp.endtime=et
            #wtmp.customer=self.customer
            wtmp.save() #---添加考勤计算任务计划
        
    class _add(ModelOperation):
        visible=False
        verbose_name=_(u'新增')
        def action(self):
            pass
    def delete(self):
        Transaction.objects.filter(UserID=self.UserID,TTime=self.CHECKTIME).delete()
        super(CheckExact,self).delete()
        
    def __unicode__(self):
        return u"%s"%self.UserID
    class OpAddManyCheckExact(ModelOperation):
        verbose_name=_(u"新增补签卡")
        help_text=_(u'新增补签卡同时会在原始记录表中增加一条相同记录，修改时会同时修改原始记录表中的相同记录')
        params=(
            ('UserID', EmpMultForeignKey(verbose_name=_(u'人员'),blank=True,null=True)),            
            ('checktime',models.DateTimeField(_(u'签卡时间'))),
            ('checktype',models.CharField(_(u'考勤状态'), choices=ATTSTATES)),
            ('reason',models.CharField(_(u'签卡原因'),blank=True,null=True,max_length=100)),
        )
        def action(self,UserID,checktime,checktype,reason):
            if self.request:
                if  UserID==0:
                    depts=self.request.POST.getlist('deptIDs')
                    UserID=Employee.objects.filter(DeptID__in=depts) 
                if not UserID:
                    raise Exception(_(u'请选择人员'))
                ce=CheckExact.objects.filter(UserID__in=UserID,CHECKTIME=checktime)
                if ce.count()>0:
                    raise Exception(_(u'补签记录输入重复'))
                
                for emp in UserID:
                    ck=CheckExact()
                    ck.UserID=emp
                    ck.CHECKTIME=checktime
                    ck.YUYIN=reason
                    ck.CHECKTYPE=checktype
                    ck.save()

    class Admin(CachingModel.Admin):
        default_give_perms=["contenttypes.can_AttCalculate",]
        sort_fields=["UserID.PIN","CHECKTIME"]
        menu_index=2
        app_menu="att"
        api_fields=('UserID.PIN','UserID.EName','CHECKTIME','CHECKTYPE','YUYIN')
        list_display=('UserID_id','UserID.PIN','UserID.EName','CHECKTIME','CHECKTYPE','YUYIN',)
        list_filter =('UserID','CHECKTIME','CHECKTYPE','YUYIN')
        query_fields=('UserID__PIN','UserID__EName','CHECKTIME','CHECKTYPE','YUYIN')
        hide_fields=('UserID_id',)
        disabled_perms=["add_checkexact",'dataimport_checkexact']
        #default_widgets={'UserID': ZMulEmpChoiceWidget}
    class Meta:
        app_label='att'
        db_table = 'checkexact'
        verbose_name=_(u'补签卡')
        verbose_name_plural=verbose_name
        
