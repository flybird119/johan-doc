#coding=utf-8
'''
实现了对文件请求或保存操作
'''
from django.conf import settings
import os
from base.options import options

def get_model_filename(model, fname="", catalog=None):
        '''
        得到模型的文件存放的物理路径和url路径
        '''
        fname="model/%s/%s%s"%(\
                model._meta.app_label+'.'+model.__name__, 
                catalog and catalog+"/" or "",
                fname or "")
        print 'johan--------------------------6.13 17:34 get_model_filename:',(settings.ADDITION_FILE_ROOT+fname, settings.ADDITION_FILE_URL+"/"+fname)
        return (settings.ADDITION_FILE_ROOT+fname, settings.ADDITION_FILE_URL+"/"+fname)

def save_model_file(model, fname, raw_data, catalog=None, overwrite=True):
        '''保存表单模型中的文件数据 参数传入文件数据'''
        fns=get_model_filename(model, fname, catalog)
        fn=os.path.split(fns[0])
        try:
                os.makedirs(fn[0])
        except: pass
        f=file(fns[0], "w+b")
        f.write(raw_data)
        f.close()
        return fns[1]


def get_model_image(model, fname, catalog="photo", check_exist=False):
        '''
        获取表单模型中的图片 几种路径
        '''
        fns=get_model_filename(model, fname, catalog)
        fnst=get_model_filename(model, fname, catalog+"_thumbnail")
        if check_exist: 
                return (os.path.exists(fns[0]) and fns[0] or None, fns[1], 
                        os.path.exists(fnst[0]) and fnst[0] or None, fnst[1])
        return (fns[0], fns[1], fnst[0], fnst[1])
                
def save_model_image_from_request(request, requestName, model, file_name, catalog='photo'):
        '''
        保存 request 请求中存在的图片数据
        '''
        print "save_model_image_from_request"
        import StringIO
        from utils import create_thumbnail
        fns=get_model_filename(model, file_name, catalog)
        fname=fns[0]
        fn=os.path.split(fname)
        try:
                os.makedirs(fn[0])
        except: pass
        output = StringIO.StringIO()
        try:
                f=request.FILES[requestName]
        except:
                print requestName, request
                import traceback; traceback.print_exc()
                return None
        for chunk in f.chunks():
                output.write(chunk)
        output.seek(0)
        try:
                import PIL.Image as Image
        except Exception, e:
                import traceback; traceback.print_exc()
                f=file(fname, "w+b")
                f.write(output.read())
                f.close()
                return 200
        try:
                im = Image.open(output)
        except IOError, e:
                return getJSResponse("result=-1; message='Not a valid image file';")
        #print f.name
        size=f.size
        max_width=int(options["dbapp.max_photo_width"])
        if im.size[0]>max_width:
                width=max_width
                height=int(im.size[1]*max_width/im.size[0])
                im=im.resize((width, height), Image.ANTIALIAS)
        try:
                im.save(fname);
        except IOError:
                im.convert('RGB').save(fname)
        
        fns=get_model_filename(model, file_name, catalog+"_thumbnail")
        fn=os.path.split(fns[0])
        try:
                os.makedirs(fn[0])
        except: pass
        create_thumbnail(fname, fns[0])
        return size        


