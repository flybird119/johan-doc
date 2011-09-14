# coding=utf-8

from django.contrib.auth.models import Group, User, Permission,Message
from models import CachingModel, InvisibleAdmin
from login_bio import OperatorTemplate
from django.utils.translation import ugettext_lazy as _
from base.operation import Operation

#====================== auth 相关模型的Admin扩展 =======================
class BaseMenuAdmin(CachingModel.Admin):
    app_menu='base'
    menu_group = 'base'

class UserAdmin(BaseMenuAdmin):
    menu_index=101
    help_text=_(u'''新增本系统的用户''')    #----新增时的暗条信息
    list_filter=('username',)
        
class GroupAdmin(BaseMenuAdmin):
    menu_index=100
    query_fields=["name"]
    disabled_perms =["delete_group"]
    help_text=_(u'''角色是一组权限的集合''')

class PermissionAdmin(BaseMenuAdmin):
    menu_index=102
    visible=True

Group.Admin =GroupAdmin
User.Admin=UserAdmin
Permission.Admin=PermissionAdmin
Message.Admin=InvisibleAdmin

#========================= User 模型的相关扩展 ====================
class _delete(Operation):
        help_text=_(u"删除选定记录")
        verbose_name=_(u"删除")
        def action(self):
                if self.object.pk!=1:
                    self.object.delete()
                    
@staticmethod
def clear():
    for e in User.objects.all():
        if e.pk!=1:
            e.delete()

def get_user_template(self):
    user_obj = self#User.objects.all()
    if user_obj:
        t9 = OperatorTemplate.objects.filter(user=user_obj, fpversion=9)
        t10 = OperatorTemplate.objects.filter(user=user_obj, fpversion=10)
    if len(t10)>=len(t9):
        return _(u"%(f)s ") % {'f':len(t10)}
    else:
        return _(u"%(f)s ") % {'f':len(t9)}
    
User._delete = _delete
User.get_user_template=get_user_template
User.clear=clear
User._meta.verbose_name=_(u"用户")
User.Admin.list_display=('username', 'first_name', 'last_name','groups|detail_str','email', 'is_staff|boolean_icon','is_superuser|boolean_icon','date_joined|fmt_shortdatetime','last_login|fmt_shortdatetime','get_user_template')

#========================= Group 模型的相关扩展 ====================
class _GroupDel(Operation):
        help_text= _(u"删除选定记录")
        verbose_name=_(u"删除")
        def action(self):
            if len(User.objects.filter(groups=self.object))>0:
                    raise Exception,_(u'该角色正在使用,不能删除')
            else:
               self.object.delete() 

Group._delete = _GroupDel
Group._meta.verbose_name=_(u"角色")

#========================= Permission 模型的相关扩展 ====================
def permission_unicode(self):
    return _("%(name)s")%{'name':_(self.name)}

Permission.__unicode__=permission_unicode