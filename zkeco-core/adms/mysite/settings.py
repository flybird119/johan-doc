# -*- coding: utf-8 -*-
import os.path
import sys, time
from pyDes import *

#调试开关
DEBUG = True
TEMPLATE_DEBUG = DEBUG

# 是否显示软件系统品牌
OEM = True

# Piston 相关配置
ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

# 定义几个全局路径
WORK_PATH=os.getcwdu()+os.sep+'mysite'
APP_HOME=os.path.split(WORK_PATH)[0]

CACHE_BACKEND = 'file://%s/tmp/django_cache?&max_entries=40000'%APP_HOME
MANAGERS = ADMINS
C_ADMS_PATH=APP_HOME+"/tmp/upload/%s/"          #----设备发送过来的数据文件存放目录


DATABASE_ENGINE='sqlite3'
DATABASE_NAME=APP_HOME+'/icdat.db'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'mydatabase'
    }
}

TIME_ZONE = 'Etc/GMT%+-d'%(time.timezone/3600)

# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
LANGUAGE_CODE = 'zh-cn'

SITE_ID = 1

#db backup step time
DB_DBCKUP_STEPTIME=1
# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = APP_HOME+'/media/'
if not os.path.exists(MEDIA_ROOT):
        MEDIA_ROOT = WORK_PATH+'/media/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media'
ADDITION_FILE_ROOT = APP_HOME+'/files/'
if not os.path.exists(ADDITION_FILE_ROOT):
        ADDITION_FILE_ROOT = WORK_PATH+'/files/'
ADDITION_FILE_URL="/file"
# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/admin/media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 't10g+$^b29eonku&fr+l50efir4&o==k*9)%#*zi5@osf6)q@x'+APP_HOME

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
#    'johnny.middleware.LocalStoreClearMiddleware',
#    'johnny.middleware.QueryCacheMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
#    'django.middleware.csrf.CsrfViewMiddleware',  #for Django 1.2
    'mysite.middleware.iclocklocale.AuthenticationMiddleware',
#    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'mysite.middleware.iclocklocale.LocaleMiddleware',
    'base.middleware.threadlocals.ThreadLocals',
#    'django.middleware.locale.LocaleMiddleware',
#    'django.middleware.cache.CacheMiddleware',
#    'django.middleware.doc.XViewMiddleware',
#    'django.middleware.csrf.CsrfResponseMiddleware',
    'django.middleware.gzip.GZipMiddleware',
#    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

CACHE_MIDDLEWARE_SECONDS=25

LANGUAGES=(
  ('en', 'English'),
  ('zh-cn', 'Simplified Chinese'),
  #('zh-tw', 'Tranditional Chinese'),
)

ROOT_URLCONF = 'mysite.urls'

template_path=APP_HOME+'/templates'
if not os.path.exists(template_path):
        template_path=WORK_PATH+'/templates'
try:
        import debug_toolbar
        dtb=debug_toolbar.__path__[0]+'/templates'
except:
        dtb=''
TEMPLATE_DIRS = (
    template_path,
    dtb
)

TEMPLATE_CONTEXT_PROCESSORS = (
        "django.core.context_processors.debug",
        "django.core.context_processors.i18n",
        "django.core.context_processors.media",
        'mysite.middleware.iclocklocale.auth',
        'mysite.middleware.iclocklocale.myContextProc',)

AUTHENTICATION_BACKENDS = (
        'django.contrib.auth.backends.ModelBackend',
        'mysite.authurls.EmployeeBackend',
        )

INSTALLED_APPS = (
    'django.contrib.sessions',
    'django.contrib.auth',
    'django.contrib.contenttypes',
#    'django.contrib.admin',
    'django_extensions',
    'base',
    'dbapp',
    'mysite.iclock',
    'mysite.att',
    'rosetta',
    'mysite.personnel',
    'mysite.johan',
    'mysite.worktable',
    'debug_toolbar',
#        'test_utils',
)

INVISIBLE_APPS = (
    'django.contrib.sessions',
    'django.contrib.contenttypes',
    'django.contrib.admin',
#        'debug_toolbar',
        'test_utils',
        'south',
        'rosetta',
        'mysite.testapp'
)

INTERNAL_IPS = ('127.0.0.1','192.168/16')

DEBUG_TOOLBAR_PANELS = (
        'debug_toolbar.panels.version.VersionDebugPanel',
        'debug_toolbar.panels.timer.TimerDebugPanel',
        'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
        'debug_toolbar.panels.headers.HeaderDebugPanel',
        'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
        'debug_toolbar.panels.template.TemplateDebugPanel',
        'debug_toolbar.panels.sql.SQLDebugPanel',
        'debug_toolbar.panels.signals.SignalDebugPanel',
        'debug_toolbar.panels.logger.LoggingPanel',
)

