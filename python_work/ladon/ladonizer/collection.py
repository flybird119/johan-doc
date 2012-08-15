# -*- coding: utf-8 -*-
import inspect,ast,re,pprint,sys,copy
from ladon.exceptions.ladonizer import *
import ladon.interfaces as interfaces
from ladon.types.ladontype import LadonType
from ladon.types import validate_type
from ladon.types.typemanager import TypeManager

# python2/3 support:
if sys.version_info[0]==2:
	from chardet_py2 import detect
	def get_function_name(f):
		return f.func_name

elif sys.version_info[0]>=3:
	from chardet_py3 import detect
	def get_function_name(f):
		return f.__name__



class LadonServiceCollection(object):
	
	"""
	LadonServiceCollection collects all services, methods and types for a given server-run
	In Ladon it is only used as a singleton global object, but this could change in time.
	The singleton behaviour is implemented in global_service_collection() which creates the
	global object the first time it is called and then returns the same object the rest of
	the time.
	
	add_service_method() is the most important method on this class as it is the central
	entry-point used by the ladonize decorator to register a service method.
	
	Ladon uses Abstract Syntax Trees (ast) to parse the source files associated with the
	service methods that are registered. We do that because the methods are unbound at
	call-time of the decorators by the Python interpreter. To actually detect the name of
	the class that will have the method as member we do a manual parse per source file.
	
	Example::
		LadonServiceCollection
		 + LadonServiceInfo (UserService)
		    + LadonMethodInfo (addUser)
		    + LadonMethodInfo (delUser)
		 + LadonServiceInfo (RoleService)
		    + LadonMethodInfo (addRole)
		    + LadonMethodInfo (delRole)
		    + LadonMethodInfo (addRoleMember)
		      .
		      .
	"""
	
	def __init__(self,collection_name='global'):
		"""
		initialize some members
		"""
		self.src_info = {}
		self.src_encoding = {}
		self.services = {}
		self.service_and_number = {}
		self.collection_name = collection_name
		self.service_counter = 1

	def source_info(self,fname):
		"""
		Parse a python source file at ast-level to internally acknowledge which
		class methods will be bound to which classes.
		"""
		# Has this source file already been parsed?
		if fname in self.src_info:
			# if yes return the previous parse-result
			return self.src_info[fname]
		
		# Create a source file parse-info-container and ast-parse the sourcefile
		self.src_info[fname] = {}
		src_fp = open(fname,'rb')
		src = src_fp.read()
		src_fp.close()
		src_encoding = detect(src)
		a = ast.parse(src)
		del src
		self.src_encoding[fname] = src_encoding['encoding']
		
		# Analyse the ast
		for obj in a.body:
			if type(obj)==ast.ClassDef:
				c = obj
				firstlineno = c.lineno
				lastlineno = c.lineno
				class_doc_lines = []
				first_class_obj = True
				for obj in c.body:
					# Detect documentation for class
					if first_class_obj and type(obj)==ast.Expr and type(obj.value)==ast.Str:
						for doc_line in obj.value.s.strip().replace('\r\n','\n').split('\n'):
							class_doc_lines += [doc_line.strip()]
					# Detect class methods
					if type(obj)==ast.FunctionDef:
						lastlineno = obj.lineno
					first_class_obj = False
				self.src_info[fname][c.name] = (firstlineno,lastlineno,class_doc_lines)
		
		# return the parse-info-container
		return self.src_info[fname]


	def add_service_method(self,f,*def_args,**def_kw):
		"""
		Register a class method. The method is expected to be registered a decorator
		and therefore unbound.
		If the class which the method is member of has not yet been registered a new
		LadonServiceInfo object will be created for it. The method itself will be
		associated with this object with the instantiation of a LadonMethodInfo
		object.
		"""
		# Extract the source filename and line number where the method is defined
		src_fname = f.__code__.co_filename
		firstlineno = f.__code__.co_firstlineno
		# get an ast-analyzed object of the source file
		sinfo = self.source_info(src_fname)
		# Detect the name of the class that the unbound method will be member of
		
		for clsname,v in sinfo.items():
			if firstlineno>v[0] and firstlineno<=v[1]:
				# The method is somewhere within this class
				# Check if the class has been registered as a service yet
				if not (src_fname,clsname) in self.services:
					# If no then do it by creating a LadonServiceInfo object for it
					self.services[(src_fname,clsname)] = LadonServiceInfo(clsname,src_fname,firstlineno,v[2],self.service_counter,self.src_encoding[src_fname])
					self.service_and_number[self.service_counter] = (src_fname,clsname)
					self.service_counter += 1
				# Register the method as member of this class/service
				method = self.services[(src_fname,clsname)].add_method(f,*def_args,**def_kw)
				return method
		
		# Method could not be recognised as a class member
		return None
	
	def servicenames(self):
		"""
		Return a list of registered service names.
		"""
		names = []
		for k,v in self.services.items():
			names += [v.servicename]
		return names
		
	def service_by_source(self,sourcefile,servicename):
		"""
		Return a specific LadonServiceInfo object registered with a certain
		source file and a service name. Service names are actually class names
		and you cannot have 2 active classes with the same name in one module
		therefore this method will not end in an ambigious result.
		"""
		if (sourcefile,servicename) in self.services:
			return self.services[(sourcefile,servicename)]
		return None

	def service_by_number(self,servicenumber):
		"""
		Return a specific LadonServiceInfo object registered with a certain
		service number. Service numbers are unique, so this cannot end in an
		ambigious result.
		"""
		if servicenumber in self.service_and_number:
			return self.services[self.service_and_number[servicenumber]]
		return None

	def services_by_name(self,servicename):
		"""
		Return LadonServiceInfo objects by service name. This will almost
		always result in a single object, but it is possible to register
		methods from classes with identical names but implementation in
		different modules. This is perfectly legal and therefore it is
		possible to have more than one LadonServiceInfo object returned
		with this method.
		"""
		res = []
		for k,v in self.services.items():
			if k[1].lower() == servicename.lower():
				res += [self.services[k]]
		return res

	def serialize(self):
		"""
		Create an serialization object
		"""
		res = {'collection':self.collection_name}
		res['services'] = {}
		for k,sinfo in self.services.items():
			res['services'][k] = sinfo.serialize()
		return res

	def __str__(self):
		"""
		Make a pretty string representation
		"""
		return pprint.pformat({'collectionname':self.collection_name,'services':self.services})



