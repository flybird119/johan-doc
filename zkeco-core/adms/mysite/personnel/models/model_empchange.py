#! /usr/bin/env python
#coding=utf-8

from django.db import models
from base.models import CachingModel
from base.operation import Operation,ModelOperation
from django.utils.translation import ugettext_lazy as _
from model_leave import YESORNO
from django.contrib.contenttypes.models import ContentType
from dbapp import data_edit
from base.base_code import BaseCode,base_code_by

from mysite.personnel.models import Department
from mysite.personnel.models.model_emp import HIRETYPE,EMPTYPE
from mysite.personnel.models.model_emp import Employee,EmpForeignKey,EmpMultForeignKey,EmpPoPForeignKey,EmpPoPMultForeignKey
from mysite.personnel.models.model_area import Area,AreaManyToManyField
from dbapp.utils import getJSResponse
from django.utils.encoding import smart_str
from django.utils.simplejson  import dumps
from django.db.models import Q
from base.base_code import BaseCode,base_code_by
from mysite.iclock.models.dev_comm_operate import *
import datetime
from django.conf import settings


APPROVAL=(
        (1,_(u'申请')),
        (2,_(u'已批')),
)
POSTION=(
        (1,_(u'部门')),
        (2,_(u'职务')),
        (3,_(u'雇用类型')),
        (4,_(u'区域')),
)
def to_json(obj):
    #print obj
    ret=[]
    for t in obj:
        x=[]
        x.append(t[0])
        x.append(u"%s"%t[1])
        ret.append(list(x))
    return ret
def get_empchange_postion(request,userid,num):
    from model_emp import Employee
    num=int(num)
    userid=int(userid)
    user=Employee.objects.filter(id=userid)    
    qs={}
    try:
        if user:
            qs['old']=get_user_postion(user[0],num)
            qs['new']=to_json(get_empchange_postion_list(num))
        #print qs
    except:
        import traceback;traceback.print_exc()
    return getJSResponse(smart_str(dumps(qs)))

def get_user_postion(user,num):
    
    if num==1:  #部门
        return user.DeptID.id
    elif num==2:#职务
        return user.Title
    elif num==3:#雇用类型
        return user.emptype
    else:       #区域
        tt=user.attarea.select_related().values_list('pk')
        ret=[]
        for i in tt:
            ret.append(i[0])               
        return ret
    
def get_empchange_postion_list(num):
    
    if num==1:  #部门
        return Department.objects.all().values_list('id','name')
    elif num==2:#职务
        return BaseCode.objects.filter(content='TITLE').values_list('id','display')
    elif num==3:#雇用类型
    
        return EMPTYPE
    else:               #区域
        return Area.objects.all().values_list('id','areaname')
            
        
POSTIONMODEL=[
        Department.objects.all(),
        base_code_by('TITLE'),
        EMPTYPE,
        Area.objects.all()
        ]

def show_visible():
    if settings.APP_CONFIG.language.language!='zh-cn':
        return False
    else:
        if "mysite.att" in settings.INSTALLED_APPS:
            return True
        else:
            return False

