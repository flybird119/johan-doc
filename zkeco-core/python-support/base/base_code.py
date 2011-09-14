# -*- coding: utf-8 -*-
'''
定义 "基础代码表"模型
'''
from django.db import models
from django.conf import settings
from cached_model import CachingModel
from translation import DataTranslation
from django.utils.translation import ugettext_lazy as _

class BaseCode(CachingModel):
    u"""
    一些常用数据代码，如“性别”、“职务”等
    数据代码仅仅是为了对数据进行选项型设定，并规范使用。
    """
    content = models.CharField(_(u'代码'), max_length=30)
    content_class = models.IntegerField(_(u'代码类别'), null=True, default=0, blank=True,editable=False)
    #parent = models.ForeignKey("BaseCode", verbose_name=_('parent code'), null=True, blank=True ,editable=False)
    display = models.CharField(_(u'显示'), max_length=30, null=True, blank=True)
    value = models.CharField(_(u'值'), max_length=30)
    remark = models.CharField(_(u'备注'), max_length=200, null=True, blank=True)
    is_add= models.CharField(_(u'是否是用户添加的'), max_length=4, null=True, blank=True,editable=False)#是否是用户添加进去的,默认为false
    def delete(self):
        if self.is_add!="true":
            raise Exception(_(u"系统初始化的记录不能删除！"))
        else:
            super(BaseCode,self).delete()
    def save(self, **args):
        tmp=BaseCode.objects.filter(content=self.content,display=self.display)
        if len(tmp)>0 and tmp[0].id!=self.id:#新增
            raise Exception(_(u'记录已经存在!'))
        elif len(tmp)==0:#新增
            self.is_add="true"
        super(BaseCode,self).save(**args)
    
        
    def __unicode__(self):
            return u"%s"%(self.display)
    def display_label(self):
            return DataTranslation.get_field_display(BaseCode, "display", self.display)
    class Meta:
            verbose_name=_(u"基础代码表")
    class Admin(CachingModel.Admin):
        menu_index=300
        visible=True
        list_display=( "display","value", "remark")                                

def base_code_by(content, content_class=None):
    '''
    根据类别名获取用于choices 的 tuple
    '''
    #chinese_no_choice=["CN_NATION","IDENTITY","CN_PROVINCE"]#非中文这些字段默认为空
    try:
        from django.utils import translation
        qs=BaseCode.objects.filter(content=content)
        if content_class!=None:
            qs=qs.filter(content_class=content_class)
        qs=[(item[0], item[1]) for item in qs.values_list('value','display')]
        return tuple(qs)
    except: 
            #import traceback; traceback.print_exc()
        return ()

def get_category(request):
    '''
    视图：用于获取所有类别的列表
    '''
    from dbapp.utils import getJSResponse
    from django.utils.encoding import smart_str
    from django.utils.simplejson  import dumps 
    qs = BaseCode.objects.distinct().values_list("content")
    data=[]
    for o in qs:
        l=list(o) 
        l.append(_(u"%(name)s")%{'name':_(o[0])})
        data.append(l)
    return getJSResponse(smart_str(dumps(data)))
