#! /usr/bin/env python
#coding=utf-8
from django.db import models, connection
from base.models import CachingModel
from django.utils.translation import ugettext_lazy as _
from accdoor import AccDoor
from acctimeseg import AccTimeSeg
from mysite.personnel.models import Employee
from base.operation import Operation
from dbapp import data_edit
from mysite.iclock.models.dev_comm_operate import sync_delete_user_privilege, sync_set_user_privilege, sync_set_user
from base.cached_model import SAVETYPE_EDIT
from django.shortcuts import render_to_response
from django.template import  RequestContext
import time
import threading
from redis.server import queqe_server
from base.middleware import threadlocals

class TThreadComm(object):
    def __init__(self,func,args):
        self.func = func
        self.args = args

    def __call__(self):
        apply(self.func, self.args)

def clear_progress_cache(devs, session_key = ""):
    q_server=queqe_server()
    q_server.set("DEV_COMM_SYNC_%s"%session_key, "%d,0"%(len(devs)*2))
    if devs:
        q_server.set("DEV_COMM_PROGRESS_%s"%session_key, "%s,0"%devs[0].alias.encode("gb18030"))
    else:
        q_server.set("DEV_COMM_PROGRESS_%s"%session_key, ",0")
    q_server.connection.disconnect()
    
def end_sync_userinfo(session_key=""):
    q_server=queqe_server()
    q_server.delete("DEV_COMM_SYNC_%s"%session_key)
    q_server.delete("DEV_COMM_PROGRESS_%s"%session_key)
    q_server.connection.disconnect()
    
def sync_total_progress(dev, tol, cur, session_key=""):
    q_server=queqe_server()
    q_server.set("DEV_COMM_SYNC_%s"%session_key, "%d,%d"%(tol, cur))
    q_server.set("DEV_COMM_PROGRESS_%s"%session_key, "%s,0"%dev.encode("gb18030"))
    q_server.connection.disconnect()

#向门禁权限组中添加人员    
def sync_userinfo(devs, objs, session_key=""):
    #print "sync_userinfo=", session_key
    tol=len(devs)*2
    cur=0
    for dev in devs:
        cur+=1
        sync_total_progress(dev.alias, tol, cur, session_key)
        sync_set_user([dev], objs, session_key)
        cur+=1
        sync_total_progress(dev.alias, tol, cur, session_key)
        sync_set_user_privilege([dev], objs, session_key)
        time.sleep(1)
    end_sync_userinfo(session_key)
    return 0

#权限组 门变动 包含可能的时间段变动
def sync_level_door_edit(dev, session_key=""):
    clear_progress_cache(dev, session_key)
    tol=len(dev)*3      
    cur=0                        
    for d in dev:
        cur+=1
        sync_total_progress(d.alias, tol, cur, session_key)              #progress end
        sync_delete_user_privilege([d], None)
        cur+=1
        sync_total_progress(d.alias, tol, cur, session_key)   #progress
        duser=d.search_accuser_bydevice()
        sync_set_user([d], duser, session_key)
        cur+=1
        sync_total_progress(d.alias, tol, cur, session_key)   #progress
        sync_set_user_privilege([d], duser, session_key)
    end_sync_userinfo(session_key)     #结束progress
    return

#权限组仅时间段变动
def sync_level_timeseg_edit(dev, session_key=""):
    clear_progress_cache(dev, session_key)
    tol=len(dev)*2     
    cur=0                        
   
    for d in dev:
        duser=d.search_accuser_bydevice()
        cur+=1
        sync_total_progress(d.alias, tol, cur, session_key)   #progress
        sync_delete_user_privilege([d], duser)
        cur+=1
        sync_total_progress(d.alias, tol, cur, session_key)   #progress
        sync_set_user_privilege([d], duser, session_key)
    end_sync_userinfo(session_key)     #结束progress
    return

#删除权限组
def sync_delete_levelset(dev, userset, session_key=""):
    clear_progress_cache(dev, session_key)
    tol=len(dev)*2    
    cur=0                        

    for d in dev:
        #duser=d.search_accuser_bydevice()
        cur+=1
        sync_total_progress(d.alias, tol, cur, session_key)   #progress
        sync_delete_user_privilege([d], userset)
        cur+=1
        sync_total_progress(d.alias, tol, cur, session_key)   #progress
        sync_set_user_privilege([d], userset, session_key)
    end_sync_userinfo(session_key)     #结束progress
    return

