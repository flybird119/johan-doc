# -*- coding: utf-8 -*-
from ctypes import *
from ctypes.wintypes import LPCSTR
from random import *
from SoftKey import*
import socket
import os
import pyDes

prototype = WINFUNCTYPE(c_int, LPCSTR, c_short,c_int,LPCSTR)
paramflags = (1, "OutString"), (1, "Address"), (1, "Outlen"), (1, "KeyPath")
ReadString = prototype(("ReadString", windll.my3l_ex), paramflags)

prototype = WINFUNCTYPE(c_int, LPCSTR, c_short,LPCSTR)
paramflags = (1, "InString"), (1, "Address"),  (1, "KeyPath")
WriteString = prototype(("WriteString", windll.my3l_ex), paramflags)

SUCCESS="success"
FAIL="fail"
PLEASE_INSERT_DOG="please_insert_dog"
WRITE_ERROR="write_error"
READER_ERROR="read_error"
PLEASE_WRITE_NUMBER="please_write_number"
ZKECO=31#起始地址31~41存加密的字符串
ZKECO_LENGTH=30
ZKTIME=61#起始地址41~51加密的字符串
ZKTIME_LENGTH=30
ZKACCESS=91#起始地址51~61加密的字符串
ZKACCESS_LENGTH=30

MAC=121
MAC_LENGTH=50

OTHER=171#其他字符起始位置61~512
OTHER_LENGTH=341
LENGTH_EXCEED="length_exceed"#超出边界

def encrypt(encrypt_str):
    '''加密字符串'''
    key="llgmgpyw"
    k=pyDes.des(key,pyDes.CBC,"\0\0\0\0\0\0\0\0",pad=None,padmode=pyDes.PAD_PKCS5)
    encrypt_str=encrypt_str.encode("base64")
    ret=k.encrypt(encrypt_str)
    ret=ret.encode("base64")
    if ret[-1:]=="\n":
        ret=ret[:-1]
    return ret

def dencrypt(dencrypt_str,type=1):
    '''解密字符串'''
    key="llgmgpyw"
    k=pyDes.des(key,pyDes.CBC,"\0\0\0\0\0\0\0\0",pad=None,padmode=pyDes.PAD_PKCS5)
    ret=k.decrypt(dencrypt_str.decode("base64"))
    return ret.decode("base64")


def write_value(address,write_str):
    u'''以address为地址，向加密狗存储器中写入字符串write_str'''
    key_path=create_string_buffer('\0'*260)
    last_error = FindPort(0, key_path)
    ret=None
    if last_error==0:
        write_len = WriteString(str(write_str),address,key_path)
        if write_len<0:
            last_error=write_len
            ret=WRITE_ERROR+str(last_error)
        else:
            ret=SUCCESS
    else:
        ret=PLEASE_INSRT_DOG
    
    return ret
def write_device_length(write_str,address,length):
    u'''write_str应该加密'''
#    try:
#        if len(str(write_str))>length:
#            return LENGTH_EXCEED
#        tt=int(write_str)
#        write_str=str(write_str).zfill(length)
#    except:
#        return PLEASE_WRITE_NUMBER
    return write_value(address,write_str)
    
def write_zkeco(write_str):
    u'''写ZKECO数据,字节长度不能大于ZKECO_LENGTH'''
    return write_device_length(write_str,ZKECO,ZKECO_LENGTH)

def write_zktime(write_str):
    u'''写ZKTIME数据,字节长度不能大于ZKTIME_LENGTH'''
    return write_device_length(write_str,ZKTIME,ZKTIME_LENGTH)

def write_zkaccess(write_str):
    u'''写ZKACCESS数据,字节长度不能'''
    return write_device_length(write_str,ZKACCESS,ZKACCESS_LENGTH)

def write_mac(write_str):
    u'''写MAC数据,字节长度不能大于'''
    return write_device_length(write_str,MAC,MAC_LENGTH)

def init_usb_device_section():
    u'''初始化设备中各数据段的数据'''
    init_zkeco_data="".join(['\xff' for i in range(ZKECO_LENGTH)])
    ret=write_zkeco(init_zkeco_data)
    if ret!=SUCCESS:
        return ret
    
    init_zktime_data="".join(['\xff' for i in range(ZKTIME_LENGTH)])
    ret=write_zktime(init_zktime_data)
    if ret!=SUCCESS:
        return ret
    
    init_zkaccess_data="".join(['\xff' for i in range(ZKTIME_LENGTH)])
    ret=write_zkaccess(init_zkaccess_data)
    if ret!=SUCCESS:
        return ret
    
    init_mac_data="".join(['\xff' for i in range(MAC_LENGTH)])
    ret=write_mac(init_mac_data)
    if ret!=SUCCESS:
        return ret
    
    return SUCCESS
    
