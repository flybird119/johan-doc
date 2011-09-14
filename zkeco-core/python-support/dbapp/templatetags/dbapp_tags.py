#coding=utf-8
import datetime
from django import template
from django.conf import settings
from cgi import escape
from django.utils.translation import ugettext_lazy as _, ugettext
from django.core.cache import cache
from dbapp.data_utils import hasPerm
from django.db import models
from django.utils.encoding import force_unicode, smart_str
from dbapp.file_handler import get_model_image

register = template.Library()
@register.inclusion_tag('dbapp_filters.html')
def filters(cl):
    return {'cl': cl}

def filter(cl, spec):
    return {'title': spec.title(), 'choices' : list(spec.choices(cl)), 'field': spec.fieldName()}
filter = register.inclusion_tag('dbapp_filter.html')(filter)


@register.simple_tag
def current_time(format_string):
    return str(datetime.datetime.now())

@register.simple_tag
def get_this_year():
	import datetime
	return datetime.datetime.now().strftime("%Y")


@register.filter
def escape_js_html(value):
    from django.utils.html import escape
    from django.template.defaultfilters import escapejs
    return escapejs(escape(value))

@register.filter
def format_date(fielddatetime):
    return fielddatetime.strftime("%Y-%m-%d")

@register.filter
def translate_str(str):
    from django.utils.translation import ugettext as _
    if str:
        return _(str)
    else:
        return ""

@register.filter
def format_int(float_value):
    return int(float_value)

@register.filter
def format_shorttime(fielddatetime):    
    return fielddatetime.strftime("%H:%M")

@register.filter
def HasPerm(user, operation): #判断一个登录用户是否有某个权限
    return user.has_perm(operation)

@register.filter
def format_whether(value): 
    if value:
        return ugettext(u"是")
    else:
        return ugettext(u"否")

@register.filter
def format_whether2(value): 
    if value=="1":
        return ugettext(u"是")
    elif value=="2":
        return ugettext(u"否")
    else:
        return ugettext(u"处理中")

            
@register.filter
def reqHasPerm(request, operation): #判断一个当前请求的数据模型表是否有某个权限
    '''
    判断一个当前请求是否有某个操作的权限
    '''
    return hasPerm(request.user, request.model, operation)

@register.filter
def hasApp(app_label):
    '''
    判断是否存在某个app
    '''
    from django.conf import settings
    if "&" in app_label:
        for app in app_label.split("&"):
            if app.strip() not in settings.INSTALLED_APPS: return False
        return True
    elif "|" in app_label:
        for app in app_label.split("|"):
            if app.strip() in settings.INSTALLED_APPS: return True
        return False
    return (app_label in settings.INSTALLED_APPS)

#用于返回当前系统（站点)是否为oem
@register.filter
def is_oem(site):#site变量暂无实际意义。
    from django.conf import settings
    return settings.OEM 

##用于返回当前系统（站点)是否是将zkeco当做zkaccess
#@register.filter
#def zkeco_as_zkaccess(site):#site变量暂无实际意义。
#    from django.conf import settings
#    return settings.ZKECO_AS_ZKACCESS

@register.filter
def buttonItem(request, operation): #根据一项操作产生操作菜单项!!!
    if hasPerm(request.user, request.model, operation):
        return u'<li><a href="%s/data/%s/">%s</a></li>'%(iclock_url_rel, model.__name__, model._meta.verbose_name)
    else:
        return u'<li>'+model._meta.verbose_name+'</li>'
    

@register.simple_tag
def version():
    return settings.VERSION+' by <a href="http://www.zksoftware.com">ZKSoftware Inc.</a>'

@register.simple_tag
def capTrans(s):
    return ugettext(u"%s"%s).capitalize()

@register.filter
def cap(s):
    return (u"%s"%s).capitalize()

@register.filter
def enabled_udisk_mod(mod_name):
    return ("udisk" in settings.ENABLED_MOD)
@register.filter
def enabled_weather_mod(mod_name):
    return ("weather" in settings.ENABLED_MOD)
@register.filter
def enabled_msg_mod(mod_name):
    return ("msg" in settings.ENABLED_MOD)
