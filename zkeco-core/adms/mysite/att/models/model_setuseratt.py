# -*- coding: utf-8 -*-
from django.db import models
from dbapp.utils import *
from django.utils.translation import ugettext_lazy as _
from django import forms
 
from base.cached_model import CachingModel
from base.operation import Operation,ModelOperation
from mysite.personnel.models.model_emp import Employee,EmpPoPMultForeignKey,EmpForeignKey,EmpMultForeignKey

ATTTYPE=(
    (0,_(u'正常上班')),
    (2,_(u'休息')),
)
# 员工调休表
class SetUserAtt(CachingModel):
    UserID=EmpForeignKey(verbose_name=_(u'人员'),blank=True,null=True)
    starttime=models.DateTimeField(_(u'开始时间'),blank=False,null=False)
    endtime=models.DateTimeField(_(u'结束时间'),blank=False,null=False)
    atttype=models.SmallIntegerField(_(u'考勤类型'),default=2,choices=ATTTYPE,blank=False,null=False)
    
    def save(self,**args):
        if self.UserID=="" or self.UserID==None:
            raise Exception(_(u'请选择人员！'))
        if self.endtime<=self.starttime:
            raise Exception(_(u'结束时间不能小于或等于开始时间！'))
        sua=SetUserAtt.objects.filter(UserID=self.UserID,starttime__lte=self.endtime,endtime__gte=self.starttime)
        if sua and sua[0].pk!=self.pk:
            raise Exception(_(u'调休记录输入重复'))
            
        
        super(SetUserAtt,self).save(**args)  
        from mysite.att.models.__init__ import get_autocalculate_time as gct
        from model_waitforprocessdata import WaitForProcessData as wfpd
        import datetime
        gct_time=gct()
        if self.starttime<gct_time or self.endtime<=gct_time:
              wtmp=wfpd()                
              st=self.starttime
              et=self.endtime
              wtmp.UserID=self.UserID
              wtmp.starttime=st
              wtmp.endtime=et
              wtmp.save()

    def __unicode__(self):
        return u"%s"%(self.UserID)
    
        
    class OpAddManyObj(ModelOperation):
        verbose_name=_(u'新增')
        help_text=_(u'新增')
        params=(
            ('UserID',EmpMultForeignKey(verbose_name=_(u'人员'),null=True,blank=True)),
            ('starttime',models.DateTimeField(_(u'开始时间'),blank=False,null=False)),
            ('endtime',models.DateTimeField(_(u'结束时间'),blank=False,null=False)),
            ('atttype',models.SmallIntegerField(_(u'考勤类型'),default=2,choices=ATTTYPE,blank=False,null=False)),
            
        )
        def action(self,UserID,starttime,endtime,atttype):     
            users=[]        
            if self.request:
                deptIDs=self.request.POST.getlist('deptIDs')
                UserIDs=self.request.POST.getlist('UserID') 
                if deptIDs:
                    users=Employee.objects.filter(DeptID__in=deptIDs)
                elif UserIDs:
                    users=Employee.objects.filter(pk__in=UserIDs)
                if not users:
                    raise Exception(u"%s"%_(u'请选择人员'))
                for u in users:
                    sua=SetUserAtt()
                    sua.UserID=u
                    sua.starttime=starttime
                    sua.endtime=endtime
                    sua.atttype=atttype
                    sua.save()
    class _add(ModelOperation):
        visible=False
        verbose_name=_(u'新增')
        help_text=_(u'新增')
        def action(self):
            pass
    
    class Admin(CachingModel.Admin):
        visible=True
        #list_display=('UserID.PIN','UserID.EName','starttime','endtime','atttype')
        query_fields=('UserID.PIN','UserID.EName','starttime','endtime','atttype')
        adv_fields=('UserID.PIN','starttime','endtime','atttype')
        help_text=_(u'设置人员调休：可以在已经安排了排班的情况下，设置人员为休息，也可以人员为休息时，设置为上班状态！')
        #default_widgets={'UserID':EmpPoPMultForeignKey}
        hide_perms = ["add_setuseratt",]
        
        pass
    class Meta:
        app_label="att"
        db_table="setuseratt"
        verbose_name=_(u'调休')
