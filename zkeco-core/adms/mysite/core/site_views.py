# coding=utf-8

from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect,HttpResponse
from mysite.settings import LOGIN_REDIRECT_URL
from dbapp.utils import set_cookie

def index(request):
        from base.auth_utils import auto_login
        auto_login(request)
        return HttpResponseRedirect(LOGIN_REDIRECT_URL)
#        return render_to_response("index.html", RequestContext(request, {}),);

def my_i18n(request):
        from django.views.i18n import set_language
        from base.options import options
        r=set_language(request)
        set_cookie(r, 'django_language', request.REQUEST['language'], 365*24*60*60)
        options['base.language']=request.REQUEST['language']
        return r
    
def checkno(request,app_label,model_name):
        from dbapp.data_utils import QueryData
        from base.model_utils import GetModel        
        from mysite.personnel.models.model_emp import format_pin
        obj=GetModel(app_label, model_name)
        data=dict(request.REQUEST.items())
        if 'PIN__exact' in data.keys():
            data['PIN__exact']=format_pin(str(data['PIN__exact']))
        d={}
        for k,v in data.items():
            d[str(k)]=v
        qs=obj.all_objects.filter(**d)
        if qs.count()>0:
                return HttpResponse("&times; " + u"%s"%_(u"已存在"));
        else:
                return HttpResponse("&radic; " + u"%s"%_(u"可使用"));