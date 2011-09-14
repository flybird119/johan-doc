#coding=utf-8
'''
通用数据添加修改视图
'''
from django.template import loader, RequestContext, Template, TemplateDoesNotExist
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.core.exceptions import ObjectDoesNotExist
from exceptions import AttributeError
import string
import datetime
from utils import *
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django import forms
from django.utils.encoding import smart_str
from django.conf import settings
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from data_utils import *
from django.utils.datastructures import SortedDict
from modelutils import getDefaultJsonDataTemplate,getUsrCreateFrameOptions
from base.model_utils import GetModel
from data_utils import get_model_master
import django.dispatch
import widgets
from enquiry import Enquiry
from base.operation import OperationBase, Operation, ModelOperation
from base.cached_model import STATUS_INVALID
from dbapp.templatetags import dbapp_tags
from traceback import print_exc
from django.db import models
from base.cached_model import SAVETYPE_NEW,SAVETYPE_EDIT

try:
    import cPickle as pickle
except:
    import pickle

def make_instance_save(instance, fields, fail_message):
    """Returns the save() method for a Form."""
    def save(self, commit=True):
            return forms.save_instance(self, instance, fields, fail_message, commit)
    return save

def make_instance_data_valid(instance, fields):
    """Returns the data_valid() method for a Form."""
    from django.forms.models import   construct_instance    #---data_valid()时会调用
    def data_valid(self,sendtype):        
            obj= construct_instance(self, instance, fields)
            if hasattr(obj,"data_valid"):
                return obj.data_valid(sendtype)
            else:
                pass
    return data_valid

def _form_for_model(model, instance=None, form=forms.BaseForm, fields=None, post=None,
               formfield_callback=widgets.form_field, lock_fields=[], read_only=False): 
    if hasattr(model.Admin, "form_class"):
            if model.Admin.form_class:
                    return model.Admin.form_class(post, instance=instance)
    opts = model._meta 
    field_list = []
    default_widgets={}
    if hasattr(model.Admin, "default_widgets"):
            default_widgets=model.Admin.default_widgets
            if callable(default_widgets): default_widgets(instance)
    for f in opts.fields + opts.many_to_many: 
            if not f.editable: 
               continue 
            if fields and not f.name in fields: 
               continue
#            if post and not f.name in post.keys(): 
#                continue
            
            current_value = None
            if instance: 
                    try:
                            current_value=f.value_from_object(instance)
                            if isinstance(f,models.BooleanField):
                                if current_value:
                                    current_value=1
                                else:
                                    current_value=0
                    except ValueError:
                            pass
            elif f.has_default and not (f.default==models.fields.NOT_PROVIDED):
                    current_value=f.default

            if read_only or f.name in lock_fields or \
                    (f.primary_key and current_value): #被锁定的字段不能被修改,主键不能被修改
                    formfield = widgets.form_field_readonly(f, initial=current_value)
            else:
                    widget=None
                    if f.name in default_widgets: 
                            widget=default_widgets[f.name]
                    elif f.__class__ in default_widgets:
                            widget=default_widgets[f.__class__]
                    if widget:
                            formfield = formfield_callback(f, initial=current_value, widget=widget)
                    else:
                            formfield = formfield_callback(f, initial=current_value)
                    if formfield: widgets.check_limit(f, model, formfield, instance)

            if formfield:
                    field_list.append((f.name, formfield)) 
    base_fields = SortedDict(field_list) 
    
    return type(opts.app_label+"_"+model.__name__+'_edit', (form,), 
            {'base_fields': base_fields, '_model': model, 
             'save': make_instance_save(instance or model(), fields, 'created'),
             'data_valid':make_instance_data_valid(instance or model(), fields),
            })(post)

def form_for_model(model, instance=None, form=forms.BaseForm, fields=None, post=None,
               formfield_callback=widgets.form_field, lock_fields=[], read_only=False): 
    import os
    f=_form_for_model(model, instance or model(), form, fields, post, formfield_callback, lock_fields, read_only)
    
    if hasattr(model.Admin, "help_text"):
            f.admin_help_text=model.Admin.help_text
    if instance and instance.pk:
            f.object_photo=dbapp_tags.thumbnail_url(instance)
    help_image="img/model/%s.%s.png"%(model._meta.app_label, model.__name__)
    if os.path.exists(settings.MEDIA_ROOT+help_image):
            f.admin_help_image=settings.MEDIA_URL+"/"+help_image
    return f

