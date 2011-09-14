#coding=utf-8
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
import django.dispatch
from admin_detail_view import retUserForm,adminForm,doPostAdmin,doCreateAdmin
import widgets
from enquiry import Enquiry
from base.operation import OperationBase, Operation, ModelOperation
from base.cached_model import STATUS_INVALID
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from traceback import print_exc

from django.utils.datastructures import SortedDict
import widgets
from django.db import models

PAGE_LIMIT_VAR = 'l'
TMP_VAR = 't'
def strToDateDef(s, defTime=None):
        import time
        d=datetime.datetime.now()
        try:
                t=time.strptime(s, settings.STD_DATETIME_FORMAT)
                d=datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday,
                        t.tm_hour, t.tm_min, t.tm_sec)
        except:
                try:#鍙�湁鏃ユ湡
                        t=time.strptime(s, settings.STD_DATETIME_FORMAT.split(" ")[0])
                        if defTime:
                                d=datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday, defTime[0], defTime[1], defTime[2])
                        else:
                                d=datetime.datetime(t.tm_year, t.tm_mon, t.tm_mday)
                except Exception: #鍙�湁鏃堕棿
#                        print e.message
                        t=time.strptime(s, settings.STD_DATETIME_FORMAT.split(" ")[1])                
                        d=datetime.datetime(d.year, d.month, d.day,
                                t.tm_hour, t.tm_min, t.tm_sec)
        return d

from signals import on_model_operation,on_object_operation

def doAction(action, request, dataModel):
        action=string.strip(action)
        params={}
        ##################### 除了delete 其他的 动作都必须在 get_all_operations 里 ############################
        if action!="delete":
                if not hasattr(dataModel,"get_all_operations"): # 是否定义了 operations
                        return getJSResponse(u"{ errorCode:-1,\nerrorInfo:\"%s\" }"%(action+" have not define 1"))
                if action not in dataModel.get_all_operations():
                        return getJSResponse(u"{ errorCode:-1,\nerrorInfo:\"%s\" }"%(action+" have not define"))
        ##################### 获取选择的对象列表 ############################
        keys=[]
        if str(request.REQUEST.get("is_select_all","")) == "1": # 参数 is_select_all 为 1 时
                keys=[e.pk for e in dataModel.objects.all()]
        else:
                keys=request.REQUEST.getlist("K")
        ##################### 执行动作 ############################
        info=[]
        ret=None
        op=getattr(dataModel, action)   # 得到动作处理方法
        if issubclass(op, Operation):   # 对象操作
                on_object_operation.send(sender=op, request=request, dataModel=dataModel, objects=keys) # 将动作处理方法绑定到特定信号上
                for i in keys:  # 执行每个选择对象的动作处理
                        aObject=dataModel.objects.get(pk=i)
                        try:
                                ret=aObject.do_action(op(aObject), request) 
                        except Exception, e:
                                print_exc()
                                return getJSResponse(u"{ errorCode:-1,\nerrorInfo:\"%s failed: %s\" }"%(action, e))
                        if ("%s"%ret)==ret:
                                info.append(ret)
        elif issubclass(op, ModelOperation):    # 模型操作
                        try:
                                on_model_operation.send(sender=op, request=request, dataModel=dataModel)    # 绑定信号
                                ret=dataModel.do_model_action(op(dataModel), request)   # 执行动作
                        except Exception, e:
                                print_exc()
                                return getJSResponse(u"{ errorCode:-1,\nerrorInfo:\"%s failed: %s\" }"%(action, e))
                        if ("%s"%ret)==ret:
                                info.append(ret)
                
        errorInfo=""
        if len(info)>0:
                errorInfo= u',\n'.join([u"%s"%f for f in info])
        if errorInfo:
                return getJSResponse(u"{ errorCode:-1,\nerrorInfo:\"%s\" }"%errorInfo)
        return None

from signals import  on_list_paginator

def model_data_list(request, dataModel, qs=None, model_url=None):
    '''
    通用列表视图
    '''
