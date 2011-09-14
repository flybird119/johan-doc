# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *
from models.model_empchange  import get_empchange_postion
from views import get_dept_tree_data
from models.empwidget import get_widget_for_select_emp
import report
import views
urlpatterns=patterns('mysite.personnel',
    (r'^getempchange_value/(?P<userid>[^/]*)/(?P<num>[^/]*)/$',get_empchange_postion),
    (r'^get_dept_tree_data$', get_dept_tree_data),
    (r'^GenerateEmpFlow/$', report.GenerateEmpFlow),
    (r'^GenerateDeptRoster/$', report.GenerateDeptRoster),
    (r'^GenerateEmpEducation/$', report.GenerateEmpEducation),
    (r'^GenerateEmpCardList/$', report.GenerateEmpCardList),
    (r'^choice_widget_for_select_emp/$',get_widget_for_select_emp),
    (r'^getchange/$', views.getchange),
    (r'^getmodeldata/(?P<app_lable>[^/]*)/(?P<model_name>[^/]*)/$',views.funGetModelData),
)
 
