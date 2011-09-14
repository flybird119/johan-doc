# -*- coding: utf-8 -*-
import os
import string
from django.contrib import auth
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.cache import cache
from dbapp.utils import *

from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.forms.models import ModelChoiceIterator
from mysite.personnel.models import Department
from base.cached_model import CachingModel
from model_device import Device, DeviceForeignKey
from base.operation import OperationBase, Operation, ModelOperation
from django.db import models, connection
import datetime
import traceback
from model_devoperate import OperateCmd
		
		
def gen_device_cmmdata(device,data,errfile=None):
    '''
    将整理后的POST数据保存到文件
    '''
    from mysite import settings
    import datetime
    import os
    tnow=datetime.datetime.now()
    if errfile:
    	filename=tnow.strftime("%Y%m%d%H%M%S")+str(tnow.microsecond/1000)+"_errorfile.txt"
    	desc=desc+u"%s"%_(u'----重新处理')
    else:	
    	filename=tnow.strftime("%Y%m%d%H%M%S")+str(tnow.microsecond/1000)+".txt"
    path=settings.C_ADMS_PATH%device.sn
    path=path+"new/"
    try:
    	if not os.path.exists(path):
    		os.makedirs(path)
    	filename=path+filename
    	upfile=file(filename,"a+")
    	upfile.write(data)
    	upfile.close()
    except:
    	print traceback.print_exc()
    return
def adj_device_cmmdata(device,area,getstring=False):
	data="cmmsubtype=2\t;dev=%s\t;area=%s"%(device.pk,area.pk)
	if getstring:
		return data
	c=OperateCmd()
	c.cmm_system=2
	c.CmdCommitTime=datetime.datetime.now()
	c.CmdContent=_(u'调整设备:%(f)s 的区域至:%(f2)s')%{'f':u"%s"%device,'f2':area.areaname}
	c.cmm_type=2
	c.receive_data=data
	c.save()
	
def save_devicearea_together(devlist,d_area,datalist):
	devdesc=",".join([u"%s"%u for u in devlist])
	if len(devdesc)>50:
		devdesc=devdesc[:47]+"..."
	areadesc=",".join([u"%s"%u for u in d_area])
	if len(areadesc)>50:
		areadesc=areadesc[:47]+"..."	
	c=OperateCmd()
	c.cmm_system=2
	c.CmdCommitTime=datetime.datetime.now()
	c.cmm_type=2
	c.CmdContent=_(u'调整设备:%(f)s 到区域:%(f2)s')%{'f':devdesc,'f2':areadesc}
	c.receive_data="\n\r".join(datalist)
	c.save()
	
def del_user_cmmdata(user,getstring=False):	
	if getstring:
		return adj_user_cmmdata(user,user.attarea.all(),[],getstring)
	desc=_(u'删除用户:%s')%(user)
	adj_user_cmmdata(user,user.attarea.all(),[],getstring,desc)
		
def del_user_together(userlist,datalist):	

	desc=_(u'删除用户:%s')%(",".join([u"%s"%u for u in list(userlist)]))
	if len(desc)>50:
		desc=desc[:47]+"..."
	save_userarea_together(userlist,[],datalist,desc)

def adj_user_cmmdata(user,s_area,d_area,getstring=False,desc=None):
	'''
	同步人员到设备
	'''
	if not isinstance(user,list):
		user=[user]
	s_dev=Device.objects.filter(area__in=list(s_area)).filter(device_type=1)   #---新设备区域
	d_dev=Device.objects.filter(area__in=list(d_area)).filter(device_type=1) #---原来设备区域

	data="cmmsubtype=3\t;user=%s\t;s_dev=%s\t;d_dev=%s"%(",".join(["%s"%u.pk for u in user]),
											",".join(["%s"%s.pk for s in s_dev]),
											",".join(["%s"%d.pk for d in d_dev]))
	if getstring:
		return data
	c=OperateCmd() #---操作命令
	c.cmm_system=2
	c.CmdCommitTime=datetime.datetime.now()
	if desc:
		c.CmdContent=u"%s"%desc
	else:
		c.CmdContent=_(u'调整用户:%(f)s 到区域:%(f2)s')%{'f':u"%s"%user[0],'f2':",".join([u"%s"%u for u in d_area])}
		
	c.cmm_type=2
	c.receive_data=data
	c.save()
	