#    if qs:
#        print 'qs-----------------------------------:',qs
    from urls import dbapp_url, surl
    from dbapp.data_utils import exist_perm
    from data_edit import form_for_model
    from dbapp.viewmodels import get_all_view         
    lng=get_language()  # 获取语言
    
    action=request.REQUEST.get(ACTION_VAR, "")  # 获取动作类型
    if len(action)>0:
            checkAction=action
            if not hasPerm(request.user, dataModel, checkAction):   # 动作权限的判断
                    return getJSResponse(u"{ errorCode:-2,errorInfo:\"%s\"}"%_(u"你没有该权限!")) # 返回 js 内容
            resp=doAction(action, request, dataModel)
            if resp: return resp
    ##################### 判断是否有 default_give_perms 权限  ############################
    if not hasPerm(request.user, dataModel, "browse"): # 没有 browse 权限 模型是否有default_give_perms项            
            if  hasattr(dataModel.Admin,"default_give_perms") and  dataModel.Admin.default_give_perms:
                flag=False
                for perm in  dataModel.Admin.default_give_perms:
                    if request.user.has_perm(perm):
                        flag=True
                        break
                if not flag:
                    if request.is_ajax():
                        return HttpResponse("session_fail_or_no_permission")
                    else:
                        return render_to_response('no_permission_info.html',RequestContext(request,{'dbapp_url': dbapp_url}))
            else:
                if request.is_ajax():
                    return HttpResponse("session_fail_or_no_permission")
                else:
                    return render_to_response('no_permission_info.html',RequestContext(request,{'dbapp_url': dbapp_url}))
    
    master=get_model_master(dataModel)
    request.model=dataModel
    request.dbapp_url=dbapp_url #已经加到中间件中了 /data/
    
    # 取缓存
    cache_key="%s_%s_cc"%(lng,dataModel.__name__)   # zh-cn_model_1_cc
    cache_cc=cache.get(cache_key)
    if not cache_cc:
        searchform=""
        if hasattr(dataModel.Admin,"query_fields") and dataModel.Admin.query_fields:        
                searchform=seachform_for_model(request,dataModel,fields=list(dataModel.Admin.query_fields)) # 查询表单html内容  
        cache_cc={
            'title': (u"%s"%dataModel._meta.verbose_name).capitalize(),
            'app_label':dataModel._meta.app_label,
            'model_name':dataModel.__name__,
            'dbapp_url': dbapp_url,
            'model_url': model_url or request.dbapp_url+dataModel._meta.app_label+"/"+dataModel.__name__+"/",
            'searchform':searchform,
            'import_perm':dataModel._meta.app_label+".dataimport_"+dataModel.__name__.lower(),  # 导入标识名
            'export_perm':dataModel._meta.app_label+".dataexport_"+dataModel.__name__.lower(),  # 导出标识名
            'menu_focus':hasattr(dataModel.Admin, "menu_focus") and dataModel.Admin.menu_focus or dataModel.__name__, #用于跟模型相关的菜单获取焦点
            'position':hasattr(dataModel.Admin, "position") and dataModel.Admin.position or None,
        }
        cache.set(cache_key,cache_cc,60*60*24*7)    # 参数字典 加入缓存

    ####################### 得到分页和排序参数字典 这些参数不缓存 #####################
    qs, cl=QueryData(request, dataModel, master, qs)    # 模型数据查询
    try:
            offset = int(request.REQUEST.get(PAGE_VAR, 1))
    except:
            offset=1
    limit= int(request.REQUEST.get(PAGE_LIMIT_VAR, settings.PAGE_LIMIT))
    
    try:
        mnp=int(request.REQUEST.get(MAX_NO_PAGE, 50))
        if qs.count()<=mnp:
            limit=mnp
    except:
        limit=50

    cc={
            'from': (offset-1)*limit+1,
            'page': offset,
            'limit': limit,
            'cl': cl,
            }
    cc.update(cache_cc) # 合并前面的参数字典
    
    isProcessed=False
    for ret in on_list_paginator.send(sender=cc, request=request, dataModel=dataModel, querySet=qs):
            if ret[1]:
                    isProcessed=True
                    break
    if not isProcessed:
            paginator = Paginator(qs, limit)    # django 的分页对象
            item_count = paginator.count
            if offset>paginator.num_pages: 
                offset=paginator.num_pages
                cc['page']=offset
            if offset<1: offset=1
            pgList = paginator.page(offset)
            cc['latest_item_list']=pgList.object_list   # 分页结果数据
            cc['page_count']=paginator.num_pages
            cc['item_count']=item_count
            
            list_exception_fields=request.REQUEST.getlist("exception_fields")
            list_addition_fields=request.REQUEST.getlist("addition_fields")
            
            if master:
                master2str=master.name
            else:
                master2str=""                
            cache_key=lng+"_"+dataModel.__name__+"_".join(list_exception_fields+list_addition_fields)+master2str
            t=cache.get(cache_key)  # 缓存 DefaultJsonDataTemplate
            if not t:
                t=getDefaultJsonDataTemplate(dataModel,list_exception_fields,list_addition_fields,master)
                cache.set(cache_key,t,60*60*24*7)
            
            var_options=u"""record_count:{{ item_count }},
                                        item_from:{{ from }},
                                        current_page:{{ page }},
                                        page_limit:{{ limit }},
                                        page_count:{{ page_count }},
                                        order_by:"{{ order_by }}",
                                        'options':%s,
                                        'actions':%s
                        """%getUsrCreateFrameOptions(dataModel,request) # 得到Options集合信息
                        
            t="{ \n "+t+var_options+" \n }"
            t_r=Template(t).render(RequestContext(request, cc)) #---------------------------------一部分内容
    if request.method=='POST':  # 如果是ajax请求------------------------------------------------------------------------------------------如“日志记录”
            return getJSResponse(smart_str(t_r))

    from urls import get_model_data_url
    from base import get_all_app_and_models
    import base
    if issubclass(dataModel, base.models.CachingModel) and dataModel.Admin.log:
            try:
                    ct=ContentType.objects.get_for_model(dataModel)
                    cc['log_url']=get_model_data_url(base.models.LogEntry)+("?content_type__id=%s"%ct.pk)
                    cc['log_search']="content_type__id=%s"%ct.pk
            except: 
                    print_exc()
    apps=get_all_app_and_models()
    cc["apps"]=apps
    admin=hasattr(dataModel, "Admin") and dataModel.Admin or None
    current_app=hasattr(admin, "app_menu") and admin.app_menu or dataModel._meta.app_label
    cc["current_app"]=current_app
    try:
        cc["myapp"]=[a for a in apps if a[0]==current_app][0][1]    # 所在app的所有信息
    except:
        pass
    
    cache_key="%s_%s_template"%(lng,dataModel.__name__)
    tmp_file=cache.get(cache_key)
    if not tmp_file:
        tmp_file=loader.select_template([
                dataModel._meta.app_label+"."+dataModel.__name__+".html", 
                dataModel.__name__+"_list.html", 
                "data_list_"+dataModel._meta.app_label+".html",
                "data_list.html"])
        #cache.set(cache_key,tmp_file,60*60*24*7)
    
    cc["query"]="&".join([k+"="+v[0] for k,v in dict(request.GET).items()]) # 查询参数
    cc['datalist']=smart_str(t_r)   # 主要数据
    return HttpResponse(tmp_file.render(RequestContext(request, cc)))


