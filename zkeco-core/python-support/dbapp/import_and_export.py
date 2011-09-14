#coding=utf-8
from django.utils.translation import ugettext_lazy as _
from base.middleware import threadlocals
from django.http import HttpResponse,HttpResponseRedirect
from base.model_utils import GetModel
from django.contrib.contenttypes.models import ContentType
from django.utils import simplejson   
from django.template import Template,Context,loader,RequestContext,TemplateDoesNotExist
from utils import getJSResponse
from django.utils.encoding import smart_str
from datetime import datetime
from dbapp.enquiry import Enquiry
from django.shortcuts import render_to_response
from django.utils.encoding import smart_str
from django.db.models import ForeignKey
import xlrd
import sys
import codecs
from django.db.models import Q
from base.log import logger
from django.template.loader import render_to_string
from django.conf import settings


#uploadpath="c:\\upload\\"
uploadpath=settings.ADDITION_FILE_ROOT+"/"
filecoding={
    'gb18030':_(u"简体"),
    #'big5':_(u"繁体"),
    #'utf-8':_("UTF-8"),
    
}
def show_import(request,app_label,model_name):
    #tables={'Employee':_(u'人员表'),'department':_(u'部门表')}
    model=GetModel(app_label,model_name)
    tables={model._meta.module_name:model._meta.verbose_name}
    #tables[model_name]=model_name;
    #t=loader.get_template("import.html")
    #return HttpResponse(t.render(RequestContext(request,{
   #                    'tables':tables
   #                    }))
    from django.utils.translation.trans_real import get_language_from_request
    lang_code=get_language_from_request(request)
    return render_to_response('import.html', {'tables': tables,"lang_code":lang_code})

    
    
