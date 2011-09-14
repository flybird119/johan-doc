# -*- coding: utf-8 -*-
'''
加入几个与数据库交互相关的信号处理
定义了AppOperation基类
重载了多对多字段成 ZManyToManyField
定义几个基于 caching Admin 的配置管理器
同步model 和数据库表及contenttype 的几个处理 

'''
from django.db import models, connection
from django.db.models import Q
from django.contrib.auth.models import User, Permission, Group
from models_logentry import LogEntry
from cached_model import CachingModel
from base_code import BaseCode, base_code_by
from operation import Operation, ModelOperation
from options import Option, SystemOption, PersonalOption, options, AppOption, appOptions
from translation import *
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.db.models.fields import NOT_PROVIDED
from model_admin import ModelAdmin, CACHE_EXPIRE
from traceback import print_exc
from django.conf import settings
from django.core.management import call_command

verbose_name = _(u"系统设置")
_menu_index = 6
class AppOperation(object):
    pass

#替换 django.db.models.ManyToManyField, 因为其控件总是显示多选的操作提示
if hasattr(models.ManyToManyField, "old_m2m"):
    pass
else:
    class ZManyToManyField(models.ManyToManyField):
        '''
        重载 django 多对多字段
        '''
        old_m2m = models.ManyToManyField
        def __init__(self, to, **kwargs):
            super(ZManyToManyField, self).__init__(to, **kwargs)
            if 'help_text' in kwargs:   # 设置 help_text 属性
                self.help_text = kwargs['kwargs']
            else:
                self.help_text = ""
    models.ManyToManyField = ZManyToManyField

#----------------------------------------定义几个基于 caching Admin 的配置管理器
class InvisibleAdmin(CachingModel.Admin):
    visible = False

class NoLogAdmin(CachingModel.Admin):
    log = False

def is_parent_model(pm, m):
    u''' 检查 模型 pm 是否模型 mo 的所属类型，即是否其外键或级联外键 '''
    if pm == m: return True
    for f in m._meta.fields:
        if isinstance(f, models.fields.related.ForeignKey):
            if not f.rel.to == m: #避免产生无穷递归
                if is_parent_model(pm, f.rel.to): return True
    return False

def custom_sql(sql, action=True):
    '''
    执行用户sql语言
    '''
    cursor = connection.cursor()
    cursor.execute(sql)
    if action:
        connection._commit()
    return cursor


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

def search_field(model, s):
    '''
    查询 model 是否存在字段 在 s 中
    '''
    for f in model._meta.fields:
        fn = "%s.%s" % (model._meta.db_table, f.column)
        if fn in s:
            return f

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
                import traceback;traceback.print_exc()



def post_syncdb_append_permissions(sender, **kwargs):
    u"""
    1、升级数据库结构, 设置字段默认值
    2、导入初始数据
    3、创建操作权限
    """
    #创建一个超级用户
    print 'johan-------------------------------------: syncdb 命令信号扩展处理'
    if not User.objects.filter(username="admin"):
        User.objects.create_superuser("admin", "admin@sina.com", "admin")

    from django.utils import translation
    from sync_contenttype import update_all_contenttypes
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
                elif issubclass(model, AppOperation) and hasattr(model, 'view'):
                    translation.activate("zh-cn")
                    check_and_create_app_permission(app, model) # 添加 app 权限
                    translation.activate("en-us")
            except:
                print_exc()
    try:
        check_and_create_app_options(app)
    except:
        print_exc()

from django.db.models.signals import post_syncdb

post_syncdb.connect(post_syncdb_append_permissions)     ################# 加入信号处理函数



def app_options():  # 配置数据容器
    '''
    系统全局配置参数
    '''
    from base.options import  SYSPARAM, PERSONAL
    import dict4ini # 读取配置文件appconfig.ini
    appconf=dict4ini.DictIni(settings.APP_HOME+"/appconfig.ini")
    language=appconf["language"]["language"]        # 设置语言
    
    return (
        #参数名称, 参数默认值，参数显示名称，解释,参数类别,是否可见
        ('date_format', '%Y-%m-%d', u"%s" % _(u'日期格式'), '', PERSONAL, True),
        ('time_format', '%H:%M:%S', u"%s" % _(u'时间格式'), '', PERSONAL, True),
        ('datetime_format', '%Y-%m-%d %H:%M:%S', u"%s" % _(u'时间日期格式'), '', PERSONAL, True),
        ('shortdate_format', '%y-%m-%d', u"%s" % _(u'短日期格式'), '', PERSONAL, True),
        ('shortdatetime_format', '%y-%m-%d %H:%M', u"%s" % _(u'短日期时间格式'), '', PERSONAL, True),
        ('language', language, u'语言', '', PERSONAL, True),
        ('base_default_page', 'data/auth/User/', u"%s" % _(u'系统默认页面'), '', PERSONAL, False),
        ('site_default_page', 'data/worktable/', u"%s" % _(u'整个系统默认页面'), "", PERSONAL, False),
        ('backup_sched', '', u'备份时间', "", SYSPARAM, True),
    )


def database_init(sender, **kwargs):
    from django.db import connection
    if 'mysql' in connection.__module__:    #设置mysql数据库的提交属性
        connection.cursor().execute('set autocommit=1')
     
from django.db.backends.signals import connection_created
connection_created.connect(database_init)   # 加入 connection_created 信号处理函数