def save_userarea_together(userlist,d_area,datalist,desc=None):
	userdesc=",".join([u"%s"%u for u in userlist])
	if len(userdesc)>50:
		userdesc=userdesc[:47]+"..."
	areadesc=",".join([u"%s"%u for u in d_area])
	if len(areadesc)>50:
		areadesc=areadesc[:47]+"..."	
	c=OperateCmd()
	c.cmm_system=2
	c.CmdCommitTime=datetime.datetime.now()
	c.cmm_type=2
	if desc:
		c.CmdContent==u"%s"%desc
	else:
		c.CmdContent=_(u'调整用户:%(f)s 到区域:%(f2)s')%{'f':userdesc,'f2':areadesc}
	c.receive_data="\n\r".join(datalist)
	c.save()
	
def parse_cmmdata(cmmdata):
	'''
	解析操作命令为下发给设备的命令
	'''
	from model_device import Device
	from mysite.personnel.models import Employee
	from mysite.personnel.models import Area
	from mysite.iclock.devview import write_data
	from mysite.iclock.models.model_devcmd import DevCmd
	from mysite.iclock.constant import REALTIME_EVENT, DEVICE_POST_DATA
	from redis.server import check_and_start_queqe_server, queqe_server
	
	if cmmdata.cmm_type==1:
		cmm=cmmdata.receive_data.split("\t;",1)
		if cmm[0]=="cmmsubtype=1":
			tmp=cmm[1].split("\t;",1)
			snid=tmp[0].split("=")[1]
			
			fn=tmp[1].split("=")[1]
			wf=file(fn,"r+")
			writedata=wf.read()
			wf.close()
			
			dev=Device.objects.get(pk=snid)
			if writedata:
				write_data(writedata,dev,cmmdata)
			
	elif cmmdata.cmm_type==2:

		cmm=cmmdata.receive_data.split("\t;",1)
		if cmm[0]=="cmmsubtype=2":
			alldata=cmmdata.receive_data.split("\n\r")
			for cmm in alldata:			
				cmm=cmm.split("\t;",1)	
				tmp=cmm[1].split("\t;",1)
				snid=tmp[0].split("=")[1]
				dev=Device.objects.get(pk=snid)
				if dev:
					cmd=DevCmd(SN=dev, CmdOperate=cmmdata, CmdContent="CLEAR DATA", CmdCommitTime=datetime.datetime.now())
					cmd.save(force_insert=True)
					
					dev.set_all_data(cmmdata)
					
		if cmm[0]=="cmmsubtype=3":	   #----所谓的调整用户到某区域
			alldata=cmmdata.receive_data.split("\n\r")
			for cmm in alldata:
				cmm=cmm.split("\t;",1)	
				tmp=cmm[1].split("\t;")
				user=tmp[0].split("=")[1].split(",")
				s_dev=tmp[1].split("=")[1].split(",")
				d_dev=tmp[2].split("=")[1].split(",")
				user=Employee.objects.filter(pk__in=user)
				if s_dev[0]:					
					devset=Device.objects.filter(pk__in=s_dev)			
					for dev in devset:
					    dev.delete_user(user, cmmdata)					    
				if d_dev[0]:
					devset=Device.objects.filter(pk__in=d_dev)		
					for dev in devset:
						dev.set_user(user,  cmmdata, "")
						dev.set_user_fingerprint(user, cmmdata)
	else:
		pass
	pass

def process_writedata():
	'''
	解析操作命令转化为下发给设备的命令
	'''
	import traceback
	import time	
	cur_obj=None  #当前对象
	cur_id=0
	
	while True:
		if cur_id==0:
			try:                
				c=OperateCmd.objects.filter(success_flag=0,cmm_system__exact=2).order_by("id")
				if c:
					cur_obj=c[0]
					cur_id=cur_obj.pk            
				else:
					#print "No data"
					cur_obj=None
					time.sleep(5)				
			except:
				#print "continue no data"
				cur_obj=None
		try:
			try:
				cur_obj=OperateCmd.objects.get(pk=cur_id)
			except:
				#print "continue no data"
				cur_obj=None                
			if cur_obj:
				if cur_obj.cmm_system==2:
					try:                       
						print "current process id:%s"%cur_obj.pk
						parse_cmmdata(cur_obj)

						cur_obj.commit_time=datetime.datetime.now()
						cur_obj.success_flag=1
						cur_obj.process_count=cur_obj.process_count+1
						cur_obj.save()                        
					except:						
						cur_obj.process_count=cur_obj.process_count+1
						cur_obj.commit_time=datetime.datetime.now()
						cur_obj.success_flag=2
						cur_obj.save()
						traceback.print_exc()
					cur_id=cur_id+1
					time.sleep(1)
				else:
					cur_id=cur_id+1
			else:
				time.sleep(5)	
		except:
			traceback.print_exc()
			break;