def get_importPara(request):                    #分析文件，并返回到前端
    tablename=""            #导入表名
    filetype=""             #文件类型   txt   xls   csv
    sparator=0              #分隔号    0智能查找    1 制表符    2   按分隔符 
    sparatorvalue=""        #分隔符
    headerflg=1             #文件内容是否含有标题
    headerln=1              #标题在文件中的行号
    recordln=2              #记录从第几行起
    filename=""             #保存上传文件的文件名
    tablename=""            #表名
    autosplit=[",",";",":","\t"," "]    #智能查找分隔符
    unicode_=""                  #字符编号
    file_obj=""
    fields=[]
    fieldsdesc=[]
    try:
        #获取导入参数
        data=dict(request.POST)
        #print data
        filetype=str(data["filetype"][0])
        sparator=int(data["sparator"][0])
        sparatorvalue=data["sparatorvalue"][0]
        headerflg=int(data["header"][0])
        headerln=int(data["headerln"][0])
        recordln=int(data["recordln"][0])
        unicode_=str(data["selectunicode"][0])
        
        tablename=str("".join(data["tablename"][0].split()))
        
        #print data
        
        #表字段及描述文字
        model,flds,rlfield=findAllFieldsAndModel(tablename)
        for f,v  in flds.items():
            fields.append(f)
            fieldsdesc.append(v)
        #获取文件
        file_obj = request.FILES.get('file', None)
    except:
        import traceback; traceback.print_exc()
        return HttpResponse(u"%s"%_(u"取文件参数错误"))
        
    if file_obj:
        
        op=threadlocals.get_current_user()
        
        dtstr=""
        dt=datetime.now()
        
        dtstr=str(dt.year)+str(dt.month)+str(dt.day)+str(dt.hour)+str(dt.minute)+str(dt.second)
        
        filename=op.username+dtstr+"."+filetype
        if filetype=='txt' or filetype=='csv':                               #txt csv文件处理
            try:
                
                print "Process txt or csv file......."
                
                stw=file_obj.file
                filedata=[]
                wr=file(uploadpath+filename,"w",)
                
                linedata=stw.readline()
                
                while linedata!="":
                    if linedata[:3]==codecs.BOM_UTF8:
                        linedata=linedata[3:]

                    filedata.append(str(linedata).decode(unicode_))
                    wr.write(linedata)
                    linedata=stw.readline()
                   
                wr.close()
                hdata=""
                ddata=""
                
                if len(filedata)==0:
                    return HttpResponse(u"%s"%_(u"文件内容为空!"))
                if headerflg and headerln:                    
                    hdata=filedata[int(headerln)-1]

                ddata=filedata[int(recordln)-1  ]           
                #智能查找分隔符
                
                colCount=0
                if int(sparator)==0:
                    for sp in autosplit:
                        
                        if len(ddata.split(sp))> colCount:                        
                            sparatorvalue=sp
                            colCount=len(ddata.split(sp))

                #分隔标题头和第一条记录
                if sparatorvalue!="":
                    ddata=ddata.split(sparatorvalue)
                    if headerflg and headerln:
                        hdata=hdata.split(sparatorvalue)
               
                #print hdata
                ret={}
                ret['tablename']=tablename
                ret['headdata']=hdata
                ret['recorddata']=ddata
                ret['fields']=fields
                ret['fieldsdesc']=fieldsdesc
                ret['filetype']=filetype
                ret['filename']=filename
                ret['sparatorvalue']=sparatorvalue
                ret['headln']=headerln
                ret['recordln']=recordln
                ret['unicode']=unicode_
                
                
                ret=simplejson.dumps(ret)
                                
                return HttpResponse(u"%s"%ret)
            except:
                import traceback; traceback.print_exc()
                return HttpResponse(u"%s"%_(u"处理txt文件出错!"))
            
        elif filetype=='xls':                       #xls文件处理
            try:
                print "Process xls file.........."
                stw=file_obj.file
                
                filedata=[]
                wr=file(uploadpath+filename,"w+b",)
                linedata=stw.read()
                wr.write(linedata)
                wr.close()
                
                
                ds=ParseXlsUxlrd(uploadpath+filename) #读XLS文件

                datash=[]
                
                for sh in range(len(ds)):             #智能查找SHEET数据
                    if len(ds[sh][1])>=0:
                        datash=ds[sh][1]
                        
                        break

                hdata=[]
                ddata=[]
                if datash:
                    if headerflg and headerln:
                        
                        for v in datash[ headerln-1]:
                            hdata.append(v[1])
                        #print hdata
                    if len(datash[1])>recordln:
                        
                        for v in datash[recordln-1]:
                            
                            ddata.append(v[1])
                        #print ddata
                
                ret={}
                ret['tablename']=tablename
                ret['headdata']=hdata
                ret['recorddata']=ddata
                ret['fields']=fields
                ret['fieldsdesc']=fieldsdesc
                ret['filetype']=filetype
                ret['filename']=filename
                ret['sparatorvalue']=sparatorvalue
                ret['headln']=headerln
                ret['recordln']=recordln
                ret['unicode']=unicode_
                ret=simplejson.dumps(ret)
                                
                return HttpResponse(u"%s"%ret)
                
            except:
                import traceback; traceback.print_exc()
                return HttpResponse(u"%s"%_(u"处理XLS文件错误!"))
            
        else:            
            return HttpResponse(u"%s"%_(u"上传文件类型未知!"))

    
    
    