@register.filter
def enabled_att_mod(mod_name):
    return ("att" in settings.ENABLED_MOD)
@register.filter
def enabled_mod(mod_name):
    return (mod_name in settings.ENABLED_MOD)

@register.filter
def lescape(s):
    if not s: return ""
    s=escape(s)
    return escape(s).replace("\n","\\n").replace("\r","\\r").replace("'","&#39;").replace('"','&quot;')

@register.filter
def isoTime(value):
    if value:
        return str(value)[:19]
    if value==0:
        return "0"
    return ""

@register.filter
def stdTime(value):
    if value:
        return value.strftime(settings.STD_DATETIME_FORMAT)
    return ""


@register.filter
def shortTime(value):
    if value:
        return value.strftime(settings.SHORT_DATETIME_FMT)
    return ""

@register.filter
def vshortTime(value):
    if value:
        return value.strftime(settings.VSHORT_DATETIME_FMT)
    return ""

@register.filter
def shortDTime(value):
    if value:
        return value.strftime(settings.SHORT_DATETIME_FMT2)
    return ""

@register.filter
def onlyTime(value):
    if value:
        try:
            return value.strftime(settings.TIME_FMT)
        except:
            return (value+datetime.timedelta(100)).strftime(settings.TIME_FMT)
    else:
        return ""

@register.filter
def shortDate(value):
    if value:
        return value.strftime(settings.DATE_FMT)
    return ""

@register.filter
def shortDate4(value):
    if value:
        return value.strftime(settings.DATE_FMT4)
    return ""


@register.filter
def left(value, size):
    s=(u"%s"%value)
    if len(s)>size:
        return s[:size]+" ..."
    return s

@register.simple_tag#{% user_perms "personnel.Employee"%}
def user_perms(app_label_model_name):
    from django.contrib.contenttypes.models import ContentType
    from django.contrib.auth.models import Permission
    from base.model_utils import GetModel
    from base.middleware import threadlocals
    user=threadlocals.get_current_user()
    split=app_label_model_name.split(".")
    m=GetModel(split[0],split[1])
    ct=ContentType.objects.get_for_model(m)
    perms=[p.codename for p in Permission.objects.filter(content_type=ct) if user.has_perm(split[0]+"."+p.codename)]
    perms=sorted(perms)
    return ".".join(perms)
    
@register.filter
def PackList(values, field):
    l=[]
    for s in values:
        l.append(s[field])
    return ','.join(l)

@register.filter
def detail_str(master_field):
    return u', '.join([u'%s'%obj for obj in master_field.all()])

#@register.filter
#def add_link(field):
    #from dbapp import urls
    #return u"<a class='link' href='1/?&_lock=1&device&door_no'>%s</a>"%(field)
    #return u"<a class='link' href='%s/?&_lock=1&device&door_no'>%s</a>"%(field)

@register.filter
def detail_list(master_field, split=u",", max_count=1000000):
    from dbapp import urls
    objs=master_field.all()
    filter, key=master_field.core_filters.items()[0]
    def edit_link(obj):
        return u"<a class='edit' href='%s?_lock=1&%s=%s'>%s</a>"%(\
            urls.get_obj_url(obj), filter, key, obj)
    def add_link():
        return u"<a class='new' href='%s?_lock=1&%s=%s'>%s</a>"%(\
            urls.get_model_new_url(master_field.model), filter, key, ugettext('Add'))
    has_add=max_count>len(objs)
    if not objs and has_add: return add_link()
    return split.join([edit_link(obj) for obj in objs])+(has_add and u" | "+add_link() or "")

@register.filter
#通用过滤器-----可供首卡开门、多卡开门使用
def detail_list_set(master_field, max_count=10000):
    from dbapp import urls
    model = master_field.__dict__['model']
    app_label = model._meta.app_label
    objs=master_field.all()
    filter, key=master_field.core_filters.items()[0]
    def add_link():
        return u"<a class='new' href='../../data/%s/%s/?_lock=1&%s=%s'>%s</a>"%(app_label, model.__name__, filter, key, ugettext(u'设置'))
    
    return ugettext(u'已设置数:%(d)d | %(s)s') % { 'd': objs.__len__(), 's': add_link()} or ""

