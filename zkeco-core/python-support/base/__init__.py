#coding=utf-8
'''
主体：扩展Django 内置的 Group, User, Permission 等几个模型
重要API：
    get_all_app_and_models(hide_visible_false=True)
    get_all_permissions(queryset=None)
'''

from django.contrib.auth.models import Group, User, Permission,Message
from django.contrib.contenttypes.models import ContentType
from models import CachingModel, InvisibleAdmin
from model_admin import ModelAdmin, CACHE_EXPIRE
from base.operation import Operation
from django.utils.translation import ugettext_lazy as _
from middleware import threadlocals 
from login_bio import OperatorTemplate
from models import AppOperation

import auth_extend

from model_utils import get_all_app_and_models, get_all_permissions

