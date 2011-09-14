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

from django.db.models.fields import NOT_PROVIDED
from model_admin import ModelAdmin, CACHE_EXPIRE
from traceback import print_exc
from django.conf import settings
from django.core.management import call_command

verbose_name = _(u"系统设置")
_menu_index = 6
class AppOperation(object):
    ''''
    AppOperation 也可和models一样加入菜单列表
    '''
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


from syncdb_addition import post_syncdb_append_permissions
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


from syncdb_addition import database_init     
from django.db.backends.signals import connection_created
connection_created.connect(database_init)   # 加入 connection_created 信号处理函数