@login_required
def DataList(request, app_label, model_name):
    '''
    通用列表视图入口
    '''
    from base.model_utils import get_AppOperation
    AppOperation = get_AppOperation(app_label,model_name)
    if AppOperation:
        try: 
            return AppOperation.view.im_func(request)
        except:
            pass
    dataModel=GetModel(app_label, model_name)   # 模型存在的判断
    if not dataModel: return NoFound404Response(request)
    try:
        return model_data_list(request, dataModel)
    except:
        print_exc()
        raise

def timeStamp(t):
        dif=t-datetime.datetime(2007,1,1)
        return "%06X%06X"%(dif.days,dif.seconds)

def stampToTime(stamp):
        dif=datetime.timedelta(string.atoi(stamp[0:3],16),string.atoi(stamp[3:],16))
        return datetime.datetime(2007,1,1)+dif

@login_required
def index(request, current_app="att", init_model=[], dataModel=None):
        '''
        app  通用默认 index 视图
        '''
        from base import get_all_app_and_models
        from urls import dbapp_url, surl
        from base.models import options
        request.dbapp_url=dbapp_url
        apps=get_all_app_and_models()   # -----------第一次执行
        if current_app=='worktable':    #-------------------------------------------------- worktable  视图的特殊处理
                from django.conf import settings
                installed_language=settings.APP_CONFIG.language.language                
                return render_to_response("worktable.html",{},RequestContext(request, {
                    "apps":apps,
                    "current_app":current_app, 
                    'app_name': dataModel and (hasattr(dataModel.Admin, "app_menu") and dataModel.Admin.app_menu or dataModel._meta.app_label) or "",
                    "init_model": init_model or "",
                    "dbapp_url": dbapp_url,
                    "installed_language":installed_language}))
        else:
                opt=current_app+"."+current_app+"_default_page"
                model_name=options[opt]
                if model_name:
                    redirect_url="/"+surl+model_name
                    url_list=redirect_url.split("/")
                    if request.user.has_perm("%s.browse_%s"%(url_list[-3],url_list[-2].lower())):
                        return HttpResponseRedirect(redirect_url)
                    elif request.user.has_perm("contenttypes.can_%s"%(url_list[-2])):
                        return HttpResponseRedirect(redirect_url)

                default_model=[m for m in dict(apps)[current_app]["models"] if (not m.has_key("parent_model"))]
                if len(default_model)!=0:
                    url=""
                    if default_model[0]["model"]:
                        if request.user.has_perm("%s.browse_%s"%(default_model[0]["model"]._meta.app_label,default_model[0]["model"].__name__.lower())):
                            url=dbapp_url+default_model[0]["model"]._meta.app_label+"/"+default_model[0]["name"]+"/"
                            return HttpResponseRedirect(url)
                        else:
                            return render_to_response('no_permission_info.html',RequestContext(request,{}))
                    else:
                        if request.user.has_perm("contenttypes.can_%s"%default_model[0]["operation"].__name__):
                            url="/"+surl+default_model[0]["url"][1:]#reverse函数返回的url是从根目录开始的,带了"/"
                            return HttpResponseRedirect(url)
                        else:
                            return render_to_response('no_permission_info.html',RequestContext(request,{}))
                else:
                    return render_to_response('no_permission_info.html',RequestContext(request,{}))

