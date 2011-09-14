#! /usr/bin/env python
#coding=utf-8
from django.db import models
from base.models import CachingModel
from django.utils.translation import ugettext_lazy as _
from dbapp import data_edit
import datetime
from mysite.iclock.models.dev_comm_operate import sync_accholiday

MAX_HOLIDAY_COUNT_PER_TYPE = 32#每种假日类型支持的最大节假日的数量

HOLIDAYTYPE_CHOICES = (
    (1, _(u'假日类型1')), (2, _(u'假日类型2')), (3, _(u'假日类型3')),
)

ISVALID_CHOICES = (
    (1, _(u'是')), (2, _(u'否')),
)

#获取单个节假日对象的日期
def get_date_between(holiday):
    date = []
    start = holiday.start_date
    delta = (holiday.end_date - start).days
    for d in range(delta+1):
        date.append(start + datetime.timedelta(d))
    
    return date

#获取所有已设置为节假日的日期
def get_all_holidays_date():
    all_date = []
    all_holidays = AccHolidays.objects.all()
    for h in all_holidays:
        all_date += get_date_between(h)
    #print '===set(all_date)=',set(all_date)
    return set(all_date)

class AccHolidays(CachingModel):
    u"""
    假日表
    """
    holiday_name = models.CharField(_(u'节假日名称'), max_length=30, null=True, blank=False, default="", unique=True)
    holiday_type = models.SmallIntegerField(_(u'节假日类型'), null=True, blank=False, choices=HOLIDAYTYPE_CHOICES, default=1)
    start_date = models.DateField(_(u'开始日期'), null=False, blank=False)
    end_date = models.DateField(_(u'结束日期'), null=False, blank=False)
    loop_by_year = models.SmallIntegerField(_(u'是否按年循环'), null=True, blank=False, choices=ISVALID_CHOICES, default=2)
    memo = models.CharField(_(u'备注'), null=True, max_length=70, blank=True, default='')

    def __unicode__(self):
        return self.holiday_name

    class Admin(CachingModel.Admin):
        menu_index = 10001
        disabled_perms = ['clear_accholidays', 'dataimport_accholidays', 'view_accholidays']
        query_fields = ('holiday_name', 'holiday_type', 'loop_by_year') #list_filter
        list_display = ('holiday_name', 'holiday_type' , 'start_date' , 'end_date', 'loop_by_year', 'memo')
        #search_field=[]
        help_text = _(u'每种假日类型包含的节假日数量不能超过32个。节假日长度不能大于365天。<br>如果某个节假日只有一天请设置结束日期等于开始日期。<br>按年循环是指某个节假日的日期在所有年份是不会变化的。')

    def data_valid(self, sendtype):
        tmp = AccHolidays.objects.filter(holiday_name=self.holiday_name.strip())
        if tmp and tmp[0] != self:
            raise Exception(_(u'门禁节假日名称设置重复'))

        if AccHolidays.objects.filter(holiday_type=self.holiday_type).count() == MAX_HOLIDAY_COUNT_PER_TYPE:
            raise Exception(_(u'每种假日类型包含的节假日数量不能超过%s个') % MAX_HOLIDAY_COUNT_PER_TYPE)

        if self.start_date > self.end_date:
            raise Exception(_(u'开始日期不能大于结束日期.'))

        if self.start_date.year < datetime.datetime.now().year:
            raise Exception(_(u'开始日期设置错误'))

        if self.end_date.year - self.start_date.year != 0:#不能跨年
            raise Exception(_(u'节假日日期不能跨年'))
        
        current_date = get_date_between(self)
        already_date = get_all_holidays_date()
        #print '---current_date=',current_date
        #print '---already_date=',already_date
        for date in current_date:
            if date in already_date:
                raise Exception(_(u'日期：%s 已经被设置为节假日，不能重复设置！') % date)

    def delete(self):
        super(AccHolidays, self).delete()
        sync_accholiday()

    class Meta:
        app_label = 'iaccess'
        db_table = 'acc_holidays'
        verbose_name = _(u'门禁节假日')
        verbose_name_plural = verbose_name

def DataPostCheck(sender, **kwargs):
    oldObj = kwargs['oldObj']
    newObj = kwargs['newObj']
    request = sender
    if isinstance(newObj, AccHolidays):
        from mysite.iclock.models.model_device import decode_holiday
        if oldObj is None:
            sync_accholiday()
        else:
            if decode_holiday([oldObj]) != decode_holiday([newObj]):    #edit deiff
                sync_accholiday()

data_edit.post_check.connect(DataPostCheck)
