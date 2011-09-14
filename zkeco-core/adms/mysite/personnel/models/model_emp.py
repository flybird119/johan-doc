# -*- coding: utf-8 -*-
from django.db import models, connection
import datetime
import os
import string
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
from dbapp.utils import *
from django.utils.translation import ugettext_lazy as _
from model_dept import DeptForeignKey, DEPT_NAME, Department
from model_morecardempgroup import AccMoreCardEmpGroup

from base.models import CachingModel, Operation, ModelOperation
from dbapp.models import BOOLEANS
from base.cached_model import STATUS_PAUSED, STATUS_OK, STATUS_LEAVE
#from mysite.iclock.dataprocaction import *
from django import forms
from base.base_code import BaseCode, base_code_by
from model_area import Area, AreaManyToManyField
from dbapp import data_edit
from mysite.iclock.models.model_device import DeviceForeignKey, Device
from mysite.iclock.models.dev_comm_operate import *
from mysite.iclock.models.modelproc import get_normal_card
from mysite.iclock.models.model_device import DEVICE_TIME_RECORDER
from base.crypt import encrypt
from django.core.files.storage import FileSystemStorage
from django.core.files import File

photo_storage = FileSystemStorage(
    location=settings.ADDITION_FILE_ROOT,
    #base_url=settings.APP_HOME+"/file"
)

GENDER_CHOICES = (
        ('M', _(u'男')),
        ('F', _(u'女')),
)

PRIV_CHOICES = (
        (0, _(u'普通员工')),
        (2, _(u'登记员')),
        (6, _(u'系统管理员维护')),
        (14, _(u'超级管理员')),
)

EMPTYPE = (
        (1, _(u'正式员工')),
        (2, _(u'试用员工')),
)

NORMAL_FINGER = 1      # 普通指纹
DURESS_FINGER = 3      # 胁迫指纹

init_settings = []
if settings.APP_CONFIG["remove_permision"]:
    init_settings = [ k.split(".")[1] for k, v in settings.APP_CONFIG["remove_permision"].items() if v == "False" and k.split(".")[0] == "Employee"]

def format_pin(pin):
        if type(pin) == int:
            pin = str(pin)
        if not settings.PIN_WIDTH: return pin
        return string.zfill(device_pin(pin.rstrip()), settings.PIN_WIDTH)

def device_pin(pin):
        if not settings.PIN_WIDTH: return pin
        i = 0
        for c in pin[0:-1]:
                if c == "0":
                        i += 1
                else:
                        break
        return pin[i:]

if settings.PIN_WIDTH == 5: MAX_PIN_INT = 65534
elif settings.PIN_WIDTH == 10: MAX_PIN_INT = 4294967294L
elif settings.PIN_WIDTH <= 1: MAX_PIN_INT = 999999999999999999999999L
else: MAX_PIN_INT = int("999999999999999999999999"[:settings.PIN_WIDTH])

CHECK_CLOCK_IN = (
        (0, _(u'依据相应时间段')),
        (1, _(u'上班必须签到')),
        (2, _(u'上班不用签到')),
)

CHECK_CLOCK_OUT = (
        (0, _(u'依据相应时间段')),
        (1, _(u'上班必须签到')),
        (2, _(u'上班不用签到')),
)

def get_default_dept():
        """ 
        获取默认部门，没有则创建
        """
        try:
                dept = Department.objects.get(DeptID=1)
        except:
                try:
                        dept = Department(id=1, name=_(u"总公司"))
                        dept.save()
                except:
                        dept = Department.objects.all()[0]
        return dept

YESORNO = (
        (1, _(u'是')),
        (0, _(u'否')),

)
HIRETYPE = (
        (1, _(u'合同内')),
        (2, _(u'合同外')),

)
LEAVETYPE = (
        (1, _(u'自离')),
        (2, _(u'辞退')),
        (3, _(u'辞职')),
        (4, _(u'调离')),
        (5, _(u'停薪留职')),
)
def show_visible():
    '''是否系统语言为中文且有att app'''
    if settings.APP_CONFIG.language.language=='zh-cn' and "mysite.att" in settings.INSTALLED_APPS:
        return True
    else:
        return False

