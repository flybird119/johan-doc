# -*- coding: utf-8 -*-
from django.http import HttpResponse
from dbapp.utils import getJSResponse
from django.template import loader, RequestContext, Template, TemplateDoesNotExist
from django.shortcuts import render_to_response
from dbapp.data_utils import NoFound404Response
from base.model_utils import GetModel
from mysite.worktable.models  import InstantMsg,GroupMsg,UsrMsg,MsgType
import datetime
from base.middleware import threadlocals
from django.utils.translation import ugettext as _
from django.conf import settings
import os
from django.db.models import Q
from threading import Event, Semaphore
from django.utils.encoding import force_unicode
import json


def outputEmpStructureImage(request):
    '''
    人员组成结构图片数据视图
    '''
    import os
    from mysite.personnel.models.model_emp import Employee
    
    type= request.GET.get("t","1")
    try:
        if type=="1":
            qs = list(Employee.objects.filter(Hiredday__isnull=False))
            if len(qs)==0:
                return getJSResponse(json.dumps([]))
            curr_dt =datetime.datetime.now()
            curr_date = datetime.date(curr_dt.year,curr_dt.month,curr_dt.day)
            ten_years=0
            eight_years=0
            five_years=0
            three_years=0
            two_years=0
            one_years=0
            for e in qs:
                hire_date= datetime.date(e.Hiredday.year,e.Hiredday.month,e.Hiredday.day)
                if (curr_date -hire_date).days >=365 *10:
                    ten_years+=1
                elif (curr_date -hire_date).days >=365 *8:
                    eight_years+=1
                elif (curr_date -hire_date).days >=365 *5:
                    five_years+=1
                elif (curr_date -hire_date).days >=365 *3:
                    three_years+=1
                elif (curr_date -hire_date).days >=365 *2:
                    two_years+=1
                elif (curr_date -hire_date).days <365 *2:
                    one_years+=1
            if not qs:
                one_years=100
            data = [
                        {"label":_(u'十年 ') + str(ten_years),"data": [[0,ten_years]]},
                        {"label":_(u'八年 ')+str(eight_years), "data":[[0,eight_years]]},
                        {"label":_(u'五年 ')+str(five_years), "data":[[0,five_years]]}, 
                        {"label":_(u'三年 ') +str(three_years),"data":[[0,three_years]]},
                        {"label":_(u'两年 ')+str(two_years), "data":[[0,two_years]]},
                        {"label":_(u'一年 ')+str(one_years), "data":[[0,one_years]]}
                    ]

        elif type=="2":
             qs = list(Employee.objects.filter(Gender__isnull=False))
             if len(qs)==0:
                return getJSResponse(json.dumps([]))
             males= len(filter(lambda e: e.Gender=="M", qs))
             females = len(filter(lambda e: e.Gender=="F", qs))
             if not males and not females:
                return  getJSResponse(json.dumps([]))
             data = [
                        {"label":_(u'男 ') + str(males),"data":[[0,males]]},
                        {"label":_(u'女 ') +str(females) ,"data":[[0,females]] }
                    ]
        elif type=="3":
             emCounts = Employee.objects.count()
             qs = list(Employee.objects.filter(Education__isnull=False))
             if emCounts==0:
                return getJSResponse(json.dumps([]))
             t0= len(filter(lambda e: e.Education=="0", qs))
             t1= len(filter(lambda e: e.Education=="1", qs))
             t2= len(filter(lambda e: e.Education=="2", qs))
             t3= len(filter(lambda e: e.Education=="3", qs))
             t4= len(filter(lambda e: e.Education=="4", qs))
             t5= len(filter(lambda e: e.Education=="5", qs))
             t6= emCounts-t0-t1-t2-t3-t4-t5
             data = [
                        {"label" : u"%s"%_(u'小学 ')+str(t0),"data":[[0,t0]]},
                        {"label" : u"%s"%_(u'中学 ')+str(t1),"data":[[0,t1]]},
                        {"label" : u"%s"%_(u'高中 ')+str(t2),"data":[[0,t2]]},
                        {"label" : u"%s"%_(u'大学 ')+str(t3),"data":[[0,t3]]},
                        {"label" : u"%s"%_(u'研究生 ')+str(t4),"data":[[0,t4]]},
                        {"label" : u"%s"%_(u'博士 ')+str(t5),"data":[[0,t5]]},
                        {"label" : u"%s"%_(u'其他 ')+str(t6),"data":[[0,t6]]}
                    ]
                    
                    
        data.sort(lambda x1,x2:x1["data"][0][1]-x2["data"][0][1])
        return getJSResponse(json.dumps(data))
    except:
        import traceback; traceback.print_exc()
    finally:
        pass
    return getJSResponse(json.dumps([]))