def write_other(write_str):
    u'''写其他数据'''
    return write_value(OTHER,write_str)

def read_value(address,length):
    u'''以address为地址，读取长度为length个字节的字符串'''
    key_path=create_string_buffer('\0'*260)
    last_error = FindPort(0, key_path)
    out_string=create_string_buffer('\0'*512)
    ret = None
    if last_error==0:
       last_error=ReadString(out_string,address,length,key_path)
       if last_error!=0:
            last_error=length
            ret=READER_ERROR
       else:
            ret=out_string.value.replace('\xff',"")
    else:
       ret=PLEASE_INSRT_DOG
    return ret

def read_zkeco():
    zkeco_length=0
    try:
        usb_str=read_value(ZKECO,ZKECO_LENGTH).replace('\xff',"")
        zkeco_length=int(dencrypt(usb_str))#解密
    except Exception,e:
        return FAIL
    return zkeco_length

def read_zktime():
    zktime_length=0
    try:
        usb_str=read_value(ZKTIME,ZKTIME_LENGTH).replace('\xff',"")
        zktime_length=int(dencrypt(usb_str))#解密
    except Exception,e:
        return FAIL
    return zktime_length

def read_zkaccess():
    zkaccess_length=0
    try:
        usb_str=read_value(ZKACCESS,ZKACCESS_LENGTH).replace('\xff',"")
        zkaccess_length=int(dencrypt(usb_str))#解密
    except Exception,e:
        return FAIL
    return zkaccess_length

def read_mac():
    mac_length=0
    try:
        usb_str=read_value(MAC,MAC_LENGTH).replace('\xff',"")
        mac_length=dencrypt(str(usb_str))#解密
    except Exception,e:
        import traceback;traceback.print_exc();
        return FAIL
    return mac_length

def get_mac():
    sd=os.popen("ipconfig/all").read()
    lans=sd.split("Ethernet adapter")
    lns=[]
    for l in lans:
        ln=[str(s).strip() for s in l.split("\r\n")]
        lns.append(ln)
    dip=socket.gethostbyname(socket.gethostname())#获取主机IP地址
    ret=""
    findlns=[]
    for i in lns:
        mac=""
        find=False
        for p in i:
            p=p.split(":")
            if p[0].strip().find("Physical Address")!=-1:
                mac=p[1].strip()
                #print mac
            if p[0].strip().find("IP Address")!=-1 and p[1].strip()==dip:#根据网卡列表查找真实的mac地址
                ret=mac
                find=True
                break
        if find:
            break
    return ret

def check_mac():
    ret=read_mac()   
    if len(ret)==0:
        return True
    elif ret==get_mac().strip():
        return True
    return False
        
