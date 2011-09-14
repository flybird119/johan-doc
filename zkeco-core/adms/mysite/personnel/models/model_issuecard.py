#! /usr/bin/env python
#coding=utf-8

from django.db import models
from base.models import CachingModel
from base.operation import Operation, ModelOperation
from django.utils.translation import ugettext_lazy as _
from model_leave import YESORNO
from django.db.models import Q

CARDSTATUS = (
        ('1', _(u'有效')),
        ('2', _(u'无效')),
        ('3', _(u'挂失')),
)


class CardType(CachingModel):
        '''卡类型'''
        cardtypecode = models.CharField(verbose_name=_(u'卡类型代码'), max_length=20, editable=True)
        cardtypename = models.CharField(verbose_name=_(u'卡类型名称'), max_length=50, null=True, blank=True, editable=True)
        def __unicode__(self):
                return u"%s %s" % (self.cardtypecode, self.cardtypename)

        class Admin(CachingModel.Admin):
                app_menu = "personnel"
                menu_index = 6
                visible = False
                @staticmethod
                def initial_data():
                        if CardType.objects.count() == 0:
                                CardType(cardtypename=u'%s'%_(u"贵宾卡"), cardtypecode="01").save()
                                CardType(cardtypename=u'%s'%_(u"普通卡"), cardtypecode="02").save()
                        pass

        class Meta:
                app_label = 'personnel'
                verbose_name = _(u'卡类型')
                verbose_name_plural = verbose_name


from mysite.personnel.models.model_emp import Employee, EmpForeignKey, EmpMultForeignKey, EmpPoPForeignKey, EmpPoPMultForeignKey, format_pin
import datetime
class IssueCard(CachingModel):
        '''发卡表'''
        UserID = EmpPoPForeignKey(verbose_name=_(u"人员"), null=False, editable=True)
        cardno = models.CharField(verbose_name=_(u'卡号'), max_length=20, null=False, blank=True, editable=True)
        effectivenessdate = models.DateField(verbose_name=_(u'有效日期'), null=True, blank=True, editable=False)
        isvalid = models.BooleanField(verbose_name=_(u'是否有效'), choices=YESORNO, editable=False, default=1)
        #cardtype=models.ForeignKey(CardType,verbose_name=_(u'卡类型'),editable=True,null=True,blank=True)
        cardpwd = models.CharField(verbose_name=_(u'卡密码'), max_length=20, null=True, blank=True, editable=False)
        #blance=models.DecimalField(verbose_name=_(u'卡上余额'),max_digits=8,null=True,blank=True,decimal_places=2,editable=True)
        failuredate = models.DateField(verbose_name=_(u'失效日期'), null=True, blank=True, editable=False)
        cardstatus = models.CharField(verbose_name=_(u'卡状态'), max_length=20, choices=CARDSTATUS, editable=False, default=1)
        issuedate = models.DateField(verbose_name=_(u'发卡日期'), null=True, blank=True, editable=False, default=datetime.datetime.now().strftime("%Y-%m-%d"))
        def __unicode__(self):
            return u"%s  %s" % (self.UserID, self.cardno)
        def data_valid(self, sendtype):
            from datetime import datetime
            from mysite.iclock.models.modelproc import get_normal_card
            print type(self.cardno)
            try:
                orgcard = str(self.cardno)
            except:
                raise Exception(_(u'卡号不正确'))
            import re
            tmp = re.compile('^[0-9]+$')
            if not tmp.search(orgcard):
                raise Exception(_(u'卡号不正确'))
            u = Employee.objects.filter(Card__exact=self.cardno)
            if u:
                raise Exception(_(u'卡号已使用'))
            if self.UserID.Card:
                raise Exception(_(u'该人员已发过卡'))
            self.issuedate = datetime.now().strftime("%Y-%m-%d")
        class _delete(Operation):
            visible = False
            verbose_name=_(u'删除')
            def action(self):
                pass


        def save(self):
            super(IssueCard, self).save()
            if self.UserID.Card != self.cardno:
                self.UserID.Card = self.cardno
                self.UserID.save()

                #同步卡号到门禁控制器
                from mysite import settings
                if "mysite.iaccess" in settings.INSTALLED_APPS:
                    from mysite.iclock.models.dev_comm_operate import sync_set_user
                    sync_set_user(self.UserID.search_accdev_byuser(), [self.UserID])
                

        class OpBatchIssueCard(ModelOperation):
            verbose_name=_(u'批量发卡')
            help_text=_(u'已经发过卡的人员，将不会在生成人员列表时出现！')
            from mysite import settings

            params=(
                ('pin_width',models.IntegerField(null=True,blank=True,default=settings.PIN_WIDTH)),
            )
            def action(self,pin_width):
                if self.request:
                    empids=self.request.POST.get("empids","")
                    cardnos=self.request.POST.get("cardnos","")
                    empids=[int(i) for i in empids.split(",")]
                    #print empids
                    cardnos=[str(i) for i in cardnos.split(",")]
                    #print cardnos
                    where={'id__in':empids}
                    emps=Employee.objects.filter(Q(**where))
                    for i in range(len(empids)):
                        tcard=IssueCard()
                        tuser=emps.get(pk=empids[i])

                        tcard.cardno=cardnos[i]
                        tcard.UserID=tuser  
                                              
                        tcard.save()
                        tuser.Card=cardnos[i]
                        tuser.save()

                    
        class _change(Operation):
            visible = False
            verbose_name=_(u'修改')
            def action(self):
                pass
#        class OpLoseCard(Operation):
#                help_text=u'挂失卡'
#                verbose_name=u'挂失卡'
#                visible=False
#                def action(self):
#                        self.object.cardstatus=3
#                        self.object.save()
#        class OpRevertCard(Operation):
#                help_text=u'解挂卡'
#                verbose_name=u'解挂卡'
#                visible=False
#                def action(self):
#                        self.object.cardstatus=1
#                        self.object.save()
#        class OpExchangeCard(Operation):
#                help_text=u'员工换卡'
#                verbose_name=u'员工换卡'
#
#                def action(self):
#                        self.object.cardstatus=1
#                        self.object.save()

        class Admin(CachingModel.Admin):
                sort_fields = ["UserID.PIN","issuedate"]
                app_menu = "personnel"
                list_filter = ('UserID', 'cardno', 'isvalid', 'cardstatus')
                query_fields = ['UserID__PIN', 'UserID__EName', 'cardno', 'cardstatus', 'isvalid']
                #list_display = ['UserID.PIN','UserID.EName','cardno','cardstatus','isvalid']
                list_display = ['UserID.PIN', 'UserID.EName', 'cardno', 'issuedate']
                disabled_perms = ['dataimport_issuecard', 'oprevertcard_issuecard', 'oplosecard_issuecard']
                menu_index = 5
                disabled_perms = ["dataimport_issuecard", "change_issuecard", "oplosecard_issuecard", "oprevertcard_issuecard"]
                help_text = _(u"目前支持手动输入卡号以及使用发卡器发卡！")
        class Meta:
                app_label = 'personnel'
                verbose_name = _(u'人员发卡')
                verbose_name_plural = verbose_name
