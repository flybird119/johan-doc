#coding=utf-8
from mysite.personnel.models.depttree import dept_treeview
import datetime
from django import template
from django.conf import settings
from cgi import escape
from django.utils.translation import ugettext_lazy as _, ugettext
from django.core.cache import cache
from dbapp.data_utils import hasPerm
from django.utils.encoding import force_unicode, smart_str

register = template.Library()

@register.simple_tag
def dept_tree():
    '''
    部门展示树
    '''
    return dept_treeview()