class AccLevelSet(CachingModel):
    u"""
    权限组
    """
    level_name = models.CharField(_(u'权限组名称'), null=True, max_length=30, blank=False, default="", unique=True)
    level_timeseg = models.ForeignKey(AccTimeSeg, verbose_name=_(u'门禁时间段'), null=True, blank=False, editable=True)
    door_group = models.ManyToManyField(AccDoor, verbose_name=_(u'门组合'), null=True, blank=True, editable=True)
    emp = models.ManyToManyField(Employee, verbose_name=_(u'人员'), null=True, blank=True, editable=False)
      
    def limit_door_group_to(self, queryset):
        #需要过滤掉用户权限不能控制的门（需要按照id排序）
        u = threadlocals.get_current_user()
        aa = u.areaadmin_set.all()
        if not u.is_superuser and aa:#非超级用户如果a不为空则默认全部区域
            areas = [a.area for a in aa]
            from mysite.iclock.models import Device
            queryset = queryset.filter(device__area__in=areas).order_by('id')
        return queryset.order_by('id')
    
    def limit_acclevelset_to(self, queryset, user):#self 为class
        #需要过滤掉用户权限不能控制的权限组(列表datalist)
        aa = user.areaadmin_set.all()
        da = user.deptadmin_set.all()
        if not user.is_superuser and aa:#非超级用户如果a不为空则默认全部区域
            a_limit = [int(a.area_id) for a in aa]
            doors = AccDoor.objects.exclude(device__area__pk__in=a_limit)
            queryset = queryset.exclude(door_group__in=doors).order_by('id')#不包含不该有的门（设备）即可（可以没有门）
            if da:
                d_limit = [int(d.dept_id) for d in da]
                emps = Employee.objects.exclude(DeptID__in=d_limit)
                queryset = queryset.exclude(emp__in=emps).order_by('id')
        #print '----queryset=',queryset
        return queryset.order_by('id')
        
    def __unicode__(self):
        return self.level_name
    
    def data_valid(self, sendtype):
        tmp = AccLevelSet.objects.filter(level_name=self.level_name.strip())
        if tmp and tmp[0] != self:
            raise Exception(_(u'权限组名称设置重复'))

        if AccLevelSet.objects.count() == 255:
            raise Exception(_(u'门禁权限组不能超过255个'))
        
        
    def save(self, *args, **kwargs):
        if self in [a for a in AccLevelSet.objects.all()]:#编辑
            obj = AccLevelSet.objects.filter(id=self.id)[0]
            obj.level_name = self.level_name
            obj.level_timeseg_id = self.level_timeseg_id
            for g in self.door_group.all():
                if g not in obj.door_group.all():
                    obj.door_group.add(g)

            super(AccLevelSet, obj).save(force_update=True, log_msg=_(u'该权限组已变动'))
        else:#新增
            super(AccLevelSet, self).save(force_insert=True)

    #此方法用于获取跟此权限组相关联的门
    def get_doors(self):
        return u",".join([door.door_name for door in self.door_group.all()]) or _(u'暂未设置门信息')
    
    def get_emps(self):
        list_emps = [u'%s %s'%(emp.PIN, emp.EName) for emp in self.emp.all()]
        return list_emps and u",".join(list_emps) or _(u'暂未设置人员信息')