def file_import(request):                   #文件导入处理
    filename=""
    filetype=""
    tablename=""
    sparatorvalue=","
    fields={}               #已选择字段列表
    target=[]               #目标文件列号
    errmode=1               #出错处理方式     1  跳过错误 继续处理     2  退出，并删除已导入记录
    headln=1
    recordln=2
    unicode_="utf-8"
    relatefield=[]
    relrecs=[]
    addrelate=1             #关联记录处理  1   自动增加       2  关键记录不存在，跳过当次记录,不增加关联记录
    
    data=dict(request.POST)
    #print data
    errmode=int(data["errmode"][0])
    filename=data["txtfilename"][0]
    filetype=data["txtfiletype"][0]
    sparatorvalue=data["sparatorvalue"][0]
    headln=int(data["headln"][0])
    recordln=int(data["recordln"][0])
    tablename=data["txttablename"][0]
    unicode_=data["unicode"][0].decode()
    addrelate=int(data["addrelate"][0])
    
    #查找字段列表，目标列号
    for n,v in data.items():
        if n.startswith("_chk_"):
            
            field=str(data["_select_"+ n[5:]][0]).decode(unicode_)
            fields[field]=int(n[5:])
    #查找模型
    model,flds,rlfield=findAllFieldsAndModel(tablename)
    objlist=[]
    Employee=GetModel("personnel","Employee")
    Department=GetModel("personnel","Department")
    error_list=[]
    
    try:
        if filetype=="txt" or filetype=="csv":
            fs=file(uploadpath+filename,"r")
            rec=fs.readline()
            ln=1
            while rec!="":
                try:
                    #logger.info(ln)
                    rec=rec.decode(unicode_)
                    if rec.endswith("\r\n"):
                        rec=rec[:len(rec)-2]
                    linedata=rec.split(sparatorvalue)
                    ltmp=[]
                    #logger.info("linedata:",linedata)
                    for l in linedata:
                        if l.startswith('"') and l.endswith('"'):
                            ltmp.append(u"%s"%l[1:len(l)-1])
                        else:
                            ltmp.append(u"%s"%l)
                    linedata=ltmp
                    currelobj=[]                                                                        #当前行外键实例列表
                    if len(linedata)>=len(fields.keys()):                                                #当前行记录不满足已选择字段
                        if ln>=recordln:                            
                            strwhere={}
                            upobj=""
                            isSave=True
                            try:
                                for tmpfld,tmpfldvalue in fields.items():
                                    rf=""
                                    if tmpfld.find(".")>0:
                                        for f in model._meta.fields:
                                            if isinstance(f,ForeignKey):
                                                if f.rel.to.__name__==tmpfld.split(".")[0]:
                                                    strwhere[str(f.name+"__"+tmpfld.split(".")[1]+"__exact")]=linedata[tmpfldvalue]
                                    else:   
                                        strwhere[str(tmpfld+"__exact")]=linedata[tmpfldvalue]
                                upobj=model.objects.filter(Q(**strwhere))
                            except Exception, e:
                                logger.error("%s"%e)
                            if upobj:
                                obj=upobj[0]
                            else:
                                obj=model()
                            for fld,value in fields.items():
                                relObj=""
                                isForeignKey=False
                                if fld.find(".")>0:                                                     #查找到需要保存关联字段
                                    print "find relate"
                                    for nkey,val in rlfield.items():                                 #查找关联记录,更新或创建,并保存
                                        if nkey.__name__==fld.split(".")[0]:
                                            strfilter={}
                                            for f  in fields:                                       #查找关联表多个相应的字段，并生成表达式
                                                if f.find(".")>0 :
                                                    if f.split(".")[0]==nkey.__name__:
                                                        tmpvalue=linedata[fields[f]]
                                                        #tmpvalue=tmpvalue.encode('utf-8')
                                                        strfilter[str(f.split(".")[1]+"__exact")]=tmpvalue
                                            
                                            if strfilter:
                                                relObj=nkey.objects.filter(Q(**strfilter))
                                            
                                            if len(relObj)<=0:                              #查找不到记录，生成新记录
                                                if addrelate!=1:
                                                   isSave=False
                                                   break     
                                                else:
                                                    relObj=nkey()                                        
                                                    for tfld in fields.keys():
                                                        if tfld.find(".")>0:
                                                            if tfld.split(".")[0]==nkey.__name__:
                                                                relObj.__setattr__(tfld.split(".")[1],linedata[fields[tfld]])
                                                    isForeignKey=True
                                                    relObj.save()
                                                    relrecs.append(relObj)
                                            else:
                                                isForeignKey=True
                                                relObj=relObj[0]
                                                
                                            currelobj.append(relObj)
                                            break
                                if not isSave:
                                    break                           #跳出当前行
                                            
                                tobj=""
                                fieldname=""
                                if isForeignKey:
                                    for f  in obj._meta.fields:    #查找字段是否是外键
                                        if isinstance(f,ForeignKey) and  f.rel.to.__name__==fld.split(".")[0]:
                                            for tobj in currelobj:
                                                if tobj==f.rel.to:
                                                    break        
                                            fieldname=f.name
                                            break

                                    obj.__setattr__(fieldname,tobj)
                                else:
                                    if fld=="PIN":
                                        
                                        model_emp=sys.modules['mysite.personnel.models.model_emp']
                                        settings=sys.modules['mysite.settings']
                                        
                                        if len(str(linedata[value]).strip())>getattr(settings,"PIN_WIDTH"):
                                            raise Exception(u"%s"%_(u"人员编号长度过长"))
                                        else:
                                            linedata[value]=getattr(model_emp,"format_pin")(str(linedata[value]))
                                    if fld=="code":
                                        
                                        dept=Department.objects.filter(code=linedata[value])
                                        if dept:
                                            raise Exception(u"%s"%_(u'部门编号已存在'))
                                    obj.__setattr__(fld,linedata[value])

                            #logger.info("file Line:%s  save is %s "%(ln,isSave))
                            if isSave:
                                obj.save()
                                
                                if type(obj)==Employee:
                                   obj.__setattr__('attarea',(1,))
                                   obj.save()
                                if type(obj)==Department:
                                    if obj.parent==None or obj.parent=="":                                        
                                         obj.parent_id=1
                                         obj.save()
                                
                                objlist.append(obj)
                    ln+=1
                    rec=fs.readline()
                except Exception,e:
                    #logger.error("%s"%e)
                    try:
                        error_list.append(str(ln)+u" 行      "+u"%s"%e)
                    except:
                        error_list.append(str(ln))
                        pass
                    
                    if errmode==1:                        
                        ln+=1
                        rec=fs.readline()                       
                        continue
                    else:
                        raise
                
                
            fs.close()
            
        elif filetype=="xls":                                                           #xls文件
      
            sheetdata=ParseXlsUxlrd(uploadpath+filename)
            datash=sheetdata[0][1]
            for row in range(len(datash)):
                try:
                    if row>=recordln-1:
                        isSave=True
                        strwhere={}
                        upobj=""
                        try:
                            
                            for tmpfld,tmpfldvalue in fields.items():
                                rf=""
                                if datash[row][tmpfldvalue][0]==2:
                                    dv=int(datash[row][tmpfldvalue][1])
                                else:
                                    dv=datash[row][tmpfldvalue][1]
                                if tmpfld.find(".")>0:
                                    for f in model._meta.fields:
                                        if isinstance(f,ForeignKey):
                                            if f.rel.to.__name__==tmpfld.split(".")[0]:
                                                strwhere[str(f.name+"__"+tmpfld.split(".")[1]+"__exact")]=dv
                                else:   
                                    strwhere[str(tmpfld+"__exact")]=datash[row][tmpfldvalue][1]=dv
                            #print strwhere
                            #print(Q(**strwhere))
                            upobj=model.objects.filter(Q(**strwhere))
                        except Exception, e:
                            logger.error("%s"%e)
                        if upobj:
                            obj=upobj[0]
                        else:
                            obj=model()
                        currelobj=[]

                        for fld,value in fields.items():

                            relObj=""
                            isForeignKey=False
                            if fld.find(".")>0:                                                     #查找到需要保存关联字段

                                    #print "find relate"
                                for nkey,val in rlfield.items():                                 #查找关联记录,更新或创建,并保存
                                    if nkey.__name__==fld.split(".")[0]:
                                        strfilter={}
                                        for f  in fields:                                       #查找关联表多个相应的字段，并生成表达式
                                            if f.find(".")>0 :
                                                if f.split(".")[0]==nkey.__name__:
                                                    tmpvalue=datash[row][fields[f]][1]
                                                    #tmpvalue=tmpvalue.encode('utf-8')
                                                    strfilter[str(f.split(".")[1]+"__exact")]=tmpvalue
                                        if strfilter:
                                            relObj=nkey.objects.filter(Q(**strfilter))
                                        if len(relObj)<=0:                              #查找不到记录，生成新记录
                                            #print "not found"
                                            
                                            if addrelate!=1:
                                                isSave=False
                                                break                                                           #跳出当前行
                                            else:
                                                relObj=nkey()                                        
                                                for tfld in fields.keys():
                                                    if tfld.find(".")>0:
                                                        if tfld.split(".")[0]==nkey.__name__:
                                                            relObj.__setattr__(tfld.split(".")[1],datash[row][fields[tfld]][1])
                                                relObj.save()
                                                relrecs.append(relObj)
                                                isForeignKey=True
                                        else:
                                            isForeignKey=True
                                            relObj=relObj[0]
                                            #print "find: %s "%relObj.__doc__
                                        currelobj.append(relObj)
                                        break
                            if not isSave:
                                break                   #跳过当前行
                            tobj=""
                            fieldname=""
                            #print"%s:%s"%(fld,datash[row][value][1])
                            if isForeignKey:
                                for f  in obj._meta.fields:    #查找字段是否是外键
                                    if isinstance(f,ForeignKey) and  f.rel.to.__name__==fld.split(".")[0]:
                                        for tobj in currelobj:
                                            if tobj==f.rel.to:
                                                break        
                                        fieldname=f.name
                                        
                                        break
                                #print "%s :%s"%(fieldname,tobj.pk)
                                obj.__setattr__(fieldname,tobj)
                            else:
                                if datash[row][value][0]==2:
                                    cellvalue=int(datash[row][value][1])
                                else:
                                    cellvalue=datash[row][value][1]
                                #print "field :%s    value:%s"%(fld,cellvalue)
                                if fld=="PIN":
                                    
                                    model_emp=sys.modules['mysite.personnel.models.model_emp']
                                    settings=sys.modules['mysite.settings']
                                    
                                    if len(str(cellvalue).strip())>getattr(settings,"PIN_WIDTH"):
                                        raise Exception(u"%s"%_(u"人员编号长度过长"))
                                    else:
                                        cellvalue=getattr(model_emp,"format_pin")(str(cellvalue))
                                if fld=="code":
                                    
                                    dept=Department.objects.filter(code=cellvalue)
                                    if dept:
                                        raise Exception(u"%s"%_(u'部门编号已存在'))
                                    
                                obj.__setattr__(fld,cellvalue)
                        if isSave:
                            obj.save()
                            if(type(obj)==Employee):
                                
                                obj.__setattr__('attarea',(1,))
                                obj.save()
                            if(type(obj)==Department):
                                if obj.parent==None or obj.parent=="":                                        
                                     obj.parent_id=1
                                     obj.save()

                            objlist.append(obj)
                except Exception,e:
                    #logger.error("%s"%e)
                    try:
                        error_list.append(str(row+1)+u"%s"%_(u" 行      ")+u"%s"%e)
                    except:
                        error_list.append(str(row+1))
                        pass
                    if errmode==1:                      # 按错误处理方式处理数据
                        continue                        
                    else:
                        raise
        else:                                       #不合文件类型
            pass
        if error_list:
            
            if len(error_list)>10:
                return HttpResponse(u"%s"%_(u"处理第\n")+u"%s"%("\n".join(error_list[:10]))+u"%s"%_(u"\n...\n还有%s条未显示，其它行导入操作成功！")%(len(error_list)-10))
            else:
                return HttpResponse(u"%s"%_(u"处理第\n")+u"%s"%("\n".join(error_list))+u"%s"%_(u"\n出错，其它行导入操作成功！"))
       
        else:
            return HttpResponse(u"%s"%_(u"文件导入操作完成！"))
    except Exception, e:
        logger.error("%s"%e)
        if errmode==2:                  # 按错误处理方式处理数据
            j=0
            while j<len(objlist):                  #删除已保存记录
                objlist[j].delete()
            for ro in relrecs:          #删除关联表记录
                ro.delete()
        return HttpResponse(u"%s"%_(u"文件导入出错!"))
    