class LadonServiceInfo(object):
	"""
	LadonServiceInfo stores information about a service that has been registered
	using LadonServiceCollection.add_service_method().
	It also aggragates all it's methods as LadonMethodInfo objects. A per service
	type manager (ladon.types.typemanager.TypeManager) that keeps track of the
	types that the service requires.
	"""
	def __init__(self,servicename,sourcefile,lineno,doc_lines,service_counter,src_encoding):
		self.servicename = servicename
		self.servicenumber = service_counter
		# store some info about the service
		self.src_encoding = src_encoding
		self.sourcefile = sourcefile
		self.doc_lines = doc_lines
		self.lineno = lineno
		# The LadonMethodInfo object container
		self.methods = {}
		# Create the type manager for the service
		self.typemanager = TypeManager()
		
	def add_method(self,f,*def_args,**def_kw):
		"""
		Add a service method by creating a LadonMethodInfo object that analyses
		the function in regards to it's parameters and documentation.
		
		@param f The function object of the method to add
		@rtype LadonMethodInfo Return the method info of the method
		"""
		method = LadonMethodInfo(self,f,*def_args,**def_kw)
		# store the method info
		self.methods[get_function_name(f)] = method
		return method
	
	def method(self,methodname):
		"""
		Get the LadonMethodInfo object registered with *methodname*.
		
		@param methodname The name og the service method
		@rtype LadonMethodInfo The method info registered with methodname or None if non-existent
		"""
		if methodname in self.methods:
			return self.methods[methodname]
		return None
	
	def method_list(self):
		"""
		Get a list of the service methods
		
		@rtype list List of LadonMethodInfo objects
		"""
		method_names = list(self.methods.keys())
		method_names.sort()
		method_list = []
		for mn in method_names:
			method_list += [self.methods[mn]]
		return method_list
		
	def serialize(self):
		"""
		make a serialization object
		
		@rtype dict A serialization dictionary for the service
		"""
		res = {
			'servicename': self.servicename,
			'sourcefile': self.sourcefile,
			'self': self.lineno,
			'methods': {}}
		for k,minfo in self.methods.items():
			res['methods'][k] = minfo.serialize()
		return res
	
	def primitive_requirements(self):
		"""
		Get a list of the primitives required by the service.
		
		@rtype list A distinct list of primitives required by this service
		"""
		return self.typemanager.primitive_list

	def list_support_required(self):
		"""
		Query the service's typemanager to whether lists are required
		by the service. This information is used by the dispatcher to
		filter out service interfaces that don't support lists.
		
		@rtype bool Are lists required by the service
		"""
		return self.typemanager.has_lists

	def dict_support_required(self):
		"""
		Query the service's typemanager to whether dicts are required
		by the service. This information is used by the dispatcher to
		filter out service interfaces that don't support dictss.
		
		@rtype bool Are dicts required by the service
		"""
		return self.typemanager.has_dicts

	def __str__(self):
		"""
		Create a pretty string representation of the service info object
		
		@rtype String Pretty string
		"""
		return pprint.pformat({'servicename':self.servicename,'doc_lines':self.doc_lines,'sourcefile':self.sourcefile,'methods':self.methods})