from model_emp import EmpForeignKey
class EmpChange(CachingModel):
        '''调动表'''
        changeno=models.AutoField(verbose_name=_(u'调动单号'),db_column='changeno',primary_key=True,editable=False)
        UserID=EmpPoPForeignKey(verbose_name=_(u"人员"),editable=True)
        changedate=models.DateTimeField(verbose_name=_(u'调动时间'),null=True,blank=True,editable=True,default=datetime.datetime.now())
        changepostion=models.IntegerField(verbose_name=_(u'调动栏位'),choices=POSTION,editable=True,null=True,blank=True,)        
        oldvalue=models.CharField(verbose_name=_(u'调动前'),max_length=100,editable=True,null=True,blank=True)
        newvalue=models.CharField(verbose_name=_(u'调动后'),max_length=100,editable=True,null=True,blank=True)
        changereason=models.CharField(max_length=200,verbose_name=_(u'调动原因'),null=True,blank=True,editable=True)
        isvalid=models.BooleanField(verbose_name=_(u'是否生效'),choices=YESORNO,editable=True,default=0)
        approvalstatus=models.IntegerField(verbose_name=_(u'审核状态'),choices=APPROVAL,editable=False,default=2)
        remark=models.CharField(verbose_name=_(u'备注'),editable=True,null=True,blank=True,max_length=200)
        def __unicode__(self):
                       return self.UserID.PIN+(self.UserID.EName and " %s"%self.UserID.EName or "")

        def save(self):
            #ContentType.objects.get_for_model(obj)
            #print "self.changepostion:%s"%self.changepostion
            try:
                if self.changepostion and int(self.changepostion) in [1,2,3,4]:  #同步人员信息表,并原还页面上有可能修改原始数据
                    cmp = [_(u'请选择调整后的部门'),_(u'请选择调整后的职务'),_(u'请选择调整后的雇佣类型'),_(u'请选择调整后的区域')]
                    if not self.newvalue:
                        raise Exception(cmp[int(self.changepostion)-1])
                    where={}
                    if self.changepostion==1:
                        self.oldvalue=self.UserID.DeptID.pk
                        where['id__exact']=int(self.newvalue)
                        self.UserID.DeptID=Department.objects.filter(Q(**where))[0]
                        
                    elif self.changepostion==2:
                        self.oldvalue=self.UserID.Title
                        try:
                            where['id__exact']=int(self.newvalue)
                            t=BaseCode.objects.filter(Q(**where))
                            if t:
                                self.UserID.Title=t[0]
                            else:
                                self.UserID.Title=""
                        except:
                            self.UserID.Title=self.newvalue
                        
                    else:
                        self.oldvalue=self.UserID.emptype
                        self.UserID.emptype=int(self.newvalue)
                        
                    self.UserID.save()
                
                super(EmpChange,self).save()
            except Exception, e:
                import traceback; traceback.print_exc();
                raise e
                return self
        class _delete(Operation):
            visible=False
            def action(self):
                pass
        class OpAvailable(Operation):
            help_text=_(u'立即生效')
            verbose_name=_(u'立即生效')
            visible=False
            def action(self):
                self.object.approvalstatus=2
                self.object.isvalid=1
                self.object.save()
            
        def get_value(self,type=1):
            #print "type:%s"%type
            from mysite.personnel.models import Department,Area
            if type==1:
                data=self.oldvalue
            else:
                data=self.newvalue
            if not data:
                return ""    
            if self.changepostion==1:
                return u"%s"%Department.objects.get(pk=int(data))
            elif self.changepostion==2:
                where={}
                where['id__exact']=int(data)
                t=BaseCode.objects.filter(Q(**where))
                return u"%s"%t[0]
            elif self.changepostion==3:
                return u"%s"%EMPTYPE[int(data)-1][1]    
            else:
                area=Area.objects.filter(pk__in=data.split(","))
                return u",".join([u"%s"%a.areaname for a in area])
            
        def get_value(self,type):
            from mysite.personnel.models import Department,Area    
            if type==1:
                data=self.oldvalue
            else:
                data=self.newvalue
            #print "emp data:%s"%data
            if not data:
                return ""    
            if self.changepostion==1:
                return u"%s"%Department.objects.get(pk=int(data))
            elif self.changepostion==2:
#                where={}
#                where['value__exact']=int(data)
#                where['display__exact']='TITLE'
#                t=BaseCode.objects.filter(Q(**where))
                t=base_code_by('TITLE')
                
                for i,v in t:
                    if int(i)==int(data):
                        return v
                return ""
