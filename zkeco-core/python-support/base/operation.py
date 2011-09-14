# -*- coding: utf-8 -*-
'''
定义了 ModelOperation 类  [模型操作]
定义了 Operation 类 继承自ModelOperation
'''
import types
from django.utils.translation import ugettext_lazy as _
from django.db import models
from django import forms
from django.db.models.query import QuerySet

class ModelOperation(object):
    u"""
    对数据进行特定操作  以下为几个参数配置项
    """
    params=() 
    verbose_name="" 
    help_text="" 
    visible=True #是否显示
    model=None                                
    for_model=True
    confirm=True
    
    @classmethod
    def permission_code(cls, model_name):
        '''
        类方法：既可以通过类调用也可通过类实例调用
        cls 为当前类
        
        返回权限名称
        '''
        cn="%s_%s"%(cls.__name__.lower(), model_name.lower())
        if cn.find('_')==0: cn=cn[1:]
#        print 'permission_code----------------------:',cn
        return cn
    def __init__(self, model, verbose_name=None):
        self.model=model
        self.operation_name=self.__class__.__name__
        if verbose_name: 
            self.verbose_name=verbose_name
    def action(self):
        '''
        action接口 在此写入实际的数据操作代码
        '''
        pass 
    def has_permission(self, user): 
        '''
        根据当前用户和实际的对象判断是否有权限进行此项操作
        '''
        return True
    def form(self, form_field=None, lock=False, init_data={}, post=None):
        f=forms.Form(post)
        for p in self.params:
            key=p[0]
            if isinstance(p[1], models.Field):
                f.fields[key]=form_field and form_field(p[1], readonly=lock and (key in init_data)) or p[1].formfield()
            else:
                f.fields[key]=p[1]
            if key in init_data:
                value=init_data[key]
                if type(value)==list and not isinstance(p[1], models.ManyToManyField):
                    value=value[0]
                f.fields[key].initial=value
                f.initial[key]=value
        f.title=(self.help_text or self.verbose_name) or "" #表单标题
        return f
    def __unicode__(self):
        return u"%s"%self.verbose_name

class Operation(ModelOperation):
        only_one_object=False   # 是否单对象操作
        for_model=False # 是否作为model
        
        def __init__(self, obj):    # 接受一个model对象参数
                super(Operation, self).__init__(obj.__class__)
                self.object=obj
                self.model=obj.__class__
        def can_action(self):
                '''
                根据实际的对象的状态判断是否可以进行该操作
                '''
                try:
                        return self.object.status==STATUS_OK
                except:
                        return True
############### 最大最小时间
import datetime
MIN_DATETIME=datetime.datetime(1,1,1)
MAX_DATETIME=datetime.datetime(3000,1,1)
NON_FIELD_ERRORS = '__all__'

#def parse_value(request, param_name, op):
#        value=request.REQUEST.get(param_name, None)
#        if value==None: return value
#        try:
#                return op.rel.to.objects.get(pk=request.REQUEST.get(param_name, None))
#        except:
#                return value

def chasPerm(user, model, operation):
    '''
    判断用户是否具有某个权限
    '''
    modelName=model.__name__.lower()
    perm='%s.%s_%s'%(model._meta.app_label, operation,modelName)
    return user.has_perm(perm)

class OperationBase(object):
    @classmethod
    def get_all_operations(self,user):
        '''
        得到用户所有可用的操作operations
        
        ('_add', '_change', '_delete')
        '''
        cc=[]
        for name in dir(self):
            try:
                if type(getattr(self, name))==types.TypeType and issubclass(getattr(self, name), ModelOperation):
                    if not name.startswith("_"):
                        tn= name
                    else:
                        tn = name[1:]    
                    op=getattr(self,name)                
                    if op.visible and chasPerm(user,self,tn.lower()):
                        cc.append(name)
            except:
                pass
#        print 'get_all_operations----------------------------------:',tuple(cc)
        return tuple(cc)
    @classmethod
    def get_operation_js(self, operation):
        '''
        得到某个操作operations 的 json信息
        
        verbose_name:"",         操作名称
        help_text:"",                 提示信息
        params:0,                     前端需传回服务器的        
        for_model:true,            是否是针对模型的操作
        confirm:true,                是否需要确认
        only_one:false              是否为只针对一个对象的操作
        '''
        op=getattr(self, operation)
        js_str =  u"""
        "%s":{
        verbose_name:"%s",
        help_text:"%s",
        params:%s,
        for_model:%s,
        confirm:%s,
        only_one:%s
        }"""%(operation, op.verbose_name and op.verbose_name.capitalize() or _(op.__name__),
            op.help_text and (" ".join(op.help_text.split("\n")).strip()).capitalize(),
            len(op.params), op.for_model and 'true' or 'false',
            op.confirm and 'true' or 'false',
            (op.for_model or not op.only_one_object) and 'false' or 'true')
        return js_str
    @classmethod
    def get_all_operation_js(self, user=None):
        '''
        得到所有操作operations 的 json信息 组成页面数据字典 actions 
        '''
        return "{"+(",\n".join(self.get_operation_js(op) for op in self.get_all_operations(user)))+"\n}"

    @classmethod        
    def do_model_action(self, op, request, param={}):
        from models_logentry import LogEntry
        try:
            op.request=request                
            ret=op.action(**param)
        except Exception, e:
            import traceback; traceback.print_exc()
            raise e
        try:
            if param: 
                    #param=u", ".join([u"%s=%s"%(p[0], unicode(p[1])) for p in param.items()])
                    param=u", ".join([u"%s=%s"%(p[0], p[1]) for p in param.items()])
            msg=u"%s(%s) %s"%(op.verbose_name, param or "", ret or "")
            LogEntry.objects.log_action_other(request.user.pk,  self, msg)
        except:
            import traceback; traceback.print_exc()
