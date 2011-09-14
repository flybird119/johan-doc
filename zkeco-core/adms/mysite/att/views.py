# Create your views here.
#coding=utf-8
from base.models import AppOperation
from django.utils.translation import ugettext_lazy as _
from django.template import loader, RequestContext, Template, TemplateDoesNotExist
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import permission_required, login_required
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, InvalidPage
from mysite.iclock.datas import *
from dbapp.utils import getJSResponse
from django.utils.encoding import smart_str
from mysite.att.models.nomodelview  import forget,saveCheckForget,submitAttParam,attrule,shift_detail,worktimezone,assignedShifts,dailycalcReport,calcReport,calcLeaveReport
from django.utils.simplejson  import dumps 
from mysite.iclock.schedule import deleteShiftTime,deleteAllShiftTime,addShiftTimeTable,deleteEmployeeShift,FetchSchPlan,ConvertTemparyShifts
from mysite.att.models import *
from mysite.att.reports import reportindex
from base.model_utils import GetModel
from mysite.settings import MEDIA_ROOT
from django.db.models import Q
from dbapp.data_list import save_datalist
from dbapp.data_utils import *
from elreport import le_reprot

#from mysite.att.att_calculate.att_rule import LoadAttRule

def funGetShifts(request):
        nrun = NUM_RUN.objects.all().order_by('Num_runID')
        len(nrun)
        re = []
        ss = {}
        for t in nrun:
                ss['shift_id'] = t.Num_runID
                ss['shift_name'] = t.Name
                t = ss.copy()
                re.append(t)
        return getJSResponse(smart_str(dumps(re)))

def funTmpShifts(request):
        return ConvertTemparyShifts(request)

def funFetchSchPlan(request):
        return FetchSchPlan(request)
        
def funAssignedShifts(request):
        return assignedShifts(request)

def funDeleteEmployeeShift(request):
        return deleteEmployeeShift(request)

def funWorkTimeZone(request):
        return worktimezone(request)

def funAttrule(request):
        return attrule(request)
def funShift_detail(request):
        return shift_detail(request)
def funDeleteShiftTime(request):
        return deleteShiftTime(request)
def funDeleteAllShiftTime(request):
        return deleteAllShiftTime(request)
def funAddShiftTimeTable(request):
        return addShiftTimeTable(request)
def fundailycalcReport(request):
        return dailycalcReport(request)
    
def funCalcReport(request):
        return calcReport(request)
    
def funCalcLeaveReport(request):
        return calcLeaveReport(request)

