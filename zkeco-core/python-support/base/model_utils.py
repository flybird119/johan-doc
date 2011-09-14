# coding=utf-8
from django.db import models, connection
from django.contrib.contenttypes.models import ContentType
from models import AppOperation


def custom_sql(sql, action=True):
    '''
    执行用户sql语言
    '''
    cursor = connection.cursor()
    cursor.execute(sql)
    if action:
        connection._commit()
    return cursor

def search_field(model, s):
    '''
    查询 model 是否存在字段 在 s 中
    '''
    for f in model._meta.fields:
        fn = "%s.%s" % (model._meta.db_table, f.column)
        if fn in s:
            return f

def is_parent_model(pm, m):
    u''' 检查 模型 pm 是否模型 mo 的所属类型，即是否其外键或级联外键 '''
    if pm == m: return True
    for f in m._meta.fields:
        if isinstance(f, models.fields.related.ForeignKey):
            if not f.rel.to == m: #避免产生无穷递归
                if is_parent_model(pm, f.rel.to): return True
    return False

def search_object(model, data, append=True):
    for field in data:
        try:
            f = model._meta.get_field(field)
        except:
            continue
        value = data[field]
        if isinstance(f, models.fields.related.ForeignKey):
            if type(value) == type({}): #
                objs = search_object(f.rel.to, value, append)
                value = objs[0]
                data[field] = value
    udata = dict([(k.replace("_id", ""), unicode(v)) for k, v in data.items()])#value需要unicode
    objs = model.objects.filter(**udata)#初始化前先判断当前数据是否已经添加过--darcy20100714
    if append and len(objs) == 0:
        obj = model(**udata)
        obj.save()
        objs = [obj, ]
    return objs