@register.filter
def detail_list_emp(master_field, max_count=1000000):
    from dbapp import urls
    objs=master_field.all()
    filter, key=master_field.core_filters.items()[0]
    def edit_link(obj):
        return u"<a class='edit' href='%s?%s=%s?_lock=1'>%s</a>"%(\
            urls.get_obj_url(obj), filter, key, obj)
    def add_link():
        return u"<a class='new' href='%s?_lock=1&%s=%s'>%s</a>"%(\
            urls.get_model_new_url(master_field.model), filter, key, ugettext('Add'))
    has_add=max_count>len(objs)
    if not objs and has_add: return add_link()
    return u', '.join([edit_link(obj) for obj in objs])+(has_add and u" | "+add_link() or "")



@register.filter
#detail_list从表max_count为1的特殊情况
def detail_list_one(master_field, max_count=1):
    from dbapp import urls
    objs=master_field.all()#最多一条记录
    filter, key=master_field.core_filters.items()[0]
    def edit_del_link(obj):
        #m_objs = master_field.model.objects.all()
        return u"<a class='edit' edit='%s?_lock=1&%s=%s' href='javascript:void(0)'>%s</a> <a class='delete' delete='%s_op_/_delete/?K=%s' href='javascript:void(0)'>%s</a>"%(\
               urls.get_obj_url(obj), filter, key, ugettext(u'修改'), urls.get_model_data_url(master_field.model), urls.get_obj_url(obj).split("/")[-2], ugettext(u'删除'))
    def add_link():
        return u"<a class='new' new='%s?_lock=1&%s=%s' href='javascript:void(0)'>%s</a>"%(\
            urls.get_model_new_url(master_field.model), filter, key, ugettext(u'设置'))
    has_add=max_count>len(objs)
    if not objs and has_add: return add_link()
    return edit_del_link(objs[0])


def _(s): return s

CmdContentNames={'DATA USER PIN=':_(u'人员信息'),
    'DATA FP PIN=':_(u'指纹'),
    'DATA DEL_USER PIN=':_(u'删除人员'),
    'DATA DEL_FP PIN=':_(u'删除指纹'),
    'CHECK':_(u'检查服务器配置'),
    'INFO':_(u'更新服务器上的设备信息'),
    'CLEAR LOG':_(u'清除考勤记录'),
    'RESTART':_(u'重新启动设备'),
    'REBOOT':_(u'重新启动设备'),
    'LOG':_(u'检查并传送新数据'),
    'PutFile':_(u'发送文件到设备'),
    'GetFile':_(u'从设备传文件'),
    'Shell':_(u'执行内部命令'),
    'SET OPTION':_(u'修改配置'),
    'CLEAR DATA':_(u'清除设备上的所有数据'),
    'AC_UNLOCK':_(u'输出开门信号'),
    'AC_UNALARM':_(u'中断报警信号'),
    'ENROLL_FP':_(u'登记人员指纹'),
}

def getContStr(cmdData):
    for key in CmdContentNames:
        if key in cmdData:
            return CmdContentNames[key]
    return "" #_("Unknown command")

@register.filter
def cmdName(value):
    return getContStr(value)

DataContentNames={
    'TRANSACT':_(u'考勤记录'),
    'USERDATA':_(u'人员信息及其指纹')}

@register.filter
def dataShowStr(value):
    if value in DataContentNames:
        return value+" <span style='color:#ccc;'>"+DataContentNames[value]+"</span>"
    return value

@register.filter
def cmdShowStr(value):
    return left(value, 30)+" <span style='color:#ccc;'>"+getContStr(value)+"</span>"