def GenerateEmpPunchCard(request):
     from mysite.iclock.models.model_trans import Transaction
     import datetime
     cudt = datetime.datetime.now().strftime("%Y-%m-%d")
     
     d1=request.POST.get("starttime",cudt) + " 00:00:00"
     d2=request.POST.get("endtime",cudt) +" 23:59:59"
    
     empids = request.POST.get("empids")
     deptids =request.POST.get("deptids")
     sql ="""
     select a.badgenumber,a.name,b.checktime 
     from userinfo a inner join checkinout b on a.userid = b.userid 
     where b.checktime>='%s' and b.checktime<='%s' 
     """%(d1,d2)
     if empids:
        sql=sql+" and a.userid in (%s) "%(empids)
     if deptids and not empids:
            sql =sql + " and a.defaultdeptid in (%s) "%(deptids)
     sql = sql + " order by a.badgenumber,b.checktime "
     dts=[]

     d1_dt = datetime.datetime.strptime(request.POST.get("starttime",cudt),"%Y-%m-%d")
     d2_dt = datetime.datetime.strptime(request.POST.get("endtime",cudt),"%Y-%m-%d")
     diffdays = (d2_dt-d1_dt).days
     
     i =0
     while i<=diffdays:
         dts.append(d1_dt+datetime.timedelta(days=i))
         i+=1
     readybaseEmp=[]
     if empids:
        requiredAtt =Employee.objects.filter(isatt='1',id__in=empids).order_by("PIN").values_list("PIN","EName")
     elif deptids:
        requiredAtt =Employee.objects.filter(isatt='1',DeptID__in=deptids).order_by("PIN").values_list("PIN","EName")
     else:
        requiredAtt =Employee.objects.filter(isatt='1').order_by("PIN").values_list("PIN","EName")
     if not requiredAtt.count():
         tmp_name=save_datalist({"data":[],"fields":fields,"heads":header})
         return getJSResponse([[]])
     else:
         for i in requiredAtt:
              for dt_temp in dts:
                 l = list(i)
                 l.append(dt_temp.strftime("%Y-%m-%d"))
                 readybaseEmp.append(l)
     
     cs = connection.cursor()
     cs.execute(sql)
     data = cs.fetchall()
     datas=[]
     for row in data:
        datas.append(list(row))

     for item in datas:
         if item[2]:
             item.append(item[2].strftime("%Y-%m-%d"))
             item.append(item[2].strftime("%H:%M"))
             item.remove(item[2])
     
     i=0
     ii=len(datas)
     
     for emp in readybaseEmp:
         cc=  filter(lambda x:x[0]==emp[0] and x[2]==emp[2],datas)
         punchcarddetail = ",".join( [i[3] for i in cc])
         emp.append(punchcarddetail)
    
     fields=['badgenumber','name','checkdate','time']
     header0=[{'badgenumber':_(u'人员编号')},{'name':_(u'姓名')},{'checkdate':_(u'打卡日期')},{'time':_(u'打卡时间')}]
     header={'badgenumber':u'%s'%_(u'人员编号'),'name':u'%s'%_(u'姓名'),'checkdate':u'%s'%_(u'打卡日期'),'time':u'%s'%_(u'打卡时间')}
     headers= "["+",".join([u"'%s'"%i.values()[0] for i in header0])+"]"
    
     r={}
     datatotmp=[]
     for row in readybaseEmp:
          datatotmp.append({'badgenumber':row[0],'name':row[1],'checkdate':row[2],'time':row[3]})
     tmp_name=save_datalist({"data":datatotmp,"fields":fields,"heads":header})
    
     if len(readybaseEmp)==0:readybaseEmp.append([])
     try:
           offset = int(request.REQUEST.get(PAGE_VAR, 1))
     except:
           offset=1
     limit= int(request.REQUEST.get(PAGE_LIMIT_VAR, settings.PAGE_LIMIT))
     mnp=request.REQUEST.get(MAX_NO_PAGE, 0)
     if len(data)<=int(mnp):
        limit=int(mnp)
    
     paginator = Paginator(readybaseEmp, limit)
     item_count = paginator.count
     if offset>paginator.num_pages: offset=paginator.num_pages
     if offset<1: offset=1
     pgList = paginator.page(offset)
     cc={}
     cc["page_count"]=paginator.num_pages
     cc["record_count"]=item_count
     cc["page_number"]=offset
     cc["heads"] =headers
     cc["data"] =pgList.object_list
     cc["fields"]= fields
     cc["tmp_name"]=tmp_name
     return GenerateEmpPunchCardJsonData(request,cc)

def GenerateEmpPunchCardJsonData(request,data):
     temp="""{tmp_name:{% autoescape off %}"{{tmp_name}}"{% endautoescape %},heads:{% autoescape off %}{{heads}}{% endautoescape %},fields:{% autoescape off %}{{fields}}{% endautoescape %},page_count:{{page_count}},record_count:{{record_count}},page_number:{{page_number}},data:[{% for i in data %}\
             [""" +"\"{{i.0}}\"," + "\"{{i.1}}\"," +"\"{{i.2}}\","+"\"{{i.3}}\"]" \
             """{%if not forloop.last%},{%endif%}{% endfor %}]}"""
     cc = Context(data)
     d = Template(temp).render(RequestContext(request,cc))
     return getJSResponse(d)

@login_required
def funGetSchclass(request):
        schclasses = GetSchClasses()
        re = []
        ss = {}
        for t in schclasses:
                #print t
                ss['SchclassID'] = t['schClassID']
                ss['SchName'] = t['SchName']
                ss['StartTime'] = t['TimeZone']['StartTime'].time().strftime('%H:%M')
                ss['EndTime'] = t['TimeZone']['EndTime'].time().strftime('%H:%M')
                t = ss.copy()
                re.append(t)
                #print re
        return getJSResponse(smart_str(dumps(re)))
     
def funAttCalculate(request):
        '''
        考勤计算与报表
        '''
        return reportindex(request)
def funAttReCalculate(request):
    '''
    考勤统计的直接视图
    '''
    try:
        #from mysite.att.models.nomodelview  import reCaluateAction
        from mysite.iclock.attcalc import reCaluateAction
        
        return reCaluateAction(request)
    except:
        import traceback;traceback.print_exc()
