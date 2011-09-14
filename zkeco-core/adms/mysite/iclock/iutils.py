#!/usr/bin/env python
#coding=utf-8
from models import DeptAdmin, AreaAdmin, Department 
from mysite.utils import *
from django.db import models
from django.utils.encoding import force_unicode, smart_str
from django.contrib.auth.models import User, Permission
from django.utils import simplejson as json
from django.conf import settings
import datetime
def userDeptList(user):
        rs_dept = DeptAdmin.objects.all().filter(user=user)
        result = []
        if rs_dept.count():
                for t in rs_dept:
                        if t.dept:
                                depts = []
                                depts = getChildDept(t.dept)
                                depts.append(t.dept)
                                result += depts
                return result
        return []

def userAreaList(user):
        rs_area = AreaAdmin.objects.all().filter(user=user)
        len(rs_area)
        Result=[]
        if rs_area.count():
                for t in rs_area:
                        if t.area:
                                areas=[]
                                areas.append(t.area)
                                Result+=areas
                return Result
        return []

def getAllAuthChildDept(curid,request=None):
        return curid
        result=[]
        if request==None or request.user.is_superuser:
                rs_dept = Department.objects.filter(id=int(curid))
                if len(rs_dept)>0:
                        child_dept_list=getChildDept(rs_dept[0])
                        child_dept_list.append(rs_dept[0])
                        result = [d.id for d in child_dept_list]
        else:
                rs_dept = Department.objects.filter(id=int(curid))
                if len(rs_dept)>0:
                        child_dept_list=getChildDept(rs_dept[0])
                        child_dept_list.append(rs_dept[0])
                        child_dept_list = [d.id for d in child_dept_list]
                        alluserdeptList=userDeptList(request.user)
                        dd=[]
                        for i in alluserdeptList:
                                dd.append(int(i.id))
                        
                        for t in child_dept_list:
                                if t in dd:
                                        result.append(t)
        return result

def userIClockList(user):
        depts=userDeptList(user)
        if depts:
                rs_SN = Device.objects.filter(DeptID__in=depts)
                return [row.SN for row in rs_SN]
        return []
# 获得部门的下级所有部门
def getChildDept(dept):
	child_list=[]
	dept.all_children(child_list)
	return child_list

def AuthedIClockList(user):
        depts=userDeptList(user)
        if depts:
#                rs_SN = iclock.objects.filter(DeptID__in=depts)
                rs_SN = IclockDept.objects.filter(dept__in=depts)
                len(rs_SN)
                return [row.SN.SN for row in rs_SN]
        return []


def getUserIclocks(user):
        return userIClockList(user)

def fieldVerboseName(model, fieldName):
        try:
                f = model._meta.get_field(fieldName)
                return f.verbose_name
        except:
                pass


class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, datetime.date):
            return obj.strftime('%Y-%m-%d')
        elif isinstance(obj, datetime.time):
            return obj.strftime('%H:%M:%S')
        return json.JSONEncoder.default(self, obj)

def dumps(data):
        return JSONEncoder().encode(data)

def loads(str):
        return json.loads(str, encoding=settings.DEFAULT_CHARSET)