@login_required
def mydesktop(request):
        from urls import dbapp_url, surl
        from base.models import options
        request.dbapp_url=dbapp_url
        try:
            if options["base.site_default_page"]:
                return HttpResponseRedirect("/"+surl+options["base.site_default_page"])
        except:
            import traceback;print_exc();

@login_required
def myapp(request,app_label):
        '''
        app 通用默认视图  登录后的第一个视图app_label=worktable
        '''
        from urls import dbapp_url
        request.dbapp_url=dbapp_url
        return index(request,current_app=app_label)

@login_required    
def set_option(request):
    from base.models import options
    try:
        query_str=request.REQUEST.get("q",None)
        if query_str:
            name,value=query_str.split("___",1)
            options[name]=value
            return  getJSResponse('{ Info:"OK" }')
    except Exception,e:
        return  getJSResponse('{ Info:"fail" }')
    
def enquiryResult(request, model_name):
    '''
    没有被调用
    '''
    enq=Enquiry(str(model_name))
    cpcd={
              ">":"__gt",
              ">=":"__gte",
              "<":"__lt",
              "<=":"__lte",
              "=":"__exact",
              "contains":"__contains",
              "in":"__in",
              "isnull":"__isnull",                            
        }
    where={}
    if request.method=="POST":
        if request.POST.has_key("lstWhere"):
            tstr=request.POST.get("lstWhere")
         
        if request.POST.has_key("lstWhere"):
            tstr=request.POST.get("lstWhere")
            tmp=tstr.split("\n")           
            
            for x in tmp[0:len(tmp)-1]:
                val=x.split()
                lk=val[0].encode("ascii")
                rk=val[1].encode("ascii")
                if len(val)>2:
                    va=val[2].encode("ascii")
                else:
                    va=""
                if va.find(",")>0:
                    va=va.split(",")
                if rk=="isnull":
                    va=True
                    
                where[lk+cpcd[rk]]=va               
        table=str(model_name)
        n=enq.Search(table,**where)       
      
        c = Context({
        'values': n
        })
        if len(n)>0:
            return HttpResponse("sucess")
        else:
            return HttpResponse("fail")
    else:
        return HttpResponse("fail")

