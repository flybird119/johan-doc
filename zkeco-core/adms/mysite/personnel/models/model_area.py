#! /usr/bin/env python
#coding=utf-8
from django.db import models
from base.models import CachingModel
from base.operation import Operation,ModelOperation
from django.utils.translation import ugettext_lazy as _
from depttree import DeptTree, ZDeptChoiceWidget
from dbapp.data_utils import filterdata_by_user
from base.middleware import threadlocals


class Area(CachingModel):
    areaid=models.CharField(max_length=20,verbose_name=_(u'区域编号'),editable=True)
    areaname=models.CharField(max_length=30,verbose_name=_(u'区域名称'),editable=True)
    parent=models.ForeignKey("self",verbose_name=_(u'上级区域'),editable=True,null=True,blank=True)
    remark=models.CharField(max_length=100,verbose_name=_(u'备注'),null=True,blank=True,editable=True)
    
    def limit_parent_to(self, queryset):
        #根区域不存在上级区域.
        if self.pk == 1:
            from django.db.models.query import QuerySet
            return Area.objects.none()
        valid_areas = filterdata_by_user(queryset, threadlocals.get_current_user())
        if self.pk:
            invalid_pks = [self.pk]#限制不能设置一个区域的上级区域为其自身
            
            for a in Area.objects.all():
                if self in a.parents():#限制不能设置一个区域的上级区域为子区域
                    invalid_pks.append(a.pk)
            return valid_areas.exclude(pk__in=invalid_pks)
        else:
            return valid_areas
    
    
    def save(self):
        tmp=Area.objects.filter(areaid__exact=self.areaid)
        if self.areaid and len(tmp)>0 and tmp[0].id!=self.id:
            raise Exception(_(u'区域编号已经存在!'))
        if self.id==1:self.parent=None
        super(Area,self).save()

    def delete(self):
        if self.id!=1:
            self.areaadmin_set.all().delete()
            super(Area,self).delete()
            
    @staticmethod
    def clear():
        for a in Area.objects.exclude(id=1): 
                a.delete()
#    class _clear(ModelOperation):
#            visible=False
#            help_text=_(u"清空区域") #删除选定的记录
#            verbose_name=u"清空区域"
#            def action(self):
#                for area in Area.objects.exclude(id=1): 
#                        area.delete()
    def get_user_count(self):
        verbose_name=_(u"该区域用户数")
        from model_emp import Employee
        return Employee.objects.filter(attarea__exact=self).count()    
    def __unicode__(self):
            if self.areaid:
                    return u"%s %s"%(self.areaid, self.areaname)
            else:
                    return u"%s"%self.areaname
    def export_unicode(self):
            return u"%s" % self.areaname
    
    def parents(self):
        ps = []
        area = self
        while area:
            try:
                area = Area.objects.get(id=area.parent_id)
                ps.append(area)
                if area == self: 
                    break;
            except:
                break
        return ps
    
    
    def children(self):
        return Area.objects.filter(parent=self)
                
    class _delete(Operation):
        help_text=_(u"撤消区域") 
        verbose_name=_(u"撤消区域")
        def action(self):
            if len(self.object.children())>0:
                    raise Exception,_(u'该区域还有下级子区域，不能撤消')
            from datetime import datetime
            dev=Area.device_set.related.model
            if len(dev.objects.filter(area=self.object))>0:
                raise Exception,_(u'该区域还有设备，不能撤消')

            if self.object.employee_set.all().count()>0:
                raise Exception,_(u'该区域还有人员，不能撤消')
            
            from django.conf import settings
            if "mysite.iaccess" in settings.INSTALLED_APPS:
                if Area.accmap_set.related.model.objects.filter(area=self.object).count() > 0:
                    raise Exception(_(u'该区域中已包含电子地图，不能撤消'))
 
            if self.object.id==1:
                raise Exception,_(u'根区域不能撤消')
            
            areaadmin= Area.areaadmin_set.related.model
            areaadmin.objects.filter(area=self.object).delete()
            self.object.delete()
            
    class Admin(CachingModel.Admin):
            sort_fields=["areaid"]
            app_menu="iclock"
            menu_group = 'iclock'
            menu_index=9990
            default_widgets={'parent': ZDeptChoiceWidget}
            adv_fields=['areaid','areaname','remark']
            list_display=['areaid','areaname','parent','remark']
            opt_perm_menu={"opadjustarea_area":"att.AttDeviceUserManage"}#{权限操作的名字（小写）:菜单的路径(app_menu.model)}
            disabled_perms = ["clear_area", "dataimport_area"]
            @staticmethod
            def initial_data(): #初始化时增加一个区域
                    if Area.objects.count()==0:
                            Area(areaname=u"%s"%_(u"区域名称"), areaid="1",parent=None).save()
                    pass
            
    class Meta:
            verbose_name=_(u'区域设置')
            verbose_name_plural=verbose_name
            app_label='personnel'
            
    class OpAdjustArea(ModelOperation):
          verbose_name=_(u"为区域添加人员")
          help_text=_(u'区域的调整,将会把该人员从所属原区域内的设备中清除掉，并自动下发到新区域内的所有设备中')  
          def action(self):
               from  mysite.personnel.models.model_emp import Employee
               #from mysite.iclock.models.dev_comm_operate import sync_delete_user,sync_set_user
               from mysite.iclock.models.model_cmmdata import adj_user_cmmdata,save_userarea_together
               import copy
               import datetime
               emps = self.request.POST.getlist('mutiple_emp')
               area =self.request.POST.getlist('AreaSelect')
               deptflag=self.request.POST.get('dept_all')
               if deptflag: #按部门选择
                  deptIDs=self.request.POST.getlist('deptIDs')
                  emps =Employee.objects.filter(DeptID__in=deptIDs)
               datalist=[] 
               print len(emps) #注意不能屏蔽掉~ 处理sqlserver2005的时候 为区域分配人员 仅分配100个人
               for i in emps:
                    if deptflag:
                        emp=Employee.objects.get(pk=i.pk)
                    else:
                        emp=Employee.objects.get(pk=i)