#def en_query_hide():
#    title_adn_education=[]
#    if settings.APP_CONFIG.language.language!='zh-cn':
#        title_adn_education=[]           
#    else:
#        title_adn_education=['Title','Education'] 
#    if "mysite.att" not in settings.INSTALLED_APPS:
#        title_adn_education=title_adn_education+["level_count",]
#    return title_adn_education
#Education=[]
#if show_visible():
#    Education=['Education',]
#def is_att_only():
#    job_transfer=[]
#    if not show_visible():
#        job_transfer=["optitilechange_employee",]
#    
#    from mysite import settings
#    installed_apps = settings.INSTALLED_APPS
#    if "mysite.iaccess"  not in installed_apps:
#        job_transfer =job_transfer+["delete_employee"]
#    
#    return job_transfer
class Employee(CachingModel):
        id = models.AutoField(db_column="userid", primary_key=True, null=False, editable=False)
        PIN = models.CharField(_(u'人员编号'), db_column="badgenumber", null=False, max_length=20)
        DeptID = DeptForeignKey(db_column="defaultdeptid", verbose_name=DEPT_NAME, editable=True, null=True)
        EName = models.CharField(_(u'姓名'), db_column="name", null=True, max_length=24, blank=True, default="")
        lastname = models.CharField(_(u'姓氏'), max_length=20, null=True, blank=True, editable=True)
        Password = models.CharField(_(u'密码'), max_length=16, null=True, blank=True, editable=True)#加密 增加长度
        Card = models.CharField(_(u'卡号'), max_length=20, null=False, blank=True, editable=True, default='')
        Privilege = models.IntegerField(_(u'是否为设备管理员'), null=True, default=0,blank=True, choices=PRIV_CHOICES)
        AccGroup = models.IntegerField(_(u'门禁组'), null=True, blank=True, editable=True)
        TimeZones = models.CharField(_(u'门禁时间段'), max_length=20, null=True, blank=True, editable=True)
        Gender = models.CharField(_(u'性别'), max_length=2, choices=GENDER_CHOICES, null=True, blank=True)
        Birthday = models.DateField(_(u'生日'), max_length=8, null=True, blank=True)
        Address = models.CharField(_(u'办公地址'), db_column="street", max_length=100, null=True, blank=True)
        PostCode = models.CharField(_(u'邮编'), db_column="zip", max_length=6, null=True, blank=True)
        Tele = models.CharField(_(u'办公电话'), db_column="ophone", max_length=20, null=True, blank=True, default='')
        FPHONE = models.CharField(_(u'家庭电话'), max_length=20, null=True, blank=True)
        Mobile = models.CharField(_(u'手机'), db_column="pager", max_length=20, null=True, blank=True)
        National = models.CharField(_(u'民族'), db_column="minzu", max_length=20, null=True, blank=True, choices=base_code_by('CN_NATION'), editable=True)
        Title = models.CharField(_(u'职务'), db_column="title", max_length=50, null=True, blank=True, choices=base_code_by('TITLE'))
        SSN = models.CharField(_(u'社保号'), max_length=20, null=True, blank=True)
        identitycard = models.CharField(_(u'身份证号码'), max_length=20, null=True, blank=True, default='')
        UTime = models.DateTimeField(_(u'更新时间'), null=True, blank=True, editable=False)
        Hiredday = models.DateField(_(u'聘用日期'), max_length=8, null=True, blank=True, default=datetime.datetime.now().strftime("%Y-%m-%d"))
        VERIFICATIONMETHOD = models.SmallIntegerField(_(u'验证方法'), null=True, blank=True, editable=False)
        State = models.CharField(_(u'省份'), max_length=50, null=True, blank=True, editable=True, choices=base_code_by('IDENTITY'))
        City = models.CharField(_(u'城市'), max_length=50, null=True, blank=True, editable=True, choices=base_code_by('CN_PROVINCE'))
        Education = models.CharField(_(u'学历'), max_length=50, null=True, blank=True, editable=True, choices=base_code_by('EDUCATION'))
        SECURITYFLAGS = models.SmallIntegerField(_(u'动作标志'), null=True, blank=True, editable=False)
        ATT = models.BooleanField(_(u'有效考勤记录'), null=False, default=True, blank=True, editable=True)
        OverTime = models.BooleanField(_(u'是否加班'), null=False, default=True, blank=True, editable=True, choices=YESORNO)
        Holiday = models.BooleanField(_(u'节假日休息'), null=False, default=True, blank=True, editable=True, choices=YESORNO)
        INLATE = models.SmallIntegerField(_(u'上班签到'), null=True, default=0, choices=CHECK_CLOCK_IN, blank=True, editable=True)
        OutEarly = models.SmallIntegerField(_(u'下班签退'), null=True, default=0, choices=CHECK_CLOCK_OUT, blank=True, editable=True)
        Lunchduration = models.SmallIntegerField(_(u'荷兰语'), null=True, default=1, blank=True, editable=False)
        MVerifyPass = models.CharField(_(u'人员密码'), max_length=6, null=True, blank=True, editable=True)
        photo = models.ImageField(storage=photo_storage, upload_to='photo')
        SEP = models.SmallIntegerField(null=True, default=1, editable=False)
        OffDuty = models.SmallIntegerField(_(u"离职标记"), null=False, default=0, editable=False, choices=BOOLEANS)
        DelTag = models.SmallIntegerField(null=False, default=0, editable=False)
        AutoSchPlan = models.SmallIntegerField(_(u'是否自动排班'), null=True, blank=True, default=1, editable=True, choices=YESORNO)
        MinAutoSchInterval = models.IntegerField(null=True, default=24, editable=False)
        RegisterOT = models.IntegerField(null=True, default=1, editable=False)
        #门禁区
        morecard_group = models.ForeignKey(AccMoreCardEmpGroup, verbose_name=_(u'多卡开门人员组'), blank=True, editable=True, null=True)
        set_valid_time = models.BooleanField(_(u'设置有效时间'), default=False, null=False, blank=True)
        acc_startdate = models.DateField(_(u'启用门禁日期'), null=True, blank=True)
        acc_enddate = models.DateField(_(u'结束门禁日期'), null=True, blank=True)

        #新加字段
        birthplace = models.CharField(_(u'籍贯'), max_length=20, null=True, blank=True, editable=True, choices=base_code_by('CN_PROVINCE'))
        Political = models.CharField(_(u'政治面貌'), max_length=20, null=True, blank=True, editable=True)
        contry = models.CharField(_(u'国家'), max_length=20, default="", null=True, blank=True, editable=True, choices=base_code_by('REGION'))
        hiretype = models.IntegerField(_(u'雇佣类型'), null=True, blank=True, editable=True, choices=HIRETYPE)
        email = models.EmailField(_(u'邮箱'), max_length=50, null=True, blank=True, editable=True)
        firedate = models.DateField(_(u'解雇日期'), null=True, blank=True, editable=True)
        attarea = AreaManyToManyField(Area, verbose_name=_(u'考勤区域'), null=True, blank=True, editable=True, default=(1,))
        isatt = models.BooleanField(verbose_name=_(u'是否考勤'), editable=True, null=False, blank=True, choices=YESORNO, default=1)
        homeaddress = models.CharField(_(u'家庭地址'), max_length=100, null=True, blank=True, editable=True)
        emptype = models.IntegerField(_(u'员工类型'), null=True, blank=True, editable=True, choices=EMPTYPE)
        bankcode1 = models.CharField(_(u'银行帐号1'), max_length=50, null=True, blank=True, editable=True)
        bankcode2 = models.CharField(_(u'银行帐号2'), max_length=50, null=True, blank=True, editable=True)
        isblacklist = models.IntegerField(_(u'是否黑名单'), null=True, blank=True, editable=True, choices=YESORNO)
        
        all_objects = models.Manager()
        
        @staticmethod
        def objByID(id):
            try:
                u = Employee.objects.get(id=id)
            except:
                connection.close()
                u = Employee.objects.get(id=id)
            u.IsNewEmp = False

            return u

        @staticmethod
        def demo(id):
            '''
            静态方法 可以通过类名来调用
            '''
            '''Employee.objects.get(id=id)'''

        def delete(self, Init_db=False):
            '''
            实例方法 self 为模型的一个实例,既一条记录
            '''
            from mysite import settings
            from mysite.iclock.models.model_device import Device, DEVICE_TIME_RECORDER
            import os
            installed_apps = settings.INSTALLED_APPS
            filepath = settings.ADDITION_FILE_ROOT + "photo/" + self.PIN + ".jpg"
            if os.path.exists(filepath):
                os.remove(filepath)
            if "mysite.att" in installed_apps:
                if not Init_db:
                    dev=Device.objects.filter(area__in=self.attarea.all()).filter(device_type=DEVICE_TIME_RECORDER)
                    sync_delete_user(dev, [self])
            if "mysite.iaccess" in installed_apps:
                sync_delete_user(self.search_accdev_byuser(), [self])
            super(Employee, self).delete()
            
        @staticmethod
        def clear():
            import time
            Employee.can_restore=True
            for e in Employee.objects.all():
                e.delete(Init_db=True)
                time.sleep(0.1)
            Employee.can_restore=False

        def data_valid(self, sendtype):
            '''
            服务器端验证
            '''
            import re
            try:
               self.PIN = str(int(self.PIN))
            except:
               raise Exception(_(u'人员编号只能为数字'))
            if int(self.PIN) == 0:
                raise Exception(_(u'人员编号不能为0'))
            orgcard = self.Card

            if len(self.PIN) > settings.PIN_WIDTH:
                raise Exception(_(u'%(f)s 人员编号长度不能超过%(ff)s位') % {"f":self.PIN, "ff":settings.PIN_WIDTH})
            self.PIN = format_pin(self.PIN)

            tmp = Employee.objects.filter(PIN__exact=self.PIN)
            if len(tmp) > 0 and tmp[0].id != self.id:   #编辑状态
                raise Exception(_(u'人员编号: %s 已存在') % self.PIN)
            
            if self.identitycard:
                self.__class__.can_restore=True
                tmpid = Employee.objects.filter(identitycard__exact=self.identitycard, isblacklist__exact=1)
                self.__class__.can_restore=False
                if len(tmpid) > 0 :   #编辑状态
                    raise Exception(_(u'%s 已存在黑名单中！') % self.identitycard)

            if self.set_valid_time == True:
                if not self.acc_startdate or not self.acc_enddate:
                    raise Exception(_(u'您已选择设置门禁有效时间,请填写开始日期和结束日期'))
                if self.acc_startdate > self.acc_enddate:
                    raise Exception(_(u'门禁有效时间的开始日期不能大于结束日期'))

            if self.Password:
                if 'mysite.iaccess' in settings.INSTALLED_APPS:
                    from mysite.iaccess.models import AccDoor
                    doors = AccDoor.objects.all()#系统里所有的，不需要权限过滤
                    force_pwd_existed = [d.force_pwd for d in doors]#[int(d.force_pwd) for d in doors if d.force_pwd]
                    from base.crypt import encrypt
                    #由于胁迫密码已经加密，须将人员密码加密后再进行比较
                    if self.Password in force_pwd_existed or encrypt(self.Password) in force_pwd_existed:#不含‘’
                        raise Exception(_(u"人员密码不能与任意门禁胁迫密码相同"))
                p = re.compile(r'^[0-9]+$')
                if not self.pk:#新增时
                    if not p.match(self.Password):
                        raise Exception(_(u"人员密码必须为整数"))
                else:
                    emp = Employee.objects.filter(pk=self.pk)
                    if emp[0].Password == self.Password and not emp[0].Password.isdigit():
                        pass    
                    elif not p.match(self.Password):
                        raise Exception(_(u"人员密码必须为整数"))
        
            if self.Birthday and self.Birthday>datetime.datetime.now().date():
                raise Exception(_(u"生日日期错误"))
            tmpre = re.compile('^[0-9]+$')
            #print self.Card
            if self.Card and not tmpre.search(orgcard):
                raise Exception(_(u'卡号不正确'))
            
            if self.Card:
                tmpcard = Employee.objects.filter(Card=self.Card)
                if tmpcard and tmpcard[0].id != self.id:#用于前端表单验证
                    raise Exception(_(u'卡号已存在，如果确认将重新发卡，请先清除该卡原持卡人 %s') % tmpcard[0])

        def save(self, **args):
            try:
                try:
                   self.PIN = str(int(self.PIN))
                except:
                   raise Exception(_(u'人员编号只能为数字'))
                if int(self.PIN) == 0:
                    raise Exception(_(u'人员编号不能为0'))

                self.PIN = format_pin(self.PIN)

                tmp = Employee.all_objects.filter(PIN__exact=self.PIN)

                if len(tmp) > 0 and tmp[0].id != self.id:   #编辑状态
                    raise Exception(_(u'人员编号: %s 已存在') % self.PIN)
                
               
                if self.Card:#新增或编缉了卡号时
                    tmpcard = Employee.all_objects.filter(Card=self.Card)
                    if tmpcard and tmpcard[0].id != self.id:#此处主要用于批量发卡重复卡号的处理
                        tmpcard[0].Card = ''
                        tmpcard[0].save(force_update=True)#清空原有的，新的写入
                    
                    
                #emp = Employee.objects.filter(id=self.pk)
                #对密码进行加密
                if self.Password!="" or None:
                    if len(tmp) !=0:
                        if tmp[0].Password == self.Password:
                            pass
                        else:
                            self.Password = encrypt(self.Password)
                    else:
                        self.Password = encrypt(self.Password)
    
                super(Employee, self).save(**args)
                installed_apps = settings.INSTALLED_APPS
                if self.Card :#新增或编缉了卡号时
                    IssueCard = self.__class__.issuecard_set.related.model
                    tmp_issuecare = IssueCard.objects.filter(UserID=self, cardno=self.Card)
                    if not tmp_issuecare:
                        issuecard = IssueCard()
                        issuecard.UserID = self
                        issuecard.cardno = self.Card
                        issuecard.issuedate = datetime.datetime.now().strftime("%Y-%m-%d")
                        issuecard.save()

                    if "mysite.att" in installed_apps and (len(tmp)==0 or (tmp and tmp[0].Card!=self.Card)):#zkeco+zktime
                        from mysite.iclock.models.model_cmmdata import adj_user_cmmdata
                        adj_user_cmmdata(self, [], self.attarea.all())
                            #sync_set_user(self.search_device_byuser(), [self])
            except Exception, e:
                    import traceback; traceback.print_exc();
                    raise e

        def pin(self):
                return device_pin(self.PIN)

        def fp_count(self):
            '''
            得到该员工的指纹数
            '''
            return models.get_model("iclock", "fptemp").objects.filter(UserID=self).count()

        def __unicode__(self):
                return self.PIN + (self.EName and u" %s" % self.EName or "")

        class OpLeave(Operation): 
                help_text = _(u"""对员工进行离职操作""")
                verbose_name = _(u'离职')
                params = [
                ('leavedate', models.DateField(verbose_name=_(u'离职日期'))),
                ('leavetype', models.IntegerField(verbose_name=_(u'离职类型'), choices=LEAVETYPE)),
                ('reason', models.CharField(verbose_name=_(u'离职原因'))),
                ('isReturnTools', models.BooleanField(verbose_name=_(u'是否归还工具'), choices=YESORNO)),
                ('isReturnClothes', models.BooleanField(verbose_name=_(u'是否归还工衣'), choices=YESORNO)),
                ('isReturnCard', models.BooleanField(verbose_name=_(u'是否归还卡'), choices=YESORNO)),
                ('closeAtt', models.BooleanField(verbose_name=_(u'立即关闭考勤'), default=True)),
                
                ('isblacklist', models.BooleanField(verbose_name=_(u'是否黑名单'), choices=YESORNO, default=0)),
                ]
                def __init__(self,obj):
                    super(Employee.OpLeave, self).__init__(obj)
                    installed_apps = settings.INSTALLED_APPS
                    if "mysite.iaccess" in installed_apps:#zkeco+iaccess
                        self.params.append(('closeAcc', models.BooleanField(verbose_name=_(u'立即关闭门禁'), default=True)))
                def action(self, leavedate, leavetype,
                        reason, isReturnTools, isReturnClothes, isReturnCard, closeAtt,isblacklist, closeAcc=False            ):                                #定义实际进行操作的函数
                        #from mysite.personnel.models.model_leave import Leave
                        if isReturnCard==1:
                            self.object.Card=""
                        self.object.isblacklist = isblacklist
                        self.object.status = STATUS_LEAVE
                        self.object.save()
                        Leave = self.object.__class__.leavelog_set.related.model
                        t = Leave()
                        t.UserID = self.object
                        t.leavedate = leavedate
                        t.leavetype = leavetype
                        t.reason = reason
                        t.isReturnTools = isReturnTools
                        t.isReturnClothes = isReturnClothes
                        t.isReturnCard = isReturnCard
                        t.save()
                        if closeAtt:
                                t.OpCloseAtt(t).action()
                        if closeAcc:
                                t.OpCloseAccess(t).action()


        class OpAdjustDept(Operation): 
                help_text = _(u'''调整部门''')
                verbose_name = _(u"调整部门")
                params = (
                        ('department', DeptForeignKey(verbose_name=_(u'调整到的部门'))),
                )
                def action(self, department):
                        empchange = self.object.__class__.empchange_set.related.model()
                        empchange.UserID = self.object
                        empchange.changepostion = 1
                        empchange.oldvalue = self.object.DeptID.pk
                        empchange.newvalue = department.pk
                        empchange.save()


        class OpAdjustArea(Operation):
                verbose_name = _(u"调整区域")
                help_text = _(u"调整区域:将会把该人员所属原区域内的设备清除掉该人员，并自动下发到新区域内的所有设备中")
                params = (
                        ('area', AreaManyToManyField(Area, verbose_name=_(u'调整到的区域'))),
                )
                def action(self, area):
                        from mysite.iclock.models.model_cmmdata import adj_user_cmmdata
                        oldObj = self.object
                        import copy
                        oldarea = copy.deepcopy(oldObj.attarea.all())

                        empchange = self.object.__class__.empchange_set.related.model()
                        empchange.UserID = self.object
                        empchange.changepostion = 4
                        empchange.oldvalue = ",".join(["%s" % i.pk for i in  self.object.attarea.all()])
                        empchange.newvalue = ",".join(["%s" % i.pk for i in  area])
                        empchange.changedate = datetime.datetime.now()
                        empchange.save(log_msg=False, force_insert=True)

                        self.object.attarea = area
                        self.object.save(log_msg=False)
                        newObj = self.object

                        adj_user_cmmdata(self.object, Area.objects.filter(pk__in=oldarea), area)

                def action_batch(self, area):
                        from mysite.iclock.models.model_cmmdata import adj_user_cmmdata, save_userarea_together
                        datalist = []
                        for oldObj in self.object:
                            empchange = oldObj.__class__.empchange_set.related.model()
                            empchange.changepostion = 4
                            empchange.newvalue = ",".join(["%s" % i.pk for i in  area])
                            empchange.changedate = datetime.datetime.now()
                            new_devs = None
                            import copy

                            old_attarea = copy.deepcopy(oldObj.attarea.select_related())
                            devs = set(list(Device.objects.filter(area__in=old_attarea).filter(device_type=DEVICE_TIME_RECORDER)))    #只管理考勤
                            empchange.oldvalue = ",".join(["%s" % i.pk for i in old_attarea])
                            empchange.UserID = oldObj
                            empchange.changeno = None
                            empchange.save()
                            oldObj.attarea = area
                            oldObj.save(log_msg=False)
                            if new_devs is None:
                                new_devs = set(list(oldObj.search_device_byuser()))
                            datalist.append(adj_user_cmmdata([oldObj], old_attarea, area, True))
                        save_userarea_together(self.object, area, datalist)
        class OpUploadPhoto(Operation):
                help_text = _(u'''上传个人照片''')
                verbose_name = _(u"上传个人照片")
                only_one_object = True
                params = (
                        ('fileUpload', models.ImageField(verbose_name=_(u'选择个人照片'), blank=True, null=True)),
                )
                def action(self, fileUpload):
                    import datetime
                    if self.request.FILES:
                        f=self.request.FILES['fileUpload']
                        self.object.photo.save(datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")+".jpg",f)
                        

        class OpIssueCard(Operation):
                verbose_name = _(u"人员发卡")
                help_text = _(u"目前支持手动输入卡号以及使用发卡器发卡！")
                only_one_object = True
                params = (
                        ('card', models.CharField(verbose_name=_(u'人员发卡'))),
                )
                def action(self, card):
                    if card != "":

                        import re
                        tmp = re.compile('^[0-9]+$')
                        if not tmp.search(card):
                            raise Exception(_(u'卡号不正确'))

                        tmpcard = Employee.objects.filter(Card=card)
                        if tmpcard:
                            #raise Exception(_(u'卡号已存在，如果确认将重新发卡，请先清除该卡原持卡人 %s' % tmpcard[0]))
                            raise Exception(_(u'卡号已存在，如果确认将重新发卡，请先清除该卡原持卡人 %s') % tmpcard[0])

                        self.object.Card = card
                        self.object.save()
        class OpRegisterFinger(Operation):
               verbose_name = _(u"登记指纹")
               help_text = _(u"指纹登记需要指纹仪驱动，如果您未安装驱动，请先下载驱动程序！")
               only_one_object = True

               params = (
                   ('tfcount', models.CharField(verbose_name=_(u'模版数量'), max_length=10, blank=True, null=True)),
                   ('tfids', models.CharField(verbose_name=_(u'手指编号'), max_length=20, blank=True, null=True)),
                   ('tfcount10', models.CharField(verbose_name=_(u'模版数量'), max_length=10, blank=True, null=True)),
                   ('tfids10', models.CharField(verbose_name=_(u'手指编号'), max_length=20, blank=True, null=True)),
                   ('fpcode', models.CharField(verbose_name=_(u'手指类型'), max_length=20, blank=True, null=True)),
                   ('tlng', models.CharField(verbose_name=_(u'当前语言'), max_length=10, blank=True, null=True)),

               )
               def __init__(self, obj):
                   from mysite.iclock.models.model_bio import Template
                   super(Employee.OpRegisterFinger, self).__init__(obj)
                   t9 = Template.objects.filter(UserID=obj, Fpversion=9)
                   t10 = Template.objects.filter(UserID=obj, Fpversion=10)
                   tcount = 0
                   tfingerid = ""
                   #if len(t) > 0:
                   if len(t10)>0 and len(t10)>=len(t9):
                       tcount = len(t10)
                       tfingerid = ",".join(["%s" % i.FingerID for i  in t10])
                       fptypecode = ",".join(["%s" % i.Valid for i in t10])    # 指纹类型代码
                   else:
                       tcount = len(t9)
                       tfingerid = ",".join(["%s" % i.FingerID for i  in t9])  
                       fptypecode = ",".join(["%s" % i.Valid for i in t9])    # 指纹类型代码

                   params = dict(self.params)

                   tfcount = params['tfcount']
                   tfcount.label = _(u'模版数量')
                   tfcount.default = tcount
                   params['tfcount'] = tfcount

                   tfids = params['tfids']
                   tfids.label = _(u'手指编号')
                   tfids.default = tfingerid
                   params['tfids'] = tfids
                   
                   fpcode = params['fpcode']
                   fpcode.label = _(u'手指类型')
                   fpcode.default = fptypecode
                   params['fpcode'] = fpcode

                   from base.models import options
                   from mysite import settings
                   lng = options['base.language']
                  
                   tlng = params['tlng']
                   tlng.label = _(u'当前语言')
                   tlng.default = lng
                   params['tlng'] = tlng


                   self.params = tuple(params.items())

               def action(self, tfcount, tfids, tfcount10, tfids10, fpcode, tlng):
                   if self.request:
                       save_finnger(self.request, self.object)
                       sync_set_user_fingerprint(self.object.search_device_byuser(), [self.object])
                       del_finnger(self.request, self.object)


        class OpTitileChange(Operation):
                help_text = _(u'''职务调动''')
                verbose_name = _(u"职务调动")
                visible=show_visible()
                params = (
                        ('ttitle', models.CharField(verbose_name=_(u'选择职务'), choices=base_code_by('TITLE'))),
                                )
                def action(self, ttitle):
                    if ttitle:
                        empchange = self.object.__class__.empchange_set.related.model()
                        empchange.UserID = self.object
                        empchange.changepostion = 2
                        empchange.oldvalue = self.object.Title
                        empchange.newvalue = ttitle
                        empchange.save()

                        self.object.Title = ttitle
                        self.object.save()
        class OpEmpType(Operation):
                help_text = _(u'''员工转正''')
                verbose_name = _(u"员工转正")
                params = (
                        ('emptype', models.IntegerField(verbose_name=_(u'员工转正'), choices=EMPTYPE)),
                                )
                def action(self, emptype):
                        if emptype:
                                empchange = self.object.__class__.empchange_set.related.model()
                                empchange.UserID = self.object
                                empchange.changepostion = 3
                                empchange.oldvalue = self.object.emptype
                                empchange.newvalue = emptype
                                empchange.save()
                                self.object.hiretype = 2
                                self.object.emptype = emptype
                                self.object.save()

        #数据中心处理接口
        def check_accprivilege(self):
            from mysite.iaccess.models import AccLevelSet
            try:
                if self.acclevelset_set.all():
                    return True
                else:
                    return False
            except:
                return False
        def search_device_byuser(self): #考勤用
            from mysite.iclock.models import Device
            return Device.objects.filter(area__in=self.attarea.select_related()).filter(device_type=DEVICE_TIME_RECORDER)

        def search_accdev_byuser(self):
            from mysite.iclock.models import Device
            sql = "select distinct device_id from acc_door where  id in (select accdoor_id from acc_levelset_door_group where acclevelset_id in (select acclevelset_id from acc_levelset_emp where employee_id = %d))" % self.id
            #print "search_accdev_byuser sql=", sql
            cursor = connection.cursor()
            cursor.execute(sql)
            fet = set(cursor.fetchall())
            dev = []
            ss = [dev.append(int(f[0])) for f in fet]
            #print dev
            return Device.objects.filter(id__in=dev).filter(device_type=DEVICE_ACCESS_CONTROL_PANEL)

        def get_attarea(self):
            return u",".join([a.areaname for a in self.attarea.all()])
#            return ['333333333333333333333333']
        def get_template(self):
            verbose_name = _(u"指纹模板")
            from mysite.iclock.models import Template
            t9 = Template.objects.filter(UserID=self, Fpversion="9")
            t10 = Template.objects.filter(UserID=self, Fpversion="10")
            #if len(t10)>=len(t9):
            #    return _(u"%(f)s ") % {'f':len(t10)}
            #else:
            #    return _(u"%(f)s ") % {'f':len(t9)}
            return _(u"9.0指纹数:%(f)s ; 10.0指纹数:%(f1)s") % {'f':len(t9), 'f1':len(t10)}            
        class Admin(CachingModel.Admin):
                #把人员浏览权限赋予其他需要此权限的任何地方,来达到一个权限多用的目的
                default_give_perms = ["personnel.browse_issuecard", "att.browse_setuseratt", "att.opaddmanycheckexact_checkexact", "personnel.browse_leavelog", "contenttypes.can_AttDeviceUserManage", "att.browse_empspecday", "personnel.browse_empchange", "contenttypes.can_AttUserOfRun", "contenttypes.can_AttCalculate", "contenttypes.can_EmpLevelSetPage", \
                                    "opaddleveltoemp_employee", "opdellevelfromemp_employee", "personnel.browse_accmorecardempgroup", "iaccess.browse_accfirstopen", "contenttypes.can_EmpLevelSetPage"]
                layout_types = ["table", "photo",'johan','json']    #    列表浏览方式
                sort_fields = ["PIN","DeptID.code"] # 排序字段
                photo_path = "photo"#指定图片的路径，如果带了".jpg",就用这个图片，没有带的话就找这个字符串所对应的字段的值
                
                app_menu = "personnel"
                list_display = ['PIN', 'EName', 'DeptID.code', 'DeptID.name', 'Gender','Privilege', 'attarea', 'get_template','Card', 'identitycard','Tele', 'Mobile', 'photo']#+en_query_hide()
                adv_fields = ['PIN', 'EName', 'DeptID.code', 'DeptID.name', 'Gender', 'Card',  'identitycard',  'Tele', 'Mobile', 'attarea']#+en_query_hide();
                newadded_column = { 'attarea': 'get_attarea', 'template': 'get_template' }
                hide_fields = ['photo', ]
                list_filter = ('DeptID', 'Gender', 'Title',)
                search_fields = ['PIN', 'EName']
                query_fields = ['PIN', 'EName', 'Card', 'Mobile', 'DeptID__name', 'identitycard']
                query_fields_iaccess = ['PIN', 'EName', 'Card', 'DeptID__name']
                help_text = _(u"人员信息是系统的基本信息，人员编号、部门为必填项<br>指纹登记需要指纹仪驱动，如果您未安装驱动，请先下载驱动程序！<br>黑白屏考勤机仅支持5位密码，彩屏考勤机支持8位密码，门禁控制器仅支持6位密码，超过规定长度后系统将自动截取！")
                cache = True
                menu_index = 2
                import_fields = ('PIN', 'EName', 'DeptID', 'Gender', 'Card', 'identitycard', 'Mobile')
                default_widgets = {'MVerifyPass': forms.PasswordInput}
                default_widgets = {'Password': forms.PasswordInput}
                api_m2m_display = { "attarea" : "areaname", }
                disabled_perms = ["clear_employee"] + init_settings
                hide_perms = ["opaddleveltoemp_employee", "opdellevelfromemp_employee"]#+is_att_only()
                #select_related_perms = {"browse_employee": "opaddleveltoemp_employee"}
                opt_perm_menu = { "opaddleveltoemp_employee": "iaccess.EmpLevelByEmpPage", "opdellevelfromemp_employee": "iaccess.EmpLevelByEmpPage" }#配置到其他目录下

        class Meta:
                app_label = 'personnel'
                db_table = 'userinfo'
                verbose_name = _(u"人员")
                verbose_name_plural = verbose_name
                unique_together = (('PIN',),)

installed_apps = settings.INSTALLED_APPS
if "mysite.iaccess" in installed_apps and "mysite.att" in installed_apps:
    pass#默认
elif "mysite.iaccess" in installed_apps:#门禁
    Employee.Admin.help_text = _(u'人员信息是系统的基本信息，人员编号、部门为必填项<br>门禁控制器仅支持6位密码，超过规定长度后系统将自动截取！')
else:#考勤
    Employee.Admin.help_text = _(u'人员信息是系统的基本信息，人员编号、部门为必填项<br>指纹登记需要指纹仪驱动，如果您未安装驱动，请先下载驱动程序！<br>黑白屏考勤机仅支持5位密码，彩屏考勤机支持8位密码，超过规定长度后系统将自动截取！')

class EmpForeignKey(models.ForeignKey):
        def __init__(self, to_field=None, **kwargs):
                super(EmpForeignKey, self).__init__(Employee, to_field=to_field, **kwargs)
class EmpMultForeignKey(models.ManyToManyField):
        def __init__(self, *args, **kwargs):
                super(EmpMultForeignKey, self).__init__(Employee, *args, **kwargs)
class EmpPoPForeignKey(models.ForeignKey):
        def __init__(self, to_field=None, **kwargs):
                super(EmpPoPForeignKey, self).__init__(Employee, to_field=to_field, **kwargs)
class EmpPoPMultForeignKey(models.ManyToManyField):
        def __init__(self, *args, **kwargs):
                super(EmpPoPMultForeignKey, self).__init__(Employee, *args, **kwargs)

from mysite.iclock.models.model_bio import Template

#处理指纹模版/个人照片
def save_finnger(request, newObj):
    fingger = request.REQUEST.get("finnger", "")
    template = request.REQUEST.get("template", "")
    finger_type = request.REQUEST.get("fptype", "")
    if finger_type:
        finger_type = finger_type.split(",")
    if fingger and template:
        fingger = fingger.split(",")
        template = template.split(",")
        for i in range(len(fingger)):
            t = Template.objects.filter(UserID=newObj, FingerID__exact=fingger[i], Fpversion="9")
            if not t:
                t = Template()
            else:
                t = t[0]
            t.UserID = newObj
            t.Template = template[i]
            t.FingerID = fingger[i]
            t.Valid = finger_type[i]
            t.Fpversion = "9"
            t.save()
    fingger = request.REQUEST.get("finnger10", "")
    template = request.REQUEST.get("template10", "")
    if fingger and template:
        fingger = fingger.split(",")
        template = template.split(",")
        for i in range(len(fingger)):
            t = Template.objects.filter(UserID=newObj, FingerID__exact=fingger[i], Fpversion="10")
            if not t:
                t = Template()
            else:
                t = t[0]
            t.UserID = newObj
            t.Template = template[i]
            t.FingerID = fingger[i]
            t.Valid = finger_type[i]
            t.Fpversion = "10"
            t.save()

def del_finnger(request, oldObj):
    from mysite import settings
    from mysite.iclock.models.model_device import Device, DEVICE_TIME_RECORDER
    installed_apps = settings.INSTALLED_APPS
    delfingger = request.REQUEST.get("delfinger", "")
    if delfingger:
        delfingger = delfingger.split(",")
        for i in range(len(delfingger)):
            t = Template.objects.filter(UserID=oldObj, FingerID__exact=delfingger[i])
            fliter = "PIN=%s\tFingerID=%s"%(oldObj.PIN,delfingger[i])
            #fliter = "PIN=%s"%oldObj.PIN
            #fliter = "PIN=%s\tFingerID=%s\tFingerID=%s\tFingerID=%s\tFingerID=%s\tFingerID=%s\tFingerID=%s\tFingerID=%s\tFingerID=%s\tFingerID=%s\tFingerID=%s" % (oldObj.PIN,0,1,2,3,4,5,6,7,8,9)
            table = "templatev10"
            if t:
                #attflag = False
                iaccessflag = False
                #if "mysite.att" in installed_apps:#zkeco+zktime
                #    dev=Device.objects.filter(area__in=self.attarea.all()).filter(device_type=DEVICE_TIME_RECORDER)
                #    sync_delete_user_finger(dev, table, fliter)
                #    attflag = True
                #else:
                #    attflag = True
                if "mysite.iaccess" in installed_apps:
                    dev = oldObj.search_accdev_byuser()
                    sync_delete_user_finger(dev, table, fliter)
                    iaccessflag = True
                else:
                    iaccessflag = True
                #if attflag and iaccessflag:
                if iaccessflag:
                    t.delete()
                    print '*********** Delete the finger of user is successful! *************************'
                else:
                    print '*********** Delete the finger of user is faled! ********************'

#处理个人照片
def saveUploadImage(request, fname, path=None):
    from   mysite import settings
    import StringIO
    import os
    photopath = path or settings.ADDITION_FILE_ROOT + "photo/"
    fname = photopath + fname
    #print "fname:%s" % fname
    try:
        os.makedirs(os.path.split(fname)[0])
    except: pass
    output = StringIO.StringIO()
    f = request.FILES.get('fileUpload', None)
    if not f:
        return  None
    for chunk in f.chunks():
        output.write(chunk)
    try:
        import PIL.Image as Image
    except:
        return None
    try:
        output.seek(0)
        im = Image.open(output)
    except IOError, e:
        return None
    size = f.size
    try:
        im.save(fname);
    except IOError:
        im.convert('RGB').save(fname)
    return size

#在表单提前，加入自定义字段
def detail_resplonse(sender, **kargs):
        from dbapp.widgets import form_field, check_limit
        from mysite.iclock.models import Template
        from mysite import settings
        import os
        
       
        if kargs['dataModel'] == Employee:
                form = sender['form']

                isexits = False
                tcount = 0
                tfingerid = ""
                fptypecode = ""
                #durtcount = 0
                #durfpid = ""
                tcount10 = 0
                tfingerid10 = ""

                pin = ""
                lng = 'chs'
                if kargs['key'] != None:
                    pin = Employee.objects.get(pk=kargs['key']).PIN
                    t9 = Template.objects.filter(UserID__exact=kargs['key'], Fpversion='9')#9.0指纹模版
                    t10 = Template.objects.filter(UserID__exact=kargs['key'], Fpversion='10')#9.0指纹模版
                    if len(t10)>0 and len(t10)>=len(t9):
                        #tcount = len(t)
                        tfingerid = ",".join(["%s" % i.FingerID for i  in t10])
                    else:
                        tfingerid = ",".join(["%s" % i.FingerID for i  in t9])
                    
                    t9 = Template.objects.filter(UserID__exact=kargs['key'], Fpversion='9')   #指纹数量
                    t10 = Template.objects.filter(UserID__exact=kargs['key'], Fpversion='10')   #指纹数量
                    if len(t10)>0 and len(t10)>=len(t9):
                        tcount = len(t10)
                        fptypecode = ",".join(["%s" % i.Valid for i in t10])     # 指纹类型代码
                    else:
                        tcount = len(t9)
                        fptypecode = ",".join(["%s" % i.Valid for i in t9])     # 指纹类型代码
                

                    #t = Template.objects.filter(UserID__exact=kargs['key'], Fpversion='9', Valid=DURESS_FINGER)   #胁迫指纹数量
                    #if len(t) > 0:
                    #    durtcount = len(t)
                    #    durfpid = ",".join(["%s" % i.FingerID for i in t])
           
                    
                    t = Template.objects.filter(UserID__exact=kargs['key'], Fpversion='10')#10.0指纹模板
                    if len(t) > 0:
                        tcount10 = len(t)
                        tfingerid10 = ",".join(["%s" % i.FingerID for i  in t])


                photopath = settings.ADDITION_FILE_ROOT + "photo/" + pin + ".jpg"
                if os.path.isfile(photopath):
                    isexits = True

                from base.models import options
                from mysite import settings
                
                lng = options['base.language']
                #print "lng:%s" % lng
                chkph = models.BooleanField(verbose_name=_(u'判断个人照片存在'), default=isexits, blank=True, null=True)
                tfcount = models.CharField(verbose_name=_(u'指纹模版数量'), max_length=10, default=tcount, blank=True, null=True)
                fpcode = models.CharField(verbose_name=_(u'手指类型'), max_length=20, default=fptypecode, blank=True, null=True)
                #durtfcount = models.CharField(verbose_name=_(u'胁迫指纹模版数量'), max_length=10, default=durtcount, blank=True, null=True)
                #durfingerid = models.CharField(verbose_name=_(u'胁迫指纹id'), max_length=10, default=durfpid, blank=True, null=True)
                tfids = models.CharField(verbose_name=_(u'手指编号'), max_length=20, default=tfingerid, blank=True, null=True)
                tlng = models.CharField(verbose_name=_(u'当前语言'), max_length=10, default=lng, blank=True, null=True)
                tfcount10 = models.CharField(verbose_name=_(u'模版数量'), max_length=10, default=tcount10, blank=True, null=True)
                tfids10 = models.CharField(verbose_name=_(u'手指编号'), max_length=20, default=tfingerid10, blank=True, null=True)
                pin_width = models.IntegerField(null=True, blank=True, default=settings.PIN_WIDTH)
                #安装语言
               # kargs["install_language"]=settings.APP_CONFIG.language.language
                install_language = models.CharField(verbose_name=_(u'安装语言'), max_length=20, default=settings.APP_CONFIG.language.language, blank=True, null=True)
                form.fields['install_language'] = form_field(install_language)
                                
                
                form.fields['chkph'] = form_field(chkph)
                form.fields['tcount'] = form_field(tfcount)
                form.fields['tfids'] = form_field(tfids)
                form.fields['fpcode'] = form_field(fpcode)
                #form.fields['durtcount'] = form_field(durtfcount)
                #form.fields['durfpid'] = form_field(durfingerid)
                form.fields['lng'] = form_field(tlng)
                form.fields['tcount10'] = form_field(tfcount10)
                form.fields['tfids10'] = form_field(tfids10)
                form.fields['pin_width'] = form_field(pin_width)

data_edit.pre_detail_response.connect(detail_resplonse)



#在表单提交后，对自定义字段进行处理
def DataPostCheck(sender, **kwargs):
    oldObj = kwargs['oldObj']
    newObj = kwargs['newObj']
    request = sender
    if isinstance(newObj, Employee):

        installed_apps = settings.INSTALLED_APPS
#        if saveUploadImage(request, newObj.PIN + ".jpg"):
#            photopath = settings.ADDITION_FILE_ROOT + "photo/"
#            newObj.photo = "/file/photo/" + newObj.PIN + ".jpg"
#            newObj.save()
        if "mysite.att" or "mysite.iaccess" in installed_apps:#zkeco+zktime
            #fingger=request.REQUEST.get("finnger","")
            #template=request.REQUEST.get("template","")

            save_finnger(request, newObj)            #保存指纹
            del_finnger(request, oldObj)             #删除指纹
            from mysite.iclock.models.model_cmmdata import adj_user_cmmdata
            if oldObj is None:  #新增人员
                if len(newObj.attarea.all()) == 0:
                    newObj.attarea.add(Area.objects.get(pk=1))
                    newObj.save()

                adj_user_cmmdata(newObj, [], newObj.attarea.all())
                #sync_set_user(newObj.search_device_byuser(), [newObj])
            else:   #修改人员信息
                area = []
                if oldObj.attarea_set != newObj.attarea_set:
                    #devs=oldObj.search_device_byuser()
                    for attarea in oldObj.attarea_set:
                        area.append(attarea)
                    #print "area=", area
                    #devs=Device.objects.filter(area__in=area).filter(device_type=DEVICE_TIME_RECORDER)
                    #print "devs=", devs
                #    sync_delete_user(devs, [oldObj])
                #sync_set_user(newObj.search_device_byuser(), [newObj])
                adj_user_cmmdata(newObj, area, newObj.attarea.all())
                #print "upload fingerprint"

        if "mysite.iaccess" in installed_apps:#zkeco+iaccess
            from mysite.iaccess.models import AccLevelSet
            levels = request.POST.getlist("level")
            changed = request.POST.getlist("level_changed")
            #print "changed=", changed
            if changed:
                #删除人的旧权限
                emp_obj = newObj#当前要操作的对象（人）
                emp_levels = emp_obj.acclevelset_set.all()#和人关联的所有权限组
                devset = []
                for emp_level in emp_levels:
                    for door in emp_level.door_group.all():
                        devset.append(door.device)
                    emp_level.emp.remove(emp_obj.id)
                dev = set(devset)
                sync_delete_user_privilege(dev, [emp_obj])
                #同步人的新权限
                devset = []
                for level in levels:#以权限组为中心，循环权限组
                    obj = AccLevelSet.objects.get(pk=level)
                    obj.emp.add(emp_obj.id)
                    for door in obj.door_group.all():
                        devset.append(door.device)
                dev = set(devset)
                sync_set_user(dev, [emp_obj])
                sync_set_user_privilege(dev, [emp_obj])
            else:
                sync_set_user(newObj.search_accdev_byuser(), [newObj])

data_edit.post_check.connect(DataPostCheck)

def update_dept_widgets():
    '''
    添加字段映射的部件
    '''
    from dbapp import widgets
    if EmpForeignKey not in widgets.WIDGET_FOR_DBFIELD_DEFAULTS:
            from empwidget import ZEmpChoiceWidget, ZMulEmpChoiceWidget, ZMulPopEmpChoiceWidget, ZPopEmpChoiceWidget
            widgets.WIDGET_FOR_DBFIELD_DEFAULTS[EmpForeignKey] = ZEmpChoiceWidget
            widgets.WIDGET_FOR_DBFIELD_DEFAULTS[EmpMultForeignKey] = ZMulEmpChoiceWidget
            widgets.WIDGET_FOR_DBFIELD_DEFAULTS[EmpPoPForeignKey] = ZPopEmpChoiceWidget
            widgets.WIDGET_FOR_DBFIELD_DEFAULTS[EmpPoPMultForeignKey] = ZMulPopEmpChoiceWidget
update_dept_widgets()

