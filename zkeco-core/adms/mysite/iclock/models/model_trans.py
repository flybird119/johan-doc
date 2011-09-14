#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.db import models, connection
from django.db.models import Q
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
from mysite.personnel.models import Department
from mysite.personnel.models.model_emp import Employee, EmpForeignKey,EmpPoPForeignKey
from model_device import Device, DeviceForeignKey
from base.operation import OperationBase, Operation, ModelOperation
def get_stored_file_name(sn, id, fname):
        fname="%s%s/%s"%(settings.ADDITION_FILE_ROOT, sn, fname)
        if id:
                fname, ext=os.path.splitext(fname)
                fname="%s_%s%s"%(fname,id,ext)
        fname.replace("\\\\","/")
        return fname


def get_upload_file_name(sn, id, fname):
        return get_stored_file_name('upload/'+sn, id, fname)

def get_stored_file_url(sn, id, fname):
        fname=settings.UNIT_URL+"iclock/file/%s/%s"%(sn, fname)
        if id:
                fname, ext=os.path.splitext(fname)
                fname="%s_%s%s"%(fname,id,ext)
        return fname


def get_upload_file_url(sn, id, fname):
        return get_stored_file_url('upload/'+sn, id, fname)



VERIFYS=(   #---签卡类型
(0, _(u"密码")),
(1, _(u"指纹")),
(2, _(u"卡")),
(5, _(u"增加")),
(9, _(u"其他")),
)

ATTSTATES=(
("I",_(u"上班签到")),
("O",_(u"下班签退")),

("8",_(u"就餐开始")),
("9",_(u"就餐结束")),
#("i",_("Break in")),
#("o",_("Break out")),
#("0",_("Check in")),
#("1",_("Check out")),
("2",_(u"外出")),
("3",_(u"外出返回")),
("4",_(u"加班签到")),
("5",_(u"加班签退")),
("255",_(u"未设置状态")),
#("160",_("Test Data")),
)
# 签卡记录表
class Transaction(models.Model):
        UserID = EmpPoPForeignKey(db_column='userid', verbose_name=_(u"人员"))
        TTime = models.DateTimeField(_(u'考勤时间'), db_column='checktime')
        State = models.CharField(_(u'考勤状态'), db_column='checktype', max_length=5, default='I', choices=ATTSTATES)
        Verify = models.IntegerField(_(u'验证方式'), db_column='verifycode', default=0, choices=VERIFYS)    #---签卡类型
        SN = DeviceForeignKey(db_column='SN', verbose_name=_(u'设备'), null=True, blank=True)
        sensorid = models.CharField(db_column='sensorid', verbose_name=u'Sensor ID', null=True, blank=True, max_length=5, editable=False)
        WorkCode = models.CharField(_(u'工作代码'), max_length=20, null=True, blank=True)
        Reserved = models.CharField(_(u'保留'), max_length=20, null=True, blank=True)
        sn_name = models.CharField(_(u'序列号'), max_length=40, null=True, blank=True)
        def limit_transaction_to(self,query_set,user): 
            from mysite.iclock.iutils import userDeptList,userAreaList
            deptids = userDeptList(user)
            if not deptids:
                return query_set
            deptids = [ int(dept.pk) for dept in deptids ]
            return query_set.filter(UserID__DeptID__in=deptids)
        def employee(self): #cached employee
                try:
                        return Employee.objByID(self.UserID_id)
                except:
                        return None
        def Time(self):
                if self.TTime.microsecond>500000:
                        self.TTime=self.TTime+datetime.timedelta(0,0,1000000-self.TTime.microsecond)
                return self.TTime
        def StrTime(self):
                return self.Time().strftime('%Y/%m%d/%H%M%S')
        @staticmethod        
        def delOld(): return ("TTime", 365)
        def Device(self):
                return get_device(self.sn_name)
        def get_img_url(self, default=None):
                device=self.Device()
                emp=self.employee()
                if device and emp:
                        try:
                                pin=int(emp.PIN)
                        except:
                                pin=emp.PIN
                        fname="%s.jpg"%(self.StrTime())
                        imgUrl=getUploadFileName(device.SN, pin, fname)
                        if os.path.exists(imgUrl):
                                return getUploadFileURL(device.SN, pin, fname)
                return default
        def get_thumbnail_url(self, default=None):
                device=self.Device()
                emp=self.employee()
                if device and emp:
                        try:
                                pin=int(emp.PIN)
                        except:
                                pin=emp.PIN
                        fname="%s.jpg"%(self.StrTime())
                        imgUrl=getUploadFileName("thumbnail/"+device.SN, pin, fname)
                        #print imgUrl
                        if not os.path.exists(imgUrl):
                                imgUrlOrg=getUploadFileName(device.SN, pin, fname)
                                if not os.path.exists(imgUrlOrg):
                                        #print imgUrlOrg, "is not exists"
                                        return default
                                if not createThumbnail(imgUrlOrg, imgUrl):
                                        #print imgUrl, "create fail."
                                        return default
                        return getUploadFileURL("thumbnail/"+device.SN, pin, fname)
                #print "device, emp", device, emp
                return default
        def __unicode__(self):
                return self.UserID.__unicode__()+', '+self.TTime.strftime("%y-%m-%d %H:%M:%S")
                
        @staticmethod
        def myData(user):
                if user.username=='employee': #employee user
                        return Transaction.objects.filter(UserID=request.employee)
                return Transaction.objects.filter(UserID__DeptID__in=userDeptList(user))
        
        def get_attpic(self):            
            from dbapp.file_handler import get_model_filename
            dt=self.TTime.strftime("%Y%m%d%H%M%S")
            pin=""
            pin= int(self.UserID.PIN)
            sn=self.sn_name

            t=get_model_filename(Transaction,            
            "%s/%s/%s" % (sn, dt[:4], dt[4:8])+"/"+ str(pin)+"_"+ dt[8:] + ".jpg",
            "picture")[1]
            return t
        
        def get_emppic(self):
            return self.UserID.photo            
        
        class dataexport(Operation):
                help_text=_(u"数据导出") #导出
                verbose_name=_(u"导出")
                visible=False
                def action(self):
                        pass
        
        class Meta:
                app_label='iclock'
                verbose_name = _(u"原始记录表")
                verbose_name_plural = verbose_name
                db_table = 'checkinout'
                unique_together = (("UserID", "TTime"),)
                permissions = (
                                ('clearObsoleteData_transaction','Clear Obsolete Data'),
                                )
        class Admin:
                default_give_perms=["contenttypes.can_AttCalculate"]
                sort_fields=["UserID.PIN","TTime"]
                app_menu="att"
                menu_group = 'att'
                visible = "mysite.att" in settings.INSTALLED_APPS#暂只有考勤使用
                read_only=True
                api_fields=('UserID.PIN','UserID.EName','TTime','State','sn_name')
                list_display=('UserID_id','UserID.PIN','UserID.EName','TTime','State','sn_name','get_attpic','get_emppic')
                photo_path_tran="get_attpic"
                photo_path="get_emppic"
                hide_fields=('UserID_id','get_attpic')
                list_filter = ('UserID','TTime','State','Verify','SN')
                query_fields=['UserID__PIN','UserID__EName','sn_name']
                search_fields=('TTime',)
                menu_index=4
                disabled_perms=["add_transaction",'change_transaction','delete_transaction','clearObsoleteData_transaction']
                layout_types=["table","photo"]