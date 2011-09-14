#coding=utf-8
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponse
from base.model_utils import GetModel
from data_utils import NoFound404Response
import types
from base.operation import Operation, ModelOperation
from django.shortcuts import render_to_response
from django.template import loader, RequestContext, Template, TemplateDoesNotExist
from widgets import form_field as form_field_default, form_field_readonly
from utils import getJSResponse
from django.http import HttpResponse
from django import forms
from django.db.models import Model
from base.cached_model import CachingModel
from base.models_logentry import LogEntry
import data_utils

def form_field(f, readonly=False, **kwargs):
    if readonly:
        return form_field_readonly(f, **kwargs)
    return form_field_default(f, **kwargs)

def get_form_(request,app_label, model_name, op_name):
    '''
    根据 op_name 得到 表单视图 2
    '''
    ############## 根据 HTTP_REFERER 来判断是否是 从worktable页链接而 ######################
    is_worktable=""
    if request.META.has_key('HTTP_REFERER'):    #---Referer:从哪个页面链接过来的
        is_worktable=request.META['HTTP_REFERER']    
    if is_worktable.find("worktable")!=-1:
        is_worktable=True
    else:
        is_worktable=False
    ############## 得到操作的模型, 及ModelOperation 对象 op_name###############    
    model=GetModel(app_label, model_name)
    if not model: return NoFound404Response(request)
    if not hasattr(model, op_name): return NoFound404Response(request)
    op=getattr(model, op_name)
    if not (type(op)==types.TypeType and issubclass(op, ModelOperation)):
            return NoFound404Response(request)
    ############## 当前用户操作权限的判断###############    
    if op_name.startswith("_"):
        opn= op_name[1:]
    else:
        opn=op_name
    if model.__name__=="Group":
        opn="groupdel"        
    if not data_utils.hasPerm(request.user, model, opn.lower()):
        return HttpResponse("session_fail_or_no_permission")
    ############## 操作表单提交的处理和生成操作页的处理###############
    if request.method=='POST':
        if issubclass(model,Model) and not issubclass(model,CachingModel):
            keys=request.REQUEST.getlist("K")
            ret=[]
            objs=model.objects.filter(pk__in=keys)
            try:
                op_class=op
                for obj in objs:
                    if len(op_class.params)==0:
                        op=op_class(obj)
                        ret.append("%s"%(op.action(**{}) or ""))
                        msg=u"%s(%s) %s"%(op.verbose_name, "", ret or "")
                        LogEntry.objects.log_action_other(request.user.pk,  obj , msg)
            except Exception, e:
                  ret.append(u"%s"%e)
            if not "".join(ret):
                return HttpResponse('{ Info:"OK" }')
            else:
                return HttpResponse('<ul class="errorlist"><li>%s </li></ul>'%("".join(ret)))
        else:
            try:
                ret=model.model_do_action(op_name, request, form_field=form_field)  #-----------------关键点
                if not ret: return HttpResponse('{ Info:"OK" }')    # 操作处理结束 返回结果到前端
                if isinstance(ret, HttpResponse): return ret
                if isinstance(ret, forms.Form):
                    f=ret
                else:
                    return HttpResponse(u"{ errorCode:-1,\nerrorInfo:\"%s\" }"%ret)
            except Exception, e:
                return HttpResponse(u"{ errorCode:-1,\nerrorInfo:\"%s\" }"%e)
    elif request.method=="GET":
        if op.for_model:
            f=op(model)
        else:
            key=request.GET.get('K',None)
            if key is None:
                f=op(model())
            else:
                f=op(model.objects.get(pk=key))
        f=f.form(form_field, lock=request.GET.get('_lock', False), init_data=dict(request.GET)) #----------调用form成员方法得到用于返回的form对象
    ########################## 操作页视图处理 ######################
    tmp_file=request.GET.get('_t',"%s_opform_%s.html"%(model.__name__,op.__name__))
    #---form对象的 admin_help_text 及 verbose_name 成员的处理
    if hasattr(op, "help_text"):
        f.admin_help_text = op.help_text
    if hasattr(op, "verbose_name"):
        f.verbose_name = op.verbose_name
    #---form对象 tips_text 成员的处理
    if not issubclass(op, Operation):#ModelOperation(Operation是继承ModelOperation的)
        if hasattr(op, "tips_text"):#仅对ModelOperation
            f.tips_text = op.tips_text
    ########################## 构造返回的变量字典 ######################
    print '################# form ##############'
    print f
    print '####################################'
    kargs={ 
            'form':f, 
            'op':op, 
            'dataOpt':model._meta, 
            'title':(u"%s"%model._meta.verbose_name).capitalize(),
            'app_label':app_label,
            'model_name':model.__name__, 
            'is_worktable':is_worktable,
            'detail': op_name,
    }
    kargs["app_menu"]=hasattr(model.Admin,"app_menu") and model.Admin.app_menu or  model._meta.app_label
    kargs["position"] = hasattr(model.Admin, "position") and model.Admin.position or None
    #--- 返回模板视图
    return render_to_response([tmp_file, 'data_opform.html'],
            RequestContext(request, kargs))        

def get_form(request,app_label, model_name, op_name):
    '''
    操作通用视图  视图 1    
    包括:删除,确认视图,操作页视图,操作提交      
    django内置api
    '''
    try:
            return get_form_(request, app_label, model_name, op_name)
    except:
            import traceback; traceback.print_exc()

    
