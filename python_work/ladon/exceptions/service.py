from ladon.exceptions.base import LadonException
import sys,os,traceback

class ServiceFault(LadonException):
	def __init__(self,faultcode,faultstring,detail,stack_depth):
		super(ServiceFault,self).__init__()
		self.faultstring = faultstring
		self.detail = detail
		self.faultcode = faultcode
		caller = sys._getframe(stack_depth)
		self.func = caller.f_code.co_name
		self.mod = os.path.splitext(os.path.split(caller.f_code.co_filename)[1])[0]
		self.lineno = caller.f_lineno
	
	def __str__(self):
		return "%s(%d): %s" % (self.mod,self.lineno,self.faultstring)


class ClientFault(ServiceFault):
	def __init__(self,faultstring,detail=None,stack_depth=2):
		super(ClientFault,self).__init__('client',faultstring,detail,stack_depth)

class ServerFault(ServiceFault):
	def __init__(self,faultstring,detail=None,stack_depth=2):
		super(ServerFault,self).__init__('server',faultstring,detail,stack_depth)
