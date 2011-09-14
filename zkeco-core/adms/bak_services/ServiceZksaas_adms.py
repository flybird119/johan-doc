from service_utils import main, DjangoService
import os
import sys


path=os.path.split(__file__)[0]

class ZksaasAdmsService(DjangoService):
    _svc_name_ = "ZKECOZksaasAdmsService"   #---服务名称
    _svc_display_name_ = "ZKECO Zksaas ADMS Service"    #---显示名称
    _svc_deps_ = []
    path = path
    cmd_and_args=["zksaas_adms"]    #---命令参数
    
if __name__=='__main__':
    main(ZksaasAdmsService)
    