#        if list_emps.__len__() > 10:#最多显示10个人
#            return u",".join(list_emps[0:10]) + u'... 共:%s'% list_emps.__len__()
#        else:
#            return list_emps and u",".join(list_emps) or _(u'尚未给权限组配置人员信息')

    def get_emp_count(self):
        return self.emp.count()
        
    def delete(self):
        devs=[]
        userset=self.emp.all();     #权限组所有人
        for door in self.door_group.all():
            if door.device not in devs:
                devs.append(door.device)    #权限组所有设备
        t = threading.Thread(target = TThreadComm(sync_delete_levelset, (devs, userset, "delete_level")))
        t.start()
        return super(AccLevelSet, self).delete()

    def clear_authorize(self):
        #print self.door_group.all(), self.emp.all()
        devs=[]
        if self.emp.all() is not None:
            for door in self.door_group.all():
                if door.device not in devs:
                    devs.append(door.device)
        #add progress
        clear_progress_cache(dev)   
        tol=len(devs)*2      
        cur=0                        
        for dev in devs:
            cur+=1
            sync_total_progress(dev.alias,tol, cur)              #progress end
            sync_delete_user_privilege([dev], self.emp.all())
            cur+=1
            sync_total_progress(d.alias, tol, cur)   #progress
            sync_set_user_privilege([dev], self.emp.all())
        end_sync_userinfo()

    def set_authorize(self, objs, session_key):
        devs=[]
        for door in self.door_group.all():
            if door.device not in devs:
                devs.append(door.device)
        clear_progress_cache(devs, session_key)
        t = threading.Thread(target = TThreadComm(sync_userinfo,(devs, objs, session_key)))
        t.start()
    
    class OpDelEmpFromLevel(Operation):
        verbose_name = _(u"删除人员")
        def action(self):
            pass

    class OpAddEmpToLevel(Operation):
        verbose_name = _(u"添加人员")
        help_text = _(u"""向门禁权限组中添加人员，使其具有开门权限。""")

        def action(self):
            dept_all = self.request.POST.getlist("dept_all")#'on'或者''
            obj = self.object

            if not dept_all:
                emps = self.request.POST.getlist("mutiple_emp")
            else:#勾选 选择部门下所有人员时
                dept_id = self.request.POST.getlist("deptIDs")
                emps = set([e.id for e in Employee.objects.filter(DeptID__in = dept_id)])
            
            #已经存在的不需要再次添加
            downlist = []
            old_emps = [o.id for o in obj.emp.all()]
            for e in emps:
                if int(e) not in old_emps:
                    #obj.emp.add(e)
                    cursor = connection.cursor()
                    sql = 'insert into acc_levelset_emp(acclevelset_id,employee_id) values(%d,%d)'%(obj.id, int(e))
                    cursor.execute(sql)
                    downlist.append(Employee.objects.get(id=int(e)))
            if downlist is not None:
                obj.set_authorize(downlist, self.request.session.session_key)
                

    class Admin(CachingModel.Admin):
        menu_index = 10003
        help_text = _(u'门禁权限组包含时间段、门组合以及能开门的人员，此处只设置时间段和门组合。<br>系统中不允许设置时间段和门组合完全相同的两个权限组。')
        list_display = ('level_name', 'level_timeseg', 'door_group', 'emp', 'emp_count')
        #api_fields = ('level_name', 'level_timeseg', 'door_group', 'emp')#.door_name.EName, 'emp'
        api_m2m_display = { "door_group": "door_name", "emp": "PIN.EName" }#多对多字段导出显示关联表的字段。PIN.EName 将默认显示 PIN EName（中间为空格）
        query_fields = ('level_name', 'level_timeseg__timeseg_name')
        search_field = ('level_name', 'level_timeseg')#过滤器
        newadded_column = {'door_group': 'get_doors', 'emp': 'get_emps', 'emp_count': 'get_emp_count' }#需要在changlist中添加一列时，将list_display中的字段名和该模型的方法组成一个字典即可
        disabled_perms = ['clear_acclevelset', 'dataimport_acclevelset', 'view_acclevelset', 'dataexport_acclevelset']
        hide_perms = ["opaddemptolevel_acclevelset", "opdelempfromlevel_acclevelset"]
        #select_related_perms = {"browse_acclevelset": "opaddemptolevel_acclevelset"}
        opt_perm_menu = { "opaddemptolevel_acclevelset":"iaccess.EmpLevelByLevelPage", "opdelempfromlevel_acclevelset":"iaccess.EmpLevelByLevelPage" }
        default_give_perms = ["contenttypes.can_EmpLevelReportPage", "contenttypes.can_EmpLevelSetPage"]

    class Meta:
        app_label = 'iaccess'
        db_table = 'acc_levelset'
        verbose_name = _(u'门禁权限组')
        verbose_name_plural = verbose_name

def data_pre_check(sender, **kwargs):
    oldObj = kwargs['oldObj']
    model = kwargs['model'] 
    request = sender

    if model == AccLevelSet:
        pk = request.POST.get("pk", 0)#0 or None
        if pk == 'None':
            pk = 0

        door_group = request.POST.getlist("door_group")
        timeseg = request.POST.get("level_timeseg", 0)#不为空故！=0
        objs = AccLevelSet.objects.filter(level_timeseg=int(timeseg))
        for obj in objs:
            if obj.id != int(pk):
                doors = obj.door_group.all()
                if map(int, door_group) == [door.id for door in doors]:
                    raise Exception(_(u'已添加过时间段和门组合完全相同的两个权限组，请重新添加！'))

data_edit.pre_check.connect(data_pre_check)#不同于pre_save

#处理权限组
def DataPostCheck(sender, **kwargs):
    oldObj=kwargs['oldObj']
    newObj=kwargs['newObj']
    request=sender
    if isinstance(newObj, AccLevelSet):
        try:
            if oldObj:  #修改权限组
                #logmsg？
                if oldObj.door_group_set!= newObj.door_group_set:     #权限组修改变动
                    #print "door_group change"
                    accdev=[]
                    for  door in oldObj.door_group_set:
                        if door not in newObj.door_group_set:
                            accdev.append(door.device)
                    for door in newObj.door_group_set:
                        if door not in oldObj.door_group_set:
                            accdev.append(door.device)
                    dev=list(set(accdev))
                    
                    t = threading.Thread(target = TThreadComm(sync_level_door_edit,(dev, request.session.session_key)))
                    t.start()
                elif oldObj.level_timeseg != newObj.level_timeseg:
                    #print "level_timeseg diff", newObj.door_group_set, oldObj.door_group_set
                    devs=[]
                    for door in newObj.door_group_set:
                        if door.device not in devs:
                            devs.append(door.device)

                    t = threading.Thread(target = TThreadComm(sync_level_timeseg_edit,(devs, request.session.session_key)))
                    t.start()
        except:
            import traceback;traceback.print_exc()

data_edit.post_check.connect(DataPostCheck)
