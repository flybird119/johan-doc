#coding=utf-8
'''
数据对象处理帮助函数集
'''
from django.utils.encoding import smart_str
import operator
from filterspecs import FilterSpec
from django.shortcuts import render_to_response
from django.utils.translation import ugettext as _
from django.utils import translation
from django.template import loader, Context, RequestContext
from django.conf import settings
from modelutils import *
from utils import *
from export import openExportFmt
from django.db.models.fields import FieldDoesNotExist
from django.db import models
from django.db.models import Q
from base.model_utils import GetModel
import sys
ALL_VAR = 'all'
ORDER_VAR = 'o'
ORDER_TYPE_VAR = 'ot'
PAGE_VAR = 'p'
ACTION_VAR = 'action'   # form 的 action 参数
SEARCH_VAR = 'q'
IS_POPUP_VAR = 'pop'
ERROR_FLAG = 'e'
STATE_VAR = 's'
EXPORT_VAR = 'f'
PAGE_LIMIT_VAR = 'l'
TMP_VAR = 't'
STAMP_VAR='stamp'
MAX_NO_PAGE='mnp'
IGNORE_PERM ='np'

def createNewOrdUrl(ordUrl, fieldName, remove):
        ordFields=(ordUrl or "").split(',')
        if "" in ordFields: ordFields.remove("")
        desc=False
        sorted=False
        if fieldName in ordFields:
                sorted=True
                if remove:
                        ordFields.remove(fieldName)
                else:
                        index=ordFields.index(fieldName)
                        ordFields[index]="-"+fieldName
        elif ("-"+fieldName) in ordFields:
                desc=True
                sorted=True
                if remove:
                        ordFields.remove("-"+fieldName)
                else:
                        index=ordFields.index("-"+fieldName)
                        ordFields[index]=fieldName
        elif not remove:
                desc=True
                ordFields.append(fieldName)
        else:
                return ""
        return ",".join(ordFields), sorted, desc

class FieldNameMulti(object): #支持多字段排序
        def __init__(self, cl, orderUrl=True):
                self.cl=cl
                self.desc=1
                self.orderUrl=orderUrl

        def __getitem__(self, fieldName):
                for f in self.cl.model._meta.fields:
                        if f.name==fieldName:
                                orderStr, sorted, desc=createNewOrdUrl(self.cl.orderStr, fieldName, False)
                                orderStr=self.cl.get_query_string({ORDER_VAR:orderStr},[ORDER_VAR]).replace("'","\\'").replace('"','\\"')
                                if self.orderUrl:
                                        if sorted:
                                                if desc:
                                                        ret="<th class='sorted descending'>%s<div class='order_hd'><a href='"+orderStr+"'>^</a>"
                                                else:
                                                        ret="<th class='sorted ascending'>%s<div class='order_hd'><a href='"+orderStr+"'>v</a>"
                                                removeOrderStr, sorted, desc=createNewOrdUrl(self.cl.orderStr, fieldName, True)
#                                                print "ORDER_: ", removeOrderStr
                                                if removeOrderStr:
                                                        removeOrderStr=self.cl.get_query_string({ORDER_VAR:removeOrderStr},[ORDER_VAR]).replace("'","\\'").replace('"','\\"')
                                                else:
                                                        removeOrderStr=self.cl.get_query_string({},[ORDER_VAR])
                                                ret+="<a href='"+removeOrderStr+"'>X</a></div></th>"
                                        else:
                                                ret="<th>%s<div class='order_hd'><a href='"+orderStr+"'>^</a></div></th>"
                                        ret=ret%((u"%s"%f.verbose_name).capitalize())
                                else:
                                        ret="<th abbr='"+fieldName+"'>%s</th>"%(u"%s"%f.verbose_name).capitalize()
                                return ret
                return ""

def get_field_verbosename(model, fieldName, spliter="__"):
    try:
        try:
            
            f=model._meta.get_field(fieldName)
            return (u"%s"%f.verbose_name).capitalize()
        except FieldDoesNotExist:
            fs=fieldName.split(spliter,1)
            for f1 in fs[:-1]:
                f=model._meta.get_field(f1)
                model=f.rel.to
                #vname=(u"%s"%f.verbose_name).capitalize()+"."+(u"%s"%f.rel.to._meta.get_field(f2).verbose_name).capitalize()
            
            return (u"%s"%model._meta.get_field(fs[-1]).verbose_name).capitalize()

    except:
        return _(fieldName)

