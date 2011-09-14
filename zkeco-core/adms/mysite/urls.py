# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *
from django.contrib.auth.views import login, logout, password_change
from settings import MEDIA_ROOT,ADDITION_FILE_ROOT,LOGIN_REDIRECT_URL,UNIT_URL
from django.template import loader, Context, RequestContext
from django.http import QueryDict, HttpResponse, HttpResponseRedirect, HttpResponseNotModified
from django.shortcuts import render_to_response
from dbapp.utils import *
from staticfiles import serve
import base
from base.log import logger
from django.core.urlresolvers import RegexURLPattern
from django.utils.translation import ugettext_lazy as _

from core.site_views import index,my_i18n,checkno

surl=UNIT_URL[1:]

def tmp_url():
    return surl+'tmp/'

urlpatterns = patterns('',
    (r'^'+surl+'api/', include('mysite.api.urls')),         #----RESTful API 接口 指向 api 目录  python-support/piston 相关 在urls最上层
    ('i18n/setlang/', my_i18n), #系统语言设置
# 几个静态文件请求
    (r'^'+surl+'file/(?P<path>.*)$', serve, {'document_root': ADDITION_FILE_ROOT, 'show_indexes': True}),
    (r'^'+tmp_url()+'(?P<path>.*)$', serve, {'document_root': tmpDir(), 'show_indexes': True}),
    (r'^'+surl+'media/(?P<path>.*)$', serve, {'document_root': MEDIA_ROOT, 'show_indexes': False}),
    (r'^media/(?P<path>.*)$', serve,  {'document_root': MEDIA_ROOT, 'show_indexes': True}),
    
    (r'^'+surl+'checkno/(?P<app_label>[^/]*)/(?P<model_name>[^/]*)/$',checkno),
    
    (r'^'+surl+'accounts/', include('mysite.authurls')),         #用户登录、登出、密码设置
    
    (r'^'+surl+'data/', include('dbapp.urls')),                         #通用数据管理
    (r'^'+surl+'iclock/', include('mysite.iclock.urls')),         #adms管理    
    (r'^'+surl+'testapp/', include('mysite.testapp.urls')),         #用于测试的应用
    (r'^'+surl+'personnel/',include('mysite.personnel.urls')),   #人事管理系统
    (r'^'+surl+'worktable/',include('mysite.worktable.urls')),   #我的工作面板
    (r'^$', index),
)

dict_urls={
    "mysite.att":url(r'^'+surl+'att/',include('mysite.att.urls'),prefix=''),#考勤系统系理
    "mysite.iaccess":url(r'^'+surl+'iaccess/',include('mysite.iaccess.urls'),prefix=''),#zkaccess门禁系统管理
    "mysite.video":url(r'^'+surl+'video/',include('mysite.video.urls'),prefix=''),#视频系统管理
    "rosetta":url(r'^rosetta/', include('rosetta.urls'),prefix='')
}

for k,v in dict_urls.items():
    if k in settings.INSTALLED_APPS:
        urlpatterns.append(v)