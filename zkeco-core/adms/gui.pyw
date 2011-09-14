# -*- coding: utf-8 -*-
import win32api, win32gui
import win32con, winerror
import sys, os
import dict4ini
import socket
import wx
import wx.lib.buttons
import wx.lib.stattext
import wx.lib.filebrowsebutton
from  pyDes import *
from wx.lib.anchors import LayoutAnchors
import time




def is_service_stoped():
    s=os.popen("sc.exe query ZKECOWEBService").read()
    if ": 1  STOPPED" in s:
        return True
    return False

def get_attsite_file():
    #current_path=os.path.split(__file__)[0]
    #if not current_path:
    if hasattr(sys, "frozen"):
        current_path=os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding( )))
    else:
        current_path=os.path.dirname(unicode(__file__, sys.getfilesystemencoding( )))

    if not current_path:
        current_path=os.getcwd()
    attsite=dict4ini.DictIni(current_path+"/attsite.ini")
    return attsite

def is_datacenter_stoped():
    s=os.popen("sc.exe query ZKECOWEBService").read()
    if ": 1  STOPPED" in s:
        return True
    return False

def get_i18_dict():
    d_language={
        "en":"en_inno.ini",
        "zh-cn":"cns_inno.ini"
    }
    if hasattr(sys, "frozen"):
        current_path=os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding( )))
    else:
        current_path=os.path.dirname(unicode(__file__, sys.getfilesystemencoding( )))
    if not current_path:
        current_path=os.getcwd()
    appconf=dict4ini.DictIni(current_path+"/appconfig.ini")
    language=u"%s"%appconf["language"]["language"]
    res_dict=dict4ini.DictIni(current_path+"/"+d_language[language])
    return res_dict["trans"]

def gettext(str_source):
    res_dict=get_i18_dict()
    if res_dict[str_source]:
        return u"%s"%res_dict[str_source]
    else:
        return u"%s"%str_source
def control_services(YesNoClose, local_db=True):
    from mysite import settings
    if YesNoClose:
        os.system("net stop ZKECOWEBService")
        os.system("net stop ZKECOBackupDB")
        os.system("net stop memcached")
        if local_db:
            os.system("net stop ZKECOMYSQL")
        if "mysite.iaccess" in settings.INSTALLED_APPS:
            os.system("net stop ZKECODataCommCenterService")
        if "mysite.att" in settings.INSTALLED_APPS:
            os.system("net stop ZKECOWriteDataService")
            os.system("net stop ZKECOInstantMessage")
    else:
        os.system("net start ZKECOWEBService")
        os.system("net start ZKECOBackupDB")
        os.system("net start memcached")
        if local_db:
            os.system("net start ZKECOMYSQL")
        if "mysite.iaccess" in settings.INSTALLED_APPS:
            os.system("net start ZKECODataCommCenterService")
        if "mysite.att" in settings.INSTALLED_APPS:
            os.system("net start ZKECOInstantMessage")
            os.system("net start ZKECOWriteDataService")

def check_port(txt_port,lbl_status):
     ret=False
     try:
        port=int(txt_port.Value)
     except Exception:
        lbl_status.Label=gettext(u'port_need_number')
        return False
     sk=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
     try:
         sk.bind(('127.0.0.1',port))
         ret= True
     except Exception:
         ret= False
     finally:
         sk.close()
     if ret:
         lbl_status.Label=gettext(u'port_enable')
     else:
         lbl_status.Label=gettext(u'port_use')


def save_dbinfo(dbframe):
    import subprocess
    db_dict=get_attsite_file()
    db_engine={
        "mysql":"mysql",
        "oracle10g":"oracle",
        "sqlserver2005":"sqlserver_ado"
    }

    port=None
    try:
        port=int(dbframe.txt_port.Value)

        dbframe.lbl_result.Label=gettext(u'dbinfo_save_success_restart')
        
    except Exception:
        dbframe.lbl_result.Label=gettext(u'port_need_number')
        return False
    txt_value=dbframe.txt_dbtype.Value.strip()
    db_dict["DATABASE"]["ENGINE"]=(txt_value in db_engine.keys()) and  db_engine[txt_value] or txt_value
    db_dict["DATABASE"]["NAME"]=dbframe.txt_dbname.Value.strip()
    db_dict["DATABASE"]["USER"]=dbframe.txt_user.Value.strip()
    db_dict["DATABASE"]["PASSWORD"]=dbframe.txt_pwd.Value.strip()
    db_dict["DATABASE"]["HOST"]=dbframe.txt_ip.Value.strip()
    db_dict["DATABASE"]["PORT"]=dbframe.txt_port.Value.strip()
    db_dict.save()

    #control_services(True)
    #control_services(False)

def save_mid_dbinfo(dbframe):
    import subprocess
    db_dict=get_attsite_file()
    db_engine={
        "mysql":"mysql",
        "oracle10g":"oracle",
        "sqlserver2005":"sqlserver_ado"
    }
    port=None
    try:
        port=int(dbframe.txt_port.Value)
        dbframe.lbl_result.Label=gettext(u'dbinfo_save_success_restart')
    except Exception:
        dbframe.lbl_result.Label=gettext(u'port_need_number')
        return False
    txt_value=dbframe.txt_dbtype.Value.strip()
    db_dict["MID_DATABASE"]["ENGINE"]=(txt_value in db_engine.keys()) and  db_engine[txt_value] or txt_value
    db_dict["MID_DATABASE"]["NAME"]=dbframe.txt_dbname.Value.strip()
    db_dict["MID_DATABASE"]["USER"]=dbframe.txt_user.Value.strip()
    db_dict["MID_DATABASE"]["PASSWORD"]=dbframe.txt_pwd.Value.strip()
    db_dict["MID_DATABASE"]["HOST"]=dbframe.txt_ip.Value.strip()
    db_dict["MID_DATABASE"]["PORT"]=dbframe.txt_port.Value.strip()
    db_dict.save()
def revert(dbframe):
    #取得原始数据库信息

     db_dict_get=get_attsite_file()["MID_DATABASE"]

    #初始化 页面显示信息 从 attsite中读取信息
     dbengine=db_dict_get["ENGINE"]
     dbname=db_dict_get["NAME"]
     dbuser=db_dict_get["USER"]
     dbpassword=db_dict_get["PASSWORD"]
     dbhost=db_dict_get["HOST"]
     dbport=db_dict_get["PORT"]

     import subprocess
     db_dict=get_attsite_file()

    #把原始数据配置信息写入到attsite文件中去
     db_dict["DATABASE"]["ENGINE"]=dbengine
     db_dict["DATABASE"]["NAME"]=dbname
     db_dict["DATABASE"]["USER"]=dbuser
     db_dict["DATABASE"]["PASSWORD"]=dbpassword
     db_dict["DATABASE"]["HOST"]=dbhost
     db_dict["DATABASE"]["PORT"]=dbport
     db_dict.save()