class FieldName(object):
        def __init__(self, cl, model, master_field=None, orderUrl=True):
                self.cl=cl
                self.desc=1
                self.orderUrl=orderUrl
                self.master_field=master_field
                self.model=model
                if cl.orderStr:
                        if cl.orderStr[0:1]=="-":
                                self.desc=0
                                self.orderField=cl.orderStr[1:]
                        else:
                                self.orderField=cl.orderStr
                else:
                        self.orderField=""
        def getFieldHeader(self, fieldName):
                try:
                        if self.master_field: fieldName=reverse_from_master_field(self.model, self.master_field, fieldName)
                        vname=get_field_verbosename(self.cl.model, fieldName)
                except:
                        vname=_(fieldName)
                orderStr=fieldName
                if self.orderUrl:
                        if fieldName==self.orderField:
                                if self.desc:
                                        orderStr="-%s"%fieldName
                                        ret="<th class='sorted descending'><a href='%s'>%s</a></th>"
                                else:
                                        ret="<th class='sorted ascending'><a href='%s'>%s</a></th>"
                        else:
                                ret="<th><a href='%s'>%s</a></th>"
                        orderStr=self.cl.get_query_string({ORDER_VAR:orderStr},[ORDER_VAR])
                        orderStr=string.join(orderStr.split('"'),'\\"')
                        orderStr=string.join(orderStr.split("'"),"\\'")
                        ret=ret%(orderStr, vname)
                else:
                        #ret="<th abbr='"+fieldName+"'>%s</th>"%vname
                        ret="%s"%vname
                return ret
        def __getitem__(self, fieldName):
                try:
                        return self.getFieldHeader(fieldName)
                except Exception, e:
                        #errorLog()
                        return ""

def xlist2str(list1 = []):
        str1 = ""
        if list1:
                for li in list1:
                        str1 += li + ","
        if str1:
                str1 = str1[:-1]
        return str1

def getVerboseName(model, name):
        for field in model._meta.fields:
                if field.name == name:
                        return u"%s"%field.verbose_name
        return ""
                           
class ChangeList(object):
        def __init__(self, request, model, master_field=None):
                self.model = model

                self.opts = model._meta
                self.params = dict(request.GET.items())
                
                self.filter_specs, self.has_filters = get_filters(self.opts, request, self.params, model)
                self.request=request
                self.orderStr=""
                self.lng=request.LANGUAGE_CODE
                if ORDER_VAR in self.params:
                        self.orderStr=self.params[smart_str(ORDER_VAR)]
                elif model._meta.ordering:
                        self.orderStr=','.join(model._meta.ordering)
                        #print "default order: ", model._meta.ordering
                elif model._meta.pk.name=="id":
                        self.orderStr="-id"

                self.FieldName=FieldName(self, model, master_field, request.REQUEST.get(ORDER_TYPE_VAR, '0')=='1')
                self.master_field=master_field
                searchHint=[]
                search_fields=()
                try:
                        search_fields=self.model.Admin.search_fields
                except: pass
                if search_fields:
                        for fn in search_fields:
                                f=self.opts.get_field(fn)
                                searchHint.append((u"%s"%f.verbose_name).capitalize())
                if len(searchHint)>0:
                        self.searchHint=string.join(searchHint, ",")
                else:
                        self.searchHint=None

        def get_query_string(self, new_params=None, remove=None):
                if new_params is None: new_params = {}
                if remove is None: remove = []
                p = {} #self.params.copy()
                for r in remove:
                        for k in p.keys():
                                if k.startswith(r):
                                        del p[k]
                for k, v in new_params.items():
                        if k in p and v is None:
                                del p[k]
                        elif v is not None:
                                p[k] = v
                return '?' + '&amp;'.join([u'%s=%s' % (k, v) for k, v in p.items()]).replace(' ', '%20')

        def getDataExportsFormats(self):
                fl=[]
                formats=openExportFmt(self.request)
                index=0
                for f in formats:
                        fds =(f+"_").split("_",1)
                        index+=1
                        if fds[0]==self.model.__name__ and fds[1]:
                                fds=(fds[1]+":").split(":")
                                if fds[0] and fds[1]:
                                        fl.append((index, unicode(fds[0].split('.')[0].decode("utf-8")),))
                return fl

def construct_search(field_name):
                if field_name.startswith('^'):
                        return "%s__istartswith" % field_name[1:]
                elif field_name.startswith('='):
                        return "%s__iexact" % field_name[1:]
                elif field_name.startswith('@'):
                        return "%s__search" % field_name[1:]
                else:
                        return "%s__icontains" % field_name

