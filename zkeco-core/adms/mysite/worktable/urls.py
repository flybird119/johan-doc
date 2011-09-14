# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
urlpatterns = patterns('mysite.worktable',
        (r'^get_search_form/(?P<app_label>[^/]*)/(?P<model_name>[^/]*)/$','common_panel.get_search_from'),
        (r'^outputEmpStructureImage/$', 'views.outputEmpStructureImage'),   #人员组成结构图片数据视图
        (r'^outputattrate/$', 'views.outputattrate'),     # 出勤率数据库视图
        (r'^instant_msg/$', 'views.get_instant_msg'),   # 即时信息数据视图
        (r'^instant_msg/(?P<datakey>[^/]*)/$', 'views.set_msg_read'),
)