def funAttParamSetting(request):
        '''
        获取考勤参数数据
        '''
        InitData()
        la = LoadAttRule()
        lc = LoadCalcItems()
        qs = la.copy()
        qs['LeaveClass'] = lc
        #print lc
        return getJSResponse(smart_str(dumps(qs)))
        
def SaveAttParamSetting(request):
        return submitAttParam(request)

def funForget(request):
        return forget(request)
        
def SaveForget(request):
    return saveCheckForget(request)
@permission_required("contenttypes.can_AttUserOfRun")
def funAttUerOfRun(request):
        from dbapp.urls import dbapp_url
        from base import get_all_app_and_models
        from mysite.att.models import USER_OF_RUN
        request.dbapp_url=dbapp_url
        apps=get_all_app_and_models()
        export=False
        export_name=USER_OF_RUN._meta.app_label+".dataexport_"+USER_OF_RUN.__name__.lower()
        return render_to_response('att_USER_OF_RUN.html',
                RequestContext(request,{
                        'dbapp_url': dbapp_url,
                        'MEDIA_URL':MEDIA_ROOT,
                        'position':_(u'考勤->员工排班'),
                        "current_app":'att', 
                        'apps':apps,
                        "help_model_name":"attUserOfrun",
        				"myapp": [a for a in apps if a[0]=="att"][0][1],
                        'menu_focus':'AttUserOfRun',
                        'export_perm':export_name,
                        })
                
                )
        
def funGetModelData(request,app_lable,model_name):
        from mysite.personnel.views import funGetModelData as fungetdata
        return fungetdata(request,app_lable,model_name)
    

@login_required
def funAttDeviceUserManage(request):
        from dbapp.urls import dbapp_url
        from base import get_all_app_and_models
        from mysite.personnel.models.model_area import Area
        request.dbapp_url =dbapp_url
        apps=get_all_app_and_models()
        if hasattr(Area,"get_all_operation_js"):
            actions=Area.get_all_operation_js(request.user)
        return render_to_response('att_DeviceUSERManage.html',
                RequestContext(request,{
                        'dbapp_url': dbapp_url,
                        'MEDIA_URL':MEDIA_ROOT,
                        "current_app":'att', 
                        'apps':apps,
                        "help_model_name":"DeviceUserManage",
        				"myapp": [a for a in apps if a[0]=="att"][0][1],
                        'specific_actions':actions,
                        'menu_focus':'AttDeviceUserManage',
                        'position':_(u'考勤->区域用户管理'),
                        })
                
                )


@login_required
def funAttDeviceDataManage(request):
       from dbapp.urls import dbapp_url
       from base import get_all_app_and_models
#       from mysite.personnel.models.model_area import Area
       request.dbapp_url =dbapp_url
       apps=get_all_app_and_models()
#       if hasattr(Area,"get_all_operation_js"):
#           actions=Area.get_all_operation_js(request.user)
       return render_to_response('att_DeviceDataManage.html',
               RequestContext(request,{
                       'dbapp_url': dbapp_url,
                       'MEDIA_URL':MEDIA_ROOT,
                       "current_app":'att', 
                       'apps':apps,
                       "help_model_name":"DeviceDataManage",
        			   "myapp": [a for a in apps if a[0]=="att"][0][1],
                       'app_label':'iclock',
                       'model_name':'Device',
                       'menu_focus':'AttDeviceDataManage',
                       'position':_(u'考勤->考勤设备管理'),
                       })
               
               )
def funGetAllExcept(request):
    from mysite.att.models import LeaveClass,LeaveClass1
    from mysite.att.models.model_leaveclass1    import LEAVE_UNITS
    ret={}
    ret['data']=[]
    l=LeaveClass.objects.all()
    for i in l:
        tmp=[]
        tmp.append(u"%s"%_(i.LeaveName))
        tmp.append(i.ReportSymbol)
        if i.Unit>=4 :
            tmp.append("")
        else:
            tmp.append(u"%s"%_(LEAVE_UNITS[i.Unit-1][1]))
        ret['data'].append(tmp)
    l=LeaveClass1.objects.all()
    for i in l:
        tmp=[]
        tmp.append(u"%s"%_(i.name))
        tmp.append(i.ReportSymbol)
        if i.Unit>=4 or i.pk in [1009,1008]:
            tmp.append("")
        else:        
            tmp.append(u"%s"%_(LEAVE_UNITS[i.Unit-1][1]))
        ret['data'].append(tmp)
    return getJSResponse(smart_str(dumps(ret)))


def funLEReport(request):
    '''统计每天第一次打卡与最后一次打卡'''
    return le_reprot(request)