#========================= 两个重要API ====================
def get_all_app_and_models(hide_visible_false=True):
    '''
    获取系统所有界面可视模型信息
    条件：
            对象类型：Model (_meta.app_label存在)   AppOperation (含 view 成员)
                             非 _meta.abstract
                             有 browse_model 权限            有 browse_model 权限
           配置项： verbose_name、visible、menu_index、app_menu、parent_model、select_related_perms、hide_perms、cancel_perms、menu_group
                         verbose_name、visible、_menu_index、_app_menu、_parent_model、_select_related_perms、_hide_perms、_cancel_perms、add_model_permission
    '''
    from django.conf import settings
    from base.translation import DataTranslation, _ugettext_ as _
    from django.db.models.loading import get_app
    from django.db import models
    from django.core.urlresolvers import reverse
    from django.core.cache import cache
    from middleware import threadlocals    
    usr=threadlocals.get_current_user()
    cache_key = "%s_%s"%(usr.username,"menu_list")  # 当前用户菜单列表缓存名
    if usr.is_anonymous():
        cache.delete(cache_key)
    menu_list= None#cache.get(cache_key)    # 不使用缓存
    if menu_list:
        return menu_list
    ################# 创建开始 ####################
    apps={}
    for application in settings.INSTALLED_APPS: # 首要条件必须在安装的app中
        if application in settings.INVISIBLE_APPS: continue # 去掉隐藏的app
        app_label=application.split(".")[-1]
        apps[app_label]={
            'models':[],
            'is_app_true':'true'
            }
    for app_label in apps.keys():
        app=get_app(app_label)  #　django 关键 api 的使用
        apps[app_label]['name']=u"%(name)s"%{'name':hasattr(app, "verbose_name") and app.verbose_name or unicode(DataTranslation.get_field_display(ContentType, 'app_label', app_label))}
        apps[app_label]['index']=hasattr(app, '_menu_index') and app._menu_index or 9999
        for i in dir(app):  # 条件二：在app.models 中的对象 如app/models/__init__.py
            app_menu=None
            try:
                model=app.__getattribute__(i)   # 得到成员对象
                m0={}
                ##################### model 对象 #####################
                if issubclass(model, models.Model) and (model._meta.app_label==app_label):  # 条件三：成员为model，app_label不为空
                    admin=hasattr(model, "Admin") and model.Admin or None
                    if not model._meta.abstract:
                        perm='%s.%s_%s'%(model._meta.app_label, "browse",model.__name__.lower())
                        if usr.has_perm(perm):
                            m0={'verbose_name': u"%(name)s"%{'name':model._meta.verbose_name},'model':model, 'index':9999}
                            if (not admin or not hasattr(admin, "visible") or admin.visible):
                                m0["visible"]=True
                            else:
                                m0["visible"]=False
                            if hasattr(admin, "menu_index"):
                                m0['index']=admin.menu_index
                            
                            if hasattr(admin, "parent_model"):
                                m0["parent_model"]=admin.parent_model
                            if hasattr(admin,"select_related_perms"):
                                m0["select_related_perms"]=admin.select_related_perms
                            if hasattr(admin,"hide_perms"):
                                m0["hide_perms"]=admin.hide_perms
                            if hasattr(admin,"cancel_perms"):
                                m0["cancel_perms"]=admin.cancel_perms
                            app_menu=app_label
                            if hasattr(admin, "app_menu"):
                                app_menu=admin.app_menu
                            
                            m0['menu_group'] = hasattr(admin, "menu_group") and admin.menu_group or app_label#未配置时取app_menu（即app_label)
                ##################### AppOperation 对象 #####################            
                elif issubclass(model, AppOperation) and hasattr(model, 'view'):    # 含view成员的 AppOperation
                    operation_flag=hasattr(model,'operation_flag') and model.operation_flag or "true"
                    menu_group = hasattr(model, '_menu_group') and model._menu_group or app_label#未配置时取app_menu（即app_label)
                    if usr.has_perm("contenttypes.can_%s"%model.__name__):
                        m0={'verbose_name':u"%(name)s"%{'name': hasattr(model, "verbose_name") and model.verbose_name or (u"%s"%_(model.__name__))},
                            'model':None,
                            'operation': model,
                            'menu_group': menu_group,
                            'operation_flag':operation_flag,
#                            'url': reverse(model.view.im_func),
                            'index': 9999}
                        if (not hasattr(model, 'visible') or getattr(model,'visible')):
                            m0["visible"]=True
                        else:
                            m0["visible"]=False
                        if hasattr(model, 'add_model_permission'):
                            m0["add_model_permission"]=model.add_model_permission
                        if hasattr(model, '_parent_model'):
                            m0["parent_model"]=model._parent_model
                        if hasattr(model, "_menu_index"):
                            m0['index']=model._menu_index
                        if hasattr(model,"_select_related_perms"):
                            m0["select_related_perms"]=model._select_related_perms
                        if hasattr(model,"_hide_perms"):
                            m0["hide_perms"]=model._hide_perms
                        if hasattr(model,"_cancel_perms"):
                            m0["cancel_perms"]=model._cancel_perms                            
                        app_menu=app_label
                        if hasattr(model, "_app_menu"):
                            app_menu=model._app_menu
                ################## 创建 models 部分信息 ######################                                    
                if m0:
                    m0['app_label']=app_label
                    m0['name']=u"%(name)s"%{'name':model.__name__}
                    if app_menu not in apps: apps[app_menu]={
                        'name':u"%(name)s"%{'name':_(app_menu)},
                        'models': [m0,],
                        'index': hasattr(app, '_menu_index') and app._menu_index or 9999
                        }
                    else:
                        apps[app_menu]['models'].append(m0)
            except TypeError:
                pass
            except:
                import traceback; traceback.print_exc()
                pass
    ###############  隐藏和排序处理(两级排序 ) ################################3
    if hide_visible_false:
        for k,v in apps.items():
            vmodels=[m for m in v['models'] if m["visible"]]    # 第三个条件
            v['models']=vmodels
    mlist=[(k,v) for k,v in apps.items() if v['models']]        # 第四个条件
    mlist.sort(lambda x1,x2: x1[1]['index']-x2[1]['index'])
    for m in mlist: 
        m[1]['models'].sort(lambda x1,x2: (x1['index']-x2['index']) or (x1['name']>=x2['name'] and 1 or -1))
    #return dict(mlist)不能排序
    cache.set(cache_key,mlist,60*60*24)
    return mlist

