from service_utils import main, PythonService
import os

path=os.path.split(__file__)[0]

class ZKECOADMSService(PythonService):
    _svc_name_ = "ZKECOWEBService"
    _svc_display_name_ = "ZKECO Web Service"
    _svc_deps_ = []
    path = path
    cmd_and_args=["svr8000.pyc", ]
    def stop_fun(self, process):
        os.system("""taskkill /IM nginx.exe /F""")

if __name__=='__main__':
    main(ZKECOADMSService)