#                if t:
#                    return u"%s"%t[0]
#                else:
#                    return ""
            elif self.changepostion==3:
                return u"%s"%EMPTYPE[int(data)-1][1]    
            else:
                area=Area.objects.filter(pk__in=data.split(","))
                return u",".join([u"%s"%a.areaname for a in area])
                
        def get_oldvalue(self):            
            return self.get_value(1)      

        def get_newvalue(self):
            return self.get_value(2)
        
        class Admin(CachingModel.Admin):
                from django.forms import Select
                sort_fields=["changeno","UserID.PIN","changedate"]
                app_menu="personnel"
                visible = show_visible()#暂只有考勤使用
                list_filter=('UserID','approvalstatus','isvalid')
                query_fields=['UserID__PIN','UserID__EName','changepostion','changereason']
                list_display=['UserID.PIN','UserID.EName','changepostion','oldvalue','newvalue','changedate','changereason','remark']
                newadded_column = {'oldvalue' : 'get_oldvalue','newvalue' : 'get_newvalue'}
                menu_index=3
                help_text=_(u"区域的调整：将会把该人员所属原区域内的设备清除掉该人员，并自动下发到新区域内的所有设备中")
                #default_widgets={'oldvalue':Select,'newvalue':Select}
                disabled_perms=['dataimport_empchange','opavailable_empchange','delete_empchange']
        class Meta:
                app_label='personnel'
                verbose_name=_(u'人员调动')
                verbose_name_plural=verbose_name
        
#在表单生成前加入自定义字段 或操作
def detail_resplonse(sender, **kargs):
        from mysite.personnel.models.depttree import ZDeptMultiChoiceWidget 
        from dbapp.templatetags import dbapp_tags
        from dbapp.widgets import form_field, check_limit
        if kargs['dataModel']==EmpChange:
                #print "sender:%s"%sender
                #print "kargs:%s"%kargs
                form=sender['form']
                ec=None
                if kargs['key']!=None:
                    ec=EmpChange.objects.get(pk=kargs['key'])
                #print form.fields
                available=models.BooleanField(verbose_name=_(u'立即生效'))
                chkdept=models.BooleanField(verbose_name=_(u'部门'))
                chkhiretype=models.BooleanField(verbose_name=_(u'雇用类型'))
                chktitle=models.BooleanField(verbose_name=_(u'职务'))
                chkarea=models.BooleanField(verbose_name=_(u'区域'))
                title=Employee._meta.get_field('Title')                
                area=AreaManyToManyField(Area,blank=True,null=True)
                dept=Employee._meta.get_field('DeptID')
                hiretype=models.CharField(verbose_name=_(u'雇用类型'),choices=EMPTYPE,blank=True,null=True)

                form.fields['available']=form_field(available)
           
                form.fields['oldtitle']=form_field(title)
                if ec and ec.changepostion==4:
                    if ec.oldvalue:
                        objs=Area.objects.filter(pk__in=ec.oldvalue.split(","))
                    else:
                        objs=[]                        
                    form.fields['oldarea']=form_field(area,initial=objs)
                else:
                    form.fields['oldarea']=form_field(area)
                if ec and ec.changepostion==1:
                    obj=None
                    if ec.oldvalue:
                        obj=Department.objects.get(pk=ec.oldvalue)
                    form.fields['olddept']=form_field(dept,initial=obj)
                else:
                    form.fields['olddept']=form_field(dept)

                form.fields['oldhiretype']=form_field(hiretype)

                form.fields['newtitle']=form_field(title)
                    
                if ec and ec.changepostion==4:  
                    if ec.newvalue:
                        objs=Area.objects.filter(pk__in=ec.newvalue.split(","))                  
                    else:
                        objs=[]
                    form.fields['newarea']=form_field(area,initial=objs)
                else:
                    form.fields['newarea']=form_field(area)
                if ec and ec.changepostion==1:  
                    obj=None
                    if ec.newvalue:
                        obj=Department.objects.get(pk=ec.newvalue)
                                                          
                    form.fields['newdept']=form_field(dept,initial=obj)
                else:
                    form.fields['newdept']=form_field(dept)

                form.fields['newhiretype']=form_field(hiretype)                
                
                form.fields['chkdept']=form_field(chkdept)
                form.fields['chkhiretype']=form_field(chkhiretype)
                form.fields['chktitle']=form_field(chktitle)
                form.fields['chkarea']=form_field(chkarea)
