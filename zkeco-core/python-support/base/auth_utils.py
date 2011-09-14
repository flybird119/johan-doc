# coding=utf-8

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import User, Permission

from model_utils import model_owner_rel


def filter_data_by_user(query_set, user):
        '''
        API 目前暂无地方调用
        根据用户user的角色权限对记录集query_set进行过滤，返回过滤后的记录集
        '''
        model=query_set.model
        q=models.Q(pk__in=[])
        for ur in user_role.objects.filter(user=user): #检查该用户的所有角色
                f=model_owner_rel(ur.role.object_type.model, model) #得到该角色对应的对象数据查询条件
                if f:
                        q|=models.Q(**{f:ur.object_id})
        return query_set.filter(q)

def filter_data_by_user_and_perm(query_set, user, perm):
        '''
        API 目前暂无地方调用
        根据用户user的角色和权限对记录集query_set进行过滤，返回其中用户具有perm权限的记录集
        '''
        model=query_set.model
        ct=ContentType.objects.get_for_model(model)
        if isinstance(perm, Permission): 
                p=perm
        else:
                p=Permission.get(content_type=ct, codename=perm)
        q=models.Q(pk__in=[])
        for ur in user_role.objects.filter(user=user): #检查该用户的所有角色
                if p in ur.role.permissions.all():
                        f=model_owner_rel(ur.role.object_type.model, model) #得到该角色对应的对象数据查询条件
                        if f:
                                q|=models.Q(**{f:ur.object_id})
        return query_set.filter(q)

def get_change_fields(obj, user):
        '''
        API 目前暂无地方调用
        查询用户user可以编辑/改变obj一个对象的那些字段
        '''
        fields=[]
        ct=ContentType.objects.get_for_model(obj.__class__)
        for ur in user_role.objects.filter(user=user): #检查该用户的所有角色
                if is_owner(ur.role.object_type.model, ur.object_id, obj): #检查用户是否对拥有该对象的主体对象具有某种角色
                        rfs=role_object_property.objects.filter(role=ur.role, object_type=ct) #检查该角色的所有对象属性可见性
                        if rfs.count(): #定义过对该对象类型的可访问性
                                fields.append([r.property for r in rfs if r.change])
                        else: #没有定义过可访问性,则该对象的全部属性可用
                                fields.append(obj._meta.get_all_field_names())
        return tuple(fields)
    
    
def get_browse_fields(model, user, search=False):
        '''
        API 目前暂无地方调用
        查询一个用户user可以浏览/查看模型model的那些字段
        '''
        fields=[]
        ct=ContentType.objects.get_for_model(model)
        for ur in user_role.objects.filter(user=user): #检查该用户的所有角色
                rfs=role_object_property.objects.filter(role=ur.role, object_type=ct) #检查该角色的所有对象属性可见性
                if rfs.count(): #定义过该角色对该对象类型的可访问性
                        if search: 
                                fields.append([r.property for r in rfs if r.search])
                        else:
                                fields.append([r.property for r in rfs if r.view])
                else: #没有定义过可访问性,则检查该对象类型的所有者类型
                        m=is_parent_model(ur.role.object_type.model_class(), model)
                        if m: fields.append(m._meta.get_all_field_names())
        return tuple(fields)

def get_search_fields(model, user):
        '''
        API
        查询用户user可以搜索一个模型的那些字段
        '''
        return get_browse_fields(model, user, "search")
    
def auto_login(request):
        '''
        自动登录处理
        '''
        from django.contrib.auth import authenticate,login
        user = authenticate(username="admin", password="admin")
        login(request, user)
        
def GetModel(app_label, model_name):
        '''
        获取模型对象 本质为django的models.get_model
        '''
        dataModel=models.get_model(app_label,model_name)
        if not dataModel:
                dataModel=models.get_model("auth",model_name)
        if dataModel:   # Admin 成员的处理
                if not hasattr(dataModel, "Admin"): dataModel.Admin=None
        return dataModel