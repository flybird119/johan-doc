#! /usr/bin/env python
#coding=utf-8
from django.utils.translation import ugettext as _
def get_base_fields():
    '''
    提供显示 统计最早与最晚 显示字段
    '''
    r={}
    strFieldNames=['deptid','badgenumber','username','ssn']
    FieldNames=['userid','badgenumber','username','deptid','deptname','date','week',
    'firstchecktime','latechecktime']
    for t in FieldNames:
            if t in strFieldNames:
                    r[t]=''
            else:
                    r[t]=''
    r['userid']=-1;
    FieldCaption=[_(u'用户ID'),_(u'人员编号'),_(u'姓名'),_(u'部门编号'),_(u'部门名称'),_(u'日期'),_(u'星期'),
                  _(u'最早打卡时间'),_(u'最晚打卡时间')]
    return [r,FieldNames,FieldCaption]
   