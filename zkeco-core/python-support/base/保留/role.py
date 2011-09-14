# -*- coding: utf-8 -*-
from django.db import models
from django.core.cache import cache
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ObjectDoesNotExist
from cached_model import CachingModel
from base_code import base_code_by
from django.utils.translation import ugettext_lazy as _
from django import forms

from model_utils import is_parent_model
        
User._menu_index=400
Permission._visible=False

class RoleObjectProperty(CachingModel):
        """
        定义一个角色对其主体对象及其从属对象的属性（字段）的可访问性：改变、搜索、浏览/查看
        注意，为简化用户操作起见，一个角色如果没有对一个对象定义属性的可访问性，则具有全部属性的全部访问权限
        """
        role = models.ForeignKey("Role")
        change = models.BooleanField(_(u'能改变自己的财产'))
        view = models.BooleanField(_(u'可以查看该财产'))
        search = models.BooleanField(_(u'可以搜索的财产'))
        object_type = models.ForeignKey(ContentType, verbose_name=_(u'这个对象类型'), blank=True, null=True) #主体对象或从属对象
        property = models.CharField(_(u'财产,或者为对象'), max_length=40) #一个对象的属性名称
        class Admin(CachingModel.Admin):
                visible=True
                menu_index = 1001
        def __unicode__(self):
                return u"%s, %s.%s"%(self.role, self.object_type, self.property)
        def limit_object_type_to(self, queryset):
                #限制对象类型只能是 角色的主体对象及其从属对象
                if not self.role: return queryset
                qs=[]
                model=self.role.object_type.model_class()
                for ct in queryset:
                        if is_parent_model(model, ct.model_class()):
                                qs.append(ct.id)
                return queryset.filter(id__in=qs)


class Role(CachingModel):
        """
        定义主体对象类型上的角色及其权限范围
        例如，以部门表为主体对象类型，可以定义该部门下的“超级管理员”、“部门经理”、“人事管理员”、“考勤机管理员”等等
        这些管理员的操作权限都会被限定在一个特定部门内，主体对象的意思是这个对象所有的从属对象也会受到限制，比如由于员工对象属于特定的部门，因此某一角色的用户在对员工进行操作时，其权限也会限定在该部门的范围内
        """
        object_type = models.ForeignKey(ContentType, blank=True, null=True)
        name = models.CharField(_(u'角色姓名'),max_length=40, blank=False, null=False)
        permissions=models.ManyToManyField(Permission, verbose_name=_(u'权限'))
        class Admin(CachingModel.Admin):
                menu_index=1003
                children=[RoleObjectProperty,]
        def __unicode__(self): 
                return _("%(name)s for %(type)s")%{'name': self.name, 'type': self.object_type}
        def limit_permissions_to(self, queryset=None):
                #限制对象类型只能是 角色的主体对象及其从属对象
                if not self.object_type: return queryset
                qs=[]
                if not queryset: queryset=Permission.objects.all()
                model=self.object_type.model_class()
                for perm in queryset:
                        m=perm.content_type.model_class()
                        if m and is_parent_model(model, m):
                                qs.append(perm.id)
                return queryset.filter(id__in=qs)
        class Meta:
                verbose_name=_(u"角色")

class UserRole(CachingModel):
        """定义用户在某些对象上的角色"""
        user = models.ForeignKey(User, related_name="userroleuser")
        objects_filter = models.CharField(max_length=200) #对象查询条件，用户在满足该查询条件的对象上才具有指定角色
        role = models.ForeignKey(Role)
        class Admin(CachingModel.Admin):
                visible=True
                menu_index = 1002









