# coding=utf-8
'''
处理暂存的设备发过来的命令
'''

from django.conf import settings
if settings.DATABASE_ENGINE=='pool':
    settings.DATABASE_ENGINE=settings.POOL_DATABASE_ENGINE

from django.core.management.base import BaseCommand, CommandError
import sys
import datetime
import time
import os
import shutil
from traceback import print_exc
from django.utils.simplejson import dumps
from mysite import settings

def sort_files(fns):
    '''
    实现按文件名排序
    '''
    sf=[]
    ln=len(fns)
    for i in range(ln-1):
        j=i+1
        while j<ln:
            if t_e(fns[i])>t_e(fns[j]):
                tmp=fns[i]
                fns[i]=fns[j]
                fns[j]=tmp
            j+=1
def t_e(d):
    x=d.split(".")[0]
    if len(x)>17:
        return int((str(d).split("_")[0]+"000000")[:17])
    else:
        return int((x+"000000")[:17])
        
        
def process_data():    
    from mysite.iclock.models.model_device import Device
    from mysite.iclock.devview import write_data
    data=""
    devs=Device.objects.all()
    path=settings.C_ADMS_PATH+"new/"
    tnow=datetime.datetime.now()
    print tnow,"      device count: ",len(devs)
    for d in devs:  #-----循环所有设备
        try:        
            objpath=path%d.sn   #----将path中的待定量换成设备序列号
            if os.path.exists(objpath): #-----目录必须存在
                files=[] #----获取目录中的所有文件
                for f in os.listdir(objpath):                    
                    if os.path.isfile(objpath+f):
                        try:
                            files.append(f)
                        except:
                            pass
                if len(files)>1:                    
                    sort_files(files)
                for f in files: #----循环获得的所有文件
                    if os.path.exists(objpath+f):
                        process_flag=True
                        try:        
                            print "import data file '%s'"%(objpath+f)
                            fs=file(objpath+f,"r+")
                            data=fs.read();                    
                            fs.close()
                            write_data(data,d)  #-----处理动作 data：文件数据 d：设备
                        except:
                            process_flag=False
                            print_exc()
                        finally:
                            try:
                                f_dir=f[:8] #---根据文件名获取日期
                                cf_path=settings.C_ADMS_PATH+f_dir+"/"
                                cf_path=cf_path%d.sn
                                if not os.path.exists(cf_path):
                                    os.makedirs(cf_path)    #----创建处理失败的文件存储路径
                                if not process_flag:
                                    f="error_"+f
                                shutil.copy(objpath+f,cf_path+f)
                                os.remove(objpath+f)    #------将处理失败的文件转移到上面的目录
                            except:
                                print_exc()
                                pass
            else: #---- 设备数据文件目录不存在           
                pass
        except:
            import traceback;traceback.print_exc()
        time.sleep(0.1) #-----每处理一个设备暂停0.1秒
        
class Command(BaseCommand):
    option_list = BaseCommand.option_list + ()
    help = "Starts zksaas adms ."
    args = ''

    def handle(self, *args, **options):
        while True: #---无限循环
            try:
                process_data()
            except:
                import traceback;traceback.print_exc()
            time.sleep(5)   #每五秒执行一次
