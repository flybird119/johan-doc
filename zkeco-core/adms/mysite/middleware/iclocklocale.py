#!/usr/bin/python
# -*- coding: utf-8 -*-

"this is the locale selecting middleware that will look at accept headers"

from django.utils.cache import patch_vary_headers
from django.utils import translation
from mysite.settings import MEDIA_URL, ADMIN_MEDIA_PREFIX
from django.conf import settings
from django.core.cache import cache
from django.core.context_processors import PermWrapper
from django.utils.translation import ugettext as _

noLocalePath=(MEDIA_URL, ADMIN_MEDIA_PREFIX,
        settings.UNIT_URL+'iclock/tmp/',
        settings.UNIT_URL+'iclock/files/',
        settings.UNIT_URL+'iclock/ccccc/',
        settings.UNIT_URL+'iclock/media/',
        '/media/',
        '/file/',
        settings.UNIT_URL+'iclock/getrequest',
        settings.UNIT_URL+'iclock/cdata',
        settings.UNIT_URL+'iclock/devicecmd',
        )

class LocaleMiddleware(object):
        """
        This is a very simple middleware that parses a request
        and decides what translation object to install in the current
        thread context. This allows pages to be dynamically
        translated to the language the user desires (if the language
        is available, of course).
        """

        def process_request(self, request):
                path=request.META["PATH_INFO"]
                for nol in noLocalePath:
                        if path.find(nol)==0:
                                request.isLocaled=False
                                return
                #print path
                request.isLocaled=True
                language = translation.get_language_from_request(request)
                translation.activate(language)
                try:
                   from mysite.urls import surl
                   from base.models import appOptions
                   from dbapp.urls import dbapp_url
                   request.surl=surl
                   request.dbapp_url=dbapp_url
                   cache_title=cache.get("browse_title")
                   if cache_title:
                        request.browse_title=cache_title
                   else:
                        request.browse_title=appOptions["browse_title"]
                        cache.set("browse_title",appOptions["browse_title"],24*60*60)
                except Exception ,e:
                    from traceback import print_exc
                    print print_exc()
                    pass
                
                request.LANGUAGE_CODE = translation.get_language()
                if "employee" in request.session: request.employee=request.session["employee"]

        def process_response(self, request, response):
                if request.isLocaled:
                        patch_vary_headers(response, ('Accept-Language',))
                        response["Pragma"]="no-cache"
                        response["Cache-Control"]="no-store"
                        response['Content-Language'] = translation.get_language()
                        translation.deactivate()
                return response

def employee(request):
#{% if user.first_name %}{{ user.first_name|escape }}{% else %}{{ user.username }}{% endif %}
        user=request.user
        if user.is_anonymous(): return ''
        if user.username=='employee' and "employee" in request.session:
                return _(u"员工 %s")%request.session["employee"]
        else:
                return user.first_name or user.username

def myContextProc(request):
        emp=None
        user=request.user
        userName=''
        if not user.is_anonymous():
                if user.username=='employee' and "employee" in request.session:
                        emp=request.session["employee"]
                        userName=_(u"员工 %s")%(emp.EName or emp.PIN)
                else:
                        userName=user.first_name or user.username
        return {#'SupportNewCSS': settings.SupportNewCSS,
                'IS_ADMIN': emp==None and not user.is_anonymous(),
                'login_username': userName,
                'employee': emp,
                'request': request,
                }


#该ContextProc用于替换django.core.context_processors.auth，
#从而使之不再查询表 auth_messages

def auth(request):
    """
    Returns context variables required by apps that use Django's authentication
    system.

    If there is no 'user' attribute in the request, uses AnonymousUser (from
    django.contrib.auth).
    """
    if hasattr(request, 'user'):
        user = request.user
    else:
        from django.contrib.auth.models import AnonymousUser
        user = AnonymousUser()
    return {
        'user': user,
        'perms': PermWrapper(user),
    }

#下面的Middleware用于替换django.contrib.auth.middleware.AuthenticationMiddleware
#使用缓存来查询登录的用户，避免每次都查询数据库

SESSION_KEY = '_auth_user_id'

class LazyUser(object):
        def __get__(self, request, obj_type=None):
                if not hasattr(request, '_cached_user'):
                        try:
                                user_id = request.session[SESSION_KEY]
                                k="user_id_%s"%user_id                                                                          
                                u=cache.get(k)
                        except:
                                from django.contrib.auth.models import AnonymousUser
                                u=AnonymousUser()
                        if u==None:
                                from django.contrib.auth import get_user
                                u = get_user(request)
                                cache.set(k, u, 60*60)
                        request._cached_user=u
                return request._cached_user

class AuthenticationMiddleware(object):
        def process_request(self, request):
                assert hasattr(request, 'session'), "The Django authentication middleware requires session middleware to be installed. Edit your MIDDLEWARE_CLASSES setting to insert 'django.contrib.sessions.middleware.SessionMiddleware'."
                request.__class__.user = LazyUser()
                return None

