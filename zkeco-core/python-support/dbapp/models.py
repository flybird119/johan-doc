# -*- coding: utf-8 -*-
from django.db import models, connection
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from base.operation import Operation,ModelOperation
import datetime
from utils import *
from django.conf import settings
from base.login_bio import BOOLEANS

VIEWTYPE_CHOICES = (
    ('personal', _(u'个人')),
    ('system', _(u'系统')),
)

#该应用是否可见
_visible=False

import views

import base


class init_db(base.models.AppOperation):
        verbose_name=_(u'初始化数据库')
        #view=views.init_db
        _app_menu="base"
        _menu_index=100000
#        visible=False

class Restore_db(base.models.AppOperation):
        verbose_name=_(u'还原数据库')
        view=views.restore_db   # 指定视图
        _app_menu="base"
        _menu_index=100000
        visible=False

class sys_option(base.models.AppOperation):
        verbose_name=_(u'系统参数设置')
        view=views.sys_option
        _menu_index=10001
        _app_menu="base"
        visible=False
        _menu_group = 'base'


class user_option(base.models.AppOperation):
        verbose_name=_(u'个性设置')
        visible=False
        view=views.user_option
        _app_menu="base"


from dbapp.model_DbManage import DbBackupLog


class ViewModel(base.models.CachingModel):
        model=models.ForeignKey(ContentType)
        name=models.CharField(_(u'视图名称'),max_length=200)
        info=models.TextField(_(u'设置字符串,json使用对象的观点'))
        viewtype=models.CharField(_(u"视图类型"),max_length=20,choices=VIEWTYPE_CHOICES)
        class Admin(base.models.CachingModel.Admin):
                app_menu="base"
                visible=True
                cache=20*60*60*24
        def save(self):
                try:
                        super(ViewModel,self).save()
                except:
                        import traceback; traceback.print_exc()

                return self


def app_options():
    from base.options import  SYSPARAM,PERSONAL
    return (
        #参数名称, 参数默认值，参数显示名称，解释,参数类别,是否可见
        ('max_photo_width', '800', u"%s"%_(u'最大图片宽度'), '',PERSONAL,True ),
        ('theme', 'flat', u'风格', "",PERSONAL,True),
        )

def create_model(name, base_model=base.models.CachingModel, attrs={}, meta_attrs={}, admin_attrs={}, module_path="dbapp.models"):
    '''
    动态构造模型 如导出的数据均需先构造成模型
    '''
    attrs['__module__'] = module_path
    class Meta: pass
    Meta.__dict__.update(meta_attrs, __module__=module_path)
    attrs['Meta']=Meta
    if admin_attrs:
        if hasattr(base_model, "Admin"):
            class Admin(base_model.Admin): pass
        else:
            class Admin: pass
        Admin.__dict__.update(admin_attrs, __module__=module_path,app_label='dbapp')
        attrs['Admin']=Admin
    return type(name, (base_model,), attrs)