def form_for_instance(instance, form=forms.BaseForm, fields=None, post=None,
               formfield_callback=widgets.form_field, lock_fields=[], read_only=False): 
    return form_for_model(instance.__class__, instance, form, fields, post, 
               formfield_callback, lock_fields, read_only)
    
#在表单生成前加入自定义字段 或操作
pre_detail_response = django.dispatch.Signal(providing_args=["dataModel", "key"])
    
def DataDetailResponse(request, dataModel, form, key=None, instance=None, **kargs):
    '''
    编辑页直接视图
    '''
    from urls import get_model_data_url, dbapp_url
    from django.db import models
    import base
    from django.contrib.contenttypes.models import ContentType
    if not kargs: kargs={}
    tmp_file=request.GET.get('_t',"%s.html"%form.__class__.__name__)
    kargs["dbapp_url"]=dbapp_url
    request.dbapp_url=dbapp_url
    kargs["form"]=form
    kargs["title"]=(u"%s"%dataModel._meta.verbose_name).capitalize()
    kargs["dataOpt"]=dataModel._meta
    kargs['model_name']=dataModel.__name__
    kargs['app']=dataModel._meta.app_label
    if issubclass(dataModel,models.Model):
        kargs["app_menu"]=hasattr(dataModel.Admin,"app_menu") and dataModel.Admin.app_menu or  dataModel._meta.app_label
    kargs["add"]=key==None
    kargs["instance"]=instance
    if key and issubclass(dataModel, base.models.CachingModel) and dataModel.Admin.log:
            try:
                    ct=ContentType.objects.get_for_model(dataModel)
                    kargs['log_url']=get_model_data_url(base.models.LogEntry)+("?content_type__id=%s&object_id=%s"%(ct.pk,key))
                    kargs['log_search']=("content_type__id=%s&object_id=%s"%(ct.pk,key))
            except:
                    print_exc()
    if hasattr(dataModel.Admin, "form_tabs"):
            kargs["tabs"]=dataModel.Admin.form_tabs
    if hasattr(dataModel.Admin, "form_before_response"):
        dataModel.Admin.form_before_response(request, kargs, key)
    kargs["position"] = hasattr(dataModel.Admin, "position") and dataModel.Admin.position or None
    pre_detail_response.send(sender=kargs, dataModel=dataModel, key=key)
    template_list = [tmp_file, dataModel.__name__+'_edit.html','data_edit.html']
    return render_to_response(template_list, RequestContext(request,kargs),)        

def new_object(model, data):
    fd={}
    fields=[]
    obj=model()
    for field in data:
            value=data[field]
            if field.find("__"): field=field.split("__")[0]
            try:
                    f=model._meta.get_field(field)
            except:
                    continue
            if isinstance(f, models.fields.related.ForeignKey):
                    fd[str(field)+"_id"]=value
            else:
                    fd[str(field)]=value
            fields.append(field)
    for f,v in fd.items():
        if hasattr(obj, f): setattr(obj, f, v)
    return obj, fields
# 验证处理信号
post_check = django.dispatch.Signal(providing_args=["oldObj", "newObj"])
# 预处理信号    providing_args 信号参数集合
pre_check = django.dispatch.Signal(providing_args=["oldObj", "model"])
post_change_check = django.dispatch.Signal(providing_args=["oldObj", "newObj"])

NON_FIELD_ERRORS = '__all__'
    