def ParseXlsUxlrd(upload):
    '''
    #变量：upload —— 用户上传的excel文件
    #返回：返回一个列表，每一项就是一个表单(sheet)；
    #      其中表单是一个二元组(表单名称,表单数据)；
    #      而表单数据可以直接当做一个“二维数组”来看待，
    #      数组的内容即为二维空间内分布的单元格数据
    #      具体到单元格数据仍为一个二元组(单元格类型，单元格值)
    #      假设ExtractXls的返回值为 sheets
    #      则范例excel文件中的表单数为 len( sheets )
    #        表单n的名称为 sheets[ n ][0]
    #        表单n的数据为 sheets[ n ][1]
    #        表单n的行数为 len( sheets[ n ][1] )
    #        表单n的列数为 len( sheets[ n ][1][0] )
    #        表单n的i行j列的单元格数据为 sheets[ n ][1][ i ][ j ]

    #备注：现在对于合并的单元格还不能判断，无法提供样式支持；
    '''

    import xlrd
    try:
      book = xlrd.open_workbook(upload)
    except xlrd.XLRDError:
      return 0 

    sheets = [ ]
    for n in range(book.nsheets):
        sheet = [ ]
        sh = book.sheet_by_index(n)
        sh_data = [ ]
        for i in range(sh.nrows):
            row = [ ]
            for j in range(sh.ncols):
                cell = [ ]
                cell.append( sh.cell_type(rowx=i, colx=j) )
                cell.append( sh.cell_value(rowx=i, colx=j) )
                row.append( cell )
            sh_data.append( row )
        sheet.append( sh.name )
        sheet.append( sh_data )
        sheets.append( sheet )
    return sheets

