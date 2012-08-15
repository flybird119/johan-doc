# -*- coding: utf-8 -*-
from wsgiref.util import request_uri
import os
import re
import sys
import tempfile
import traceback

from ladon.ladonizer.collection import global_service_collection
from ladon.server.dispatcher import Dispatcher
from ladon.server.customresponse import CustomResponse
from ladon.server.default.css import catalog_default_css,service_default_css
from ladon.server.default.templates import catalog_default_template,service_default_template
from ladon.tools.multiparthandler import MultiPartReader, MultiPartWriter
from ladon.interfaces import _interfaces,name_to_interface
from ladon.exceptions.dispatcher import UndefinedInterfaceName,UndefinedService
from ladon.compat import type_to_jsontype,PORTABLE_STRING_TYPES
from jinja2 import Template

import ladon.tools.log as log
if sys.version_info[0]==2:
	from StringIO import StringIO
	from urlparse import parse_qs, urlparse
elif sys.version_info[0]>=3:
	from urllib.parse import parse_qs, urlparse
	from io import StringIO

rx_ctype_charset = re.compile('charset\s*=\s*([-_.a-zA-Z0-9]+)',re.I)
rx_detect_multipart = re.compile('multipart/([^; ]+)',re.I)
rx_detect_boundary = re.compile('boundary=([^; ]+)',re.I)

def probe_charset(env,default='UTF-8'):
	try:
		global rx_ctype_charset
		res = rx_ctype_charset.findall(env['CONTENT_TYPE'])
		if len(res):
			return res[0]
		return env['HTTP_ACCEPT_CHARSET'].split(';')[0].split(',')[0]
	except:
		return default

def probe_client_path(environ):
	# Simplification of probe_client_path
	# Contributed by: George Marshall
	if 'HTTP_LADON_PROXY_PATH' in environ:
		return environ['HTTP_LADON_PROXY_PATH']
	return request_uri(environ)