def get_filters(opts, request, params, dataModel):
        filter_specs = []
        try:
                if dataModel.Admin.list_filter:
                        filter_fields = [opts.get_field(field_name) \
                                for field_name in dataModel.Admin.list_filter]
                        for f in filter_fields:
                                spec = FilterSpec.create(f, request, params, dataModel)
                                if spec and spec.has_output():
                                        filter_specs.append(spec)
        except Exception, e:
                #print "get_filters", e.message
                pass
        return filter_specs, bool(filter_specs)

def get_model_master(dataModel):
        '''
        根据Admin _meta 得到一个模型的主键
        '''
        master=None
        try:
                master_field=dataModel.Admin.master_field
                master_field=dataModel._meta.get_field(master_field)
                if isinstance(master_field, models.ForeignKey):
                        master=master_field
        except:
                pass
        return master

def reverse_from_master_field(model, master_field, field_name):
        master_model=master_field.rel.to
        master_var=master_field.related.var_name
        name=master_field.name
        if field_name.find(master_var+"__")==0: return field_name[len(master_var)+2:]
        try:
                return "%s__%s"%(name, master_model._meta.get_field(field_name).name)
        except:
                return field_name

def change_to_master_field(model, master_field, field_name):
        master_model=master_field.rel.to
        master_var=master_field.related.var_name
        name=master_field.name
        if field_name.find(name+".")==0: return field_name[len(name)+1:]
        try:
                return "%s.%s"%(master_var, model._meta.get_field(field_name).name)
        except:
                return field_name

def filterdata_by_user(query_set,user):
    model = query_set.model
    lname = "limit_%s_to" % model.__name__.lower()
    if hasattr(model, lname):#特殊的地方就直接用自定义的方法（定义的模型中），否则走通用的
        return getattr(model(), lname)(query_set, user)
    from mysite.iclock.iutils import userDeptList, userAreaList
    
    Department=GetModel("personnel", "Department")
    Area=GetModel("personnel", "Area")
    Device=GetModel("iclock", "Device")
    
    if  model==Area: #区域表直接过滤
        areaids = userAreaList(user)
        if not areaids:
            return query_set
        areaids = [ area.pk for area in areaids ]
        return query_set.filter(pk__in=areaids)
    if  model==Device:  #如果设备表就直接根据区域控制行权限
        areaids = userAreaList(user)
        if not areaids:
            return query_set
        areaids = [ area.pk for area in areaids ]
        q = {"area__in":areaids}
        return query_set.filter(Q(**q))

    q={}
    #以设备为外键的模型按照区域过滤（通用）
    for f in model._meta.fields:
        if isinstance(f,models.fields.related.ForeignKey):
            if f.rel.to.__name__=="Device": 
                areaids = userAreaList(user)
                if areaids:
                    q = {f.name +"__area__in":areaids}
                    return query_set.filter(Q(**q))
                else:
                    return query_set

    deptids = userDeptList(user)    # 获取授权的部门
    
    if not deptids:
        return query_set
    deptids = [ int(dept.pk) for dept in deptids ]
    if model ==Department: #部门表直接过滤
        return query_set.filter(pk__in=deptids)
    for f in model._meta.fields:    # 遍历每一个字段
        if isinstance(f,models.fields.related.ForeignKey):
            if f.rel.to.__name__=="Department": #以部门为外键的部门过滤
                q = {f.name +"__in":deptids}
                return query_set.filter(Q(**q))
            elif f.rel.to.__name__=="Employee":
                q = {f.name+"__DeptID__in":deptids}#以部门为外键的人员过滤（如Employee中通过DeptID过滤）
                q = {f.name+"__DeptID__in":deptids}
                query_set.exclude()
                return query_set.filter(Q(**q))
#            return query_set.filter(Q(**q))
    return query_set


