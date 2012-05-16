# -*- coding: utf-8 -*-

from ladon.ladonizer.collection import global_service_collection
from ladon.types import get_type_info,validate_type
from ladon.types.attachment import attachment,extract_attachment_reference
from ladon.types.typeconverter import TypeConverter
from ladon.exceptions.dispatcher import *
from ladon.exceptions.service import *
from ladon.tools.multiparthandler import AttachmentHandler
from ladon.server.customresponse import CustomResponse
import os,re,traceback

class Dispatcher(object):
	"""
	The dispatcher class handles the communication between the service interface and
	the user functionality. This happens in dispatch_request()
	
	1. It recieves the raw protocol data and attempts to parse it using the service
	interface's request handler. If successful a req_dict (request dictionary) is returned.

	2. The request dictionary is parsed call_method() where the arguments are converted to
	fit the user defined method.
	
	3. If the call to the user defined method is successful the result is converted to a
	res_dict (response dictionary) in result_to_dict()
	
	4. The response dictionary is passed to the service interface's response handler and
	returned as raw protocol data.
	
	"""
	def __init__(self,sinst,ifclass,response_encoding):
		self.response_encoding = response_encoding
		self.sinst = sinst
		self.iface = ifclass(sinst)


	def call_method(self,method,req_dict,tc,export_dict):
		"""
		call_method converts the res_dict delivered from an interface
		to the type of arguments expected by the service method.
		tc is the TypeConverter associated to the service method.
		"""
		global rx_cid,rx_cidx
		args = []
		for arg in method.args():
			if arg['name'] not in req_dict['args']:
				if 'default' in arg:
					args += [arg['default']]
				else:
					raise UndefinedServiceMethod(self.iface._interface_name(),self.sinst.servicename,'Parameter "%s" is not optional' % arg['name'])
			else:
				if type(arg['type'])==list:
					arg_list = []
					type_info = get_type_info(arg['type'][0])
					if type_info:
						for item in req_dict['args'][arg['name']]:
							arg_list += [arg['type'][0](prime_dict=item,tc=tc,export_dict=export_dict)]
					elif arg['type'][0]==attachment:
						for item in req_dict['args'][arg['name']]:
							arg_list += [extract_attachment_reference(item,export_dict,self.response_encoding,self.iface._interface_name(),self.sinst.servicename)]
					else:
						for item in req_dict['args'][arg['name']]:
							arg_list += [tc.from_unicode_string(item,arg['type'][0])]
					args += [arg_list]
				else:
					type_info = get_type_info(arg['type'])
					val = req_dict['args'][arg['name']]
					if type_info:
						args += [arg['type'](prime_dict=val,tc=tc,export_dict=export_dict)]
					elif arg['type']==attachment:
						args += [extract_attachment_reference(val,export_dict,self.response_encoding,self.iface._interface_name(),self.sinst.servicename)]
					else:
						args += [tc.from_unicode_string(val,arg['type'])]
					
		path,fname = os.path.split(method.sinfo.sourcefile)
		mname = os.path.splitext(fname)[0]
		service_module = __import__(mname, globals(),  locals(), '*')
		service_class_instance = getattr(service_module,method.sinfo.servicename)()
		if method._has_keywords:
			kw = {'LADON_METHOD_TC':tc}
			kw.update(export_dict)
			result = getattr(service_class_instance,req_dict['methodname'])(*args,**kw)
		else:
			result = getattr(service_class_instance,req_dict['methodname'])(*args)
		return result


	def result_to_dict(self,method,result,tc,response_attachments):
		"""
		Convert the result of a method call to it's dictionary representation.
		tc is a TypeConverter
		"""
		res_dict = {
			'servicename': method.sinfo.servicename,
			'servicenumber': method.sinfo.servicenumber,
			'method': method.name()}
		typ = method._rtype
		type_info = get_type_info(typ)
		if type_info==None:
			if [list,tuple].count(type(typ)):
				result_list = []
				res_dict['result'] = result_list
				type_info = get_type_info(typ[0])
				if result == typ:
					# Assumption list attributes are always optional
					return
				
				if type_info:
					for item in result:
						result_list += [item.__dict__(tc,response_attachments)]
				elif typ[0]==attachment:
					for item in result:
						if not type(item) == attachment:
							raise AttachmentExpected(self.iface._interface_name(),self.sinst.servicename,'Attachment expected got: %s' % type(item))
						result_list += [response_attachments.add_attachment(item)]
				else:
					for item in result:
						result_list += [tc.to_unicode_string(item,typ[0])]
			elif typ==attachment:
				res_dict['result'] = response_attachments.add_attachment(result)
			else:
				res_dict['result'] = tc.to_unicode_string(result,typ)
		else:
			res_dict['result'] = result.__dict__(tc,response_attachments)
		
		return res_dict


	def dispatch_request(self,request_data,export_dict):
		try:
			export_dict['response_attachments'] = AttachmentHandler()
			methodname,method = None,None
			req_dict = self.iface.parse_request(request_data,encoding=self.response_encoding)
			methodname = req_dict['methodname']
			method = self.sinst.method(methodname)
			if not method:
				raise UndefinedServiceMethod(self.iface._interface_name(),self.sinst.servicename,'Service method "%s" is not declared in service' % methodname)
			tc = TypeConverter(
				encoding=method._encoding,
				allow_unsafe_conversion=method._allow_unsafe_conversion,
				only_strings_to_unicode=(not self.iface.stringify_res_dict()))
			result = self.call_method(method,req_dict,tc,export_dict)
		except Exception as e:
			if isinstance(e,ServiceFault):
				response = self.iface.build_fault_response(e,methodname,encoding=self.response_encoding)
			elif method==None:
				response = self.iface.build_fault_response(ClientFault(str(e)),methodname,encoding=self.response_encoding)
			else:
				response = self.iface.build_fault_response(ServerFault(str(e)),methodname,encoding=self.response_encoding)
			return response
		if isinstance(result,CustomResponse):
			# In some cases it can be nessecary to override the normal response system and return
			# something completely different - ie. 
			# 1. if a certain method should return a file as a http attachment response for
			#    browsers (Content-Disposition: attachment;).
			# 2. or a commandline tool that sends a SOAP request and should output raw text as
			#    result
			# Objects of CustomResponse descendents are intercepted in the wsgi_application part
			# so the service developer has full control over response headers and data.
			return result
		res_dict = self.result_to_dict(method,result,tc,export_dict['response_attachments'])
		if 'mirror' in req_dict:
			res_dict['reflection'] = req_dict['mirror']
		response = self.iface.build_response(res_dict,encoding=self.response_encoding)
		return response