def findAllFieldsAndModel(tablename):
    enq=Enquiry(tablename)
    tb=enq.findAllRelationTables()                #根据表名生成模型实例
    model=tb[0]  

    relatefield={}                                #关联表与主表字段影射
    fields={}
    list_display=[]
    if hasattr(model,"Admin"):
        daf=[]
        if hasattr(model.Admin,"import_fields"):
            daf=model.Admin.import_fields
        else:
            daf=model.Admin.list_display
        if daf:            
            for f in daf:
                if f.find("|")>0:
                    f=f.split("|")[0]
                if f.find(".")>0 or f.find("__")>0:
                    if f.find(".")>0:
                        f=f.split(".")[0]
                    if f.find("__")>0:
                        f=f.split("__")[0]
                list_display.append(f)
    
    for fl in model._meta.fields:
        if fl.name in list_display:                
            if isinstance(fl,ForeignKey):            
                relatefield[fl.rel.to]=fl
            else:
                fields[fl.name]= u"%s"%fl.verbose_name
    for t,f in relatefield.items():
        x=[]
        if hasattr(t.Admin,"import_fields"):
            x=t.Admin.import_fields
        else:
            x=t.Admin.list_display
        
        for fl in x:
            if fl.find("|")>0:
                fl=fl.split("|")[0]
            if fl.find(".")>0 or fl.find("__")>0:
                if fl.find(".")>0:
                    fl=fl.split(".")[0]
                if f.find("__")>0:
                    fl=fl.split("__")[0]
            
            fl=t._meta.get_field(fl)
            if isinstance(fl,ForeignKey) and fl.rel.to==t:
                pass
            else:
                fields[t.__name__+"."+fl.name]=u"%s.%s"%(f.verbose_name,fl.verbose_name)
    return (model,fields,relatefield)
            
    

