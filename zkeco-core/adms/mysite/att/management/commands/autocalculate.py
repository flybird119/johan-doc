from django.conf import settings
if settings.DATABASE_ENGINE=='pool':
    settings.DATABASE_ENGINE=settings.POOL_DATABASE_ENGINE

from django.core.management.base import BaseCommand, CommandError
import os
import time
import sys
import datetime
from redis.server import check_and_start_queqe_server, queqe_server

class Command(BaseCommand):
    option_list = BaseCommand.option_list + ()
    help = "Automatic calculate attdance"
    args = ''

    def handle(self, *args, **options):
        from mysite.iclock.attcalc import auto_calculate#,send_msg
        import time
        
        
        yesterday=datetime.datetime.now().date()
        while True:
            try:   
                calculate_all=False
                t_now=datetime.datetime.now()
                #cal_time=datetime.datetime(t_now.year,t_now.month,t_now.day,3,0,0)
                
                if t_now.date()>yesterday:
                    calculate_all=True
                    yesterday=t_now.date()             
                auto_calculate(calculate_all)
                time.sleep(5)
            except:
                import traceback;traceback.print_exc()
        #send_msg()
            