#                    if emp.check_accprivage():
#                        devs=emp.search_device_byuser()
#                        sync_delete_user(devs, [emp]) 
                    oldarea=["%s"%u.pk for u in emp.attarea.select_related()]
                    
                    empchange=emp.__class__.empchange_set.related.model()
                    empchange.UserID=emp
                    empchange.changepostion=4
                    empchange.oldvalue=",".join(["%s"%i for i in  emp.attarea.select_related().values_list('pk')] )         
                    empchange.newvalue=",".join(area)
                    empchange.changedate=datetime.datetime.now()
                    empchange.save()
                    
                    emp.attarea=tuple(area)
                    emp.save()
                    #新增下载人员信息    
                      
                    #sync_set_user(emp.search_device_byuser(), [emp]) 
                    
                    datalist.append(adj_user_cmmdata(emp,Area.objects.filter(pk__in=oldarea),emp.attarea.all(),True))
                    
                    
               save_userarea_together(Employee.objects.filter(pk__in=emps),Area.objects.filter(pk__in=area),datalist)

class AreaForeignKey(models.ForeignKey):
        def __init__(self, to_field=None, **kwargs):
                super(AreaForeignKey, self).__init__(Area, to_field=to_field, **kwargs)

class AreaManyToManyField(models.ManyToManyField):
        def __init__(self, *args, **kwargs):
                super(AreaManyToManyField, self).__init__(*args, **kwargs)
        
def update_dept_widgets():
        from dbapp import widgets
        if AreaForeignKey not in widgets.WIDGET_FOR_DBFIELD_DEFAULTS:
            from depttree import ZDeptChoiceWidget
            widgets.WIDGET_FOR_DBFIELD_DEFAULTS[AreaForeignKey]=ZDeptChoiceWidget
        if AreaManyToManyField not in widgets.WIDGET_FOR_DBFIELD_DEFAULTS:
            from depttree import ZDeptMultiChoiceWidget
            widgets.WIDGET_FOR_DBFIELD_DEFAULTS[AreaManyToManyField]= ZDeptMultiChoiceWidget
                
update_dept_widgets()



