# -*- coding: utf-8 -*-

from django.conf.urls.defaults import *
import models
from mysite.personnel.models.empwidget import get_widget_for_select_emp
import views
from mysite.att.models.nomodelview import getData
from mysite.att.models.schclass import getSchClass

from models import nomodelview

urlpatterns=patterns('mysite.att',
(r'^getallexcept/$',views.funGetAllExcept),
(r'^tmpshifts/$',views.funTmpShifts),
(r'^FetchSchPlan/$',views.funFetchSchPlan),
(r'^assignedShifts/$',views.funAssignedShifts),
(r'^deleteEmployeeShift/$',views.funDeleteEmployeeShift),
(r'^worktimezone/$',views.funWorkTimeZone),
(r'^getshifts/$',views.funGetShifts),
(r'^attrule/$',views.funAttrule),
(r'^shift_detail/$',views.funShift_detail),
(r'^deleteShiftTime/$',views.funDeleteShiftTime),
(r'^deleteAllShiftTime/$',views.funDeleteAllShiftTime),
(r'^addShiftTimeTable/$',views.funAddShiftTimeTable),

(r'^getschclass/$',views.funGetSchclass),
(r'^AttCalculate/$',views.funAttCalculate),
(r'^AttReCalc/$',views.funAttReCalculate),
(r'^AttParamSetting/$',views.funAttParamSetting),
(r'^SaveAttParamSetting/$',views.SaveAttParamSetting),
(r'^Forget/$',views.funForget),
(r'^AttUserOfRun/$',views.funAttUerOfRun),
(r'^SaveForget/$',views.SaveForget),
(r'^newgetSchClass/$',getSchClass),
(r'^choice_widget_for_select_emp/$',get_widget_for_select_emp),
(r'^getmodeldata/(?P<app_lable>[^/]*)/(?P<model_name>[^/]*)/$',views.funGetModelData),
(r'^getData/$', getData),   #-----------------------------------------
(r'^DeviceUserManage/$',views.funAttDeviceUserManage),
(r'^DeviceDataManage/$',views.funAttDeviceDataManage),
(r'^DailyCalcReport/$', views.fundailycalcReport),
(r'^CalcReport/$', views.funCalcReport),    #---考勤汇总表
(r'^att_abnormal_report/$', nomodelview.att_abnormal_report),    #---考勤异常表
(r'^CalcLeaveReport/$', views.funCalcLeaveReport),
(r'^GenerateEmpPunchCard/$', views.GenerateEmpPunchCard),
(r'^lereport/$', views.funLEReport),
)


