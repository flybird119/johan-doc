#coding=utf-8
from piston.handler import BaseHandler
from piston.resource import Resource
from piston.authentication import HttpBasicAuthentication, NoAuthentication
from piston.doc import documentation_view
from piston.utils import rc
from django.db import models
from dbapp.data_utils import QueryData, get_field_verbosename
import datetime
import sys
from mysite.urls import tmpDir, tmp_url
from django.utils.translation import ugettext_lazy as _
auth = HttpBasicAuthentication(realm='ZK-ECO API')

def get_auth(request):
    if request.user.is_authenticated():
        return NoAuthentication()
    else:
        return auth

class APIHandler(BaseHandler):
    def read(self, request, data_key):
        if data_key is None:
            if hasattr(self,'qs') and self.qs!=None:return self.qs
            qs, cl=QueryData(request, self.model)
            #print dict(request.GET)
            recordtype=int(request.GET.get('t', '1'))
            if recordtype==1:
                if qs.count()>10000:
                    qs, cl=QueryData(request, self.model)
                    return qs[:10000]
                return qs[:]
            elif recordtype==2:
                l=int(request.GET.get('l', '15'))
                p1=int(request.GET.get('p1', '1'))
                p2=int(request.GET.get('p2', '1'))
                if p1<=0:
                    p1=1
                if p2<=0:
                    p2=1
                return qs[(p1-1)*l:p2*l]
            else:
                s1=int(request.GET.get('s1', '1'))
                s2=int(request.GET.get('s2', '1'))          
                if s1<=0:
                    s1=1
                if s2<=0:
                    s2=1                                
                return qs[s1-1:s1+s2-1]
        return self.model.objects.get(pk=data_key)
    def delete(self, request, data_key=None):
        if data_key is None:
            qs, cl=QueryData(request, self.model)
            qs.delete()
        else:
            obj = self.model.objects.get(kp=data_key)
            obj.delete()
    def update(self, request, data_key=None):
        if data_key is None:
            qs, cl=QueryData(request, self.model)
            qs.update(**dict(request.POST))
        else:
            obj = self.model.objects.get(kp=data_key)
            for p in request.POST: 
                setattr(obj, p, request.POST[p])
            obj.save()

def api(request, app_label, model_name, data_key=None):
    '''
    模型api 直接视图  返回模型的所有记录数据
    '''
    model=models.get_model(app_label,model_name)
    return api_for_model(request,model,data_key)
    
def api_for_model(request, model, data_key=None,query_set=None):
    '''
    模型api 间接视图
    '''
    from dbapp.modelutils import default_fields
    try:
        fields=request.GET.get("fields", "")
        if fields:
            fields=fields.split(",")
        if len(fields)==0:
            fields=None
            if hasattr(model,'Admin'):                
                if model.Admin:
                    
                    if hasattr(model.Admin,'api_fields'): 
                        fields=model.Admin.api_fields
                    elif hasattr(model.Admin, "list_display"):
                        fields=model.Admin.list_display
            if not fields:
                fields=[isinstance(f, models.ForeignKey) and f.name+"_id" or f.name for f in model._meta.fields if f.name not in default_fields]
        else:
            of=fields
            if hasattr(model.Admin,'api_fields'): 
                of=model.Admin.api_fields            
            f=[i for i in fields if i.split("|")[0] in of]
            fields=f
        handler=type(str("_%s_%s_APIHandler"%(id(model.Admin), model.__name__)), (APIHandler, ), {
            'model':model,
            'fields': fields,
            'qs':query_set,
            }
        )
        return Resource(handler=handler, authentication=get_auth(request))(request, data_key)
    except UnicodeError:
        from django.http import HttpResponse  
        import traceback;traceback.print_exc();      
        return HttpResponse(u"%s"%_(u'导出的内容与选择的编码不符'))
    
def api_list(request,tmp_name):
    '''
    导出数据动作直接视图
    '''   
    from dbapp.utils import load_tmp_file
    from dbapp.models import create_model
    from dbapp.data_list import QSList 
    try:
        attrs, admin_attrs, data=load_tmp_file(tmp_name)
    except:
        raise Exception(u"%s"%_(u'导出超时，临时数据已经不存在!'))    
    meta_attrs={}
    rn=request.REQUEST.get('reporttitle','')
    if rn:
        meta_attrs['verbose_name']=rn       
    model=create_model(tmp_name.encode("utf-8"),meta_attrs=meta_attrs, base_model=models.Model, attrs=attrs, admin_attrs=admin_attrs)   #---构造模型
    return api_for_model(request,model,data_key=None,query_set=QSList(model,data))
    
class APIListHandler(BaseHandler):
    '''
    本文件中未用到
    '''
    allowed_methods = ('GET', )
    def read(self, request,data):        
        return data
    
