#! /usr/bin/env python
#coding=utf-8

from django.db import models
from base.models import CachingModel
from base.operation import Operation,ModelOperation
from django.utils.translation import ugettext_lazy as _
from model_emp import LEAVETYPE,YESORNO
from base.cached_model import  STATUS_OK,STATUS_INVALID,STATUS_LEAVE
from dbapp import data_edit
from mysite.personnel.models.model_emp import Employee,EmpForeignKey,EmpMultForeignKey,EmpPoPForeignKey,EmpPoPMultForeignKey
from mysite.iclock.models.dev_comm_operate import *

from django.conf import settings
from mysite import settings as st

init_settings = []
if settings.APP_CONFIG["remove_permision"]:
    init_settings = [ k.split(".")[1] for k,v in settings.APP_CONFIG["remove_permision"].items() if v=="False" and k.split(".")[0]=="LeaveLog"]
    
acc=[]
if "mysite.iaccess" in st.INSTALLED_APPS:#zkeco+iaccess
    acc=["isClassAccess",]
               

class LeaveLog(CachingModel):
        """
        离职操作
        """
        UserID=EmpPoPForeignKey(verbose_name=_(u"人员"),null=False,editable=True)
        leavedate=models.DateField(verbose_name=_(u'离职日期'),editable=True)
        leavetype=models.IntegerField(verbose_name=_(u'离职类型'),choices=LEAVETYPE,editable=True)
        reason=models.CharField(verbose_name=_(u'离职原因'),max_length=200,null=True,blank=True,editable=True)        
        isReturnTools =models.BooleanField(verbose_name=_(u'是否归还工具'),choices=YESORNO, null=False,default=True,  editable=True)
        isReturnClothes=models.BooleanField(verbose_name=_(u'是否归还工衣'),choices=YESORNO, null=False,default=True,  editable=True)
        isReturnCard=models.BooleanField(verbose_name=_(u'是否归还卡'),choices=YESORNO, null=False,default=True, editable=True)
        isClassAtt=models.BooleanField(verbose_name=_(u'立即关闭考勤'),choices=YESORNO, null=False,default=0, editable=False)
        isClassAccess=models.BooleanField(verbose_name=_(u'立即关闭门禁'),choices=YESORNO, null=False,default=0, editable=False)
        
        def __unicode__(self):
                return self.UserID.PIN +"  "+ (self.UserID.EName and u" %s"%self.UserID.EName or "")
        def save(self):
                try:    
                        
                        super(LeaveLog,self).save()
                        if self.UserID.status==0:            
                            self.UserID.status=STATUS_LEAVE
                            self.UserID.save()
                except:
                        import traceback;traceback.print_exc()
                        pass
        class _delete(Operation):
            help_text = _(u"删除选定记录") #删除选定的记录
            verbose_name = _(u"删除")
            visible=False
            def action(self):
                        self.object.delete()       
        class OpRestoreEmpLeave(Operation):
                help_text=_(u'恢复离职人员')
                verbose_name=_(u'离职恢复')
                def action(self):
                    import datetime
                    emp=self.object.UserID
                    if emp.isblacklist==1:
                        raise Exception(_(u'黑名单不能处理离职恢复！'))
                    emp.__class__.can_restore=True
                    emp.isblacklist=None
                    emp.status=STATUS_OK
                    emp.Hiredday=datetime.datetime.now().strftime("%Y-%m-%d")
                    emp.save()
                    emp.__class__.can_restore=False
                    #下载到设备
                    newObj=self.object.UserID
                    from mysite.iclock.models.model_cmmdata import adj_user_cmmdata                      
                    #sync_set_user(newObj.search_device_byuser(), [newObj])
                    adj_user_cmmdata(newObj,[],newObj.attarea.all())
                    self.object.delete()

        class OpCloseAtt(Operation):
                help_text=_(u'关闭考勤')
                verbose_name=_(u'关闭考勤')
                def action(self):
                    oldObj=self.object.UserID
                    if self.object.isClassAtt==1:
                            raise Exception(_(u"考勤已经关闭！"))                    
                    self.object.isClassAtt=1
                    self.object.save()

                    devs=oldObj.search_device_byuser()
                    sync_delete_user(devs, [oldObj])


        class _change(ModelOperation):
            visible=False
            def action(self):
                pass            
        class OpCloseAccess(Operation):
                help_text=_(u'关闭门禁')
                verbose_name=_(u'关闭门禁')
                def action(self):
                    oldObj=self.object.UserID
                    if oldObj.check_accprivilege():
                        devs=oldObj.search_accdev_byuser()
                        sync_delete_user(devs,[oldObj]) 
                        sync_delete_user_privilege(devs,[oldObj])
                    if self.object.isClassAccess==1:
                        raise Exception(_(u"门禁已经关闭！"))
                    self.object.isClassAccess=1
                    self.object.save()
                        
                        
        class Admin(CachingModel.Admin):
                sort_fields=["UserID.PIN","leavedate"]
                app_menu="personnel"
                menu_index=4
                visible = "mysite.att" in settings.INSTALLED_APPS#暂只有考勤使用
                list_filter=('UserID','leavedate','leavetype','isReturnTools','isReturnCard','isReturnClothes')
                query_fields=['UserID__PIN','UserID__EName','leavedate','leavetype','reason']
                list_display=['UserID.PIN','UserID.EName','UserID.DeptID','UserID.isblacklist','leavedate','leavetype','isClassAtt','reason']+acc
                disabled_perms=['change_leavelog','dataimport_leavelog','delete_leavelog']+init_settings
                help_text=_(u"加入黑名单的人员，将不能离职恢复")

        class Meta:
                verbose_name=_(u'人员离职')
                verbose_name_plural=verbose_name
                app_label='personnel'


#在表单生成前加入自定义字段 或操作
def detail_resplonse(sender, **kargs):
        from dbapp.templatetags import dbapp_tags
        from mysite.personnel.models.model_emp import Employee
        from dbapp.widgets import form_field, check_limit
        if kargs['dataModel']==LeaveLog:
                form=sender['form']
                #print form.fields
                if "mysite.att" in settings.INSTALLED_APPS:
                    closeatt=models.BooleanField(verbose_name=_(u'立即关闭考勤'),default=True)
                    form.fields['opcloseatt']=form_field(closeatt)
                if "mysite.iaccess" in settings.INSTALLED_APPS:
                    closeacc=models.BooleanField(verbose_name=_(u'立即关闭门禁'),default=True)
                    form.fields['opcloseacc']=form_field(closeacc)
                    
                field = models.BooleanField(_(u'是否黑名单'), choices=YESORNO, default=0)
                form.fields['isblacklist']=form_field(field)
                
data_edit.pre_detail_response.connect(detail_resplonse)        


#在表单提交后，对自定义字段进行处理
def DataPostCheck(sender, **kwargs):
        from mysite.personnel.models.model_emp import device_pin,Employee
        from mysite.iclock.models.modelproc  import getEmpCmdStr
        oldObj=kwargs['oldObj']
        newObj=kwargs['newObj']
        request=sender
        if isinstance(newObj, LeaveLog):
                bl=request.REQUEST.get("isblacklist","")
                att=request.REQUEST.get("opcloseatt","")
                acc=request.REQUEST.get("opcloseacc","")                
                if acc:
                        newObj.OpCloseAccess(newObj).action()
                if bl:
                        newObj.UserID.isblacklist=bl
                        newObj.UserID.save()
                if att:
                        newObj.OpCloseAtt(newObj).action()                        
                        
data_edit.post_check.connect(DataPostCheck)
                