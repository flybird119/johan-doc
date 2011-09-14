# coding=utf-8
from django.contrib.auth.models import User, Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.conf import settings
from traceback import print_exc
from django.core.management import call_command
from django.db import models, connection
from models import AppOperation
from django.db.models.fields import NOT_PROVIDED
from operation import Operation, ModelOperation

def database_init(sender, **kwargs):
    if 'mysql' in connection.__module__:    #设置mysql数据库的提交属性
        connection.cursor().execute('set autocommit=1')
        
def try_add_permission(ct, cn, cname):
    '''
    添加权限
    '''
    try:
        Permission.objects.get(content_type=ct, codename=cn)
    except:
        try:
            Permission(content_type=ct, codename=cn, name=cname).save()
            #print "Add permission %s OK"%cn
        except Exception, e:
            print "Add permission %s failed:" % cn, e
            
def check_and_create_app_permission(app, operation):
    '''
    添加 can_operation 权限
    '''
    ct = ContentType.objects.get_for_model(ContentType)
    try_add_permission(ct, 'can_' + operation.__name__, u"%s" % operation.verbose_name)
    
def check_and_create_model_permissions(model):
    '''
    添加 browse_model，和各个model._meta.permissions权限
    '''
    if hasattr(model, "check_and_create_model_permissions"): return
    ct = ContentType.objects.get_for_model(model)
    cn = 'browse_' + model.__name__.lower()
    cname = u'浏览%s' % model._meta.verbose_name
    try_add_permission(ct, cn, cname)
    for perm in model._meta.permissions:
        try_add_permission(ct, perm[0], perm[1])
    for op_name in dir(model):
        try:
            op = getattr(model, op_name)
            if issubclass(op, ModelOperation):
                cn = op.permission_code(model.__name__)
                cname = u"%s" % (op.verbose_name)
                try_add_permission(ct, cn, cname)
        except TypeError:
            pass
        except AttributeError:
            pass
        except:
            print_exc()
    model.check_and_create_model_permissions = True
    
def check_and_create_model_new_fields(model):
    from south.db import db
    c = 0
    for i in range(40):
        hc = 0
        try:
            d = list(model.objects.filter(pk=0))
        except Exception, e:
            info = u"%s" % e
            infos = info.replace('"', ' ').replace("'", " ").replace(",", ' ').replace(". ", " ").split(" ")
            from model_utils import search_field
            f = search_field(model, infos)
            hc += 1
            if f:
                print info
                print "add_field: ", model.__name__, f.name, "... ",
                try:
                    db.add_column(model._meta.db_table, f.name, f)
                except:
                    if not f.null and not f.has_default():
                        f.default = f.get_default()
                        if f.default is None: f.default = 1
                    db.add_column(model._meta.db_table, f.name, f)
                    print f.null, f.has_default(), f.default
                print " OK"
                c += 1
        if hc == 0: break;
    return c

def check_and_create_model_default(model):
    from model_utils import custom_sql
    db_table = model._meta.db_table
    for f in model._meta.fields:
        if not (f.default == NOT_PROVIDED):
            db_column = f.db_column or f.column
            value = "'%s'" % f.get_default()
            sql = "ALTER TABLE %s ADD CONSTRAINT default_value_%s_%s DEFAULT %s FOR %s" % (db_table, db_table, db_column, value, db_column)
            try:
                custom_sql(sql)
            except:
                pass
            
def check_and_create_model_initial_data(model):
    '''
    执行 model 初始化数据
    '''
    if not hasattr(model, "Admin"): return
    if not hasattr(model.Admin, "initial_data"): return
    datas = getattr(model.Admin, "initial_data")
    if type(datas) in (list, tuple):
        for data in datas:
            try:
                from model_utils import search_object
                obj = search_object(model, data, True)
            except:
                print '-----error-----'
                print_exc()
    elif callable(datas):
        model.Admin().initial_data()
        
def check_and_create_app_options(app):
    import os
    print "check_and_create_app_options------"
    p0, p1 = os.path.split(os.path.split(app.__file__)[0])
    if p1 == 'models':
        p1 = os.path.split(p0)[1]
    if hasattr(app, "app_options"):
        from base.options import options
        ao = app.app_options
        if callable(ao):
            ao = ao()
        for o in ao:
            try:
                options.add_option(p1 + "." + o[0], o[1], o[2], o[3], o[4], o[5])
            except:
                print '----------', o[0], o[1], o[2], o[3], o[4], o[5], '-----------'
                print_exc()
                
def post_syncdb_append_permissions(sender, **kwargs):
    u"""
    1、升级数据库结构, 设置字段默认值
    2、导入初始数据
    3、创建操作权限
    """
    #创建一个超级用户
#    print u'johan-------------------------------------: syncdb 命令信号扩展处理'
    if not User.objects.filter(username="admin"):
        User.objects.create_superuser("admin", "admin@sina.com", "admin")

    from django.utils import translation
    from syncdb_contenttype import update_all_contenttypes
    language = settings.LANGUAGE_CODE

    app = sender
    if app.__name__=="base.models":
        call_command('loaddata', 'initial_data_'+language, verbosity=1, database="default") #  将固化数据插入数据库
    created_models = list(kwargs['created_models'])
    verbosity = kwargs["verbosity"]
    interactive = kwargs["interactive"]

    translation.activate(language)  #设置语言
    translation.activate("en-us")   #？？？？？
    
    update_all_contenttypes()   # 同步 models 和 contenttype

    all_models = []
    for i in dir(app):
        try:
            model = app.__getattribute__(i)
        except:
            continue
        if callable(model) and type(model) not in [type(issubclass), type(post_syncdb_append_permissions)]:
            try:
                if issubclass(model, models.Model) and not model._meta.abstract:
                    check_and_create_model_new_fields(model)    #添加新字段
                    check_and_create_model_default(model)         #设置表字段默认值
                    translation.activate("zh-cn")
                    check_and_create_model_permissions(model)   # 添加 model 权限
                    translation.activate(language)
                    check_and_create_model_initial_data(model)  # 执行 model 初始化数据
                    translation.activate("en-us")
                elif issubclass(model, AppOperation) and hasattr(model, 'view'): #-----------------------如果是AppOperation则只添加相应的权限 
                    translation.activate("zh-cn")
                    check_and_create_app_permission(app, model) # 添加 app 权限
                    translation.activate("en-us")
            except:
                print_exc()
    try:
        check_and_create_app_options(app)
    except:
        print_exc()