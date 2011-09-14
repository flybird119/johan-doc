#coding=utf-8
from django import forms
import datetime
from django.utils import simplejson

def render_device_widget(name, data, multiple, popup, filter):
    js_attrs={}
    try:
#        from depttree import DeptTree
#        from mysite.personnel.models import Employee, Department
        from mysite.iclock.models import Device
        from mysite.personnel.models import Area
        from dbapp.urls import dbapp_url
        from mysite.urls import surl
        if type(data) == list:
            data = ','.join(d for d in [str(i) for i in data])
        url=data and ("%s%s/Device/?id__exact=%s"%(dbapp_url,Device._meta.app_label,data)) or ("%s%s/Device/?%s"%(dbapp_url, Device._meta.app_label, filter))
        date_now=datetime.datetime.now()
        str_now=str(date_now.strftime('%Y%m%d%H%M%S'))+str(date_now.microsecond)
        js_attrs["multiple_select"]=multiple
        js_attrs["popup"]=popup
        js_attrs["select_record"]=data and data or False
        js_attrs["field_name"]=name
        js_attrs["grid_id"]="device_select_%s"%(str_now)
        js_attrs["surl"]=surl
        js_attrs["model_url"]=url
        js_attrs["display_field"]= ['sn','ipaddress']
        js_attrs["parent_verbose_name"]= '区域'
        js_attrs["sub_verbose_name"]= '设备'
        js_attrs["search_field_verbose_name"]= '按照设备序列号/IP查找'
        js_attrs["parent_url"]= 'personnel/Area'
        json_attrs=simplejson.dumps(js_attrs)
        html=""
        if multiple:
            html+=u"<input type='hidden' name='multipleFieldName' value='%s' />"%name
        html+=u"<table id='id_corner_tbl' class='corner_tbl' cellpadding='0' cellspacing='0' style='float:left;'><tr><td></td><td></td><td class='tboc1 h1'></td><td></td><td></td></tr>" \
            +u"<tr><td></td><td class='tboc1 w1 h1'>&nbsp;</td><td class='tbac1'></td>" \
            +u"<td class='tboc1 w1 h1'>&nbsp;</td><td></td></tr><tr><td class='tboc1 w1'>&nbsp;" \
            +u"</td><td class='tbac1 tbg'></td><td class='tbac1 tbg td_contant'><div class='div_contant'>" \
                    +u"<div class='zd_Emp div_box_emp'>" \
                            +u"<div id='%s'></div>"%(js_attrs["grid_id"]) \
                            +"<script> $.zk._select_obj(%s);</script>"%(json_attrs) \
                    +"</div>" \
            +u"<div class='clear'></div></div></td><td class='tbac1 tbg'>"\
            +u"</td><td class='tboc1 w1'>&nbsp;</td></tr>" \
            +u"<tr><td></td><td class='tboc1 w1 h1'>&nbsp;</td><td class='tbac1'></td><td class='tboc1 w1 h1'>&nbsp;</td>" \
            +u"<td></td></tr><tr><td></td><td></td><td class='tboc1 h1'></td><td></td><td></td></tr></table>"
        return html
    except:
        import traceback; traceback.print_exc()


class ZDeviceChoiceWidget(forms.Select):
    popup=False
    def __init__(self, attrs={}, choices=()):
            super(ZDeviceChoiceWidget, self).__init__(attrs=attrs, choices=choices)
    def render(self, name, data, attrs=None, filter=None):
            if attrs: self.attrs.update(attrs)
            if 'id' not in self.attrs: self.attrs['id']='id_'+name
            self.attrs = self.build_attrs(self.attrs, name=name)
            return render_device_widget(name, data, False, self.popup, filter)
        
class ZPopDeviceChoiceWidget(ZDeviceChoiceWidget):
    popup=True
    
    
    
class ZMulDeviceChoiceWidget(forms.SelectMultiple):
    popup=False
    def __init__(self, attrs={}, choices=()):
            super(ZMulDeviceChoiceWidget, self).__init__(attrs=attrs, choices=choices)
    def value_from_datadict(self, data, files, name):
        from django.utils.datastructures import MultiValueDict, MergeDict
        if isinstance(data, (MultiValueDict, MergeDict)):
            dept_all = data.getlist("dept_all")#'on'或者'off'
                
            if dept_all:#选择部门下所有人员
                dept_id = data.getlist("deptIDs")
                #print '------dept_id=',dept_id
                from mysite.personnel.models import Device
                return [e.pk for e in Device.objects.filter(area__in = dept_id)]
            else:
                return data.getlist(name)
        else:
            return data.get(name, None)
    
    def render(self, name, data, attrs=None, filter=None):
            if attrs: self.attrs.update(attrs)
            if 'id' not in self.attrs: self.attrs['id']='id_'+name
            self.attrs = self.build_attrs(self.attrs, name=name)
            return render_device_widget(name, data, True, self.popup, filter)