# Regular expressions for documentation parsing 
rx_doc_params=re.compile('^@param\s+([_a-zA-Z0-9]+):\s*(.*)$')
rx_doc_rtype=re.compile('^@rtype:\s*(.*)$')
rx_doc_param_lines=re.compile('^\s+(\S.*)$')

class LadonMethodInfo(object):
	"""
	Structure for method information. Objects of this class holds method,
	arg and return type documentation and type-info. User-options defined
	via keyword args to the method like *encoding* and *allow_unsafe_conversion*
	are also stored here.
	"""
	def __init__(self,sinfo,f,*def_args,**def_kw):
		global rx_doc_params,rx_doc_rtype,rx_doc_param_lines
		# Inspect the methods's parameters
		argspecs = inspect.getargspec(f)
		# Get the method's doc-string
		doc = inspect.getdoc(f)
		if doc:
			if sys.version_info[0]==2:
				# Convert the documentation to unicode
				doc = unicode(doc,sinfo.src_encoding)
		# Associate the method with it's parent service-info object
		self.sinfo = sinfo
		# _args: Store for arguments (name, type, documentation and default value)
		self._args = {}
		# _has_keywords: Check if the method takes keyword arguments (**kw). The
		# dispatcher will use this information to decide whether to push ladon's
		# helper tools to the method. Helper tools are sent via keyword arguments
		# therefore keyword arguments are required in the method in order to recieve
		# the helper tools
		self._has_keywords = argspecs.keywords!=None
		# _arg_names,_defaults: Store method parameter names and defalut values here. 
		# These will be used later in the parsing process.
		self._arg_names = argspecs.args[1:]
		self._defaults = argspecs.defaults
		# Store the raw doc-string in _doc
		self._doc = f.__doc__
		# Extract the method name
		self._func_name = get_function_name(f)
		# Store the parameter types delivered by the user via the ladonize decorator
		self._arg_types = def_args
		# _encoding: is kind of a contract between the method and Ladon's dispatcher.
		# It tells Ladon that it must deliver raw strings to the service method in that
		# encoding thus converting if nessecary. You can think of it as the method's
		# internal encoding. The method itself also commit's itself to the contract by
		# promising to deliver raw strings back to the dispatcher in the same encoding.
		# Raw strings are defined as: str in Python2 and bytes in Python3
		self._encoding = 'UTF-8'
		# _allow_unsafe_conversion: is a user-option that tells Ladon whether it may do
		# unsafe convertions or not. An example of an unsafe convertion is float to int.
		# unsafe convertions are disabled by default
		self._allow_unsafe_conversion = False
		# _rtype: The return type of the method.
		try:
			self._rtype = def_kw['rtype']
		except KeyError as ke:
			# return type must be specified.
			raise ReturnTypeUndefined(sinfo,self._func_name)
		# _rtype_doc: Initialize the return type doc-string container
		self._rtype_doc = []
		# overwrite the default values of user options if they are passed on via the
		# ladonize decorator.
		if 'encoding' in def_kw:
			self._encoding = def_kw['encoding']
		if 'allow_unsafe_conversion' in def_kw:
			self._allow_unsafe_conversion = def_kw['allow_unsafe_conversion']
		# Let the parent service's TypeManager object parse, analyze and store the return type
		self._multipart_response_required = sinfo.typemanager.analyze_param(self._rtype)
		self._multipart_request_required = False
		if self._defaults==None:
			self._defaults = tuple()
		# Identify which arguments are mandatory and which are optional
		self._mandatory_args = self._arg_names[:-len(self._defaults)]
		self._optional_args = self._arg_names[-len(self._defaults):]
		# Check that the number of type defines (via the ladonize decorator) matches then
		# number of method arguments
		if len(self._arg_names)!=len(def_args):
			raise ArgDefCountMismatch(sinfo,self._func_name,self._arg_types,self._arg_names)
		
		alen = len(self._arg_names)
		dlen = len(self._defaults)
		for argidx in range(len(self._arg_names)):
			# Let the parent service's TypeManager object parse, analyze and store the argument
			self._multipart_request_required |= sinfo.typemanager.analyze_param(def_args[argidx])

			has_default = False
			# find the index of this parameter's default value in _defaults. If index is below
			# 0 it means it has no default value, thus a mandatory parameter.
			defidx = dlen - (alen - argidx)
			if defidx>-1:
				# Optional parameter, check and store it's default value
				has_default = True
				def_val = self._defaults[defidx]
				def_type = type(self._defaults[defidx])
				# Check that the default value matches the user defined type
				if not validate_type(def_args[argidx],def_val):
					# type mismatch
					raise DefaultArgTypeMismatch(
						sinfo,
						self._func_name,
						self._arg_names[argidx],
						self._arg_types[argidx],
						def_type)

			# Store the info about this parameter
			self._args[self._arg_names[argidx]] = {
				'name': self._arg_names[argidx],
				'type': def_args[argidx],
				'optional': has_default,
				'doc': []}
			if has_default:
				self._args[self._arg_names[argidx]]['default'] = def_val
		
		# Parse the methods documentation
		self._method_doc = []
		if doc:
			# Make sure all newlines in doc are Unix style, then split it into lines
			doc = doc.replace('\r\n','\n')
			doclines = doc.split('\n')
			
			cur_argname = None
			for dline in doclines:
				# Iterate through doc lines and do regular expression matches to
				# find method, argument and return documentation
				
				# Does the current doc line match the beginning of a parameters documentation
				param_match = rx_doc_params.match(dline)
				if param_match:
					# Set the parameter as current
					cur_argname = param_match.groups()[0]
					# if not an actual parameter cancel param documentation
					if not cur_argname in self._args:
						cur_argname = None
						continue
					# Add the first doc line to the parameter doc lines
					docline1 = param_match.groups()[1].strip()
					if docline1:
						self._args[cur_argname]['doc'] += [docline1]
					continue
				
				# Does the current doc line match the beginning of the return documentation
				rtype_match = rx_doc_rtype.match(dline)
				if rtype_match:
					# Add the first doc line to the return doc lines
					cur_argname = '_rtype'
					docline1 = rtype_match.groups()[0].strip()
					if docline1:
						self._rtype_doc += [docline1]
					continue
				
				# does the doc line look like a param or return line
				param_line_match = rx_doc_param_lines.match(dline)
				# Add it to the current param doc that is being processed
				if param_line_match and cur_argname:
					if cur_argname=='_rtype':
						self._rtype_doc += [ dline.strip() ]
					else:
						self._args[cur_argname]['doc'] += [param_line_match.groups()[0].strip()]
					continue
				
				# If this doc line cannot be mapped to an argument or the return documentation, then
				# add it to the methods documentation
				if not len(dline.strip()) and cur_argname:
					if cur_argname=='_rtype':
						self._rtype_doc += [ dline.strip() ]
					else:
						self._args[cur_argname]['doc'] += [dline.strip()]
					continue
				
				# If no match found, reset the current param if one is in focus
				cur_argname = None
				self._method_doc += [ dline ]
				
		self.__doc__ = '\n'.join(self._method_doc)
		
	def name(self):
		"""
		Fetch the name of the method being mapped by this LadonMethodInfo.
		
		@param rtype String The name of the method
		"""
		return self._func_name

	def args(self):
		"""
		Fetch information about this methods parameters.
		
		@rtype list A list of argument description dicts
		"""
		ret = []
		for argname in self._arg_names:
			ret += [self._args[argname]]
		return ret

	def serialize(self):
		"""
		Serialize this method
		"""
		return {'methodname':self.name(),'doc':self.__doc__,'args':self.args(),'rtype':self._rtype, 'rtype_doc':self._rtype_doc}

	def __str__(self):
		return pprint.pformat(self.serialize())


global_lsc = None

# Singleton
def global_service_collection():
	"""
	Fetch the singleton instance of LadonServiceCollection refered to as the
	global service collection.
	
	@rtype LadonServiceCollection The global service collection
	"""
	global global_lsc
	# If this is the first call then the object is not yet created
	if not global_lsc:
		# Create the global object
		global_lsc = LadonServiceCollection()
	return global_lsc
