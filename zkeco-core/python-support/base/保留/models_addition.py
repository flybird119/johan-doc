# -*- coding: utf-8 -*-
'''
定义AdditionData model 用于记录数据对象的创建 实现操作日志记录
'''
from django.db import models
from django.core.cache import cache
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import smart_unicode
from model_admin import ModelAdmin, CACHE_EXPIRE

class AdditionData(models.Model):
    '''
    用于cached_model 的记录的日志记录
    继承自django 本身的Model 将不能在app里显示
    '''
    create_time = models.DateTimeField(_(u'创建时间'), auto_now=True)
    user = models.ForeignKey(User, verbose_name=_(u"用户"), null=True)
    content_type = models.ForeignKey(ContentType, verbose_name=_("对象类型"), blank=True, null=True)
    object_id = models.CharField(_(u'对象ID'), max_length=100, blank=False, null=False)
    key = models.CharField(_(u'键'), max_length=64, blank=False)
    value = models.CharField(_(u'值'), max_length=128, blank=True)
    data = models.TextField(_(u'数据'), blank=True)
    delete_time = models.DateTimeField(null=True, blank=True, editable=False)
    class Admin(ModelAdmin):
            list_display=('create_time|fmt_datetime','user|obj_url','content_type|content_type_str', 'object_repr|content_url:item', 'value', 'data')
            list_filter=('action_time', 'user', 'content_type')
            read_only=True
            menu_index=10000
    class Meta:
            verbose_name = _(u'增加的数据')
            ordering = ('-create_time',)

    def __unicode__(self):
            return u"[%s]%s: %s %s"%(self.action_time, self.user, self.get_action_flag_display(), self.object_repr)

    def get_edited_object(self):
            "Returns the edited object represented by this log entry"
            print 'johan------------------------------6.14 17:05: get_edited_object'
            return self.content_type.get_object_for_this_type(pk=self.object_id)

    