@register.filter
def thumbnail_url(obj, field=""):
    try:
        url=obj.get_thumbnail_url()
        if url:
            try:
                fullUrl=obj.get_img_url()
            except: #only have thumbnail, no real picture
                return "<img src='%s' />"%url
            else:
                if not fullUrl:
                    return "<img src='%s' />"%url
            return "<a href='%s'><img src='%s' /></a>"%(fullUrl, url)
    except:
        import os
        f=getattr(obj, field or 'pk')
        if callable(f): f=f()
        fn="%s.jpg"%f
        fns=get_model_image(obj.__class__, fn, "photo", True) #image_file, image_url, thumbnail_file, thumbnail_url
        #print fns
        if fns[0]:
            if fns[2]: #has thumbnail
                return "<a href='%s'><img src='%s' /></a>"%(fns[1], fns[3])
            else:
                return "<a href='%s'><img src='%s' width='120'/></a>"%(fns[1], fns[1])
        elif fns[2]:
               return "<img src='%s' />"%fns[3]
    return ""

#表单里的label_suffix，非filter---add by darcy 20100605
def label_tag(field):   #--------------------------------------------  没有 @register.filter  无用
    label_suffix = ':'
    label_tag = field.label_tag()
    label = label_tag.split('<')[1].split('>')[1]
    if label[-1] not in ':?.!':
        label += label_suffix 
    return field.label_tag(label)

#表单里的label_suffix(无星号,可用于查询）---add by darcy 20100617
@register.filter 
def field_as_label_tag_no_asterisk(field):
    result = label_tag(field)
    if result.__contains__("required"):
        result = result.replace('required','')
    return """%s"""%result

#表单里的label_suffix(有星号（非必填项）,前端判空）---add by darcy 20101225
@register.filter 
def field_as_label_tag_asterisk(field):
    result = label_tag(field)
    if not result.__contains__("required"):
        result = result.replace('label for', 'label class="required" for')
    return """%s""" % result


#只返回label_tag包含：和for等
@register.filter 
def field_as_label_tag(field):
    return """%s""" % label_tag(field)

#返回help_text 字段中的注释
@register.filter 
def field_as_help_text(field):
    return field.help_text and ("<span class='gray'>%s</span>"%unicode(field.help_text)) or ""

@register.filter    
def field_format(field, fmt_str):
    return fmt_str%{ \
        'label_tag':label_tag(field), 
        'as_widget':field.as_widget(), 
        'errors':field.errors and "<ul class='errorlist'>%s</ul>"%("".join(["<li>%s</li>"%e for e in field.errors])) or "",
        'help_text':field.help_text and ("<span class='gray'>%s</span>"%unicode(field.help_text)) or ""
    }

@register.filter    
def field_as_td_h(field, colspan=1):
    return """<th>%s</th><td%s>%s%s%s</td>"""%( \
        label_tag(field),
		colspan>1 and " colspan=%s"%colspan or "",
        field.as_widget(), 
        field.errors and "<ul class='errorlist'>%s</ul>"%("".join(["<li>%s</li>"%e for e in field.errors])) or "",
        field.help_text and ("<span class='gray'>%s</span>"%unicode(field.help_text)) or ""
    )

#将表中无星号的在表单中添加星号（用户设备表等）
@register.filter    
def field_as_td_h_asterisk(field, colspan=1):
    return """<th>%s</th><td%s>%s%s%s</td>"""%( \
        field_as_label_tag_asterisk(field),
		colspan>1 and " colspan=%s"%colspan or "",
        field.as_widget(), 
        field.errors and "<ul class='errorlist'>%s</ul>"%("".join(["<li>%s</li>"%e for e in field.errors])) or "",
        field.help_text and ("<span class='gray'>%s</span>"%unicode(field.help_text)) or ""
    )

    
@register.filter    
def field_as_ul_li(field):
    return """<div><ul><li>%s</li><li>%s%s%s</li></ul></div>"""%( \
        label_tag(field),  
        field.as_widget(), 
        #"<input type='text' name='%s'/>"%field.name,
        field.errors and "<ul class='errorlist'>%s</ul>"%("".join(["<li>%s</li>"%e for e in field.errors])) or "",
        field.help_text and ("<span class='gray'>%s</span>"%unicode(field.help_text)) or ""
    )
    

@register.filter    
#用于不需要显示label的特殊模板
def field_as_td_h_special(field):
    return """<td>%s%s%s</td>"""%( \
        field.as_widget(), 
        field.errors and "<ul class='errorlist'>%s</ul>"%("".join(["<li>%s</li>"%e for e in field.errors])) or "",
        field.help_text and ("<span class='gray'>%s</span>"%unicode(field.help_text)) or ""
    )