DEBUG_TOOLBAR_CONFIG = {
	"INTERCEPT_REDIRECTS":False,   # 是否禁止跳转
}

VERSION="Ver 2152(Build: 20081111)"
ALL_TAG="ALL"

SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_COOKIE_AGE=int(60*15)#15分钟
SESSION_SAVE_EVERY_REQUEST=True
MAX_UPDATE_COUNT=50
UPDATE_COUNT=0
MCOUNT=0
APPEND_SLASH=False
LOGIN_REDIRECT_URL="/data/index/"
LOGIN_URL="/accounts/login/"
ICLOCK_AUTO_REG=1   #---允许设备自动注册到服务器
PIN_WIDTH=9 #----------人员编号长度
transaction_absolute_path = ""
REBOOT_CHECKTIME=0  #
NOCMD_DEVICES=[]
ENCRYPT=0   #---设备POST数据是否加密
PAGE_LIMIT=15   #---最大页数
UPGRADE_FWVERSION="Ver 6.39 Jan  1 2009"
MIN_TRANSINTERVAL=2 #最小传输数据间隔时间(分钟）
MIN_REQ_DELAY=60   #最小检查服务器命令间隔时间(秒）
DISABLED_PINS=["0"]        #不允许的考勤号码
TRANS_REALTIME=1        #设备是否实时上传记录
NATIVE_ENCODE='GB18030'
MAX_EXPORT_COUNT=20000


try:
        TMP_DIR=os.environ['TMP']
except:
        TMP_DIR="/tmp"

if not os.path.exists(TMP_DIR+"/"):
        TMP_DIR=os.path.split(os.tempnam())[0]

UNIT=""

LOG_DIR=APP_HOME+"/tmp"
LOG_LEVEL=0

if "USER_COMPANY" in os.environ:
        UNIT=os.environ['USER_COMPANY']
else:
        u=os.path.split(APP_HOME)
        if u[0][-6:] in ('/units', '\\units'):
                UNIT=u[1]

POOL_CONNECTION=0    #----数据库连接池使用的连接数，0 表示不使用连接池
SQL_POOL_PORT=6556  #----数据库连接池服务端口
WRITEDATA_CONNECTION=1  #---后台写数据库进程使用的连接数，0 表示不使用后台写方式

if UNIT:
        #UNIT_URL="/u/"+UNIT+'/'    #用于Hosting业务不同企业使用
        UNIT_URL='/'
        p_path=APP_HOME+'/attsite.ini'
        LOGIN_REDIRECT_URL=UNIT_URL+"data/index/"
        LOGIN_URL=UNIT_URL+"accounts/login/"
#        SESSION_COOKIE_PATH=UNIT_URL
        LOGOUT_URL=UNIT_URL+"accounts/logout/"
        SESSION_COOKIE_NAME='sessionid'+UNIT.encode("ascii")
        ADDITION_FILE_URL=UNIT_URL+"file"
elif len(sys.argv)>1 and not ("manage." in sys.argv[0]):
        UNIT_URL="/"
        p_path=APP_HOME+'/'+sys.argv[1]
else:
        UNIT_URL="/"
        p_path=APP_HOME+'/attsite.ini'

cfg=None
if os.path.exists(p_path+'.dev'):
        p_path=p_path+'.dev'