class APICountHandler(BaseHandler):
    allowed_methods = ('GET', )
    def read(self, request):
        qs, cl=QueryData(request, self.model)
        return {'count': len(qs)}

def api_count(request, app_label, model_name):
    '''
    返回模型记录的行数
    '''
    model=models.get_model(app_label,model_name)
    handler=type(str("_%s_%s_APICounter"%(app_label, model_name)), (APICountHandler, ), { 'model':  model })
    return Resource(handler=handler, authentication=get_auth(request))(request)


from piston.emitters import HttpStatusCode, Mimer, Emitter

class ColumnEmitter(Emitter):
    head=False
    def render(self, request):
        from django.db.models.query import QuerySet
        seria = self.construct()
        title="table"
        heads="" 

        if isinstance(self.data, QuerySet):

            model = self.data.model
            fields=[('|' in f) and f.split("|")[0] or f for f in self.fields]
            heads=[get_field_verbosename(model, f, ".") for f in fields]
            title=model._meta.verbose_name
            self.cells = []
            for a in seria:
                cells_list = []
                for f in fields:
                    if f in a:
                        f_check = '.' in f and f.split('.')[0] or f
                        field=""
                        try:                            
                            field = model._meta.get_field(f_check)
                        except :
                            pass
                        if field:                                
                            if isinstance(field, models.fields.related.ManyToManyField):
                                m2m_field_display = hasattr(model,'Admin') and model.Admin.api_m2m_display[f] or ""#m2m要显示字段,多对多字段要导出必须在api_fields中配置要显示的字段（一个或多个，多个时用“ ”隔开显示）
                                m2m_field_verbose = []
                                for record in a[f]:
                                    d_list = []
                                    for d in m2m_field_display.split('.'):
                                        d_list.append(record[d])
                                    m2m_field_verbose.append(' '.join(d_list))
                                cells_list.append(','.join(m2m_field_verbose))
                            elif type(a[f])==dict and isinstance(field,models.fields.related.ForeignKey):
                                if u"%s"%a[f]['id']=='None':
                                    cells_list.append('')
                                else:
                                    if hasattr(field.rel.to,"export_unicode"):
                                        instance=field.rel.to.objects.get(id=a[f]['id'])
                                        if instance:
                                            cells_list.append(instance.export_unicode())
                                    else:
                                        cells_list.append(a[f])
                            else:                                
                                if a[f]==None:
                                    cells_list.append('')
                                else:
                                    if type(a[f])==dict and  u"%s"%(a[f]['verbose'])=='None':
                                        cells_list.append('')
                                    else:
                                        cells_list.append(a[f])
                                
                        else:
                            if a[f]==None :
                                cells_list.append('')
                            else:
                               if type(a[f])==dict and  u"%s"%(a[f]['verbose'])=='None':
                                  cells_list.append('')
                               else:
                                  cells_list.append(a[f])

                            
                    
                self.cells.append(tuple(cells_list))
            
        else:

            fields=self.fields or (self.data and self.data[0].keys() or [])
            self.cells=[tuple([a[f] or '' for f in fields if f in a]) for a in seria]
        

        self.head=heads
        rn=request.REQUEST.get("reportname",'')                
        title=rn and rn or title        
        self.title=title
        self.file_name="%s_%s"%(title, datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
        return self.render_data(request)

def csv_format(a):
    l=[]
    for item in a:
        t = type(item)
        if t==type(0): l.append("%s"%item)
        elif t == datetime.datetime: l.append("\"%s\""%(item.strftime("%Y-%m-%d %H:%M:%S")))
        elif t == type({}): l.append("\"%s\""%item['verbose'])
        else: l.append(u"\"%s\""%item)
    return u",".join(l)

class CSVEmitter(ColumnEmitter):
    """
    CSV emitter, understands timestamps  返回客户端CSV文件.
    """
    def render_data(self, request):
        filecode=request.REQUEST.get('filecode','gb18030')
        Emitter.register('csv', CSVEmitter, 'applicatioin/download; charset=%s'%filecode)
        lines=[csv_format(a) for a in self.cells]
        lines.insert(0, csv_format(self.head))
        return u"\r\n".join(lines).encode(filecode)
    
Emitter.register('csv', CSVEmitter)

def txt_format(a):
    l=[]
    for item in a:
        t = type(item)
        if t == type({}): 
            l.append(item['verbose'])
        else:
            if t == datetime.datetime: 
                p="%s"%(item.strftime("%Y-%m-%dT%H:%M:%S"))
            elif item is not None: 
                p=u"%s"%item
                p=p.replace("\t","\\t").replace("\r", "\\r").replace("\n","\\n")
            else:
                p=""
            l.append(p)
    return u"\t".join(l)

class TXTEmitter(ColumnEmitter):
    """
    TXT emitter 返回客户端Txt文本文件
    """
    def render_data(self, request):
        filecode=request.REQUEST.get('filecode','gb18030')
        Emitter.register('txt', TXTEmitter, 'text/plain; charset=%s'%filecode)
        lines=[txt_format(a) for a in self.cells]
        lines.insert(0, txt_format(self.head))
        return u"\r\n".join(lines).encode(filecode)
    
Emitter.register('txt', TXTEmitter)

def cell_format(a):
    l=[]
    for item in a:
        t = type(item)
        if t == datetime.datetime: 
            l.append("%s"%(item.strftime("%Y-%m-%d %H:%M:%S")))
        elif t == type({}): 
            l.append(u"%s"%item["verbose"])
        else: 
            l.append(u"%s"%(item or ""))
    return tuple(l)

def get_page_size(c):
    #(最大字符数，纸张尺寸名称，是否横向打印，每页行数)
    default_page_sizes=((130, 'A4', False, 41), 
        (200, "A4", True, 25),
        (300, "A3", True, 41),
    ) 
    for s in default_page_sizes:
        if s[0]>c: return s
    return default_page_sizes[-1] 
   
class PDFEmitter(ColumnEmitter):
    """
    PDF emitter 返回客户端PDF文件
    """
    def render_data(self, request):
        from report import Report, Paragraph, Spacer, Table
        from django.http import HttpResponseRedirect
        from mysite.urls import tmpDir, tmp_url
        cells=[cell_format(a) for a in self.cells]
        rn=request.REQUEST.get("reportname",'')
        
        title=rn and rn or self.title
        if self.head=="":
            heads=[k for k in self.data[0].keys()]
        else:
            heads=self.head
        file_name=u"%s_%s.pdf"%(title, datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
        filecode=request.REQUEST.get("fielcode",'gb18030')
        
        whs=colwidths = [len(i.encode(filecode)) for i in heads]
        wcells=[[len(item.encode("gb18030")) for item in line] for line in cells[:40]]
        wcells.insert(0, whs)
        chars_cnt=sum(wcs)
        page_size=get_page_size(chars_cnt)

        p=Report()
        p.set_page_size(page_size[1], page_size[2])
        allws=min(6, max(3.7, 2.85*(p.width-23)/chars_cnt)) #计算每个字符的最大可能宽度
        page_head=(Paragraph(title, p.style_title), )
        grid_head=[Paragraph(col_text, p.style_grid_head) for col_text in heads]
        p.colwidths=[(allws*item or 20) for item in wcs]
        p.grid_head_height=20
        p.row_height=15
        p.print_report(cells, page_size[3], grid_head, page_head, file_name=u"%s/%s"%(tmpDir(), file_name))
        f="/"+tmp_url()+file_name
        return HttpResponseRedirect(f.encode("utf-8"))
       
try:
    import report
    Emitter.register('pdf', PDFEmitter, 'application/pdf; charset=utf-8')
except:
    import traceback; traceback.print_exc()

        
def xls_format(a):
    l=[]
    for item in a:
        t = type(item)
        if t==type(0): l.append("%s"%item)
        elif t == datetime.datetime: l.append("%s"%(item.strftime("%Y-%m-%d %H:%M:%S")))
        elif t == type({}): l.append("%s"%item['verbose'])
        else: l.append(u"%s"%(item or ""))
    return l

class EXCELEmitter(ColumnEmitter):
    """
    Excel emitter   返回客户端Excel文件 
    """
    def render_data(self, request):
        import xlwt
        from django.http import HttpResponse,HttpResponseRedirect
        from mysite.urls import tmpDir, tmp_url
        rn=request.REQUEST.get("reportname",'')
        title=rn and rn or self.title
        sheet_name=u"%s_%s"%(title, datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
        
        if self.head=="":
            heads=[k for k in self.data[0].keys()]
        else:
            heads=self.head
        
        lines=[xls_format(a) for a in self.cells]
        lines.insert(0, xls_format(self.head))
        filecode=request.REQUEST.get('filecode','gb18030')#编码
        
        wb = xlwt.Workbook(encoding=u"%s"%filecode)
        ws = wb.add_sheet(sheet_name)
        
        row_index=0
        for row in lines:
            col_index=0
            for col in row:
                ws.write(row_index,col_index,col)
                col_index+=1
            row_index+=1
        filename="%(d1)s_%(d2)s.xls"%{
            "d1":u"%s"%title,
            "d2":datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        }
        wb.save(u"%s/%s"%(tmpDir(), filename))
        f="/"+tmp_url()+filename
        return HttpResponseRedirect(f.encode("utf-8"))
    
Emitter.register('xls', EXCELEmitter,"application/vnd.ms-excel; charset=utf-8")
