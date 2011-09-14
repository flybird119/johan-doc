#! /usr/bin/env python
#coding=utf-8
#from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext as _
from django.template import loader, RequestContext, Template, TemplateDoesNotExist
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import permission_required, login_required
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator, InvalidPage
from dbapp.utils import getJSResponse
from django.utils.encoding import smart_str
from django.utils.simplejson  import dumps 
from base.model_utils import GetModel
from mysite.settings import MEDIA_ROOT
from django.db.models import Q
from dbapp.data_list import save_datalist
from mysite.personnel.models import Employee
from mysite.iclock.models import Transaction
from basefield import get_base_fields
import datetime

def le_reprot_calculate(request,deptids,userids,st,et,totalall=False):
    '''
    根据传递过来的参数 来返回 考勤汇总
    '''
       
    if len(userids)>0 and userids!='null':#获取人
        ids=userids.split(',')
    elif len(deptids)>0:
        deptids=deptids.split(',')
        deptids=deptids
        ot=['PIN','DeptID']
        ids=Employee.objects.filter(DeptID__in=deptids,OffDuty__lt=1).values_list('id', flat=True).order_by(*ot)

    total_days=int((et-st).days)+1#总天数
    
    Result={}#定义返回的字典，也就是 传递到前台
    re=[]#储存每条记录数
    try:
        #分页        
        try:
            offset = int(request.REQUEST.get('p', 1))#获取分页信息
        except:
            offset=1
            #print "offset:%s"%offset
        uids=[]#储存人员信息
        k=0
        limit= int(request.POST.get('l', settings.PAGE_LIMIT)) 
        if not totalall:
#            limit= int(request.POST.get('l', settings.PAGE_LIMIT))  #导出时使用
            item_count =len(ids)*total_days #获取记录总数
            
            if item_count % limit==0:
                page_count =item_count/limit
            else:
                page_count =int(item_count/limit)+1            
                
            if offset>page_count and page_count:offset=page_count
             
#            ids=ids[(offset-1)*limit:offset*limit]#分页操作
            
            Result['item_count']=item_count#记录总数
            Result['page']=offset          #第几页
            Result['limit']=limit           #每页显示数
            Result['from']=(offset-1)*limit+1 #
            Result['page_count']=page_count  #总页数
        for u in ids:
            uids.append(u)
       
        r,Fields,Capt=get_base_fields()
        
        #print "Result['fieldnames']=",Fields
        Result['fieldnames']=Fields
        Result['fieldcaptions']=Capt
        Result['datas']=r
        date =st.date()
           
        for  emp in uids:
            checkdate=date
            for i in range(total_days):#遍历 这个人的 每天 数据
                r={'username': '', 'deptid': '', 'firstchecktime': '', 'userid': -1, 'badgenumber': '', 'latechecktime': ' ','date':'','week':'','deptname':''}
                
                y=int(checkdate.year)
                m=int(checkdate.month)
                int_d=int(checkdate.day)
                userid =int (emp)
                #  查找考勤记录         
                check = Transaction.objects.filter(UserID=userid,TTime__year=y,TTime__month=m,TTime__day=int_d).values_list("UserID__PIN","UserID__EName","UserID__DeptID__code","UserID__DeptID__name","TTime").order_by("TTime")
                if  not check:#如果没有考勤记录
                    emp_pin = Employee.objects.filter(pk=userid).values_list("PIN","EName","DeptID__code","DeptID__name")
                    r["badgenumber"]=emp_pin[0][0]
                    r["username"]=emp_pin[0][1]
                    r["deptid"]=emp_pin[0][2]
                    r["deptname"]=emp_pin[0][3]
                    r["firstchecktime"]=""
                    r["latechecktime"]=""
                else:
                    r["badgenumber"]=check[0][0]
                    r["username"]=check[0][1]
                    r["deptid"]=check[0][2]
                    r["deptname"]=check[0][3]
                    if len(check)==1:
                        r["firstchecktime"]=check[0][4].strftime("%Y-%m-%d %H:%M:%S")
                        r["latechecktime"]=""
                    if len(check)>=2:
                        r["firstchecktime"]=check[0][4].strftime("%Y-%m-%d %H:%M:%S")
                        r["latechecktime"]=check[len(check)-1][4].strftime("%Y-%m-%d %H:%M:%S")
                r["date"]=str(checkdate)
                xx=checkdate.weekday()
                if xx==0:
                    r["week"]=_(u"星期一")
                elif xx==1:
                    r["week"]=_(u"星期二")
                elif xx==2:
                    r["week"]=_(u"星期三")
                elif xx==3:
                    r["week"]=_(u"星期四")
                elif xx==4:
                    r["week"]=_(u"星期五")
                elif xx==5:
                    r["week"]=_(u"星期六")
                elif xx==6:
                    r["week"]=_(u"星期日")
               
                re.append(r)
                checkdate = checkdate +datetime.timedelta(days=1) 
        
        #分页数据
        
        if not totalall:
           re=re[((offset-1)*limit):(offset*limit)]
        
        Result['datas']=re
        return Result
    except:
        import traceback;traceback.print_exc()
    

