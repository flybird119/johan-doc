# coding=utf-8
from django.http import HttpResponse

def device_response(msg=""):
    '''
    生成标准的设备通信响应头
    '''
    response = HttpResponse(mimetype='text/plain')  #文本格式
    response["Pragma"]="no-cache"                   #不要缓存，避免任何缓存，包括http proxy的缓存
    response["Cache-Control"]="no-store"            #不要缓存
    if msg:
        response.write(msg)
    return response