def show_export(request,app_label,model_name):
    '''
    导出界面视图
    '''
    models={}
    filetype={}
    template={}
    #models["Employee"]=_("Employee Table")
    #models["Department"]=_("Department Table")
    rn=request.REQUEST.get("reportname",'')    
    if app_label!="list":    
        models[model_name]=rn and rn or GetModel(app_label,model_name)._meta.verbose_name
    else:
        models[model_name]=rn and rn or model_name
    filetype["txt"]=_(u"TXT 文件")
    filetype["csv"]=_(u"CSV 文件")
    filetype["pdf"]=_(u"PDF 文件")
    filetype["xls"] = _(u"EXCEL 文件")
    #filetype["json"]=_("JSON File")
    template["stdemployee"]=_(u"标准的员工模板")
    template["smpemployee"]=_(u"简单的雇员的模板")
    template["stddepartment"]=_(u"指纹模板")
    template["standard"]=_(u"标准模板")
    tables={'Employee':_(u'人员'),'department':_(u'授权部门')}

    return render_to_response('export.html', {
            'models': models,
            'filetype': filetype,
            'template': template,
            'filecoding':filecoding,
            'model_name':model_name,
            })
    
def file_export(request,app_label,model_name):       
    
    exportpath=settings.ADDITION_FILE_ROOT+"/"
    #print exportpath
    filename=""
    filetype=""
    model=""
    templatename=""
    filecode=""
    viewname=""
    
    data=dict(request.POST)
    filetype=str(data["filetype"][0])
    model=str(data["model"][0])
    templatename=data["templatename"][0].decode("utf-8")
    filecode=str(data["filecode"][0])
    viewname=str(data["txtviewname"][0])
    op=threadlocals.get_current_user()
   
    dtstr=""
    dt=datetime.now()
   
    dtstr=str(dt.year)+str(dt.month)+str(dt.day)+str(dt.hour)+str(dt.minute)+str(dt.second)
    
    Displayfileds=""                                #导出字段列表,可从视图中提取,或定制
    data=[]
    tblname=""
    model=GetModel(app_label,model_name)
    if viewname:
        from viewmodels import get_view_byname_js
        Displayfileds =get_view_byname_js[viewname]["fields"]
        
        
    if filetype=='txt':
        try:
            if templatename=='stdemployee':
                tblname="emp"
                Displayfileds=["id","EName","Gender","DeptID"]
                data=Employee.objects.all().values_list(*Displayfileds).order_by("id")

            elif templatename=='smpemployee':
                Displayfileds=["id","EName","Gender","DeptID"]
                data=Employee.objects.all().values_list(*Displayfileds).order_by("id")
                tblname="emp"
            elif templatename=='stddepartment': 
                Displayfileds=["DeptID","DeptCode","DeptName","parent"]
                data=Department.objects.all().values_list(*Displayfileds).order_by("DeptID")
                tblname="dep"
            else:
                Displayfileds=[fl.name for fl in model._meta.fields]
                data=model.objects.all().values_list(*Displayfileds).order_by("id")
                tblname=model.__name__
            #print "%s"%data
            filename=op.username+dtstr+tblname+"."+filetype

            ret= render_to_string(templatename+".txt", {
                    'fields': Displayfileds,
                    'tdata': data,
                    })
            f=file(exportpath+filename,'w')
            f.write(ret.encode(filecode))
            f.close()
            #print ret
            response = HttpResponse(ret,mimetype='application/octet-stream')   
            response['Content-Disposition'] = 'attachment; filename=%s' % filename  
            return response  
            
            
#           return HttpResponseRedirect("/data/file/%s"%filename)
            
            
#            response = HttpResponse(mimetype='text/csv')
#            response['Content-Disposition'] = 'attachment; filename=%s' % filename
#            
#            t = loader.get_template(templatename+".txt")
#            c = Context({
#                'tdata': data,
#                'fields': Displayfileds,
#            })
#            response.write(t.render(c))
#            return response
            
        except:
            import traceback; traceback.print_exc()
    elif filetype=='xls':
        pass
    elif filetype=='pdf':
        pass
    else:
        pass

    
    return HttpResponse(u"%s"%_(u"文件导入操作完成！"))
    