def le_reprot(request):
    '''
    汇总最早与最晚计算报表
    '''
    deptids=request.POST.get('DeptIDs','')
    userids=request.POST.get('UserIDs','')
    st=request.POST.get('ComeTime','')
    et=request.POST.get('EndTime','')
    st=datetime.datetime.strptime(st,'%Y-%m-%d')
    et=datetime.datetime.strptime(et,'%Y-%m-%d')
    r=le_reprot_calculate(request,deptids,userids,st,et)
    loadall=request.REQUEST.get('pa','')
    if not loadall:
       objdata={}
       allr=le_reprot_calculate(request,deptids,userids,st,et,True)
    
       objdata['data']=allr['datas']
       objdata['fields']=allr['fieldnames']
       heads={}
       for i  in  range(len(allr['fieldnames'])):
           heads[allr['fieldnames'][i]]=allr['fieldcaptions'][i]
       objdata['heads']=heads
       tmp_name=save_datalist(objdata)
       r['tmp_name']=tmp_name#用于导出  没有这个字段导出报错。
       
    return getJSResponse(smart_str(dumps(r)))
    
    
    
    '''
        total_days=int((et-st).days)+1#总天数
        #    print et.date()
        #等到页面返回的数据
        #对人员及部门分开对待
        if len(userids)>0 and userids!='null':
            ids=userids.split(',')
        elif len(deptids)>0:
            deptIDS=deptids.split(',')
            deptids=deptIDS
            ot=['PIN','DeptID']
            ids=Employee.objects.filter(DeptID__in=deptIDS,OffDuty__lt=1).values_list('id', flat=True).order_by(*ot)

        Result={}
        limit= int(request.POST.get('l', settings.PAGE_LIMIT))  #每页显示 多少数据
        item_count =len(ids)*total_days #获取总人数*天数,
        #page_count=总数 除以每页数
        if item_count % limit==0:#page_count获取总页数
            page_count =item_count/limit
        else:
            page_count =int(item_count/limit)+1   
            
        try:
            offset = int(request.REQUEST.get('p', 1))
        except:
            offset=1

        if offset>page_count and page_count:
            offset=page_count
                 
        ids=ids[(offset-1)*limit:offset*limit]

        Result['item_count']=item_count
        Result['page']=offset
        Result['limit']=limit
        Result['from']=(offset-1)*limit+1
        Result['page_count']=page_count
        #    Result['tmp_name']=
        uids=[]
        for u in ids:
            uids.append(u)

        #    global get_base_fields
        r,FieldNames,FieldCaption=get_base_fields()
        #    {'username': '', 'deptid': '', 'firstchecktime': '', 'userid': -1, 'badgenumber'
        #    : '', 'latechecktime': ''} r
        loadall=request.REQUEST.get('pa','')
        #    r=[{'username': 'dawdaad', 'deptid': '22adw', 'firstchecktime': 'adadada', 'userid': -1, 'badgenumber'
        #      : '87878', 'latechecktime': 'dawdadad '}]
        if not loadall:
            objdata={}
            Result['fieldnames']=FieldNames
            Result['fieldcaptions']=FieldCaption
            Result['datas']=r
        #        objdata['fields']=Result['fieldnames']
        #        
        #        objdata['data']=Result['datas']
        #        heads={}
        #        for i  in  range(len(Result['fieldnames'])):
        #            heads[Result['fieldnames'][i]]=Result['fieldcaptions'][i]
        #        objdata['heads']=heads
        #        
        #        
        #        tmp_name=save_datalist(objdata)
        #        #            print  tmp_name,'tmp_name'
        #        Result['tmp_name']=tmp_name
            
        #    from mysite.iclock.models import Transaction
        datas=[]
        #取数据 封装成元祖。然后 加入到 返回对象 中去， 注意顺序。然后返回出来。

        date =st.date()

        for  emp in uids:
            for i in range(total_days):#遍历 这个人的 每天 数据
                r={'username': '', 'deptid': '', 'firstchecktime': '', 'userid': -1, 'badgenumber': '', 'latechecktime': ' ','date':'','deptname':''}
                y=int(date.year)
                m=int(date.month)
                int_d=int(date.day)
                userid =int (emp)
        #            r={'username': '', 'deptid': '', 'firstchecktime': '', 'userid': -1, 'badgenumber': '', 'latechecktime': ' '}
                check = Transaction.objects.filter(UserID=userid,TTime__year=y,TTime__month=m,TTime__day=int_d).values_list("UserID__PIN","UserID__EName","UserID__DeptID__code","UserID__DeptID__name","TTime").order_by("TTime")
        #            print personnel
                
                if  not check:
                    emp_pin = Employee.objects.filter(pk=userid).values_list("PIN","EName","DeptID__code","DeptID__name")
                    r["badgenumber"]=emp_pin[0][0]
                    r["username"]=emp_pin[0][1]
                    r["deptid"]=emp_pin[0][2]
                    r["deptname"]=emp_pin[0][3]
                    r["firstchecktime"]=""
                    r["latechecktime"]=""
                else:
                    r["badgenumber"]=check[0][0]
                    r["username"]=check[0][1]
                    r["deptid"]=check[0][2]
                    r["deptname"]=check[0][3]
                    if len(check)==1:
                        r["firstchecktime"]=check[0][4].strftime("%Y-%m-%d %H:%M:%S")
                        r["latechecktime"]=""
                    if len(check)>=2:
                        r["firstchecktime"]=check[0][4].strftime("%Y-%m-%d %H:%M:%S")
        #                    print 'sssss'
        #                    print  check[len(check)-1][4].strftime("%Y-%m-%d %H:%M:%S")
                        r["latechecktime"]=check[len(check)-1][4].strftime("%Y-%m-%d %H:%M:%S")
                r["date"]=str(date)
                datas.append(r)
                date = date +datetime.timedelta(days=1)
                
        Result['datas']=datas
        objdata['fields']=Result['fieldnames']
               
        objdata['data']=Result['datas']
        heads={}
        for i  in  range(len(Result['fieldnames'])):
            heads[Result['fieldnames'][i]]=Result['fieldcaptions'][i]
        objdata['heads']=heads

        tmp_name=save_datalist(objdata)
        #            print  tmp_name,'tmp_name'
        Result['tmp_name']=tmp_name
        Result['disableCols']=[]
        return getJSResponse(smart_str(dumps(Result)))
    '''