data_edit.pre_detail_response.connect(detail_resplonse)        


#在表单提交后，对自定义字段进行处理
def DataPostCheck(sender, **kwargs):
        from model_area import Area        
        oldObj=kwargs['oldObj']
        newObj=kwargs['newObj']
        request=sender
        if isinstance(newObj, EmpChange):
                newarea=[]
                acc=request.REQUEST.get("available","")
                chkdept  =str(request.REQUEST.get("chkdept","")  )
                chkhiretype  =str(request.REQUEST.get("chkhiretype","")  )
                chktitle  =str(request.REQUEST.get("chktitle","")  )
                chkarea  =str(request.REQUEST.get("chkarea","")  )
                newdept =request.REQUEST.get("newdept","")  
                newtitle =request.REQUEST.get("newtitle","")  
                newhiretype =request.REQUEST.get("newhiretype","")  
                newarea =request.REQUEST.getlist("newarea")                                  
                #无4种中的任意一种调动时删除已保存记录
                if (not chkdept) and (not chkhiretype) and (not chktitle) and (not chkarea):
                    newObj.delete()
                    return                   
                #循环保存多次调动
                lst=[]
                if chkdept:
                    lst.append(1)
                if chktitle:
                    lst.append(2) 
                if chkhiretype:
                    lst.append(3)
                onlyChange=True
                for i  in range(len(lst))  :
                   if onlyChange:
                        tmpObj=newObj
                        onlyChange=False
                   else:
                        tmpObj=EmpChange() 
                        tmpObj.UserID=newObj.UserID    
                        tmpObj.changereason=newObj.changereason
                        tmpObj.isvalid=newObj.isvalid
                        tmpObj.approvalstatus=newObj.approvalstatus
                        tmpObj.changedate=newObj.changedate
                        tmpObj.remark=newObj.remark
                          
                   tmpObj.changepostion=lst[i]             
                   if lst[i]==1:
                       tmpObj.newvalue=newdept
                   elif lst[i]==2:
                       tmpObj.newvalue=newtitle
                   else:
                       tmpObj.newvalue=newhiretype
                   if acc:
                        tmpObj.approvalstatus=2
                        tmpObj.isvalid=1
                   tmpObj.save()
                
                if chkarea:
                    if onlyChange:
                        tmpObj=newObj
                    else:
                        tmpObj=EmpChange()
                        tmpObj.UserID=newObj.UserID
                        tmpObj.changereason=newObj.changereason
                        tmpObj.isvalid=newObj.isvalid
                        tmpObj.approvalstatus=newObj.approvalstatus
                        tmpObj.changedate=newObj.changedate
                        tmpObj.remark=newObj.remark                        
                    tmpObj.changepostion=4
                    if newarea:#同步人员考勤区域
                        from mysite.iclock.models.model_cmmdata import adj_user_cmmdata
                        import copy
                        oldarea=copy.deepcopy(tmpObj.UserID.attarea.all())
                        where={'id__in':[int(i) for i in newarea]}
                        tmpObj.oldvalue=",".join(["%s"%i for i in  newObj.UserID.attarea.select_related().values_list('pk')] )         #保留原始区域值
                        tmpObj.UserID.attarea=Area.objects.filter(Q(**where))
                        tmpObj.UserID.save()
                        adj_user_cmmdata(tmpObj.UserID,oldarea,tmpObj.UserID.attarea.all())
                        tmpObj.newvalue=",".join([str(i) for i in newarea])
                    if acc:
                        tmpObj.isvalid=1                    
                        tmpObj.approvalstatus=2
                    tmpObj.save()   
                if not chkarea and len(lst)==0:
                    newObj.delete()
data_edit.post_check.connect(DataPostCheck)     # -------------------------------- 添加 post_check 信号的处理