def get_model_or_AppOperation_DicInfo(app_label, model_name):
    all = get_all_app_and_models()
    app = [e for e in all if e[0]==app_label]
    result= None
    if app:
        models = app[0][1]["models"]
        model = [e for e in models if e["name"].lower()==model_name.lower()]
        if model:
            result = model[0]
    return result

def get_AppOperation(app_label,op_name):
    operation_class = None
    obj = get_model_or_AppOperation_DicInfo(app_label,op_name)
    if obj:
        if obj.has_key("operation"):
            operation_class = obj["operation"]
    return operation_class
    

def get_all_permissions(queryset=None):
        appss=get_all_app_and_models()
        apps=dict(appss)
        empty_app=[]
        change_operation_menu=[]
        
        if queryset==None: queryset=Permission.objects.all()
        for app_index in apps:
                empty_models=[]
                app_models=apps[app_index]['models']
                for model in app_models:
                        m=model['model']
                        admin=hasattr(m, "Admin") and m.Admin or None
                        disabled_perm=[]
                        if admin:
                                if hasattr(admin,"disabled_perms"):
                                    disabled_perm=admin.disabled_perms
                        elif hasattr(model["operation"],"_disabled_perms"):
                                disabled_perm=model["operation"]._disabled_perms
                        permissions=[]
                        if m==None:
                                ct=ContentType.objects.get_for_model(ContentType)
                                code_name='can_%s'%model['operation'].__name__
                                try:
                                        if code_name not in disabled_perm:
                                                permissions.append(queryset.get(content_type=ct, codename=code_name))
                                except: pass
                                if model.has_key("add_model_permission"):
                                        for  elem in model["add_model_permission"]:
                                            ct=ContentType.objects.get_for_model(elem)
                                            for perm in queryset.filter(content_type=ct):
                                                        if perm.codename not in disabled_perm:
                                                                permissions.append(perm)
                        else:
                                ct=ContentType.objects.get_for_model(m)
                                for perm in queryset.filter(content_type=ct):
                                        if hasattr(m.Admin,"opt_perm_menu") and m.Admin.opt_perm_menu.has_key(perm.codename):
                                            change_operation_menu.append([m.Admin.opt_perm_menu[perm.codename],perm])#单个模型操作配置菜单
                                            continue
                                        if perm.codename not in disabled_perm:
                                                permissions.append(perm)
                        if permissions:        
                                model['permissions']=permissions
                        else:
                                empty_models.append(model)
                for m in empty_models: app_models.remove(m)
                if len(app_models)==0:
                        empty_app.append(app_index)
        for app_index in empty_app: apps.pop(app_index)
        for elem in change_operation_menu:#elem->["app_menu.model",perm]
            elem_app,elem_model=elem[0].split(".",1)#必须为模型名，不能为权限的名字
            try:
                for e in dict(apps)[elem_app]["models"]:
                    if e["name"]==elem_model:
                        e["permissions"].append(elem[1])
            except:
                from traceback import print_exc
                print_exc()
        mlist=apps.items()
        mlist.sort(lambda x1,x2: x1[1]['index']-x2[1]['index'])
        return  mlist
    
def model_owner_rel(parent_model, model, obj_id=""):
        if parent_model==model:
                return obj_id+"pk"
        for rel in parent_model._meta.get_all_related_objects():
                ret=model_owner_rel(rel.model, model, obj_id=obj_id+rel.field.name+"__")
                if ret: return ret
        return None
    
def is_obj_owner(model, id, obj):
        '''
        没有地方调用
        '''
        if isinstance(obj, model):
                return id==obj.pk
        for f in obj._meta.fields:
                if isinstance(f, models.fields.related.ForeignKey):
                        ret=is_obj_owner(model, id, getattr(obj, f.name))
                        if ret: return ret
                        if ret==False: return ret
        return None
    
def GetModel(app_label, model_name):
        '''
        获取模型对象 本质为django的models.get_model
        '''
        dataModel=models.get_model(app_label,model_name)
        if not dataModel:
                dataModel=models.get_model("auth",model_name)
        if dataModel:   # Admin 成员的处理
                if not hasattr(dataModel, "Admin"): dataModel.Admin=None
        return dataModel