#        print 'do_model_action------------------------------------------:',ret
        return ret

    @classmethod
    def do_action_by_request(cls, op, request, form_field):
        '''
        模型操作提交最终的处理 4
        '''
#        print 'do_action_by_request-----------------------------------'
        f=None
        try:
            if len(op.params)==0:
                f=op.form(form_field, post=None)#f.is_valid ==True----add by darcy 20100430
                ret=do_action(op, request)
            else:
                f=op.form(form_field, post=request.POST)
                if not f.is_valid(): 
                    return f
                ret=do_action(op, request, f.cleaned_data)
        except Exception, e:
            import traceback; traceback.print_exc()
            if f: ret=u"%s"%e
        if f and ret:
            f.errors[NON_FIELD_ERRORS]=u'<ul class="errorlist"><li>%s</li></ul>'%ret
            return f
    
    @classmethod
    def model_do_action(cls, action, request, form_field=None, key_name="K"):
        '''
        通用模型操作提交处理 3
        '''
     #   print cls, u"model_do_action: %s"%action
        op_class=getattr(cls, action)        
        #print issubclass(op_class, ModelOperation)
        if not issubclass(op_class, ModelOperation): raise Exception(u"Error of action name: %s"%action)
                
        ret=None
        f=None
        if issubclass(op_class, Operation): #针对对象的操作
           
            try:
                if str(request.REQUEST.get("is_select_all","")) == "1":
                    objs=cls.objects.all()
                else:
                    keys=request.REQUEST.getlist(key_name)
                    objs=cls.objects.filter(pk__in=keys)
                op=op_class(objs[0])
                
                if hasattr(op, "action_batch"):
                    op=op_class(objs)
                    return cls.do_action_by_request(op, request, form_field)
                for obj in objs:
                    ret=cls.do_action_by_request(op_class(obj), request, form_field)
                    if ret: return ret
            except:
                import traceback; traceback.print_exc()
        else: #ModelOperation，针对模型的操作
            try:
                op=op_class(cls)
                if len(op.params)==0:
                        f = op.form(form_field, lock=False, init_data=None, post=None)#添加f，修改前端无法捕获异常，一直返回正确的bug----add by darcy 20100920
                        ret=cls.do_model_action(op, request)
                else:
                        f=op.form(form_field, lock=request.GET.get('_lock', False), init_data=dict(request.GET), post=request.POST) #-------------------提交后得到form对象
                        if not f.is_valid(): return f
                        ret=cls.do_model_action(op, request, f.cleaned_data)
            except Exception, e:
                import traceback; traceback.print_exc()
                if f: ret=u"%s"%e
            if f and ret:
                f.errors[NON_FIELD_ERRORS]=u'<ul class="errorlist"><li>%s</li></ul>'%ret
                return f
#        print 'model_do_action------------------------------------------:',ret
        return ret

def dump_object(obj):
#    print 'dump_object--------------------------------------'
    t=type(obj)
    if t==tuple: return "(%s)"%(", ".join([dump_object(i) for i in obj]))
    if t in [list, QuerySet]: return "[%s]"%(", ".join([dump_object(i) for i in obj]))
    if t==dict: 
        return "(%s)"%(", ".join([u"%s=%s"%(dump_object(key), 
            dump_object(v)) for key,v in obj.items()]))
    try:
        return u"%s"%obj
    except:
        print "error to dump_object", obj, type(obj)
        return obj

def do_action(op, request, param={}):
    print 'do_action--------------------------------------'
    from models_logentry import LogEntry
    print "do_action for op, param:%s"%param
    try:
        op.request=request
        if hasattr(op, "action_batch"): 
            ret=op.action_batch(**param)
        else:
            ret=op.action(**param)
    except Exception, e:
        import traceback; traceback.print_exc()
        raise e
    try:
        if param: 
                param=dump_object(param)
        msg=u"%s%s %s"%(op.verbose_name, param or "", ret or "")
        if isinstance(op.object, models.Model):
            LogEntry.objects.log_action_other(request.user.pk, op.object, msg)
        else:
            for obj in op.object:
                LogEntry.objects.log_action_other(request.user.pk, obj, msg)
    except:
        import traceback; traceback.print_exc()
    return ret