def outputattrate(request):
    '''
    出勤率数据库视图
    '''
    json_data=[]
    try:
       from mysite.personnel.models.model_emp import Employee
       emCounts = Employee.objects.count()
       if emCounts==0:
           return getJSResponse(json.dumps([]))
       from mysite.iclock.models.model_trans import Transaction
       from mysite.att.models.model_empspecday import EmpSpecDay
       curr_dt= datetime.datetime.now()
       d1= datetime.datetime(curr_dt.year,curr_dt.month,curr_dt.day,0,0,1)
       d2= datetime.datetime(curr_dt.year,curr_dt.month,curr_dt.day,23,59,59)
       d3 = datetime.datetime(curr_dt.year,curr_dt.month,curr_dt.day)
       qs_atts_emp=Transaction.objects.select_related().filter(TTime__range=(d1,d2),UserID__isatt=True).distinct().values("UserID__PIN").values_list("UserID")
       #atts = Transaction.objects.select_related().filter(TTime__range=(d1,d2),UserID__isatt=True).distinct().values("UserID__PIN").count()
       atts=qs_atts_emp.count()
       specialDays = EmpSpecDay.objects.select_related() \
                    .filter(Q(end__gte=d3,start__lte=d3)
                            |Q(start__year=d3.year,start__month=d3.month,start__day=d3.day)
                            |Q(end__year=d3.year,end__month=d3.month,end__day=d3.day)
                        ) \
                    .exclude(emp__in=qs_atts_emp) \
                    .distinct().values("emp__PIN")  \
                    .count()
       absents= Employee.objects.count() -atts - specialDays
       json_data.append({
            "label":u"%s"%_(u'考勤 ')+ str(atts),
            "data":[[20,atts]]
       })
       json_data.append({
            "label":u"%s"%_(u'缺勤 ')+str(absents),
            "data":[[20,absents]]
       })
       json_data.append({
            "label":u"%s"%_(u'请假 ') + str(specialDays),
            "data":[[20,specialDays]]
       })
    
       json_data.sort(lambda x1,x2:x1["data"][0][1]-x2["data"][0][1])
       return getJSResponse(json.dumps(json_data))
    except:
        import traceback; traceback.print_exc()
    finally:
        pass
    return getJSResponse(json.dumps([]))


def set_msg_read(request,datakey):
    u=threadlocals.get_current_user()
    try:
        um=UsrMsg()
        um.user=u
        um.msg=InstantMsg.objects.filter(pk=datakey)[0]
        um.readtype="1"
        um.save()
        return getJSResponse('{ Info:"OK" }')
    except:
        import traceback; traceback.print_exc()
        return getJSResponse('{ Info:"exception!" }')

def get_instant_msg(request):
    '''
    即时信息数据视图
    '''
    from dbapp.data_viewdb import model_data_list
    from django.contrib.auth.models import User,Group
    from django.template.defaultfilters import escapejs
    from django.db.models import Q
    import json
    u=threadlocals.get_current_user()
    if u and u.is_anonymous():
        return getJSResponse(u"[]")
    d={}
    qs=None
    [SYSMSG,ATTMSG,IACCESSMSG,PERSONNELMSG]=[1,2,3,4 ]
    exclude_msgtype=[]
    if "mysite.att" not in settings.INSTALLED_APPS:
        exclude_msgtype.append(ATTMSG)
    if "mysite.iaccess" not in settings.INSTALLED_APPS:
        exclude_msgtype.append(IACCESSMSG)

    msgtypes=MsgType.objects.exclude(pk__in=exclude_msgtype)
    dt=datetime.datetime.now()
    dt=datetime.datetime(year=dt.year,month=dt.month,day=dt.day)

    #持续时间过滤条件
    querys=[]
    for elem in msgtypes:
        begin_date=dt-datetime.timedelta(days=elem.msg_keep_time)
        querys.append((Q(change_time__gte=begin_date)&Q(msgtype=elem)))
    combine_query=querys[0]
    for i in querys[1:]:
        combine_query|=i

    #不是超级管理员过滤条件
    if not u.is_superuser:
        ms=GroupMsg.objects.filter(group__user=u).values_list("msgtype")
        d["msgtype__in"]=ms

    #是否已读过滤条件
    has_read=UsrMsg.objects.filter(user=u).values_list("msg")

    qs=InstantMsg.objects.filter(**d).exclude(id__in=has_read)
    qs=qs.filter(combine_query).order_by("-pk")

    json_data={"fields":["id","msgtype","content","change_time"],"data":[]}
    for ee in qs:
        json_data["data"].append([ee.id,u"%s"%ee.msgtype,ee.content,ee.change_time.strftime("%Y-%m-%d")])

    return getJSResponse(json.dumps(json_data))