def login_check(request,client_language):
    u'''登入验证'''
    from django.utils.translation import ugettext_lazy as _
    import locale
    from django.conf import settings
    from mysite.iclock.models import Device
    
    #客户浏览器的语言(FireFox,S...)，或者客户浏览器的系统的语言（IE)
    #zktime8.0非中文版本如果没有加密狗设置为20台
    DEVICE_TIME_RECORDER = 1 #考勤设备类型
    DEVICE_ACCESS_CONTROL_PANEL = 2 #门禁设备类型
    
    if CheckKey()==1:#有狗
        if check_mac():
            settings.HAS_DOG=True
            zkeco_length=read_zkeco()
            zktime_length=read_zktime()
            zkaccess_length=read_zkaccess()
            if zkeco_length==FAIL or zktime_length==FAIL or zkaccess_length==FAIL:
                return u"%s"%_(u"软件狗初始化失败！")
            settings.ZKECO_DEVICE_LIMIT=zkeco_length
            settings.ATT_DEVICE_LIMIT=zktime_length
            settings.MAX_ACPANEL_COUNT=zkaccess_length
            qs=Device.objects.filter(device_type__in=[DEVICE_TIME_RECORDER,DEVICE_ACCESS_CONTROL_PANEL])
            qs_count=qs.count()
            if zkeco_length!=0:
                if qs_count>zkeco_length:
                    return u"%s"%_(u"ECO设备台数%(d1)s超过软件狗所允许的台数%(d2)s，请升级！")%{"d1":qs_count,"d2":zkeco_length}
            else:
                att_count=qs.filter(device_type=DEVICE_TIME_RECORDER).count()
                if att_count>zktime_length:
                    return u"%s"%_(u"ECO考勤设备台数%(d1)s超过软件狗所允许的台数%(d2)s，请升级！")%{"d1":att_count,"d2":zktime_length}
                acc_count=qs.filter(device_type=DEVICE_ACCESS_CONTROL_PANEL).count()
                if acc_count>zkaccess_length:
                    return u"%s"%_(u"ECO门禁设备台数%(d1)s超过软件狗所允许的台数%(d2)s，请升级！")%{"d1":acc_count,"d2":zkaccess_length}
            return True
        else:
            settings.HAS_DOG=False
            return u"%s"%_(u"未找到对应的加密狗。")
    else:#没有狗
        settings.HAS_DOG=False
        if client_language!="zh-cn" and locale.getdefaultlocale()[0]!="zh_CN":#国外
            settings.ZKECO_DEVICE_LIMIT=0
            settings.ATT_DEVICE_LIMIT=20
            settings.MAX_ACPANEL_COUNT=50
            att_count=Device.objects.filter(device_type=DEVICE_TIME_RECORDER).count()
            if att_count>20:
                return u"%s"%_(u"考勤设备台数%(d1)s超过系统所允许的台数%(d2)s，请升级！")%{"d1":att_count,"d2":20}
            acc_count=Device.objects.filter(device_type=DEVICE_ACCESS_CONTROL_PANEL).count()
            if acc_count>50:
                return u"%s"%_(u"门禁设备台数%(d1)s超过系统所允许的台数%(d2)s，请升级！")%{"d1":acc_count,"d2":50}
            return True
        else:#国内
            zkeco_length=settings.ZKECO_DEVICE_LIMIT=0
            zktime_length=settings.ATT_DEVICE_LIMIT=0
            zkaccess_length=settings.MAX_ACPANEL_COUNT=50
            qs=Device.objects.filter(device_type__in=[DEVICE_TIME_RECORDER,DEVICE_ACCESS_CONTROL_PANEL])
            att_count=qs.filter(device_type=DEVICE_TIME_RECORDER).count()
            if att_count>zktime_length:
                return u"%s"%_(u"ECO考勤设备台数%(d1)s超过系统所允许的台数%(d2)s，请升级！")%{"d1":att_count,"d2":zktime_length}
            acc_count=qs.filter(device_type=DEVICE_ACCESS_CONTROL_PANEL).count()
            if acc_count>zkaccess_length:
                return u"%s"%_(u"ECO门禁设备台数%(d1)s超过系统所允许的台数%(d2)s，请升级！")%{"d1":acc_count,"d2":zkaccess_length}
            return True
def check_push_device(language):
    '''
    设备第一次请求时加设备处理
    根据语言参数、不同类型的设备设置不同的数量限制
    '''
    import locale
    from django.conf import settings
    if not settings.HAS_DOG:#---没有狗
        if language:#---有语言参数的机器
            if language!=u'83':#---国外
                settings.ZKECO_DEVICE_LIMIT=0
                settings.ATT_DEVICE_LIMIT=20
                settings.MAX_ACPANEL_COUNT=50
            else:#---国内
                settings.ZKECO_DEVICE_LIMIT=0
                settings.ATT_DEVICE_LIMIT=0
                settings.MAX_ACPANEL_COUNT=50
        else:#---以前的无语言参数的机器
            if locale.getdefaultlocale()[0]=="zh_CN":
                settings.ZKECO_DEVICE_LIMIT=0
                settings.ATT_DEVICE_LIMIT=0
                settings.MAX_ACPANEL_COUNT=50
            else:
                settings.ZKECO_DEVICE_LIMIT=0
                settings.ATT_DEVICE_LIMIT=20
                settings.MAX_ACPANEL_COUNT=50
    else:#---有狗
        pass
def datalist_check(request):
    u'''列表验证'''
    from django.conf import settings
    if CheckKey()==1:
        b=YSetValue(-123)
        if b!=-123:
            return FAIL
        c=compare(123,12345678,'<')
        if c!=True:
            return FAIL
        return SUCCESS
    else:
        return FAIL
    return PLEASE_INSERT_DOG
#def can_get_datalist(request):
#    u'''列表是否验证通过'''
#    ret=datalist_check(request)
#    if ret==PLEASE_INSERT_DOG or ret==SUCCESS:
#        return True
#    else:
#        return False
#print can_get_datalist(None)
def dataoperation_check(request):
    u'''操作验证'''
    if CheckKey()==1:
        d=Ystrcpy(u'zhongguo')
        if d!=u"zhongguo":
            return FAIL
        e=Ystrcat(u'123woddee',u'menabc')
        if e!=u"123woddeemenabc":
            return FAIL
        f=YCompareString('ABCDEFG','ABCDEFG')
        g=YAnd(1,0)
        if g:
            return FAIL
        h=Yor(1,0)
        if not h:
            return FAIL
        return SUCCESS
    else:
        return FAIL
    return PLEASE_INSERT_DOG

#def can_operate(request):
#    u'''能否操作'''
#    ret=dataoperation_check(request)
#    if ret==PLEASE_INSERT_DOG or ret==SUCCESS:
#        return True
#    else:
#        return False
#print can_operate(None)

