# -*- coding: utf-8 -*-
from mysite import settings
import os

#���� django ����
os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite.settings'

from django.contrib.auth.models import User
ad = User.objects.filter(username="admin")
ad[0].delete()
User.objects.create_superuser("admin", "admin@sina.com", "admin")
