#coding=utf-8
from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib.auth.decorators import permission_required
import data_viewdb, views, data_edit
import viewmodels
import data_operation
import import_and_export
from django.core.urlresolvers import reverse
from modelutils import setview,advance_query_index

from base import base_code

from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponse
from django.db.models import Q
from data_list import data_list_, data_demo



urlpatterns = patterns('',
    (r'^list/(?P<fn>.*)/$', data_list_),
    (r'^data_demo/', data_demo),    
    (r'^index/$', data_viewdb.mydesktop),   # 系统 默认视图 index
    (r'^system/help/$', data_viewdb.sys_help),
    (r'^set_option$', data_viewdb.set_option),

    (r'^(?P<app_label>[^/]*)/$',data_viewdb.myapp), # app通用默认视图    登录后的第一个视图 app_label = worktable  
    (r'^BaseCode/category/', base_code.get_category),
    (r'^(?P<app_label>[^/]*)/(?P<model_name>[^/]*)/$', data_viewdb.DataList),    # 列表页
    (r'^(?P<app_label>[^/]*)/(?P<model_name>[^/]*)/_new_/$', data_edit.DataNew), # 新增页
    (r'^(?P<app_label>[^/]*)/(?P<model_name>[^/]*)/(?P<DataKey>[^/]*)/$', data_edit.DataDetail), # 编辑修改页
    (r'^(?P<app_label>[^/]*)/(?P<model_name>[^/]*)/choice_data_widget$', views.get_chioce_data_widget), # 下拉选择
    
    (r'^(?P<app_label>[^/]*)/(?P<model_name>[^/]*)/_op_/(?P<op_name>[^/]*)/$', data_operation.get_form), # 操作通用视图
    
    (r'^(?P<app_label>[^/]*)/(?P<model_name>[^/]*)/query/show$', advance_query_index),
    (r'^(?P<app_label>[^/]*)/(?P<model_name>[^/]*)/view/show$', setview),
    (r'^(?P<app_label>[^/]*)/(?P<model_name>[^/]*)/view$', viewmodels.save_view),
    (r'^(?P<app_label>[^/]*)/(?P<model_name>[^/]*)/view/(?P<view_name>[^/]*)$', viewmodels.get_view),
    (r'^(?P<app_label>[^/]*)/(?P<model_name>[^/]*)/view/(?P<view_name>[^/]*)/delete$', viewmodels.delete_view),
    
    (r'^(?P<app_label>[^/]*)/(?P<model_name>[^/]*)/import/show_import$', import_and_export.show_import),
    (r'^(?P<app_label>[^/]*)/(?P<model_name>[^/]*)/export/show_export$', import_and_export.show_export),
    (r'^(?P<app_label>[^/]*)/(?P<model_name>[^/]*)/export/file_export$', import_and_export.file_export),
    (r'^import/get_import$', import_and_export.get_importPara),
    (r'^import/file_import$', import_and_export.file_import),


    (r'^BackupDBValidate/(?P<type>[^/]*)$', views.backup_db_validate), #备份数据库的有效性验证，如验证在当前时间的一个小时内只能备份一次数据库
    (r'^getBackupsched$', views.getBackupsched),
    (r'^init_db$', views.init_db),
    (r'^option$', views.user_option),
    (r'^sys_option$', views.sys_option),
#    (r'^restore_db$', views.restore_db),
    (r'^get_init_db_data',views.get_init_db_data),
    (r'^update_process',views.update_process),#更新备份数据库后的状态
)

dbapp_url=settings.UNIT_URL+"data/"#"/".join(reverse(views.init_db).split('/')[:-1])+'/'
surl=settings.UNIT_URL[1:]

def get_model_new_url(model):
        return reverse(data_edit.DataNew, args=(model._meta.app_label, model.__name__))

def get_model_data_url(model):
        return reverse(data_viewdb.DataList, args=(model._meta.app_label, model.__name__))

def get_obj_url(obj):
        return reverse(data_edit.DataDetail, args=(obj._meta.app_label, obj.__class__.__name__, obj.pk))


