#coding=utf-8
from django.conf.urls.defaults import *
from django.contrib.auth.decorators import permission_required
import models

urlpatterns = patterns('mysite.iclock',
#设备连接相关
    (r'^cdata$', 'devview.cdata'),  #---设备的http请求
    (r'^getrequest$', 'devview.getreq'),    #---设备读取服务器上存储的命令
    (r'^devicecmd$', 'devview.devpost'),    #---返回设备命令的执行结果
    (r'^fdata$', 'devview.post_photo'), #---设备采集现场图片并上传到服务器
#数据管理相关        
    (r'^_checktranslog_$', 'datamisc.newTransLog'), #实时记录下载
    (r'^_checkoplog_$', 'datamisc.newDevLog'), #设备实时记录
    (r'^ic1ock$', 'datasql.sql_page'),                                #执行SQL
    (r'^upload$', 'importdata.uploadData'),                                #上传导入数据文件
#其他功能
    (r'^ouputtreejson$', 'testtreeview.ouputtreejson'),
    (r'^funTestTree$','testtreeview.funTestTree'),        
    (r'^options/', 'setoption.index'),
    (r'^filemng/(?P<pageName>.*)$', 'filemngview.index'),
    (r'^tasks/del_emp$', 'taskview.FileDelEmp'),
    (r'^tasks/disp_emp$', 'taskview.FileChgEmp'),
    (r'^tasks/name_emp$', 'taskview.FileChgEmp'),
    (r'^tasks/disp_emp_log$', 'taskview.disp_emp_log'),
    (r'^tasks/del_emp_log$', 'taskview.del_emp_log'),
    (r'^tasks/app_emp$', 'taskview.app_emp'),
    (r'^tasks/upgrade$', 'taskview.upgrade'),
    (r'^tasks/restart$', 'taskview.restartDev'),
    (r'^tasks/autorestart$', 'taskview.autoRestartDev'),
    (r'^data_exp/(?P<pageName>.*)$', 'expview.index'),
    (r'^pics/(?P<path>.*)$', 'browsepic.index'),

    (r'^upload/(?P<path>.*)$', 'datamisc.uploadFile'),
    (r'^DevRTMonitorPage/$', 'models.models.render_devrtmonitor_page'),
    (r'^tasks/check_old_commpwd/$' ,'taskview.check_old_commpwd'),
)
