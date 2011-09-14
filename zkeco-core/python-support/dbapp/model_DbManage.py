# coding=utf-8
from django.db import models
from base.operation import Operation,ModelOperation
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _

import datetime
from django.conf import settings
import base

SUCCESS_FLAG = (
    ('1', _(u'是')),
    ('2', _(u'否')),
    ('3', _(u'待处理')),
)

class DbBackupLog(base.models.CachingModel):
    user=models.ForeignKey(User, verbose_name=_(u"用户"))
    #备份时间
    starttime=models.DateTimeField(_(u'开始时间'), db_column='starttime', null=True, blank=True)
    #是否立即备份标志,主要针对手工备份
    imflag=models.BooleanField(_(u"立即备份"))
    successflag=models.CharField(_(u"是否成功备份"), max_length=1,choices=SUCCESS_FLAG)  #是否成功备份

    def __unicode__(self):
        return self.user.username + "  " + self.starttime.strftime("%Y-%m-%d %H:%M:%S")

    def save(self):
        super(DbBackupLog,self).save()

    class Admin(base.models.CachingModel.Admin):
        disabled_perms=["add_dbbackuplog","change_dbbackuplog","dataimport_dbbackuplog"]
        menu_index=400
        app_menu="base"
        menu_group = 'base'
        list_display=('user.username','starttime','imflag|format_whether','successflag|format_whether2',)

    class Meta:
        db_table = 'dbbackuplog'
        verbose_name=_(u"数据库管理")

    class _change(Operation):
        help_text=_(u"修改选定记录")
        verbose_name=_(u"修改")
        visible=False
        confirm=""
        only_one_object=True
        def action(self):
                pass

    class OpBackupDB(ModelOperation):
        help_text=_(u"备份数据库，数据库服务器和本系统服务器必须在同一台电脑上，暂不支持备份Oracle数据库。如果备份失败，请参考用户手册中的用户使用FAQ。")
        verbose_name=_(u"备份数据库")
        def action(self):
            from base.models import PersonalOption,Option
            database_engine = settings.DATABASES["default"]["ENGINE"]
            if database_engine == "django.db.backends.oracle":#oracle
                raise Exception(_(u"暂不支持备份Oracle数据库"))
            backuptype=self.request.POST.get('backuptype','1')
            if backuptype=='1':
                try:
                    o=DbBackupLog(user=self.request.user,imflag=True,starttime=datetime.datetime.now())
                    o.save()
                except:
                    import traceback; traceback.print_exc()
            elif backuptype=='2':
                start = self.request.POST.get('start')
                inc = self.request.POST.get('intervaltime')
                #OptionClass["backup_sched"]= start +u"|" +inc
                cc=PersonalOption.objects.filter(user=self.request.user,option__name="backup_sched")
                id =Option.objects.filter(name__exact='backup_sched')[0]
                if cc:
                    cc[0].value=start +u"|" +inc
                    cc[0].save()
                else:
                    o=PersonalOption(user=self.request.user,value=start +u"|" +inc,option=id)
                    o.save()
            elif backuptype=="3":
                try:
                    cc=PersonalOption.objects.get(user=self.request.user,option__name="backup_sched")
                    cc.delete()
                except:
                    pass

    class OpInitDB(ModelOperation):
        help_text=_(u'''初始化数据库是将数据恢复到系统初始化状态!''')
        verbose_name=_(u"初始化数据库")
        def action(self):
            import time
            from base.model_utils import GetModel
            models_list=self.request.POST.getlist("KK")
            count=0
            for elem in models_list:
                count=count+1
                print 'count: %s'%count
                split_models=elem.split("__")
                flag=True
                for i in split_models:
                    app_label,model_name=i.split(".")
                    model=GetModel(app_label,model_name)
                    if model:
                        if hasattr(model,"clear"):
                            try:
                                model.clear()
                                time.sleep(0.1)
                            except:
                                flag=False
                                import traceback; traceback.print_exc()
                                pass
                        else:
                            for obj in model.objects.all():
                                try:
                                    obj.delete()
                                    time.sleep(0.1)
                                except:
                                    flag=False
                                    import traceback; traceback.print_exc()
                                    pass
                    else:
                        flag=False
                if flag:
                    print split_models,'ok\n'
                else:
                    print split_models,'fail\n'