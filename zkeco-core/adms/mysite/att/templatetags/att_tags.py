#!/usr/bin/env python
#coding=utf-8
import datetime
from django import template
from base.options import options
from django.utils.translation import ugettext_lazy as _, ugettext
from django.core.cache import cache
from django.db import models
from django.utils.encoding import force_unicode, smart_str
from django.conf import settings

register = template.Library()

@register.filter
def AttExceptDesc(exceptID):
    from mysite.att.models import LeaveClass
    t=LeaveClass.objects.get(pk=exceptID)
    if t:
        return u"%s"%t.LeaveName
    else:
        return exceptID