@register.filter    
#用于不需要显示label的特殊模板--不显示td
def field_as_no_td(field):
    return """%s%s%s"""%( \
        field.as_widget(), 
        field.errors and "<ul class='errorlist'>%s</ul>"%("".join(["<li>%s</li>"%e for e in field.errors])) or "",
        field.help_text and ("<span class='gray'>%s</span>"%unicode(field.help_text)) or ""
    )

@register.filter    
#用于不需要显示label的特殊模板(带自动输入）
def field_as_td_h_tz(field):
    return """<td><div class='displayN'>%s%s%s</div><div id='%s'></div></td>"""%( \
        field.as_widget(), 
        field.errors and "<ul class='errorlist'>%s</ul>"%("".join(["<li>%s</li>"%e for e in field.errors])) or "",
        field.help_text and ("<span class='gray'>%s</span>"%unicode(field.help_text)) or "",
        field.name
    )


@register.filter    
def field_as_td_v(field):
    return """<td>%s<br/>%s%s%s</td>"""%( \
        label_tag(field), 
        field.as_widget(), 
        field.errors and "<br/><ul class='errorlist'>%s</ul>"%("".join(["<li>%s</li>"%e for e in field.errors])) or "",
        field.help_text and ("<br/><span class='gray'>%s</span>"%unicode(field.help_text)) or ""
    )


@register.filter
def int_color(color):
    if color:
        return "<span style='background-color: #%02x%02x%02x; padding-left: 1em;' class='color'>&nbsp;</span>"%(color>>16&0xff, color>>8&0xff ,color&0xff)
    else:
        return "<span class='color'>&nbsp;</span>"
@register.filter
def boolean_icon(value):
	if value:
		return u"<img src='%s/img/icon-yes.gif' alt='%s' />"%(settings.MEDIA_URL, ugettext(u'是'))
	return u"<img src='%s/img/icon-no.gif' alt='%s' />"%(settings.MEDIA_URL, ugettext(u'否'))

@register.filter
def treeview(dept, node="li"):
        TREE_SPACE="<%(n)s class='space'></%(n)s>"%{"n": node}
        TREE_PARENT_LINE="<%(n)s class='parent_line'></%(n)s>"%{"n": node}
        TREE_LEAF="<%(n)s class='leaf'></%(n)s>"%{"n": node}
        TREE_LAST_LEAF="<%(n)s class='last'></%(n)s>"%{"n": node}
        TREE_FOLDER="<%(n)s class='folder'></%(n)s>"%{"n": node}
        TREE_FIRST_FOLDER="<%(n)s class='folder first'></%(n)s>"%{"n": node}
        TREE_LAST_FOLDER="<%(n)s class='folder last'></%(n)s>"%{"n": node}
        TREE_CONVERT={'l':TREE_PARENT_LINE, ' ':TREE_SPACE, 'L':TREE_LAST_LEAF}
        TREE_FOLDER_CONVERT={'l':TREE_PARENT_LINE, ' ':TREE_SPACE, 'L':TREE_LAST_FOLDER}
        if not hasattr(dept, "tree_prefix") or not dept.tree_prefix:
                if dept.tree_folder:
                        ret=TREE_FIRST_FOLDER
                else:
                        ret=TREE_LEAF
        else:
                ret= [TREE_CONVERT[tp] for tp in dept.tree_prefix]
                if dept.tree_folder:
                        ret[-1]=TREE_FOLDER
                        if dept.tree_prefix[-1]=='L':
                                ret[-1]=TREE_LAST_FOLDER
                elif dept.tree_prefix[-1]=='L':
                        ret[-1]=TREE_LAST_LEAF
                else:
                        ret[-1]=TREE_LEAF
                ret=TREE_SPACE+(''.join(ret))
        return u"<span class='tree'>%s<span class='content'>%s</span></span>"%(ret, dept)

@register.filter
def mod_by(value, div):
	return int(value)%int(div)

