# coding=utf-8

def getreq(request):
    '''
    设备读取服务器上存储的命令------------------------------------------------------------------
    '''
    from http_utils import device_response
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
            device.fw_version=info[0]
            device.user_count=int(info[1])
            device.fp_count=int(info[2])
            device.transaction_count=int(info[3])
            if len(info)>4:
                device.ipaddress=info[4]
                if device.alias=="auto_add":
                    device.alias=info[4]#由于网关问题，使名称对应的IP地址与机器IP不同时的更正。
            if len(info)>5:             
                device.Fpversion=info[5]   #新版本支持INFO时，算法版本提交
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