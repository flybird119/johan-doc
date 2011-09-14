#coding=utf-8
'''
通用数据列表视图
'''
from dbapp import data_viewdb
from dbapp import utils
from django.core.urlresolvers import reverse
from dbapp.models import create_model
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.db.models.query import QuerySet


def data_list_(request, fn):
    attrs, admin_attrs, data=utils.load_tmp_file(fn)
    model=create_model(fn.encode("utf-8"), base_model=models.Model, attrs=attrs, admin_attrs=admin_attrs)
    return data_viewdb.model_data_list(request, model, QSList(model,data), model_url=reverse(data_list_, args=(fn,)))
    
class QSValue(object):
    def __init__(self, index, data):
        self.data=data
        self.index=index
    def __getitem__(self, i):
        return self.data.get(i, self.index) or ""
    def __str__(self):
        return ""

class QSList(QuerySet): #---构造query_set
    def __init__(self, model, data):
        self.model=model
        ret=[]
        start=0
        for item in data:
            start+=1
            ret.append(self.model(id=start,**item))
        self.data=ret
    def count(self):
        return len(self.data)
    def __len__(self):
        return len(self.data)
    def __iter__(self):
        return iter(self.data)
    def order_by(self, *fields):
        return self
    def __getitem__(self, i):
        return self.data[i]
        #return [QSValue(index, ret[index]) for index in range(len(ret))]
    
def save_datalist(data):#---临时保存报表计算后所得的数据
    fn="_tmp_%s"%id(data)
    head=data['heads']
    attrs=dict([(str(k), models.CharField(max_length=1024, verbose_name=head[k])) for k in data['fields']])
    admin_attrs={"read_only":True, "cache": False, "log":False}
    utils.save_tmp_file(fn, (attrs, admin_attrs,  data['data']))
    return fn
    
def response_datalist(request, data):
    fn="_tmp_%s"%id(data)
    attrs=dict([(k, models.CharField(max_length=1024, verbose_name=k)) for k in data['fields']])
    admin_attrs={"read_only":True, "cache": False, "log":False}
    utils.save_tmp_file(fn, (attrs, admin_attrs,  data['data']))
    model=create_model(fn, base_model=models.Model, attrs=attrs, admin_attrs=admin_attrs)  
    return data_viewdb.model_data_list(request, model, QSList(model,data['data']), model_url=reverse(data_list, args=(fn,)))

def data_demo(request):
    return ""