def QueryData(request, dataModel, master_field=None, qs=None):
        opts = dataModel._meta
        params = dict(request.REQUEST.items())  # request 参数字典
        
        ######################### 根据请求参数查询得到模型或者模型主键表的记录 ########################
        if qs is None:
            if master_field:
                qs=master_field.rel.to.objects.all()
            else:
                qs=dataModel.objects.all()
        search=request.REQUEST.get(SEARCH_VAR,"")   # 查询参数
        search=unquote(search);
        if request.REQUEST.has_key(SEARCH_VAR): # 是否有obj['q']
                search_fields=()
                try: 
                        search_fields=dataModel.Admin.search_fields
                except: pass
                if search_fields:
                        for bit in search.split():  # 循环每个查询参数
                                or_queries = [models.Q(**{construct_search(field_name): bit}) for field_name in search_fields]  # 查询结果
                                other_qs = dataModel.objects.all()
                                try:
                                        other_qs.dup_select_related(qs)
                                except:                        
                                        if qs._select_related:
                                                other_qs = other_qs.select_related()
                                other_qs = other_qs.filter(reduce(operator.or_, or_queries))
                                qs = qs & other_qs

        # 去除request请求的一些特定参数
        lookup_params = params.copy() # a dictionary of the query string
        for i in (ALL_VAR, ORDER_VAR,STAMP_VAR,ORDER_TYPE_VAR, SEARCH_VAR, IS_POPUP_VAR, PAGE_VAR, STATE_VAR, EXPORT_VAR,PAGE_LIMIT_VAR,TMP_VAR, ACTION_VAR,MAX_NO_PAGE):
                if i in lookup_params:
                        del lookup_params[i]

        #用来获取当前模型所有相关的字段（包括外键和多对多字段）
        from django.db.models.fields.related import ManyRelatedObjectsDescriptor as mrod, ReverseManyRelatedObjectsDescriptor as rmrod, ForeignRelatedObjectsDescriptor as frod
        model_fields=[f.name for  f in dataModel._meta.fields]
        for p,v in dataModel.__dict__.items() : # 遍历模型 __dict__ 键值项
            if isinstance(v,mrod) or isinstance(v,frod) or isinstance(v,rmrod):
#                print 'ManyRelatedObjectsDescriptor、ReverseManyRelatedObjectsDescriptor、ForeignRelatedObjectsDescriptor-------------------------------:',v
                if str(p).endswith("_set"):
#                    print 'p (key) -------------------------------:',str(p)
                    model_fields.append(str(p[:len(p)-4]))
#                    print 'str(p[:len(p)-4] -------------------------------:',str(p[:len(p)-4])
                else:
                    model_fields.append(p) 

        for k,v in lookup_params.items():#循环去掉不在当前模型中的字段(带":"的跳过)
            if k.__contains__(":"):#通过从表字段查询主表（当前表）-add by darcy 20100708
                kl = k.split(":")[1]
                lookup_params[kl] = v
                del lookup_params[k]
            else:#通过主表查询当前表（从表）
                if k.find("__")>0:
                    ky=k.split("__")[0]
                else:
                    ky=k                 
                if ky not in model_fields:
                    del lookup_params[k]
                    
        for key, value in lookup_params.items():
                if not isinstance(key, str):
                        del lookup_params[key]
                        k=smart_str(key)
                        lookup_params[k] = value
                else:
                        k=key
                if (k.find("__in")>0) or (k.find("__exact")>0 and value.find(',')>0):
                        del lookup_params[key]
                        lookup_params[k.replace("__exact","__in")]=value.split(",")
                if(k.find("__range")>0):
                    x=eval(value)
                    lookup_params[k] = x
        # Apply lookup parameters from the query string.
        if lookup_params:
            qs = qs.filter(**lookup_params).distinct()
        ######################## 排序 ###########################
        cl=ChangeList(request, dataModel, master_field)
        if cl.orderStr:
                ot=cl.orderStr.split(",")
                qs=qs.order_by(*ot)
                #print "cl.orderStr", cl.orderStr
        else:
            qs=qs.order_by("-pk")
            
        qs =filterdata_by_user(qs,request.user) # 最后进行用户级过滤                       
        return qs, cl

def NoPermissionResponse(title=''):
        return render_to_response("info.html", {"title": title, "content": _(u"你没有该权限!")});        

def hasPerm(user, model, operation):
        '''
        判断用户 user 是否对 model 有 operation 权限
        '''
        modelName=model.__name__.lower()
        perm='%s.%s_%s'%(model._meta.app_label, operation,modelName)
        return user.has_perm(perm)

def NoFound404Response(request):
        '''
        公共NoFound 页面视图
        '''
        return render_to_response("404.html",{"url":request.path},RequestContext(request, {}),);

#app_label.codename
def exist_perm(app_codename):
    from django.contrib.auth.models import Permission
    from django.contrib.contenttypes.models import ContentType
    app_label,codename=app_codename.split(".")
    perms=Permission.objects.filter(codename=codename)
    for elem in perms:
        if elem.content_type.app_label==app_label:
            return True
    return False
    