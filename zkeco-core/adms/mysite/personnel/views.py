# Create your views here.
#coding=utf-8
from models.model_dept import Department
from dbapp.utils import getJSResponse
from django.utils.encoding import smart_str
from base.model_utils import GetModel
from django.db.models import Q
from django.utils.simplejson  import dumps 
import datetime

def get_dept_tree_data(request):
    selected=request.REQUEST.getlist("K")
    selected=[int(item) for item in selected]
    level=request.REQUEST.get("LEVEL","1")
    root=request.REQUEST.get("root","1")
    try:
        root=int(root)
    except:
        root=None
        if level=='1': level=2
    from models import depttree
    html=depttree.DeptTree(Department.objects.all()).html_jtree(selected,root_id=root, next_level=int(level))
    return getJSResponse(html)

def getchange(request):
    from mysite.personnel.models import Employee    
    id=request.GET.get("k")
    u=Employee.objects.get(pk=id)
    data={}
    if u:
        data['dept']=int(u.DeptID_id)
        data['title']=u.Title and str(u.Title) or 0
        data['hiretype']=u.emptype and str(u.emptype) or 1
        data['attarea']=[int(i.pk) for i in u.attarea.all()]
    return getJSResponse(smart_str(data))

def funGetModelData(request,app_lable,model_name):
        from mysite.personnel.models.model_emp  import format_pin
        model=GetModel(app_lable,model_name)
        fields=request.REQUEST.get("fields","")
        userid=request.REQUEST.get("userid","")
        orgdept=request.REQUEST.get("orgdept","")
        para=dict(request.REQUEST)
        where={}
        for p in para:
                
                if p.find("__")>0:
                    t=p.split("__")
                    
                        
                    if p.find("__range")>0:
                        where[str(p)]=eval(para[p])
                    elif p.find("__in")>0:
                        where[str(p)]=para[p].split(",")
                    else:
                        where[str(p)]=para[p].decode("utf-8")                
                    
        #print where
        #print model
        if fields:
                fields=fields.split(",")
        if model:
                if userid:
                        data=model.objects.filter(id__in=userid)
                else:
                        data=model.objects.all()
                if where:
                        data=model.objects.filter(Q(**where))
                #print data
                if fields:
                        data=data.values_list(*fields)
                #print data
                xdata=[]
                i=0 
                while i<len(data):
                        tmpdata=data[i]
                        j=0
                        ndata=[]
                        while j<len(tmpdata):
                                #print type(tmpdata[j])
                                if type(tmpdata[j])==datetime.time:
                                        #print "1"
                                        ndata.append(tmpdata[j].strftime("%H:%M:%S"))
                                elif type(tmpdata[j])==datetime.date:
                                        ndata.append(tmpdata[j].strftime("%Y-%m-%d"))
                                else:
                                        ndata.append(tmpdata[j])
                                j+=1
                        xdata.append(ndata)
                        i+=1
                #print xdata
                if orgdept:
                    xdata=processdept(xdata)
                return getJSResponse(smart_str(dumps(xdata)))
        else:
                return NoFound404Response(request)
def processdept(xdata):
    first=0
    ret=[]    
    tmp=[]
    for d in xdata:
        if d[2]==None or d[2]==d[0]:
            ret.append(d)
        else:
            tmp.append(d)
    cur=0
    while cur<len(ret):
        xtmp=[]
        for i in tmp:
            if i[2]==ret[cur][0]:
                ret.append(i)
            else:
                xtmp.append(i)
        tmp=xtmp
        cur+=1
   # print ret
    return ret
