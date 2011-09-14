# -*- coding: utf-8 -*-

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