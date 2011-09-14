#! /usr/bin/env python
#coding=utf-8
from django.db import models
from base.models import CachingModel
from django.conf import settings
from django.core.cache import cache
from dbapp.utils import *
from django.utils.translation import ugettext_lazy as _
from model_device import DeviceForeignKey, COMMU_MODE_PUSH_HTTP
from model_devoperate import OperateCmd
import datetime
from traceback import print_exc
from base.operation import OperationBase, Operation, ModelOperation
import socket
from redis.server import check_and_start_queqe_server, queqe_server
import threading
from base.operation import OperationBase, Operation

try:
    import cPickle as pickle
except:
    import pickle

def trigger_cmd_device(cmd_obj):
    '''
    设备写入命令到队列
    '''
    old_cmd=0
    try:
        q_server=queqe_server()
        cln=cmd_obj.SN.new_command_list_name()
        if cmd_obj.CmdImmediately:
            q_server.rpush(cln, pickle.dumps(cmd_obj))  #---紧急就添加到头            python 对象序列化/反序列化
        else:    
            q_server.lpush(cln, pickle.dumps(cmd_obj))  #---添加到尾
        #命令总数
        cntkey=cmd_obj.SN.command_count_key()
        cnt=q_server.get(cntkey)
        if cnt is None:
            cnt='0'
        if cnt.find('\x00'):
            cnt=cnt.strip('\x00')
        q_server.set(cntkey, "%d"%(int(cnt)+1)) #---设备命令计数

        old_cmd=q_server.llen(cln)  #--- name 元素个数
        q_server.connection.disconnect()
    except:
        print_exc()
    if not (cmd_obj.SN.comm_type==COMMU_MODE_PUSH_HTTP): #门禁设备不须通知
        return
    pass
    if old_cmd: #若新命令队列不空，说明设备上次的命令还没有执行，不需要再次通知设备
        return  
    try:
        ip=cmd_obj.SN.ipaddress #---UDP 广播发送“R-CMD”通知该设备读取服务器下发的命令
        sNotify = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        if ip: sNotify.sendto("R-CMD", (ip, 4374))
    except:
        print_exc()
        
CMDRETURN=(
(0, _(u"命令成功执行")),
(-1, _(u"参数错误")),
(-3, _(u"机器存取错误")),
(-10 ,_(u"用户不存在")), 
(-11, _(u"非法的指纹模板格式")),
(-12, _(u"非法的指纹模板")),
(-99999,_(u"命令处理失败")),
(-99996,_(u"命令处理超时，等待下次下发此命令")),
(-99997,_(u"命令处理超时，等待下次下发此命令")),
(-99998,_(u"命令处理超时，等待下次下发此命令")),

)
class DevCmd(CachingModel):
    '''
    服务器下发命令：服务器请求设备的命令
    '''
    SN = DeviceForeignKey(verbose_name=_(u'设备'), null=True)
    CmdOperate = models.ForeignKey(OperateCmd, verbose_name = _(u'操作任务'), null=True)
    CmdContent = models.TextField(_(u'命令内容'),max_length=2048)   #----命令字符串的内容
    CmdCommitTime = models.DateTimeField(_(u'提交时间'),default=datetime.datetime.now())
    CmdTransTime = models.DateTimeField(_(u'传送时间'),null=True, blank=True)
    CmdOverTime = models.DateTimeField(_(u'返回时间'),null=True, blank=True)
    CmdReturn = models.IntegerField(_(u'返回值'), null=True, blank=True,choices=CMDRETURN)
    CmdReturnContent = models.TextField(_(u'返回内容'), null=True, blank=True)
    CmdImmediately=models.BooleanField(_(u'是否是立即备份'), default=False)
    
    def device(self):
        return get_device(self.SN_id)
    
    class _delete(Operation):
            help_text=_(u"删除选定记录") #删除选定的记录
            verbose_name=_(u"删除")
            def action(self):
                    self.object.delete()
    
    def __unicode__(self): 
        from base.templatetags.base_tags import fmt_shortdatetime
        try:
            return u"%s, %s" % (self.SN, fmt_shortdatetime(self.CmdCommitTime))
        except:
            return u"%s, %s" % (self.SN_id, fmt_shortdatetime(self.CmdCommitTime))
    
    def save(self, **kargs):
        if not self.CmdCommitTime: self.CmdCommitTime=datetime.datetime.now()
        ret = models.Model.save(self, kargs)
        if self.SN and not self.CmdTransTime:
            trigger_cmd_device(self)
        return ret
    
    def file_url(self):
        if self.CmdContent.find("GetFile ")==0:
            fname=self.CmdContent[8:]
        elif self.CmdContent.find("Shell ")==0:
            fname="shellout.txt"
        else:
            return ""
        return getUploadFileURL(self.SN.SN, self.id, fname)
    class dataexport(Operation):
        help_text=_(u"数据导出") #导出
        verbose_name=u"导出"
        visible=False
        def action(self):
                pass

    class OpClearDevCmd(ModelOperation):
        verbose_name = _(u'''清空命令表''')
        help_text = _(u"清空服务器下发命令表。")
        tips_text =  _(u"确认要清空命令表")
        def action(self):
            self.model.objects.all().delete()

            
    class Admin(CachingModel.Admin):
        #visible = False
        list_display=('SN.alias','SN.sn','CmdCommitTime|fmt_shortdatetime','CmdTransTime|fmt_shortdatetime','CmdOverTime|fmt_shortdatetime','CmdContent','CmdReturn')
        adv_fields=('SN.sn', 'SN.alias','CmdCommitTime','CmdTransTime','CmdOverTime','CmdContent','CmdReturn')
        search_fields = ["CmdContent"]
        list_filter =['SN', 'CmdCommitTime', 'CmdOverTime']
        query_fields=['SN.alias', 'SN.sn', 'CmdReturn']
        disabled_perms = ["change_devcmd", "add_devcmd", "dataexport_devcmd"]#"dataexport_devcmd"]"delete_devcmd"
   
    class Meta:
        app_label='iclock'
        db_table = 'devcmds'
        verbose_name = _(u"服务器下发命令")
        verbose_name_plural=verbose_name
