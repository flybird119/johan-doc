# -*- coding: utf-8 -*-
'''
dbapp包：主要实现了通用数据管理
初始化：
实现扩展tags的注册
'''
import base

# 实现扩展tags的注册
from django.template import add_to_builtins
add_to_builtins('dbapp.templatetags.dbapp_tags')
add_to_builtins('base.templatetags.base_tags')

from dbapp.model_DbManage import DbBackupLog

