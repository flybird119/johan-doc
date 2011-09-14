# -*- coding: utf-8 -*-

from base.cached_model import STATUS_PAUSED, STATUS_STOP
from constant import IP4_RE
from constant import MAX_TRANS_IN_QUEQE
from constant import REALTIME_EVENT, DEVICE_POST_DATA
import datetime
import time
from dbapp.utils import *
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import connections, IntegrityError, DatabaseError, models
from django.http import HttpResponse
from dataprocaction import append_dev_cmd
from dataprocaction import dev_update_firmware
from dataprocaction import getFW
from models import *
from models.modelproc import get_normal_card
from models.model_device import device_cmd
from mysite.personnel.models.model_emp import Employee,format_pin
from dbapp.file_handler import save_model_file
import os
from redis.server import check_and_start_queqe_server, queqe_server
from traceback import print_exc
from cmdconvert import std_cmd_convert
from models.model_devcmd import DevCmd
from mysite.iclock.models.dev_comm_operate import *
import time
try:
    import cPickle as pickle
except:
    import pickle

conn = connections['default']

''' 设备的请求日志 '''
import logging
logger = logging.getLogger()
hdlr = logging.FileHandler(settings.APP_HOME+"/tmp/dev_post.log")
formatter = logging.Formatter('%(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.NOTSET)

''' 得到当前系统数据库类型 '''
from base.django_utils import get_db_type
db_select = get_db_type()

from model_utils import get_employee
from commen_utils import normal_state, normal_verify, card_to_num, excsql, device_response

server_time_delta = datetime.datetime.now()-datetime.datetime.utcnow()

from conv_att import line_to_log
from conv_device import line_to_oplog

from mysite.utils import fwVerStd
up_version = fwVerStd(settings.UPGRADE_FWVERSION)

from conv_device import update_device_sql,get_device,check_device,sync_dev,check_sync_devs,check_and_save_cache,cdata_get_options, parse_dev_info
from conv_emp import cdata_get_pin

def write_data(raw_data, device=None,Op=None):
    '''
    解析暂存的设备命令
    将设备发送的数据解析保存到数据库
    '''
    import UrlParas
    head_data, raw_data=raw_data.split("\n",1)
    stamp_name, head=head_data.split(": ")
    stamp_name=stamp_name[1:]
    head=dict([item.split("=",1) for item in head.split("\t")])
    if device is None:
        device=get_device(head['SN'])
    msg=None
    c=0
    ec=0
    if stamp_name=='log_stamp': #-------Stamp
        c, ec, msg=UrlParas.cdata_post_trans(device, raw_data, head,head_data)
    elif stamp_name=='oplog_stamp': #----OpStamp
        c, ec, msg=UrlParas.cdata_post_userinfo(device, raw_data,Op, head)
    elif stamp_name=='FPImage':
        c=UrlParas.cdata_post_fpimage(device, raw_data, head)    #---FPImage
    if msg is not None: #---写入上传记录日志表
        try:
            DevLog(SN=device, Cnt=c, OP=stamp_name, ECnt=ec, Object=msg[:20], OpTime=datetime.datetime.now()).save(force_insert=True)
        except:
            print_exc()
    return (c, ec+c, msg)

TRANS_QUEQE='TRANS'
#---设备可能的各种时间戳映射字典
STAMPS={'Stamp':'log_stamp', 'OpStamp': 'oplog_stamp', 'FPImage':'FPImage', 'PhotoStamp':'photo_stamp'}




def cdata_post(request, device): 
    '''
    处理设备的POST请求
    涉及http参数: "raw_post_data"、stamp_name
    '''
    raw_Data = request.raw_post_data
    if not raw_Data:
        raw_Data = request.META['raw_post_data']
    logger.error(raw_Data)  #---把post数据记录到日志
    if settings.ENCRYPT:
        import lzo
        rawData = lzo.bufferDecrypt(raw_Data, device.sn)#---解密POST数据
    else:
        rawData = raw_Data
    
    ######################### 新加入的请求 api 接口区 ######################    
    #
    #
    #            在此 return 返回给设备的数据
    #
    #
    ########################## 新加入的请求 api 接口区 ######################
        
    #---时间戳及其他POST数据的整理
    stamp=None
    for s in STAMPS:
        stamp=request.REQUEST.get(s, None)
        if not (stamp is None):
            stamp_name=STAMPS[s]
            break
    if stamp is None:
        return "UNKNOWN"
    
    msg=None
    if stamp_name=='FPImage': 
        head_data=":%s: SN=%s\tIP=%s\tTIME=%s\tPIN=%s\tFID=%s\tFPImage=%s"%(stamp_name, str(device.sn).strip(),
            request.META["REMOTE_ADDR"], datetime.datetime.now(),
            request.REQUEST["PIN"], request.REQUEST.get("FID",0), request.REQUEST['FPImage'])
    else:
        head_data=":%s: SN=%s\tIP=%s\tTIME=%s"%(stamp_name, str(device.sn).strip(),
            request.META["REMOTE_ADDR"], datetime.datetime.now())
    try:
        s_data="%s\n%s\n\n"%(head_data, rawData)
    except:
        s_data="%s\n%s\n\n"%(head_data, rawData)
    #---将命令类型头基本信息和POST数据的保存到文件缓存队列
    if settings.WRITEDATA_CONNECTION>0:
        #----写入到队列，后台进程在进行实际的数据库写入操作
        try:
            obj=""
            try:                
                from mysite.iclock.models.model_cmmdata import gen_device_cmmdata
                obj=gen_device_cmmdata(device,s_data)   #---将整理后的POST数据保存到文件
            except Exception, e:
                raise 
        except Exception, e:
            import traceback; traceback.print_exc()
            raise 
        c=1
    else:        
        c, lc, msg=write_data(s_data, device)
        
    if hasattr(device, stamp_name): setattr(device, stamp_name, stamp)
    device.save()   #---更新设备对象的相关属性
    return "OK:%s\n"%c

#设备读取配置信息、或者主动向服务器发送的数据
def cdata(request):
    '''
    设备向服务器的http:://xxx/cdata请求
    '''
    from device_http.network import network_monitor
    network_monitor(request)
    
    encrypt = 1
    response = device_response()
    try:
        resp = ""
        from mysite import authorize_fun
        language=request.REQUEST.get('language',None)   #---获得语言参数
        authorize_fun.check_push_device(language)   #---连接设备数量控制
        device = check_device(request, True)    #---检测、验证当前发出请求的设备
        if device is None: 
            response.write("UNKNOWN DEVICE")
            return response
        else:        
            if request.REQUEST.has_key('action'):
                resp += "OK\n"
            elif request.method == 'GET':   #---设备GET请求
                if request.REQUEST.has_key('PIN'):  #---带人员PIN参数
                    resp+=cdata_get_pin(request, device)
                else:   #--- 设备push的版本及其他一些信息的返回
                    alg_ver="1.0" #--- push 默认版本
                    if request.REQUEST.has_key('pushver'):  #---没有"PIN"但有"pushver" push版本参数
                        alg_ver=request.REQUEST.get('pushver')    #2010-8-25  device字段alg_ver用来区分新老固件  >=2.0为新固件，默认为旧固件
                    device.alg_ver=alg_ver
                    device.save()
                    resp+=cdata_get_options(device)
                    encrypt = 0
            elif request.method == 'POST':  #---设备POST请求
                try:
                    resp+=cdata_post(request, device)
                except Exception, e:
                    resp = u"ERROR: %s" % e
                    errorLog(request)
            else:
                resp += "UNKOWN DATA\n"
                resp += "POST from: " + device.sn + "\n"
            check_and_save_cache(device)
    except  Exception, e:
        errorLog(request)
        resp = u"%s" % e
    response["Content-Length"] = len(resp)
    response.write(resp)    #---返回服务器对设备的验证结果
    return response

from django.db import connection

def getreq(request):
    '''
    http://xxx/getrequest
    设备读取服务器上存储的命令------------------------------------------------------------------
    '''
    from device_http.network import network_monitor
    network_monitor(request)
    response = device_response()
    try:
        resp = "" #---要直接发送的内容
        device = check_device(request)  #---从请求得到设备对象  不自动注册
        if device is None: 
            response.write("UNKNOWN DEVICE")
            return response
        #读取服务器上存储的命令的请求都带有设备INFO信息  更新设备信息
        info = request.GET.get("INFO", "") #版本号，用户数,指纹数,记录数,设备自身IP地址
        if info:
            sql=[]
            info = info.split(",")
            device.fw_version=info[0]   #---主版本号
            device.user_count=int(info[1])  #---注册用户数
            device.fp_count=int(info[2])    #---注册指纹数
            device.fp_count=int(info[2])
            device.transaction_count=int(info[3])   #---考勤记录数
            if len(info)>4:
                device.ipaddress=info[4]    #---考勤机IP地址
                if device.alias=="auto_add":
                    device.alias=info[4]#由于网关问题，使名称对应的IP地址与机器IP不同时的更正。
            if len(info)>5:             
                device.Fpversion=info[5]   #指纹算法版本
            device.save()
            
        # 自动升级固件功能
        if not hasattr(device, "is_updating_fw"): #该设备现在没有正升级固件
            fw = fwVerStd(device.fw_version) 
            if fw: #该设备具有固件版本号
                up_version=device.get_std_fw_version() #用于升级的设备固件标准版本号
                if up_version>fw:   #该设备固件版本号较低
                    n=int(q_server.get_from_file("UPGRADE_FW_COUNT") or "0")
                    if n < settings.MAX_UPDATE_COUNT: #没有超出许可同时升级固件的范围
                        #升级固件
                        errMsg = dev_update_firmware(device)
                        if not errMsg: 
                            device.is_updating_fw=device.last_activity
                        if errMsg: #升级命令错
                            appendFile((u"%s UPGRADE FW %s:%s" % (device.sn, fw, errMsg)))
                        else:
                            q_server.incr("UPGRADE_FW_COUNT")
        upsql=[]
        c=0
        
        const_sql="update devcmds set CmdTransTime='%(tr)s',CmdReturn=%(cm)s where id=%(id)s"
        if db_select==4:#postgresql 数据库
            const_sql ='''update devcmds set "CmdTransTime"='%(tr)s',"CmdReturn"=%(cm)s where id=%(id)s'''
        elif db_select==3:#oracle 数据库
            const_sql="update devcmds set CmdTransTime=to_date('%(tr)s','yyyy-mm-dd hh24:mi:ss'),CmdReturn=%(cm)s where id=%(id)s"
      
        maxRet = device.max_comm_count  #---每次传送给设备的命令数
        maxRetSize = device.max_comm_size * 1024    #---最大数据包长度(KB)
        get_sql="select top "+ str(maxRet) +" id,CmdContent,CmdReturn from devcmds "
        get_sql+=" where SN_id="+str(device.pk)+" and (CmdTransTime is null or (CmdReturn <=-99996 and CmdReturn>-99999)) order by id "   

        if db_select==1:
            get_sql="select id,CmdContent,CmdReturn from devcmds "
            get_sql+=" where SN_id="+str(device.pk)+" and (CmdTransTime is null or (CmdReturn <=-99996 and CmdReturn>-99999)) order by id limit "+str(maxRet) 
        elif db_select==4:
            get_sql ='''select id,"CmdContent","CmdReturn" from devcmds '''
            get_sql+=''' where "SN_id"='''+str(device.pk)+''' and ("CmdTransTime" is null or ("CmdReturn" <=-99996 and "CmdReturn">-99999) ) order by id limit '''+str(maxRet) 
           
        elif db_select==3:
            get_sql="select id,CmdContent,CmdReturn from devcmds "
            get_sql+=" where SN_id="+str(device.pk)+" and (CmdTransTime is null or CmdReturn <=-99996 and CmdReturn>-99999)) and ROWNUM <= "+str(maxRet)+" ORDER BY ROWNUM ASC  " 
             
        dev_cur=conn.cursor()
        dev_cur.execute(get_sql)
        devcmds=dev_cur.fetchall()
        connection._commit()
        for d in devcmds:   #---循环要发送给设备的命令
            cr=d[2] #---命令返回值
            if cr:
                cr+=-1
            else:
                cr=-99996
            if cr<-99999:
                continue
            if db_select==3:
                CmdContent=d[1].read()
            else:
                CmdContent=d[1]
            if CmdContent.find("DATA UPDATE user")==0 or CmdContent.find("SMS ")==0: #传送用户命令,需要解码成GB2312
                cc=CmdContent
                try:
                    cc=cc.encode("gb18030")
                except:
                    try:
                        cc=cc.decode("utf-8").encode("gb18030")
                    except:
                        errorLog(request)
            else:                    
                cc=str(CmdContent)
            nowcmd=str(cc)
            cc=std_cmd_convert(cc, device)  #----ZK-ECO 标准命令到 PUSH-SDK 命令的转换
            if cc: resp+="C:%d:%s\n"%(d[0],cc)  #---格式: Ｃ:设备序列号:内容 \n

            c=c+1
            if db_select==1:
                excsql("update devcmds set CmdTransTime= now() ,CmdReturn="+str(cr)+" where id="+str(d[0]))
            elif db_select==3:
                excsql(const_sql%{"tr":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"cm":cr,"id":d[0]})
            else: 
                upsql.append(const_sql%{"tr":datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),"cm":cr,"id":d[0]})
            if (c>=maxRet) or (len(resp)>=maxRetSize): break;     #达到了最大命令数或最大命令长度限制
            if CmdContent in ["CHECK","CLEAR DATA","REBOOT", "RESTART"]: break; #重新启动命令只能是最后一条指令  #增加查找到CHECK指令后，直接发送
        if upsql:    
            excsql(";".join(upsql))
        if db_select==1:
            excsql("update iclock set last_activity=now() where id="+str(device.pk))
        elif db_select==3:
            excsql("update iclock set last_activity=to_date('"+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"','yyyy-mm-dd hh24:mi:ss') where id="+str(device.pk))
        else:
            excsql("update iclock set last_activity='"+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")+"' where id="+str(device.pk))
        if c == 0:#没有发送任何命令时，简单向设备返回 "OK" 即可
            resp += "OK"
    except  Exception, e:
        resp = u"%s" % e
        errorLog(request)
    if settings.ENCRYPT:    #---如果要加密
        import lzo
        resp = lzo.bufferEncrypt(resp + "\n", device.sn)
    response["Content-Length"] = len(resp)  #----向设备发送数据
    response.write(resp)
    return response

def check_upgrade_fw(device, cmdobj):
    '''
    固件升级相关
    '''
    if cmdobj.CmdContent.find("PutFile file/fw/") == 0 and cmdobj.CmdContent.find("main.") > 0: #it is an upgrade firmware command
        if hasattr(device, "is_updating_fw"): del device.is_updating_fw
        url, fname = getFW(device)
        q_server=check_and_start_queqe_server()
        q_server.decr("UPGRADE_FW_COUNT")
        diff = int(cmdobj.CmdReturn)-os.path.getsize(fname) #返回的文件字节数和实际的文件字节数比较
        if diff in [0, 1]: #升级成功, 有一旧版本的固件下载文件后会多出一个字节
            fname=os.path.split(fname)[1]
            if cmdobj.CmdContent.find("%s.tmp"%fname) > 0: #如果是下载固件到临时文件的话需要改名
                append_dev_cmd(device, "Shell mv %s.tmp /mnt/mtdblock/%s"%(fname, fname))
            append_dev_cmd(device, "REBOOT") #重新启动机器
        else:
            append_dev_cmd(device, cmdobj.CmdContent) #重新失败，重新发送升级命令
        q_server.connection.disconnect()

def check_upload_file(request, data):
    d = request.raw_post_data
    index = d.find("Content=")
    if not index: return
    d = d[index + 8:]
    if not d: return
    try:
        fname = data['FILENAME']
    except:
        fname = ""
    if not fname: return
    save_model_file(Device, "%s/%s-%s"%(data["SN"], fname, data['ID']), 
        d, "upload_file")

from commen_utils import parse_posts
        
from model_utils import update_cmd,update_cmds

#设备返回数据
def devpost(request):
    '''
    设备返回命令执行结果的请求
    '''
    response = device_response()
    resp = ""
    device = check_device(request)
    if device is None: 
        response.write("UNKNOWN DEVICE")
        return response
    try:
        rd = request.raw_post_data
        
        if settings.ENCRYPT:    #---解密
            try:
                import lzo
                rawData = lzo.bufferDecrypt(rd, device.sn)
            except:
                rawData = rd
        else:
            rawData = rd
            
        try:
            data0 = rawData.decode("gb18030")   #---解码
        except:
            data0 = rawData
            
        rets = {}
        pdata = parse_posts(data0)  #---解析,结果为字典的数组
        
        for apost in pdata:
            id = int(apost["ID"])   #---【字段】命令ID
            ret = apost["Return"]   #---【字段】命令执行结果
            if apost["CMD"] == "INFO":#--- 【字段】命令类别
                parse_dev_info(device, apost['Content'])
                rets[id] = ret
            elif apost['CMD'] == 'PutFile' and ret > 100 * 1024:  #可能是固件升级命令
                cmdobj = update_cmd(device, id, ret)
                if cmdobj: check_upgrade_fw(device, cmdobj, request)
            elif (apost["CMD"] == "GetFile" or apost["CMD"] == "Shell") and ret > 0:
                check_upload_file(request, apost)
                rets[id] = ret
            else:
                rets[id] = ret
        if len(rets) > 0:
            update_cmds(device, rets)
        resp += "OK"
        #check_and_save_cache(device)
        device.save()
    except:
        errorLog(request)
    response["Content-Length"] = len(resp)
    response.write(resp)
    return response

def post_photo(request):
    response = device_response()
    device = check_device(request)
    if device is None: 
        response.write("UNKNOWN DEVICE")
        return response
    try:
        pin = request.REQUEST.get("PIN","")
        
        pin = pin.split(".")[0].split("-")
        dt = pin[0]
        if len(pin) == 2: #Success Picture
            pin = pin[1]
        else:
            pin = ""
        d = request.raw_post_data
        if "CMD=uploadphoto" in d: d = d.split("CMD=uploadphoto")[1][1:]
        if "CMD=realupload" in d: d = d.split("CMD=realupload")[1][1:]
        save_model_file(Transaction,
            "%s/%s/%s" % (device.sn, dt[:4], dt[4:8])+"/"+ pin+"_"+ dt[8:] + ".jpg", 
            d, "picture")
        if request.REQUEST.has_key('PhotoStamp'):
            DevLog(SN=device, Cnt=1, OP=u"PICTURE", Object=pin, OpTime=datetime.datetime.now()).save()
            device.photo_stamp = request.REQUEST['PhotoStamp']
            device.save()
            
        check_and_save_cache(device)
    except:
        errorLog(request)
    response.write("OK\n")
    return response



def device_http_request(request):
    initialization()
    device = check_device(request, True)    #---检测、验证当前发出请求的设备
    if device is None: 
        response.write("UNKNOWN DEVICE")
        return response
    else:
        pass