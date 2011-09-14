# coding=utf-8

from django.conf.urls.defaults import *
import views     

urlpatterns = patterns('',
   url(r'^list/(?P<tmp_name>[^/]*)/$', views.api_list), #---导出数据
   url(r'^(?P<app_label>[^/]*)/(?P<model_name>[^/]*)/$', views.api),    #---返回模型的所有记录数据
   url(r'^(?P<app_label>[^/]*)/(?P<model_name>[^/]*)/count$', views.api_count),     #---返回模型记录的行数
   url(r'^(?P<app_label>[^/]*)/(?P<model_name>[^/]*)/(?P<data_key>[^/]*)/', views.api), #---返回模型指定ID的记录
   )

