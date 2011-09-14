# coding=utf-8
'''
解析操作命令转化为下发给设备的命令
'''

from django.conf import settings
if settings.DATABASE_ENGINE=='pool':
	settings.DATABASE_ENGINE=settings.POOL_DATABASE_ENGINE

from django.core.management.base import BaseCommand, CommandError
import os
import time
import sys
from mysite.iclock.constant import REALTIME_EVENT, DEVICE_POST_DATA
from mysite.iclock.devview import write_data
from redis.server import check_and_start_queqe_server, queqe_server

class Command(BaseCommand):
    option_list = BaseCommand.option_list + ()
    help = "Starts write data process."
    args = ''

    def handle(self, *args, **options):
		from mysite.iclock.models.model_cmmdata import process_writedata
		process_writedata()
