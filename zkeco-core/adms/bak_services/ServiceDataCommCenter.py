from service_utils import main, DjangoService
import win32serviceutil
import win32service
import win32event
import os
import sys
import time
import glob
from redis.server import queqe_server_path
from mysite.settings import APP_HOME
from mysite.utils import printf

CENTER_PROCE_LIST="CENTER_PROCE_LIST"

path=os.path.split(__file__)[0]

def killall_pid():
    try:
        fqpath="%s/_fqueue/"%(os.getcwd())
        q_server=queqe_server_path(fqpath)
        q_server.delete("CENTER_RUNING")
        main_pid=q_server.get(CENTER_MAIN_PID)
        os.system("taskkill /PID %s /F /T"%main_pid)   
        q_server.connection.disconnect()
    except:
        q_server.connection.disconnect()
    
def set_center_stop():
    fqpath="%s/_fqueue/"%(os.getcwd())
    printf("*********%s"%fqpath, True)
    q_server=queqe_server_path(fqpath)
    len=q_server.llen(CENTER_PROCE_LIST)
    printf("****************%d"%len)
    for i in range(0, len, 1):
        proce_name = q_server.lindex(CENTER_PROCE_LIST, i)
        proce_server_key="%s_SERVER"%proce_name
        printf("********%s"%proce_server_key)
        q_server.set(proce_server_key, "STOP")
    q_server.connection.disconnect()

def check_center_stop():
    fqpath="%s/_fqueue/"%(os.getcwd())
    fn="%s*_SERVER"%(fqpath)
    filelist=glob.glob(fn)
    printf("*********filelist=%s"%filelist)
    return len(filelist) != 0

def delete_server_key():
    fqpath="%s/_fqueue/"%(os.getcwd())
    q_server=queqe_server_path(fqpath)
    q_server.delete("CENTER_RUNING")
    q_server.connection.disconnect()
        
class ServiceDataCommCenter(DjangoService):
    _svc_name_ = "ZKECODataCommCenterService"
    _svc_display_name_ = "ZKECO Data Comm Center Service"
    _svc_deps_ = [""]
    path = path
    cmd_and_args=["datacommcenter"]
   
    def SvcStop(self):
        printf("*******ServiceDataCommCenter stop", True)
        set_center_stop()
        while check_center_stop():
            time.sleep(1)
        killall_pid()
        if check_center_stop():
            return
        delete_server_key() 
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        sys.stopservice = "true"
        win32event.SetEvent(self.hWaitStop)

if __name__=='__main__':
    main(ServiceDataCommCenter)