class LadonWSGIApplication(object):
	'''wsgi 应用'''
	def __init__(self,service_list,path_list=None,catalog_name=None,catalog_desc=None):

		self.catalog_name = catalog_name  # 分类名称
		self.catalog_desc = catalog_desc  #分类描述
		if not catalog_name:
			self.catalog_name = "Ladon Service Catalog"
		if not catalog_desc:
			self.catalog_desc = "This is the Ladon Service Catalog. It presents the services exposed by on this particular site. Click on a service name to examine which methods and interfaces it exposes."
		if type(service_list) in PORTABLE_STRING_TYPES:   #服务名列表，可以是单个字符串或者数组
			self.service_list = [service_list]
		else:
			self.service_list = service_list
		
		self.path_list = path_list    #服务模块路径列表并加入到Path中
		if path_list and type(path_list) in PORTABLE_STRING_TYPES:
			self.path_list = [path_list]
		
		if self.path_list and type(self.path_list) in [list,tuple]:
			for p in self.path_list:
				if p not in sys.path:
					sys.path += [p]



	def generate_catalog_html(self,services,client_path,catalog_name,catalog_desc,charset):
		'''
		service集合视图
		'''
		fix_path = urlparse(client_path)
		
		catalog_info = {
			'catalog_name': catalog_name,
			'catalog_desc': catalog_desc,
			'query_string': fix_path.query,
			'charset': charset,
			'services': services.values()
		}
		template = "cate_index.html"
		return template.render(catalog_info).encode(charset)
		

	def generate_service_html(self,service,client_path,charset,skin=None):
		'''
		service实例视图
		'''
		def get_ladontype(typ):
			if type(typ)==list:
				if typ[0] in service.typemanager.type_dict:
					return typ[0].__name__
				else:
					return False
			else:
				if typ in service.typemanager.type_dict:
					return typ.__name__
				else:
					return False
			
		def type_to_string(typ):
			paramtype = typ
			if type(paramtype)==list:
				paramtype = paramtype[0]
				if paramtype in service.typemanager.type_dict:
					paramtype_str = '[ %s ]' % paramtype.__name__
				else:
					paramtype_str = '[ %s ]' % type_to_jsontype[paramtype]
			else:
				if paramtype in service.typemanager.type_dict:
					paramtype_str = paramtype.__name__
				elif paramtype in type_to_jsontype:
					paramtype_str = type_to_jsontype[paramtype]
				else:
					paramtype_str = paramtype.__name__
			return paramtype_str

		service_info = {
			'servicename': service.servicename,
			'doc_lines': service.doc_lines,
			'interfaces': _interfaces.keys(),
			'methods': [],
			'types': [],
			'charset': charset,
		}
		'''获取所有可用接口方法的信息'''
		for method in service.method_list():
			method_info = {
				'methodname': method.name(),
				'params': [],
				'doc_lines': method._method_doc,
				'returns': {
					'type': type_to_string(method._rtype),
					'ladontype': get_ladontype(method._rtype),
					'doc_lines': method._rtype_doc } }
			for param in method.args():
				param_info = {
					'name': param['name'],
					'type': type_to_string(param['type']),
					'ladontype': get_ladontype(param['type']),
					'optional': param['optional'],
					'doc_lines': param['doc'] }
				if 'default' in param:
					default_type = param['default']
					if param['type'] in PORTABLE_STRING_TYPES:
						param_info['default'] = '"%s"' % param['default']
					else:
						param_info['default'] = str(param['default'])
				method_info['params'] += [ param_info ]
			service_info['methods'] += [method_info]
		''''获取所有可用类型的信息 '''
		types = service_info['types']
		type_order = service.typemanager.type_order
		for typ in type_order:
			if type(typ)==dict:
				desc_type = {}
				desc_type['name'] = typ['name']
				desc_type['attributes'] = {}
				for k,v,props in typ['attributes']:
					desc_type_val = type_to_string(v)
					desc_type['attributes'][k] = {
						'type': desc_type_val,
						'props': props,
						'ladontype': get_ladontype(v) }
				types += [desc_type]

		template = 'service_index.html'
		return template.render(service_info).encode(charset)

	def import_services(self,service_list):
		# Fix thar eleminates the need for exec()
		# contributed by: Tamás Gulácsi
		for service in service_list:
			__import__(service)
			
	def parse_environ(self,environ):
		global rx_detect_multipart,rx_detect_boundary
		path_parts = []
		path_info=['']
		if 'PATH_INFO' in environ:
			path_info = environ['PATH_INFO'].strip().split('/')
		if path_info[0]=='':
			path_info = path_info[1:]
		for p in path_info:
			if p.strip():
				path_parts += [p]
		
		# path based schema
		sname = ifname = action = None
		if len(path_parts)>0:
			sname = path_parts[0]
		if len(path_parts)>1:
			ifname = path_parts[1] 
		if len(path_parts)>2:
			action = path_parts[2]
		
		# Multipart detection
		multipart = boundary = None
		if 'CONTENT_TYPE' in environ:
			content_type = environ['CONTENT_TYPE']
			content_type = content_type.replace('\n','')
			multipart_match = rx_detect_multipart.findall(content_type)
			if len(multipart_match):
				multipart = multipart_match[0]
				boundary_match = rx_detect_boundary.findall(content_type)
				if len(boundary_match):
					boundary = boundary_match[0]
		return sname,ifname,action,multipart,boundary
	
	def __call__(self,environ, start_response):
		''' wsgi 应用执行 '''
		status = '200 OK'
		response_headers = []
		content_type = 'text/plain'
		output = ''
		charset = probe_charset(environ,default='UTF-8')

		try:
			self.import_services(self.service_list)
			''' 得到客户端请求的信息 '''
			sname,ifname,action,multipart,boundary = self.parse_environ(environ)
			client_path = probe_client_path(environ)
			print 'Jone@-------',sname,ifname,action,multipart,boundary
			print 'Jone@-------',client_path
			sinst = ifclass = None
			if ifname:
				'''检验请求的协议是否合法 soap/jsonwsp'''
				ifclass = name_to_interface(ifname)
				if not ifclass:
					raise UndefinedInterfaceName(ifname,'The interface name "%s" has not been defined' % ifname)

			if sname:
				'''获取请求的service实例'''
				service_search = global_service_collection().services_by_name(sname)
				if not len(service_search):
					raise UndefinedService(ifname,'Service "%s" has not been exposed' % sname)
				sinst = service_search[0]
				
			'''{'doc_lines': ['This service does the math, and serves as example for new potential Ladon users.'],
			 'methods': {'add': <ladon.ladonizer.collection.LadonMethodInfo object at 0x01069EB0>},
			 'servicename': 'Calculator',
			 'sourcefile': 'E:\\open-source\\ladon-0.7.0\\jone_demo\\examples\\services\\calculator.py'}'''
			 
			dispatcher = None
			if sinst and ifclass:
				dispatcher = Dispatcher(sinst,ifclass,charset)
			elif not sname:
				''' 首页'''
				content_type = 'text/html'
				output = self.generate_catalog_html(
					global_service_collection().services,
					client_path,
					self.catalog_name,
					self.catalog_desc,charset)
			elif sinst and not ifname:
				'''service 实例首页'''
				content_type = 'text/html'
				query = parse_qs(urlparse(client_path).query)
				skin = query.get('skin', [None])[0]
				output = self.generate_service_html(sinst,client_path,charset,skin)
			
			if dispatcher and dispatcher.iface:
				if action=='description':
					'''描述视图'''
					content_type = dispatcher.iface.description_content_type()
					service_url = client_path[0:client_path.find('/description')]
					output += dispatcher.iface.description(service_url,charset)
				else:
					'''调用执行视图'''
					allowed_methods = ['POST']
					if environ['REQUEST_METHOD'] not in allowed_methods or not environ.get('CONTENT_LENGTH', ''):
						output += '''不合法的请求方法'''
						#response_headers.append(('Allow', ','.join(allowed_methods)))
					else:
						content_type = dispatcher.iface.response_content_type()
						content_length = int(environ['CONTENT_LENGTH'])
						if multipart and boundary:
							''' 文件上传 '''
							mph = MultiPartReader(20000,boundary.encode(charset),environ['wsgi.input'],content_length)
							mph.read_chunk()
							while not mph.eos:
								mph.read_chunk()
							encapsulated_charset = probe_charset(mph.interface_request_headers,default=None)
							request_data = mph.interface_request
							if encapsulated_charset:
								# If a specific charset is/usr/local/bin/rdesktop specified for the interface request multipart
								# let this charset superseed the charset globally specified for the request.
								dispatcher.response_encoding = encapsulated_charset
							
							environ['attachments'] = mph.attachments
							environ['attachments_by_id'] = mph.attachments_by_id
						else:
							request_data = environ['wsgi.input'].read(content_length)
						response_part = dispatcher.dispatch_request(request_data,environ)
						if isinstance(response_part,CustomResponse):
							''' 如果为视图对象 '''
							response_headers += response_part.response_headers()
							start_response(status, response_headers)
							return response_part.response_data()
						elif len(environ['response_attachments'].attachments_by_cid): #返回文件的标记 response_attachments
							''' 返回文件 '''
							# Attachments present - Send multipart response
							response_temp_fname = tempfile.mktemp()
							temp_buffer = open(response_temp_fname,'wb')
							mpw = MultiPartWriter(temp_buffer)
							mpw.add_attachment(response_part,'%s, charset=%s' % (content_type,charset),'rpc-part')
							for cid,a in environ['response_attachments'].attachments_by_cid.items():
								mpw.add_attachment(a,'application/octet-stram',cid,a.headers)
							mpw.done()
							temp_buffer.close()
							content_length = str(os.stat(response_temp_fname).st_size)
							output = open(response_temp_fname,'rb')
							if sys.version_info[0]==2:
								content_type = "multipart/related; boundary=" + mpw.boundary
							elif sys.version_info[0]>=3:
								content_type = "multipart/related; boundary=" + str(mpw.boundary,'iso-8859-1')
							
						else:
							''' 返回普通内容 '''
							# No attachments - Send normal response
							output = response_part
		
		except Exception as e:
			status = '500 An Error occured while processing the request' 
			content_type = 'text/plain'
			strio = StringIO()
			traceback.print_exc(file=strio)
			output = strio.getvalue()
		
		if 'attachments_by_id' in environ:
			for a_id,a_info in environ['attachments_by_id'].items():
				os.unlink(a_info['path'])

		if not hasattr(output,'read'):
			# not file-like object
			content_length = str(len(output))

		response_headers += [
			('Content-Type', "%s; charset=%s" % (content_type,charset)),
			('Content-Length', content_length)
		]
		start_response(status, response_headers)

		if hasattr(output,'read'):
			# File-like object
			block_size = 4096
			if 'wsgi.file_wrapper' in environ:
				return environ['wsgi.file_wrapper'](output, block_size)
			else:
				return iter(lambda: output.read(block_size), '')
		
		if sys.version_info[0]>=3:
			# Python 3 support
			if type(output)==str:
				output = bytes(output,charset)

		return [output]