def save_webserver_port(txt_port,lbl_status):
    db_dict=get_attsite_file()
    port=None
    try:
        port=int(txt_port.Value)
        lbl_status.Label=gettext(u'portinfo_save_success')
    except Exception:
        lbl_status.Label=gettext(u'port_need_number')
        return False
    db_dict["Options"]["Port"]=port
    db_dict.save()
    os.system("net stop ZKECOWEBService")
    os.system("net start ZKECOWEBService")


[wxID_DIALOG1, wxID_DIALOG1BTN_CLOSE, wxID_DIALOG1BTN_TEST, wxID_DIALOG1BTN_SAVE,
 wxID_DIALOG1LBL_DBINFO, wxID_DIALOG1LBL_DBNAME, wxID_DIALOG1LBL_DBTYPE,
 wxID_DIALOG1LBL_IP, wxID_DIALOG1LBL_PORT, wxID_DIALOG1LBL_PWD,
 wxID_DIALOG1LBL_RESULT, wxID_DIALOG1LBL_USER, wxID_DIALOG1STATICTEXT1,
 wxID_DIALOG1TXT_DBNAME, wxID_DIALOG1TXT_DBTYPE, wxID_DIALOG1TXT_IP,
 wxID_DIALOG1TXT_PORT, wxID_DIALOG1TXT_PWD, wxID_DIALOG1TXT_USER,
] = [wx.NewId() for _init_ctrls in range(19)]

class DialogDb(wx.Dialog):
    def _init_ctrls(self, prnt):
        # generated method, don't edit
        wx.Dialog.__init__(self, id=wxID_DIALOG1, name='', parent=prnt,
              pos=wx.Point(539, 130), size=wx.Size(535, 388),
              style=wx.DEFAULT_DIALOG_STYLE, title=gettext(u'db_connect_settings'))
        self.SetClientSize(wx.Size(527, 354))

        self.lbl_dbinfo = wx.StaticBox(id=wxID_DIALOG1LBL_DBINFO,
              label=gettext(u"db_connect_settings"),
              name=u'lbl_dbinfo', parent=self, pos=wx.Point(32, 24),
              size=wx.Size(456, 272), style=0)

        self.lbl_dbType = wx.StaticText(id=wxID_DIALOG1LBL_DBTYPE,
              label=gettext(u"db_type"), name=u'lbl_dbType',
              parent=self, pos=wx.Point(69, 57), size=wx.Size(128, 14),
              style=wx.ALIGN_RIGHT)

        self.lbl_user = wx.StaticText(id=wxID_DIALOG1LBL_USER,
              label=gettext(u"usrname"), name=u'lbl_user', parent=self,
              pos=wx.Point(70, 125), size=wx.Size(127, 14),
              style=wx.ALIGN_RIGHT)

        self.lbl_dbName = wx.StaticText(id=wxID_DIALOG1LBL_DBNAME,
              label=gettext(u"db_name"), name=u'lbl_dbName',
              parent=self, pos=wx.Point(70, 92), size=wx.Size(127, 14),
              style=wx.ALIGN_RIGHT)

        self.lbl_pwd = wx.StaticText(id=wxID_DIALOG1LBL_PWD,
              label=gettext(u"pwd"), name=u'lbl_pwd', parent=self,
              pos=wx.Point(78, 161), size=wx.Size(119, 14),
              style=wx.ALIGN_RIGHT)

        self.lbl_ip = wx.StaticText(id=wxID_DIALOG1LBL_IP,
              label=gettext(u"host_address"), name=u'lbl_ip', parent=self,
              pos=wx.Point(78, 194), size=wx.Size(119, 14),
              style=wx.ALIGN_RIGHT)

        self.lbl_port = wx.StaticText(id=wxID_DIALOG1LBL_PORT,
              label=gettext(u"port"), name=u'lbl_port', parent=self,
              pos=wx.Point(80, 230), size=wx.Size(118, 14),
              style=wx.ALIGN_RIGHT)

        self.lbl_result = wx.StaticText(id=wxID_DIALOG1LBL_RESULT,
              label=u'', name=u'lbl_result', parent=self, pos=wx.Point(89,
              264), size=wx.Size(351, 24), style=0)

        self.txt_dbtype = wx.ComboBox(choices=['mysql','oracle10g','sqlserver2005'],id=wxID_DIALOG1TXT_DBTYPE,
              name=u'txt_dbtype', parent=self, pos=wx.Point(203, 53),
              size=wx.Size(160, 22), style=0, value=u'')

        #self.comboBox1.Bind(wx.EVT_KILL_FOCUS, self.OnComboBox1KillFocus)

       # self.txt_dbtype.Bind(wx.EVT_KILL_FOCUS, self.Ontxt_dbtypeKillFocus)        
        self.txt_dbtype.Bind(wx.EVT_COMBOBOX, self.Ontxt_dbtypeKillFocus)
        
        
        self.txt_dbname = wx.TextCtrl(id=wxID_DIALOG1TXT_DBNAME,
              name=u'txt_dbname', parent=self, pos=wx.Point(203, 88),
              size=wx.Size(160, 22), style=0, value=u'')
        self.txt_user = wx.TextCtrl(id=wxID_DIALOG1TXT_USER, name=u'txt_user',
                    parent=self, pos=wx.Point(203, 121), size=wx.Size(160, 22),
                    style=0, value=u'')
        
        
        self.txt_pwd = wx.TextCtrl(id=wxID_DIALOG1TXT_PWD, name=u'txt_pwd',
              parent=self, pos=wx.Point(204, 156), size=wx.Size(160, 22),
              style=wx.TE_PASSWORD, value=u'')

        self.txt_ip = wx.TextCtrl(id=wxID_DIALOG1TXT_IP, name=u'txt_ip',
              parent=self, pos=wx.Point(203, 191), size=wx.Size(160, 22),
              style=0, value=u'')

        self.txt_port = wx.TextCtrl(id=wxID_DIALOG1TXT_PORT, name=u'txt_port',
              parent=self, pos=wx.Point(204, 228), size=wx.Size(160, 22),
              style=0, value=u'')


       

        self.btn_save = wx.lib.buttons.GenButton(id=wxID_DIALOG1BTN_SAVE,
              label=gettext(u"save"), name=u'btn_save', parent=self,
              pos=wx.Point(230, 307), size=wx.Size(79, 26), style=0)
        self.btn_save.Bind(wx.EVT_BUTTON, self.OnBtn_saveButton,
              id=wxID_DIALOG1BTN_SAVE)
        self.btn_test = wx.lib.buttons.GenButton(id=wxID_DIALOG1BTN_TEST,
                     label=gettext(u"test"), name=u'btn_test', parent=self,
                     pos=wx.Point(90, 307), size=wx.Size(100, 26), style=0)
        
        self.btn_test.Bind(wx.EVT_BUTTON, self.OnBtn_testButton,
                    id=wxID_DIALOG1BTN_TEST)
        
        self.btn_close = wx.lib.buttons.GenButton(id=wxID_DIALOG1BTN_CLOSE,
              label=gettext(u"close"), name=u'btn_close', parent=self,
              pos=wx.Point(350, 307), size=wx.Size(79, 26), style=0)
        self.btn_close.Bind(wx.EVT_BUTTON, self.OnBtn_closeButton,
              id=wxID_DIALOG1BTN_CLOSE)

       

        # label=u'mysql,oracle10g,sqlserver2005'
        self.staticText1 = wx.StaticText(id=wxID_DIALOG1STATICTEXT1,
              label=u' ', name='staticText1',
              parent=self, pos=wx.Point(370, 56), size=wx.Size(30, 14),
              style=0)
    def Ontxt_dbtypeKillFocus(self, event):
        #if self.txt_dbtype.Value=="sqlserver2005":
            #self.txt_port.Enable(True)
          #  self.txt_port.Value="1433"
        #else:
            #self.txt_port.Enable(True)
          #  if self.txt_dbtype.Value=="mysql":
          #      self.txt_port.Value="3306"
          #  else:
           #     self.txt_port.Value="1521"
        event.Skip()

    def __init__(self, parent):
        self._init_ctrls(parent)
        db_dict=get_attsite_file()["DATABASE"]
        db_engine={
                "mysql":"mysql",
                "oracle":"oracle10g",
                "sqlserver_ado":"sqlserver2005"
            }
        #初始化 页面显示信息 从 attsite中读取信息
        self.txt_dbtype.Value=(u"%s"%db_dict["ENGINE"] in db_engine.keys()) and db_engine[u"%s"%db_dict["ENGINE"]] or  u"%s"%db_dict["ENGINE"]
        self.txt_dbname.Value=u"%s"%db_dict["NAME"]
        self.txt_user.Value=u"%s"%db_dict["USER"]
        self.txt_pwd.Value=u"%s"%db_dict["PASSWORD"]
        self.txt_ip.Value=u"%s"%db_dict["HOST"]
        self.txt_port.Value=u"%s"%db_dict["PORT"]
        #if self.txt_dbtype.Value=="sqlserver2005":
             #self.txt_port.Enable(False)
        save_mid_dbinfo(self)
        self.btn_save.Enable(False)
        self.lbl_result.Label=gettext(u'port_need_number')

    def OnBtn_saveButton(self, event):
        save_succ=save_dbinfo(self)
        save_mid_dbinfo(self)
        if save_succ!=False:
            dial = wx.MessageDialog(None, gettext(u'Whether_the_synchronization_database'), gettext(u'message'),
                                          wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
            result = dial.ShowModal()
            try:
                if result == wx.ID_YES:
                    self.lbl_result.Label=gettext("Initializing_database")
                    os.system("python manage.pyc syncdb --noinput")
                    self.lbl_result.Label=gettext("init_success")
                    self.Refresh()
                else:
                    print "Cancel"
            finally:
                dial.Destroy()
        self.btn_save.Enable(False)
        event.Skip()

    def OnBtn_testButton(self,event):
        #save_dbinfo(self)
        save_suc=save_dbinfo(self)
        #print save_suc        
        import subprocess
        if save_suc==False:
            self.lbl_result.Label=gettext(u'test_fail')
        else:
            try:
                self.lbl_result.Label=gettext("testing")
                flag=False
                p = subprocess.Popen("python manage.pyc test_conn", shell=False,stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                creationflags=win32con.CREATE_NO_WINDOW)
                t_beginning = time.time()
                seconds_passed = 0
                timeout=30
                while True:
                    if p.poll() is not None:
                        break
                    seconds_passed = time.time() - t_beginning
                    if timeout and seconds_passed > timeout:
                        p.terminate()
                        self.lbl_result.Label=gettext("test_connecton_fail")
                        break
                    time.sleep(0.1)

                stderrdata = p.communicate()
                #print 'error--------',stderrdata,'p.returncode',p.returncode
                if stderrdata[1]!='' or p.returncode!=0:
                    flag=False
                    self.btn_save.Enable(False)
                    self.lbl_result.Label=gettext("test_connecton_fail")
                else:
                    flag=True
                    self.btn_save.Enable(True)
                    self.lbl_result.Label=gettext("test_connecton_success")
               # if flag:
                #加入弹出框告诉是否同步
               #     self.lbl_result.Label=gettext("test_connecton_success")
               #     dial = wx.MessageDialog(None, gettext(u'Whether_the_synchronization_database'), gettext(u'message'),
               #               wx.YES_NO | wx.NO_DEFAULT | wx.ICON_QUESTION)
               #     result = dial.ShowModal()
               #     try:
                #        if result == wx.ID_YES:
                #            self.lbl_result.Label=gettext("Initializing_database")
                #            os.system("python manage.pyc syncdb --noinput")
                #            self.lbl_result.Label=gettext("init_success")
                #            self.Refresh()
                #        else:
                #            print "Cancel"
                #    finally:
                 #       dial.Destroy()
               # else:
                 #   self.lbl_result.Label=gettext("test_connecton_fail")
            except:
                self.lbl_result.Label=gettext("test_connecton_fail")
            revert(self)
            self.Refresh()
        

    def OnBtn_closeButton(self, event):
        self.Close()
        event.Skip()



[wxID_WEBPORTSET, wxID_WEBPORTSETBTN_CLOSE, wxID_WEBPORTSETBTN_SAVE,
 wxID_WEBPORTSETBTN_TEST_PORT, wxID_WEBPORTSETLBL_PORT,
 wxID_WEBPORTSETLBL_TEST_RESULT, wxID_WEBPORTSETSTATICBOX1,
 wxID_WEBPORTSETTXT_PORT,
] = [wx.NewId() for _init_ctrls in range(8)]

class WebPortSet(wx.Dialog):
    def _init_ctrls(self, prnt):
        # generated method, don't edit
        wx.Dialog.__init__(self, id=wxID_WEBPORTSET, name=u'WebPortSet',
              parent=prnt, pos=wx.Point(462, 263), size=wx.Size(444, 259),
              style=wx.DEFAULT_DIALOG_STYLE, title=gettext(u"settings"))
        self.SetClientSize(wx.Size(436, 225))
        self.Show(True)
        #self.SetToolTipString(u'WebPortdialog')

        self.staticBox1 = wx.StaticBox(id=wxID_WEBPORTSETSTATICBOX1,
              label=gettext(u"port_settings"), name='staticBox1', parent=self,
              pos=wx.Point(55, 16), size=wx.Size(345, 128),
              style=wx.RAISED_BORDER)

        self.btn_save = wx.lib.buttons.GenButton(id=wxID_WEBPORTSETBTN_SAVE,
              label=gettext(u"save"), name=u'btn_save', parent=self,
              pos=wx.Point(96, 160), size=wx.Size(79, 26), style=0)
        self.btn_save.Bind(wx.EVT_BUTTON, self.OnBtn_saveButton,
              id=wxID_WEBPORTSETBTN_SAVE)

        self.btn_close = wx.lib.buttons.GenButton(id=wxID_WEBPORTSETBTN_CLOSE,
              label=gettext(u"close"), name=u'btn_close', parent=self,
              pos=wx.Point(233, 158), size=wx.Size(79, 26), style=0)
        self.btn_close.Bind(wx.EVT_BUTTON, self.OnBtn_closeButton,
              id=wxID_WEBPORTSETBTN_CLOSE)

        self.lbl_port = wx.StaticText(id=wxID_WEBPORTSETLBL_PORT,
              label=gettext(u"port"), name=u'lbl_port', parent=self,
              pos=wx.Point(61, 66), size=wx.Size(83, 18), style=wx.ALIGN_RIGHT)

        self.txt_port = wx.TextCtrl(id=wxID_WEBPORTSETTXT_PORT,
              name=u'txt_port', parent=self, pos=wx.Point(156, 64),
              size=wx.Size(100, 22), style=0, value=u'')

        self.btn_test_port = wx.lib.buttons.GenButton(id=wxID_WEBPORTSETBTN_TEST_PORT,
              label=gettext(u"test_port"), name=u'btn_test_port',
              parent=self, pos=wx.Point(289, 62), size=wx.Size(79, 26),
              style=0)
        self.btn_test_port.Bind(wx.EVT_BUTTON, self.OnBtn_test_portButton,
              id=wxID_WEBPORTSETBTN_TEST_PORT)

        self.lbl_test_result = wx.StaticText(id=wxID_WEBPORTSETLBL_TEST_RESULT,
              label=u'', name=u'lbl_test_result', parent=self, pos=wx.Point(64,
              120), size=wx.Size(0, 14), style=wx.ALIGN_CENTRE)

    def __init__(self, parent):
        self._init_ctrls(parent)
        db_dict=get_attsite_file()["Options"]
        self.txt_port.Value=u"%s"%db_dict["Port"]

    def OnBtn_saveButton(self, event):


        save_webserver_port(self.txt_port,self.lbl_test_result)
        event.Skip()

    def OnBtn_closeButton(self, event):
        self.Close()
        event.Skip()

    def OnBtn_test_portButton(self, event):
        check_port(self.txt_port,self.lbl_test_result)
        event.Skip()




def create(parent):
    return RestoreDB(parent)

[wxID_DIALOG1, wxID_DIALOG1BUTTON1, wxID_DIALOG1BUTTON2,
 wxID_DIALOG1FILEBROWSEBUTTON1, wxID_DIALOG1GENSTATICTEXT1,
 wxID_DIALOG1GENSTATICTEXT2,
] = [wx.NewId() for _init_ctrls in range(6)]

class RestoreDB(wx.Dialog):
    def _init_ctrls(self, prnt):
        # generated method, don't edit
        wx.Dialog.__init__(self, id=wxID_DIALOG1, name='', parent=prnt,
              pos=wx.Point(462, 263), size=wx.Size(420, 250),
              style=wx.DEFAULT_DIALOG_STYLE, title=gettext(u'restore_db'))
        #self.SetClientSize(wx.Size(350, 200))
        self.Show(True)

        self.lbl_restore_db = wx.StaticBox(id=wxID_DIALOG1LBL_DBINFO,
              label=gettext(u"restore_db"),
              name=u'lbl_restore_db', parent=self,
              pos=wx.Point(25, 20), size=wx.Size(370, 150), style=0)

        self.lbl_submit = wx.lib.buttons.GenButton(id=wxID_DIALOG1BUTTON1, label=gettext(u'submit'),
              name='lbl_submit', parent=self, pos=wx.Point(100, 175),
              size=wx.Size(75, 24), style=0)
        self.lbl_submit.Bind(wx.EVT_BUTTON, self.Onlbl_submitButton,
              id=wxID_DIALOG1BUTTON1)

        self.lbl_cancel = wx.lib.buttons.GenButton(id=wxID_DIALOG1BUTTON2, label=gettext(u'close'),
              name='lbl_cancel', parent=self, pos=wx.Point(258, 175),
              size=wx.Size(75, 24), style=0)
        self.lbl_cancel.Bind(wx.EVT_BUTTON, self.Onlbl_cancelButton,
                      id=wxID_DIALOG1BUTTON2)

        self.lbl_browse = wx.lib.filebrowsebutton.FileBrowseButton(buttonText=gettext(u'browse'),
              dialogTitle=u'Choose a file', fileMask='*.*',
              id=wxID_DIALOG1FILEBROWSEBUTTON1, initialValue='', labelText=u'',
              parent=self, pos=wx.Point(38, 70), size=wx.Size(340, 56),
              startDirectory='.', style=wx.TAB_TRAVERSAL,
              toolTip=gettext(u't_select_file'))
        self.lbl_browse.SetAutoLayout(False)
        self.lbl_browse.SetLabel(u'')
        self.lbl_browse.SetValue(u'')
        db_dict=get_attsite_file()
        database_engine = db_dict["DATABASE"]["ENGINE"]
        start_path = db_dict["Options"]["BACKUP_PATH"]
        self.lbl_browse.startDirectory = start_path
        if database_engine == 'mysql':
            self.lbl_browse.fileMask = '*.sql'
        elif database_engine == 'sqlserver_ado':
            self.lbl_browse.fileMask = '*.bak'
        elif database_engine == 'oracle':
            self.lbl_browse.fileMask = '*.dmp'
        self.lbl_select_file = wx.lib.stattext.GenStaticText(ID=wxID_DIALOG1GENSTATICTEXT1,
            label=gettext(u'select_file'), name='lbl_select_file', parent=self,
            pos=wx.Point(40, 50), size=wx.Size(160, 24), style=0)
        self.lbl_info = wx.StaticText(id=wxID_DIALOG1GENSTATICTEXT2,
            label=u'', name='lbl_info', parent=self,
            pos=wx.Point(40, 125), size=wx.Size(240, 24), style=wx.ALIGN_LEFT)
        #self.genStaticText2.BestSize(360,24)

    def __init__(self, parent):
        self._init_ctrls(parent)

    def Onlbl_submitButton(self, event):
        #print dir(self.fileBrowseButton1)
        check_and_restore_db(self.lbl_browse,self.lbl_info)
        event.Skip()
    def Onlbl_cancelButton(self, event):
           self.Close()
           event.Skip()

def check_and_restore_db(fileBrowse,lbl_info):
    path = fileBrowse.GetValue()
    path = path.encode("gbk")
    db_dict=get_attsite_file()["DATABASE"]
    database_engine = db_dict["ENGINE"]
    database_user = db_dict["USER"]
    database_password = db_dict["PASSWORD"]
    database_host = db_dict["HOST"]
    database_name = db_dict["NAME"]
    #print database_engine
    if path == "" or path == None:
        #print 'please select a file'
        #print gettext(u'restore_ok_start_service')
        #print gettext(u'none_file')
        lbl_info.Label= gettext(u'none_file')
    else:
        s = path.split(".")[1]
        if s=='sql' and database_engine == 'mysql':
            lbl_info.Label = gettext(u'stop_service')
            control_services(True, False)
            lbl_info.size = wx.Size(460, 24)
            lbl_info.Label = gettext(u'restoring')
            if database_password != "":
                cmd = 'mysql -u%s -p%s -h %s --database %s <%s'%(database_user,database_password,database_host,database_name,path)
            else:
                cmd = 'mysql -u%s -h %s --database %s <%s'%(database_user,database_host,database_name,path)
            #print cmd
            try:
                res = os.system(cmd)
                if res == 1:
                    lbl_info.Label=gettext(u'restore_failed')
                    control_services(False, False)
                    return
                lbl_info.Label=gettext(u'restore_ok_start_service')
                control_services(False, False)
                lbl_info.Label=gettext(u'complate')
            except:
                lbl_info.Label=gettext(u'restore_failed')
                import traceback;traceback.print_exc();
        elif s == 'bak' and database_engine == 'sqlserver_ado':
            lbl_info.Label= gettext(u'stop_service')
            control_services(True, False)
            lbl_info.Label = gettext(u'restoring')
            cmd  = '''sqlcmd -U %s -P %s -S %s -Q "restore database %s from disk='%s'"'''%(database_user,database_password,database_host,database_name,path)
            #print cmd
            try:
                res = os.system(cmd)
                if res == 1:
                    lbl_info.Label=gettext(u'restore_failed')
                    control_services(False, False)
                    return

                lbl_info.Label = gettext(u'restore_ok_start_service')
                control_services(False, False)
                lbl_info.Label=gettext(u'complate')

            except:
                lbl_info.Label=gettext(u'restore_failed')
                import traceback;traceback.print_exc();
        elif s == 'dmp' and database_engine == 'oracle':
            lbl_info.Label= gettext(u'stop_service')
            control_services(True, False)
            lbl_info.Label = gettext(u'restoring')
            cmd = 'imp %s/%s@%s file=%s full=y'%(database_user,database_password,database_name,path)
            #print cmd
            try:
                res = os.system(cmd)
                if res == 1:
                    lbl_info.Label=gettext(u'restore_failed')
                    control_services(False, False)
                    return

                lbl_info.Label=gettext(u'restore_ok_start_service')
                control_services(False, False)
                lbl_info.Label=gettext(u'complate')

            except:
                lbl_info.Label=gettext(u'restore_failed')
                import traceback;traceback.print_exc();

        else:
            lbl_info.Label=gettext(u'invalid_file')

def create(parent):
    return Dialog1(parent)

[wxID_DIALOG1, wxID_DIALOG1DIRBROWSEBUTTON1, wxID_DIALOG1GENBUTTON1,
 wxID_DIALOG1GENBUTTON2, wxID_DIALOG1STATICTEXT1,
] = [wx.NewId() for _init_ctrls in range(5)]


class SetupBackupPath(wx.Dialog):
    def _init_ctrls(self, prnt):
        # generated method, don't edit
        wx.Dialog.__init__(self, id=wxID_DIALOG1, name='', parent=prnt,
              pos=wx.Point(462, 263), size=wx.Size(420, 265),
              style=wx.DEFAULT_DIALOG_STYLE, title=gettext(u'setup_backup_path'))
        #self.SetClientSize(wx.Size(348, 184))

        self.setup_path_box = wx.StaticBox(id=wxID_DIALOG1LBL_DBINFO,
              label=gettext(u'setup_backup_path'),
              name=u'lbl_restore_db', parent=self,
              pos=wx.Point(25, 20), size=wx.Size(370, 175), style=0)

        self.setup_backup_path = wx.StaticText(id=wxID_DIALOG1STATICTEXT1,
              label=gettext(u'select_backup_file'), name='setup_backup_path', parent=self,
              pos=wx.Point(40, 50), size=wx.Size(280, 30), style=0)

        self.select_backup_path = wx.lib.filebrowsebutton.DirBrowseButton(buttonText=gettext(u'browse'),
              dialogTitle='', id=wxID_DIALOG1DIRBROWSEBUTTON1,
              labelText='', newDirectory=False, parent=self,
              pos=wx.Point(38, 70), size=wx.Size(340, 48), startDirectory='.',
              style=wx.TAB_TRAVERSAL,
              toolTip=gettext(u't_select_directory'))
        self.success_info = wx.StaticText(id=8,
              label='', name='lbl_info', parent=self,
              pos=wx.Point(40, 120), size=wx.Size(240, 24), style=wx.ALIGN_LEFT)

        self.star = wx.StaticText(id=9,
              label=u"**", name=u'lbl_note', parent=self,
              pos=wx.Point(30, 140), size=wx.Size(20, 30), style=wx.ALIGN_LEFT)
        self.star.SetForegroundColour(wx.Colour(255, 0, 0))
        self.note = wx.StaticText(id=9,
              label=gettext(u'path_note'), name=u'lbl_note', parent=self,
              pos=wx.Point(45, 140), size=wx.Size(345, 45), style=wx.ALIGN_LEFT)

        self.submit = wx.lib.buttons.GenButton(id=wxID_DIALOG1GENBUTTON1,
              label=gettext(u'save'), name='submit', parent=self,
              pos=wx.Point(100, 200), size=wx.Size(79, 26), style=0)
        self.submit.Bind(wx.EVT_BUTTON, self.OnsubmitButton,
              id=wxID_DIALOG1GENBUTTON1)

        self.close = wx.lib.buttons.GenButton(id=wxID_DIALOG1GENBUTTON2,
              label=gettext(u'close'), name='close', parent=self,
              pos=wx.Point(258, 200), size=wx.Size(79, 26), style=0)
        self.close.Bind(wx.EVT_BUTTON, self.OncloseButton,
              id=wxID_DIALOG1GENBUTTON2)

    def __init__(self, parent):
        self._init_ctrls(parent)
        db_dict=get_attsite_file()
        self.select_backup_path.SetValue(u'%s'%db_dict["Options"]["BACKUP_PATH"])
    def OnsubmitButton(self, event):
        setup_backup_path(self.select_backup_path,self.success_info)
        event.Skip()
    def OncloseButton(self, event):
        self.Close()
        event.Skip()





class RegisterLicence(wx.Dialog):
    def _init_ctrls(self, prnt):
        # generated method, don't edit
        wx.Dialog.__init__(self, id=wxID_DIALOG1, name='', parent=prnt,
              pos=wx.Point(462, 263), size=wx.Size(470, 265),
              style=wx.DEFAULT_DIALOG_STYLE, title=gettext(u"authorization"))
        #self.SetClientSize(wx.Size(348, 184))

        self.frame_customer = wx.StaticBox(id=wxID_DIALOG1LBL_DBINFO,
              label=gettext(u"customer_info"),
              name=u'lbl_restore_db', parent=self,
              pos=wx.Point(25, 20), size=wx.Size(420, 175), style=wx.RAISED_BORDER)

        self.customer = wx.StaticText(id=12,
                     label=gettext(u"customer_code"), name='setup_backup_path', parent=self,
                     pos=wx.Point(40, 50), size=wx.Size(120, 30), style=0)

       
        
        self.macaddress = wx.StaticText(id=13,
              label=gettext(u"machine_number"), name='setup_backup_path', parent=self,
              pos=wx.Point(40, 80), size=wx.Size(120, 30), style=0)

        self.licence = wx.StaticText(id=14,
              label=gettext(u"authorization_code"), name='lbl_info', parent=self,
              pos=wx.Point(40, 110), size=wx.Size(120, 24), style=wx.ALIGN_LEFT)
            
        self.explanation= wx.StaticText(id=19,
                           label=gettext(u"explanation_code"), name='setup_backup_path', parent=self,
                           pos=wx.Point(50, 150), size=wx.Size(350, 30), style=0)
        
        self.txt_customer = wx.TextCtrl(id=15, name=u'txt_customer',
            parent=self, pos=wx.Point(160, 50), size=wx.Size(150, 22),
            style=0, value=u'')

        self.txt_mac = wx.TextCtrl(id=16, name=u'txt_mac',
            parent=self, pos=wx.Point(160, 80), size=wx.Size(270, 22),
            style=0, value=u'')
        self.txt_licence1 = wx.TextCtrl(id=17, name=u'txt_licence1',
                     parent=self, pos=wx.Point(160, 110), size=wx.Size(270, 22),
                     style=0, value=u'')
        self.submit = wx.lib.buttons.GenButton(id=wxID_DIALOG1GENBUTTON1,
              label=gettext(u'register'), name='submit', parent=self,
              pos=wx.Point(100, 200), size=wx.Size(79, 26), style=0)
        self.submit.Bind(wx.EVT_BUTTON, self.OnsubmitButton,
              id=wxID_DIALOG1GENBUTTON1)

        self.close = wx.lib.buttons.GenButton(id=wxID_DIALOG1GENBUTTON2,
              label=gettext(u'close'), name='close', parent=self,
              pos=wx.Point(258, 200), size=wx.Size(79, 26), style=0)
        self.close.Bind(wx.EVT_BUTTON, self.OncloseButton,
              id=wxID_DIALOG1GENBUTTON2)

    def __init__(self, parent):

        self._init_ctrls(parent)
        db_dict=get_attsite_file()
        cust=db_dict["SYS"]["CUSTOMER_CODE"]
        if cust:
            self.txt_customer.SetValue(cust)
        sn=db_dict["SYS"]["SN"]
        if sn:
            self.txt_licence1.SetValue(sn)
        mac=self.get_mac()
        tt=self.d_encrypt(mac,2)

        self.txt_mac.SetValue(tt)

    def OnsubmitButton(self, event):
        licence=str(self.txt_licence1.Value).strip()
        customer_code=str(self.txt_customer.Value).strip()
        continueflag=True

        if not customer_code:
            wx.MessageDialog(parent=None,
                                        message=u"%s"%gettext(u"input_customer_code"),
                                        caption=u"%s"%gettext(u"note"),
                                        style=wx.OK).ShowModal()
            continueflag=False
        if continueflag and not licence:
            wx.MessageDialog(parent=None,
                                        message=u"%s"%gettext(u"input_authorization_code"),
                                        caption=u"%s"%gettext(u"note"),
                                        style=wx.OK).ShowModal()
            continueflag=False
        ret=""
        try:
            ret=self.d_encrypt(licence)
        except:
            pass
        if len(ret)!=41:
            wx.MessageDialog(parent=None,
                                        message=u"%s"%gettext(u"authorization_error"),
                                        caption=u"%s"%gettext(u"note"),
                                        style=wx.OK).ShowModal()
            continueflag=False
        if continueflag:
            mac=self.d_encrypt(self.get_mac().strip(),2)

            customer=ret[:14]
            dmac=ret[-17:]
            findpos=0
            saveflag=False
            for i in range(14):
                if(customer[i:i+1]!="0"):
                    findpos=i
                    break
            customer=customer[findpos:]
            if customer and customer==customer_code and self.get_mac().strip()==dmac:
                saveflag=True
            else:
                wx.MessageDialog(parent=None,
                                            message=u"%s"%gettext(u"authorization_error"),
                                            caption=u"%s"%gettext(u"note"),
                                            style=wx.OK).ShowModal()
            if saveflag:
                db_dict=get_attsite_file()
                db_dict["SYS"]["CUSTOMER_CODE"]=customer.strip()
                db_dict["SYS"]["MAC"]=mac.strip()
                db_dict["SYS"]["SN"]=licence.strip()
                db_dict.save()
                wx.MessageDialog(parent=None,
                                message=u"%s"%gettext(u"authorization_success"),
                                caption=u"%s"%gettext(u"note"),
                                style=wx.OK).ShowModal()

#            else:


        event.Skip()
    def OncloseButton(self, event):
        self.Close()
        event.Skip()
    def d_encrypt(self,data,type=1):
        key="softbyzk"
        k=des(key,CBC,"\0\0\0\0\0\0\0\0",pad=None,padmode=PAD_PKCS5)
        if type==1:
            ret=k.decrypt(data.decode("base64"))
        else:
            ret=k.encrypt(data)
            ret=ret.encode("base64")
            if ret[-1:]=="\n":
                ret=ret[:-1]
        return ret

    def get_mac(self):
        sd=os.popen("ipconfig/all").read()
        lans=sd.split("Ethernet adapter")
        lns=[]
        for l in lans:
            ln=[str(s).strip() for s in l.split("\r\n")]
            lns.append(ln)
        dip=socket.gethostbyname(socket.gethostname())#获取主机IP地址
        ret=""
        findlns=[]
        for i in lns:
            mac=""
            find=False
            for p in i:
                p=p.split(":")
                if p[0].strip().find("Physical Address")!=-1:
                    mac=p[1].strip()
                    #print mac
                if p[0].strip().find("IP Address")!=-1 and p[1].strip()==dip:#根据网卡列表查找真实的mac地址
                    ret=mac
                    find=True
                    break
            if find:
                break
        return ret


def setup_backup_path(select_backup_path,success_info):
    #print select_backup_path.GetValue()
    db_dict=get_attsite_file()
    path = select_backup_path.GetValue().strip()
    try:
        if path.find(u"桌面")!=-1:
            success_info.Label=gettext(u"error_path")
        elif path.split("\\")[1]=="":
            success_info.Label=gettext(u"error_path")
        elif path.find(u"Desktop")!=-1:
            success_info.Label=gettext(u"error_path")
        else:
            db_dict["Options"]["BACKUP_PATH"] = path
            db_dict.save()
            success_info.Label = gettext(u'save_success')
    except:
        from traceback import print_exc
        print_exc()
        success_info.Label=gettext(u"error_path")

app=wx.App()
app.MainLoop()

class MainWindow:
    def __init__(self):
        self.root=None
        msg_TaskbarRestart = win32gui.RegisterWindowMessage("TaskbarCreated");
        message_map = {
                msg_TaskbarRestart: self.OnRestart,
                win32con.WM_DESTROY: self.OnDestroy,
                win32con.WM_COMMAND: self.OnCommand,
                win32con.WM_USER+20 : self.OnTaskbarNotify,
        }
        # Register the Window class.
        wc = win32gui.WNDCLASS()
        hinst = wc.hInstance = win32api.GetModuleHandle(None)
        wc.lpszClassName = "iClockTaskbar"
        wc.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW;
        wc.hCursor = win32api.LoadCursor( 0, win32con.IDC_ARROW )
        wc.hbrBackground = win32con.COLOR_WINDOW
        wc.lpfnWndProc = message_map # could also specify a wndproc.

        # Don't blow up if class already registered to make testing easier
        try:
            classAtom = win32gui.RegisterClass(wc)
        except win32gui.error, err_info:
            if err_info.winerror!=winerror.ERROR_CLASS_ALREADY_EXISTS:
                raise

        # Create the Window.
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        self.hwnd = win32gui.CreateWindow( wc.lpszClassName, "Taskbar iClock", style,
                0, 0, win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT,
                0, 0, hinst, None)
        win32gui.UpdateWindow(self.hwnd)
        self._DoCreateIcons()
    def _DoCreateIcons(self):
        # Try and find a custom icon
        hinst =  win32api.GetModuleHandle(None)
        if hasattr(sys, "frozen"):
            current_path=os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding( )))
        else:
            current_path=os.path.dirname(unicode(__file__, sys.getfilesystemencoding( )))
        if not current_path:
            current_path=os.getcwd()

        iconPathName = current_path+"/mysite/favicon.ico"
        if os.path.isfile(iconPathName):
            icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
            hicon = win32gui.LoadImage(hinst, iconPathName, win32con.IMAGE_ICON, 0, 0, icon_flags)
        else:
            #print "Can't find a Python icon file - using default"
            hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)

        flags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP
        nid = (self.hwnd, 0, flags, win32con.WM_USER+20, hicon, gettext(u"service_control"))
        try:
            win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)
        except win32gui.error:
            # This is common when windows is starting, and this code is hit
            # before the taskbar has been created.
            #print "Failed to add the taskbar icon - is explorer running?"
            # but keep running anyway - when explorer starts, we get the
            # TaskbarCreated message.
            pass

    def OnRestart(self, hwnd, msg, wparam, lparam):
        self._DoCreateIcons()

    def OnDestroy(self, hwnd, msg, wparam, lparam):
        nid = (self.hwnd, 0)
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
        win32gui.PostQuitMessage(0) # Terminate the app.

    def OnTaskbarNotify(self, hwnd, msg, wparam, lparam):
        if lparam==win32con.WM_LBUTTONUP:
            #print u"单击了一下"
            pass
        elif lparam==win32con.WM_LBUTTONDBLCLK:
            #print u"双击了一下"
            #win32gui.DestroyWindow(self.hwnd)
            pass
        elif lparam==win32con.WM_RBUTTONUP:
            menu = win32gui.CreatePopupMenu()
            win32gui.AppendMenu(menu, win32con.MF_STRING, 1023, gettext(u"config_server_port"))
            win32gui.AppendMenu(menu, win32con.MF_STRING, 1024, gettext(u"config_db"))
            win32gui.AppendMenu(menu, win32con.MF_STRING, 1027, gettext(u"restore_db"))
            win32gui.AppendMenu(menu, win32con.MF_STRING, 1028, gettext(u"setup_backup_path"))
            if is_service_stoped() or is_datacenter_stoped():
                win32gui.AppendMenu( menu, win32con.MF_STRING, 1025, gettext(u"service_start"))
            else:
                win32gui.AppendMenu( menu, win32con.MF_STRING, 1025, gettext(u"service_stop"))

            win32gui.AppendMenu( menu, win32con.MF_STRING, 1029, gettext(u"authorization"))
            win32gui.AppendMenu( menu, win32con.MF_STRING, 1026, gettext(u"exit_server_control" ))

            pos = win32gui.GetCursorPos()
            win32gui.SetForegroundWindow(self.hwnd)
            win32gui.TrackPopupMenu(menu, win32con.TPM_LEFTALIGN, pos[0], pos[1], 0, self.hwnd, None)
            win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)
        return 1


    def OnCommand(self, hwnd, msg, wparam, lparam):
        id = win32api.LOWORD(wparam)
        if id==1023:
            if self.root:
               self.root.Close()
            frame1=WebPortSet(None)
            self.root=frame1
            frame1.ShowModal()


#            db_dict=get_attsite_file()["Options"]
#            root=Tk(className="端口信息")
#
#            root.resizable(width=False,height=False)
#            root.geometry("440x240")
#            lbl_main=Label(root,relief=RAISED,text=u'web服务器端口配置',anchor=NW).place(x=25,y=9,width=388,height=220)
#            lbl_webserver=Label(root,borderwidth=1,relief=SUNKEN).place(x=42,y=73,width=351,height=90)
#
#            lbl_txt=Label(root,text = u'端口：',anchor=E).place(x=43,y=76,width=115,height=21)
#            txt_port=Text(root)
#            txt_port.place(x=180,y=76,width=100,height=21)
#            txt_port.insert(END,db_dict["Port"])
#
#            lbl_status=Label(root,text=u'状态信息提示',anchor=W)
#            lbl_status.place(x=83,y=101,width=280,height=21)
#
#            btn_check=Button(root,text = u'测试端口',command =lambda:check_port(txt_port,lbl_status))
#            btn_check.place(x=300,y=76,width=80,height=21)
#            btn_save=Button(root,text = u'保存',command=lambda:save_webserver_port(txt_port,lbl_status)).place(x=110,y=168,width=74,height=21)
#            btn_close=Button(root,text = u'关闭',command=lambda:close_tk_window(root)).place(x=237,y=168,width=74,height=21)
            #root.mainloop()

        elif id == 1024:  #open dialog
            if self.root:
                self.root.Close()
            frame2=DialogDb(None)
            self.root=frame2
            frame2.ShowModal()
        elif id==1029:
            if self.root:
                self.root.Close()
            frame2=RegisterLicence(None)
            self.root=frame2
            frame2.ShowModal()



#            db_dict=get_attsite_file()["DATABASE"]
#            root=Tk(className="数据库信息")
#
#            root.geometry("490x300")
#            lbl_main=Label(root,relief=RAISED,text=u'数据库连接信息配置',anchor=NW).place(x=25,y=9,width=428,height=250)
#            lbl_webserver=Label(root,borderwidth=1,relief=SUNKEN).place(x=42,y=43,width=391,height=180)
#
#            lbl_dbtype=Label(root,text = u'数据库类型：',anchor=E).place(x=53,y=46,width=115,height=21)
#            txt_dbtype=Text(root)
#            txt_dbtype.place(x=200,y=46,width=110,height=21)
#            txt_dbtype.insert(END,db_dict["ENGINE"])
#
#            lbl_db=Label(root,text = u'数据库名称：',anchor=E).place(x=53,y=71,width=115,height=21)
#            txt_db=Text(root)
#            txt_db.place(x=200,y=71,width=110,height=21)
#            txt_db.insert(END,db_dict["NAME"])
#
#            lbl_user=Label(root,text = u'用户名：',anchor=E).place(x=53,y=96,width=115,height=21)
#            txt_user=Text(root)
#            txt_user.place(x=200,y=96,width=110,height=21)
#            txt_user.insert(END,db_dict["USER"])
#
#            lbl_pwd=Label(root,text = u'密码',anchor=E).place(x=53,y=121,width=115,height=21)
#            txt_pwd=Entry(root,show="*")
#            txt_pwd.place(x=200,y=121,width=110,height=21)
#            txt_pwd.insert(END,db_dict["PASSWORD"])
#
#            lbl_ip=Label(root,text = u'IP地址：',anchor=E).place(x=53,y=148,width=115,height=21)
#            txt_ip=Text(root)
#            txt_ip.place(x=200,y=148,width=110,height=21)
#            txt_ip.insert(END,db_dict["HOST"])
#
#            lbl_status=Label(root,text=u'请谨慎填写配置信息，配置错误，系统将无法连接数据库！',anchor=W)
#            lbl_status.place(x=53,y=199,width=370,height=21)
#
#            lbl_port=Label(root,text = u'端口：',anchor=E)
#            lbl_port.place(x=53,y=174,width=115,height=21)
#            txt_port=Text(root)
#            txt_port.place(x=200,y=174,width=110,height=21)
#            txt_port.insert(END,db_dict["PORT"])
#
#            #lbl_run_status=Label(root,text = 'Running').place(x=168,y=199,width=120,height=21)
#           # ckb_auto_window_start=Checkbutton(root, text="When start-up Windows,start-up this program").place(x=33,y=225,width=305,height=21)
#
#            btn_save=Button(root,text = u'保存',command =lambda:save_dbinfo(txt_dbtype,txt_db,txt_user,txt_pwd,txt_ip,txt_port,lbl_status)).place(x=110,y=268,width=74,height=21)
#            btn_close=Button(root,text = u'关闭',command=lambda:close_tk_window(root)).place(x=237,y=268,width=74,height=21)
#            root.mainloop()


        elif id == 1025: #Start services
            #print "start services"
            try:
                 if is_datacenter_stoped():
                     control_services(False)
                 else:
                     control_services(True)
            except Exception,e:
                 import traceback;traceback.print_exc();
        elif id == 1026: #
            #print "Goodbye"
            if self.root:
                self.root.Close()
            win32gui.DestroyWindow(self.hwnd)

        elif id == 1027:
            #print "restore db"
            if self.root:
                self.root.Close()
            frame3 = RestoreDB(None)
            self.root = frame3
            frame3.ShowModal()
        elif id == 1028:
            if self.root:
                self.root.Close()
            frame4 = SetupBackupPath(None)
            self.root = frame4
            frame4.ShowModal()



        else:
            #print "Unknown command -", id
            pass

def main():
    w=MainWindow()
    win32gui.PumpMessages()

if __name__=='__main__':
    main()