if os.path.exists(p_path):
        import dict4ini
        cfg=dict4ini.DictIni(p_path, 
                values={
                'DATABASE': DATABASES['default'].copy(),
                'SYS':{
                        'PIN_WIDTH':PIN_WIDTH, 
                        'ENCRYPT':ENCRYPT,
                        'PAGE_LIMIT':PAGE_LIMIT, 
                        'REALTIME':TRANS_REALTIME, 
                        'AUTO_REG':ICLOCK_AUTO_REG,
                        'NATIVE_ENCODE': NATIVE_ENCODE,
                        'MAX_EXPORT_COUNT': MAX_EXPORT_COUNT,
                        'TIME_ZONE': TIME_ZONE,
                        'memcached': 'locmem://', 
                        },
                'LOG':{
                        'DIR':LOG_DIR,
                        'FILE':"",
                        'LEVEL':LOG_LEVEL,
                        }
                })
        TIME_ZONE = cfg.SYS.TIME_ZONE
        DATABASES['default'] = dict(cfg.DATABASE).copy()
        DATABASE_NAME=cfg.DATABASE.NAME
        if "{unit}" in DATABASE_NAME:
                DATABASE_NAME=DATABASE_NAME.replace("{unit}",UNIT)
        elif DATABASE_NAME.startswith('{tmp_file}'):
                source=DATABASE_NAME[10:]
                target=TMP_DIR+"/"+source
                source=file(WORK_PATH+"/"+source,"rb").read()
                if not os.path.exists(target):
                        f=file(target,"w+b")
                        f.write(source)
                        f.close()
                DATABASE_NAME=target
        DATABASES['default']['NAME'] = DATABASE_NAME
        POOL_CONNECTION=DATABASES['default'].get('POOL', 0) #数据库连接池
        WRITEDATA_CONNECTION=DATABASES['default'].get('WRITEDATA', 0) #后台写数据库进程
       	WRITEDATA_LIVE_MINUTES=DATABASES['default'].get("WRITEDATA_LIVE_MINUTES", 10) 
        PIN_WIDTH=cfg.SYS.PIN_WIDTH
        ENCRYPT=cfg.SYS.ENCRYPT
        PAGE_LIMIT=cfg.SYS.PAGE_LIMIT
        TRANS_REALTIME=cfg.SYS.REALTIME 
        ICLOCK_AUTO_REG=cfg.SYS.AUTO_REG 
        NATIVE_ENCODE=cfg.SYS.NATIVE_ENCODE
        MAX_EXPORT_COUNT=cfg.SYS.MAX_EXPORT_COUNT
        if cfg.SYS.memcached:
                if "://" in cfg.SYS.memcached:
                        CACHE_BACKEND = cfg.SYS.memcached
                else:
                        CACHE_BACKEND="memcached://%s/?&max_entries=40000"%cfg.SYS.memcached
        if cfg.LOG.DIR=="{tmp_file}":
                LOG_DIR=TMP_DIR
                ADDITION_FILE_ROOT = TMP_DIR+'/files/'
        else:
                LOG_DIR=cfg.LOG.DIR
        if cfg.LOG.FILE: LOG_FILE=cfg.LOG.FILE
        LOG_LEVEL=cfg.LOG.LEVEL


if POOL_CONNECTION: #启用数据库连接池
    if "django.db.backends." in DATABASES['default']['ENGINE']:
        DATABASES['default']['POOL_ENGINE']=DATABASES['default']['ENGINE']
    else:
        DATABASES['default']['POOL_ENGINE']="django.db.backends."+DATABASES['default']['ENGINE']
        DATABASES['default']['ENGINE']='pool'

MAX_DEVICES=100
VALID_DAYS=100	#100天内的考勤记录才会保存到数据库中，之前的考勤记录被忽略
CHECK_DUPLICATE_LOG=False	#保存考勤记录到数据库时检查是否该记录已经存在
SYNC_DEVICE_CACHE=60		#同步缓存中的设备对象和数据库的时间（秒）


ATT_DEVICE_LIMIT=0           #限制考勤机台数,根据登记的先后顺序来确定是否达到限制
MAX_ACPANEL_COUNT = 50     #最大支持50台门禁控制器
ZKECO_DEVICE_LIMIT=0

JOHNNY_MIDDLEWARE_KEY_PREFIX='jc_myproj'
import dict4ini
APP_CONFIG=dict4ini.DictIni(APP_HOME+"/appconfig.ini")

if APP_CONFIG.language.language:
    LANGUAGE_CODE=APP_CONFIG.language.language
ldirs=list(TEMPLATE_DIRS)
for e in INSTALLED_APPS:
    tdir=WORK_PATH+os.sep+e.split(".")[-1]+os.sep+"templates"
    if os.path.exists(tdir):
        ldirs.append(tdir)
TEMPLATE_DIRS=tuple(ldirs)
CUSTOMER_CODE=""

HAS_DOG=False

def ungen_licence(pcode,mac):
    uv=[]
    mac=mac.zfill(12).upper()
    pmac=mac[-6:]+mac[:6]
    pcode=str(pcode).zfill(48)
    for i in range(24):
        uv.append(str(int(pcode[i*2:i*2+2],16)).zfill(4))
    
    uv="".join(uv)
    #print "uv:",uv
    uvp1=uv[:48]
    uvp2=uv[-48:]
    up1=[]
    up2=[]
    for i in range(12):
        up1.append(chr(int(uvp1[i*4:i*4+4])^ord(pmac[i:i+1])))
        up2.append(chr(int(uvp2[i*4:i*4+4])^ord(pmac[i:i+1])))
    up1="".join(up1)
    up2="".join(up2)
    #print "up1:",up1
    #print "up2:",up2
    ret=up1[:7]+up2[:7]+up1[-5:]+up2[-5:]
#读软件狗中设备的数量
import authorize_fun
if authorize_fun.Ini()==0:
    if authorize_fun.CheckKey()==1 and authorize_fun.check_mac():
        HAS_DOG=True
        ZKECO_DEVICE_LIMIT=authorize_fun.read_zkeco()
        ATT_DEVICE_LIMIT=authorize_fun.read_zktime()
        MAX_ACPANEL_COUNT=authorize_fun.read_zkaccess()