def save_for_files(request,instance):
    u"图片字段保存"
    import datetime
    if request.FILES:
        for k,v in request.FILES.items():
            if hasattr(instance,k):
                getattr(instance,k).save(datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")+".jpg",v)
        #instance.save()
            
def DataNewPost(request, dataModel):
    '''
    新增页提交表单的处理
    '''
    from admin_detail_view import doPostAdmin,doCreateAdmin
    from django.db import IntegrityError 
    if dataModel==User:     # user 模型的转向处理
            return doPostAdmin(request, dataModel, '_new_')
            
    f = form_for_model(dataModel, post=request.POST)    #---得到模型的表单对象
    
    if hasattr(dataModel.Admin, "form_post"):   #---扩展apiAdmin.form_post 
        dataModel.Admin.form_post(request, f, None)
    
    if f.is_valid():    #---表单验证
        obj=None    #---待添加的对象
        key=(dataModel._meta.pk.name in f.cleaned_data) and f.cleaned_data[dataModel._meta.pk.name] or None
        if key:
                try:
                        obj=dataModel.objects.get(pk=key)
                        if not (fieldVerboseName(dataModel, "status") and obj.status==STATUS_INVALID):
                                f.errors[dataModel._meta.pk.name]=[_(u"复制")]
                                return DataDetailResponse(request, dataModel, f)
                except ObjectDoesNotExist:
                        print_exc()
                        pass
        oldEmp=None                
        try:
                pre_check.send(sender=request, model=dataModel, oldObj=oldEmp) #---触发预处理信号 pre_check              
                f.data_valid(SAVETYPE_NEW)      # 重要 api Admin.data_valid 初始数据验证  SAVETYPE_NEW=1  #-----------------Model 扩展api            
                obj=f.save()    #预保存
                save_for_files(request,obj)
                key=obj.pk
        except IntegrityError: #---一般异常的处理
                if dataModel.__name__=="Group":
                    info = _(u"角色名称不能重复")
                else:
                    info =_(u"数据不能重复")
                f.errors[NON_FIELD_ERRORS]=u'<ul class="errorlist"><li>%s</li></ul>'%info
                return DataDetailResponse(request, dataModel, f)
        except Exception, e: #---其他异常的处理
                f.errors[NON_FIELD_ERRORS]=u'<ul class="errorlist"><li>%s</li></ul>'%e
                return DataDetailResponse(request, dataModel, f)
            
        if hasattr(dataModel.Admin, "form_after_save"): #---扩展api Admin.form_after_save
            dataModel.Admin.form_after_save(request, oldEmp, obj)
            
        try:    #---#---触发处理信号post_check
            post_check.send(sender=request, oldObj=oldEmp, newObj=obj)
        except Exception, e:
            f.errors[NON_FIELD_ERRORS]=u'<ul class="errorlist"><li>%s</li></ul>'%e
            return DataDetailResponse(request, dataModel, f)

        popup = request.GET.get("_popup", "")
        if popup:
                the_add_object = unicode(obj)
                return HttpResponse(u'<script type="text/javascript">\nopener.dismissAddAnotherPopup(window, "%s", "%s");\n</script>' % (key, the_add_object))

        return HttpResponse('{ Info:"OK" }')
        
    else:   # ------------------------验证出错的处理
        for i,v in dict(f.errors).items(): 
            print i, ":"
            for vi in v: print "\t", vi
        f.errors[NON_FIELD_ERRORS]=u'<ul class="errorlist"><li>%s: %s</li></ul>' % (i, vi)
        return DataDetailResponse(request, dataModel, f)

@login_required        
def DataNew(request, app_label, model_name):
    '''
    通用添加视图入口
    '''
    from admin_detail_view import retUserForm,adminForm,doPostAdmin,doCreateAdmin
    try:
        dataModel=GetModel(app_label, model_name)
        lock=request.GET.get("_lock",None)
        read_only=lock=='ALL'
        if not hasPerm(request.user, dataModel, "add"):
                return NoPermissionResponse()
        if not dataModel: return NoFound404Response(request)
        if request.method=="POST" and not read_only:
                return DataNewPost(request, dataModel)

        instance,fields=new_object(dataModel, request.GET)
        if dataModel==User:
                return retUserForm(request, adminForm(request), isAdd=True)
        dataForm=form_for_instance(instance, lock_fields=lock and fields or [], read_only=read_only)
        return DataDetailResponse(request, dataModel, dataForm, None, instance) #------------------------转向其他处理
    except:
        import traceback;traceback.print_exc()

def DataChangePost(request, dataModel, dataForm, emp):
    '''
    编辑提交处理视图
    '''
    f=dataForm
    if hasattr(dataModel.Admin, "form_post"):
        dataModel.Admin.form_post(request, f, emp)

    if f.is_valid():
        #检查有没有改变关键字段
        key=(dataModel._meta.pk.name in f.cleaned_data) and f.cleaned_data[dataModel._meta.pk.name] or emp.pk
        if key and "unicode" not in str(type(key)):
            key = unicode(key)
        if key and ('%s'%emp.pk)!=('%s'%key):
            f.errors[dataModel._meta.pk.name]=[_(u"关键字段%(object_name)s不能修改!")%{'object_name':fieldVerboseName(dataModel, dataModel._meta.pk.name)}];
            return DataDetailResponse(request, dataModel, f, key=emp.pk)
        obj=None
        for field in emp._meta.many_to_many:
            setattr(emp, field.name+"_set", tuple(getattr(emp, field.name).all()))

        obj_old_str=pickle.dumps(emp)
        obj_old=pickle.loads(obj_old_str)

        try:
            pre_check.send(sender=request, model=dataModel, oldObj=obj_old)
            f.data_valid(SAVETYPE_EDIT)#进行业务逻辑处理
            obj=f.save()
            save_for_files(request,obj)
        except Exception, e: #通常是不满足数据库的唯一性约束导致保存失败
            f.errors[NON_FIELD_ERRORS]=u'<ul class="errorlist"><li>%s</li></ul>'%e
            return DataDetailResponse(request, dataModel, f, key=emp.pk)
        for field in obj._meta.many_to_many:
            setattr(obj, field.name+"_set", tuple(getattr(obj, field.name).all()))

        if hasattr(dataModel.Admin, "form_after_save"):
            dataModel.Admin.form_after_save(request, obj_old, obj)
        post_check.send(sender=request, oldObj=obj_old, newObj=obj)
        return HttpResponse('{ Info:"OK" }')
    else:
        for i,v in dict(f.errors).items(): 
            print i, ":"
            for vi in v: print "\t", vi
        return DataDetailResponse(request, dataModel, f, key=emp.pk)

@login_required
def DataDetail(request, app_label, model_name, DataKey):
    '''
    通用编辑视图入口
    '''
    from admin_detail_view import retUserForm,adminForm,doPostAdmin,doCreateAdmin
    dataModel=GetModel(app_label, model_name)
    if not dataModel: return NoFound404Response(request)
    lock=request.GET.get("_lock",None)
    read_only=(lock=='ALL')
    if not read_only:
            try: 
                    if dataModel.Admin.read_only: read_only=True
            except: pass
    perm=hasPerm(request.user, dataModel, "change")
    if not perm and not read_only: 
            if not hasPerm(request.user, dataModel, "browse"):
                    return NoPermissionResponse()
            read_only=True
    master=get_model_master(dataModel)        
    if dataModel==User:        ######### 用户编辑的处理 ##########
            if request.method=="POST" and not read_only:
                    if not perm: return NoPermissionResponse()
                    return doPostAdmin(request, dataModel, DataKey)
            else:
                    return doCreateAdmin(request, dataModel, DataKey)
    
    if master:
            try:
                    m_instance=master.rel.to.objects.get(pk=DataKey)
            except ObjectDoesNotExist:
                    return NoFound404Response(request)
            try:
                    instance=dataModel.objects.get(**{master.name:m_instance})
            except ObjectDoesNotExist:
                    instance=dataModel(**{master.name: m_instance})
    else:
            try:
                    instance=dataModel.objects.get(pk=DataKey)
            except ObjectDoesNotExist:
                    return NoFound404Response(request)

    if request.method=="POST" and not read_only:
            if not perm: return NoPermissionResponse()
            return DataChangePost(request, dataModel, form_for_instance(instance, post=request.POST), instance)
    if lock:
            fields=[field.find("__") and field.split("__")[0] or field for field in dict(request.GET)]
    return DataDetailResponse(request, dataModel, 
            form_for_instance(instance, lock_fields=master and [master.name] or (lock and fields or []), read_only=read_only), instance.pk, instance)
#        return DataChangeGet(request, dataModel, form_for_instance(instance, lock_fields=master and [master.name] or []), instance)