def seachform_for_model(request,model,fields=[]):
    '''
    查询区域表单视图
    '''
    from django.forms import forms,widgets as wg
    
    from django.db import models
    form=forms.Form() 
    for f in fields:
        if f.find('__')>0 or f.find('.')>0:
            f=f.replace(".","__")
            s,p=f.split("__")
            if s.__contains__(":") > 0:#通过子表查询主表(如输入门名称查询设备)--add by darcy 20100708
                children_models = dict((r.model.__name__.lower(), r.model) for r in model._meta.get_all_related_objects())
                #print '----children_models=',children_models
                try:
                    #print '--searchform for model-s=',s
                    pf = children_models[s.split(":")[1]]._meta.get_field(p)
                except:
                    import traceback;print_exc()
            else:
                pf=model._meta.get_field(s).rel.to._meta.get_field(p)
            if not pf.editable:
                continue
            fd=pf.formfield()
        else:           
            mf=model._meta.get_field(f)
            if not mf.editable:
                continue
            if isinstance(mf,models.ForeignKey) or isinstance(mf,models.ManyToManyField):                
                fd=mf.formfield(widget=wg.TextInput)
            else:
                widget=None                               
                #print "mf.class :%s"% mf.__class__
                if mf.__class__ in widgets.WIDGET_FOR_DBFIELD_DEFAULTS:
                    widget=widgets.WIDGET_FOR_DBFIELD_DEFAULTS[mf.__class__]
                if widget:
                    fd=mf.formfield(widget=widget)
                else:
                    fd=mf.formfield()
        form.fields[f]=fd
        #print form.as_table()
    search_html=Template("""
        <table width="100%" class="tbl_form_search" id="id_form_search">
           {% autoescape off %}
           {% for field in searchform %}
               {% if forloop.first %}<tr class="header_div_left"> {% endif%}
                    <td align="right">{{ field|field_as_label_tag_no_asterisk }}</td> <td>{{ field.as_widget }}</td>
               {% if forloop.counter|divisibleby:"3" %}
                   </tr>
                   <tr class="header_div_left">
               {% endif %}
               {% if forloop.last %}  </tr> {% endif %}
           {% endfor %}    
           {% endautoescape %}
               </td></tr>    
       </table>
    """).render(RequestContext(request,{"searchform":form}))
    return search_html


def sys_help(request):
    from django.utils.translation.trans_real import get_language_from_request
    installed_apps=settings.INSTALLED_APPS
    redirect_url=request.REQUEST.get("p","")
    d={"apps":installed_apps}
    if redirect_url:
        d["redirect_url"]=redirect_url
    lang_code=get_language_from_request(request)
    return render_to_response("help_default_"+lang_code+".html",RequestContext(request,d))

def has_attribute_value(obj,attr):
    pass
#    if hasattr(dataModel.Admin,"query_fields") and dataModel.Admin.query_fields: