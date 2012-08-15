# -*- coding: utf-8 -*-
# vim: set noet:

from ladon.interfaces.base import BaseInterface,ServiceDescriptor,BaseRequestHandler,BaseResponseHandler
from ladon.interfaces import expose
from ladon.compat import PORTABLE_STRING,type_to_xsd,pytype_support
import sys,re
import logging
LOG = logging.getLogger(__name__)


def getCharacters(nodelist):
	raw = PORTABLE_STRING()
	for n in nodelist:
		if n.nodeType == n.TEXT_NODE:
			raw += n.data
	return raw

def getElementsByTagNameAndDepthNS(baseNode,namespaceURI,tagname,depth):
	res = []
	for e in baseNode.getElementsByTagNameNS(namespaceURI,tagname):
		parent = None
		for idx in range(depth):
			if not parent:
				parent = e.parentNode
			else:
				parent = parent.parentNode
			if parent == baseNode:
				res += [e]
	return res


def nodeListToDict(nodelist):
	res_dict = {}
	for n in nodelist:
		items = getElementsByTagNameAndDepthNS(n,'*','item',1)
		if len(items):
			res_dict[n.localName.replace('-','_')] = []
			for item in items:
				if len(item.childNodes)==1 and item.childNodes[0].nodeType==n.TEXT_NODE:
					res_dict[n.localName.replace('-','_')] += [getCharacters([item.childNodes[0]])]
				else:
					res_dict[n.localName.replace('-','_')] += [nodeListToDict(item.childNodes)]
		else:
			res_dict[n.localName.replace('-','_')] = getCharacters(n.childNodes)
	return res_dict


class SOAPServiceDescriptor(ServiceDescriptor):

	xsd_type_map = type_to_xsd
	_content_type = 'text/xml'

	def generate(self,servicename,servicenumber,typemanager,methodlist,service_url,encoding):
		"""
		Generate WSDL file for SOAPInterface
		"""
		type_dict = typemanager.type_dict
		type_order = typemanager.type_order

		def map_type(typ):
			if typ in SOAPServiceDescriptor.xsd_type_map:
				return SOAPServiceDescriptor.xsd_type_map[typ]
			else:
				return typ.__name__

		import xml.dom.minidom as md
		doc = md.Document()

		# SERVICE DEFINITION
		# Create the definitions element for the service
		definitions = doc.createElement('definitions')
		definitions.setAttribute('xmlns:SOAP','http://schemas.xmlsoap.org/wsdl/soap/')
		definitions.setAttribute('xmlns:WSDL','http://schemas.xmlsoap.org/wsdl/')
		definitions.setAttribute('name', servicename)
		definitions.setAttribute('targetNamespace','urn:%s' % servicename)
		definitions.setAttribute('xmlns:tns','urn:%s' % servicename)
		definitions.setAttribute('xmlns:SOAP-ENV','http://schemas.xmlsoap.org/soap/envelope/')
		definitions.setAttribute('xmlns:SOAP-ENC','http://schemas.xmlsoap.org/soap/encoding/')
		definitions.setAttribute('xmlns:xsi','http://www.w3.org/2001/XMLSchema-instance')
		definitions.setAttribute('xmlns:xsd','http://www.w3.org/2001/XMLSchema')
		definitions.setAttribute('xmlns:ns%d' % servicenumber,'urn:%s' % servicename)
		definitions.setAttribute('xmlns','http://schemas.xmlsoap.org/wsdl/')
		doc.appendChild(definitions)

		# TYPES
		# The types element
		types = doc.createElement('types')
		definitions.appendChild(types)

		# Service schema for types required by the target namespace we defined in the definition element
		schema = doc.createElement('schema')
		schema.setAttribute('targetNamespace','urn:%s' % servicename)
		schema.setAttribute('xmlns:SOAP-ENV','http://schemas.xmlsoap.org/soap/envelope/')
		schema.setAttribute('xmlns:SOAP-ENC','http://schemas.xmlsoap.org/soap/encoding/')
		schema.setAttribute('xmlns:xsi','http://www.w3.org/2001/XMLSchema-instance')
		schema.setAttribute('xmlns:xsd','http://www.w3.org/2001/XMLSchema')
		schema.setAttribute('xmlns:ns%d' % servicenumber,'urn:%s' % servicename)
		schema.setAttribute('xmlns','http://www.w3.org/2001/XMLSchema')
		types.appendChild(schema)

		# Import namespace schema
		import_tag = doc.createElement('import')
		import_tag.setAttribute('namespace','http://schemas.xmlsoap.org/soap/encoding/')
		schema.appendChild(import_tag)

		# Define types, the type_order variable holds all that need to be defined and in the
		# correct order.
		# * If a list is encountered as a type it will be handled as a complex type with a single element reflecting the inner type.
		# * LadonTypes (identified by being contained in type_dict) are also handled as complex types with an element-tag per attribute
		# * Primitive types (either as LadonType attributes or list inner-types) are added as xsd - SOAP types.
		for typ in type_order:
			if type(typ)==list:
				inner = typ[0]
				complextype = doc.createElement('complexType')
				complextype.setAttribute('name','ArrayOf%s' % inner.__name__)
				schema.appendChild(complextype)
				complexcontent = doc.createElement('complexContent')
				complextype.appendChild(complexcontent)
				restriction = doc.createElement('restriction')
				restriction.setAttribute('base','SOAP-ENC:Array')
				complexcontent.appendChild(restriction)
				sequence = doc.createElement('sequence')
				element = doc.createElement('element')
				element.setAttribute('name','item')
				if inner in type_dict:
					element.setAttribute('type','ns%d:%s' % (servicenumber,inner.__name__))
				else:
					element.setAttribute('type','xsd:%s' % map_type(inner))
				element.setAttribute('minOccurs','0')
				element.setAttribute('maxOccurs','unbounded')
				sequence.appendChild(element)
				restriction.appendChild(sequence)
				attribute = doc.createElement('attribute')
				attribute.setAttribute('ref','SOAP-ENC:arrayType')
				if inner in type_dict:
					attribute.setAttribute('WSDL:arrayType','ns%d:%s[]' % (servicenumber,inner.__name__))
				else:
					attribute.setAttribute('WSDL:arrayType','xsd:%s[]' % map_type(inner))
				restriction.appendChild(attribute)

			else:
				complextype = doc.createElement('complexType')
				complextype.setAttribute('name',typ['name'].replace('_','-'))
				schema.appendChild(complextype)
				sequence = doc.createElement('sequence')
				complextype.appendChild(sequence)
				for k,v in typ['attributes']:
					element = doc.createElement('element')
					element.setAttribute('name',k.replace('_','-'))
					element.setAttribute('maxOccurs','1')
					if type(v)==list:
						inner = v[0]
						element.setAttribute('type','ns%d:ArrayOf%s' % (servicenumber,inner.__name__))
						element.setAttribute('minOccurs','0')
						element.setAttribute('nillable','true')
					else:
						if v in type_dict:
							element.setAttribute('type','ns%d:%s' % (servicenumber,v.__name__))
						else:
							element.setAttribute('type','xsd:%s' % map_type(v))
						element.setAttribute('minOccurs','1')
					sequence.appendChild(element)

		#<complexType name="ArrayOfstring">
		#<complexContent>
		#<restriction base="SOAP-ENC:Array">
		#<sequence>
		#<element name="attr" type="xsd:string" minOccurs="0" maxOccurs="unbounded"/>
		#</sequence>
		#<attribute ref="SOAP-ENC:arrayType" WSDL:arrayType="xsd:string[]"/>
		#</restriction>
		#</complexContent>
		#</complexType>

		#<message name="listUserRoles">
		#<part name="session-id" type="xsd:string"/>
		#<part name="domain" type="xsd:string"/>
		#<part name="uid" type="xsd:string"/>
		#</message>

		#<message name="listUserRolesResponse">
		#<part name="capa-res" type="ns2:CapaResult"/>
		#<part name="roles" type="ns2:ArrayOfRoleInfo"/>
		#</message>

		for m in methodlist:
			message = doc.createElement('message')
			message.setAttribute('name',m.name())
			definitions.appendChild(message)
			for arg in m.args():
				part = doc.createElement('part')
				part.setAttribute('name',arg['name'].replace('_','-'))
				if [list,tuple].count(type(arg['type'])):
					part.setAttribute('type','ns%d:ArrayOf%s' % (servicenumber,arg['type'][0].__name__))
				else:
					if arg['type'] in type_dict:
						part.setAttribute('type','ns%d:%s' % (servicenumber,arg['type'].__name__))
					else:
						part.setAttribute('type','xsd:%s' % map_type(arg['type']))
				message.appendChild(part)
			message = doc.createElement('message')
			message.setAttribute('name',"%sResponse" % m.name())
			definitions.appendChild(message)
			if [list,tuple].count(type(m._rtype)):
				part = doc.createElement('part')
				part.setAttribute('name','result')
				part.setAttribute('type','ns%d:ArrayOf%s' % (servicenumber,m._rtype[0].__name__))
				message.appendChild(part)
			elif m._rtype in type_dict:
				for k,v in type_dict[m._rtype]['attributes']:
					part = doc.createElement('part')
					part.setAttribute('name',k.replace('_','-'))
					part.setAttribute('maxOccurs','1')
					if type(v)==list:
						inner = v[0]
						part.setAttribute('type','ns%d:ArrayOf%s' % (servicenumber,inner.__name__))
						part.setAttribute('minOccurs','0')
						part.setAttribute('nillable','true')
					else:
						if v in type_dict:
							part.setAttribute('type','ns%d:%s' % (servicenumber,v.__name__))
						else:
							part.setAttribute('type','xsd:%s' % map_type(v))
						part.setAttribute('minOccurs','1')
					message.appendChild(part)
			else:
				part = doc.createElement('part')
				part.setAttribute('name','result')
				if m._rtype in type_dict:
					part.setAttribute('type','ns%d:%s' % (servicenumber,m._rtype.__name__))
				else:
					part.setAttribute('type','xsd:%s' % map_type(m._rtype))
				message.appendChild(part)

		#<portType name="userservicePortType">
		#<operation name="createUser">
		#<documentation>Service definition of function ns2__createUser</documentation>
		#<input message="tns:createUser"/>
		#<output message="tns:createUserResponse"/>
		#</operation>
		porttype = doc.createElement('portType')
		porttype.setAttribute('name','%sPortType' % servicename)
		definitions.appendChild(porttype)

		for m in methodlist:
			operation = doc.createElement('operation')
			operation.setAttribute('name',m.name())
			porttype.appendChild(operation)
			if m.__doc__:
				documentation = doc.createElement('documentation')
				documentation.appendChild(doc.createTextNode(m.__doc__))
				operation.appendChild(documentation)
			input_tag = doc.createElement('input')
			input_tag.setAttribute('message','tns:%s' % m.name())
			operation.appendChild(input_tag)
			output_tag = doc.createElement('output')
			output_tag.setAttribute('message','tns:%sResponse' % m.name())
			operation.appendChild(output_tag)



		#<binding name="userservice" type="tns:userservicePortType">
		#<SOAP:binding style="rpc" transport="http://schemas.xmlsoap.org/soap/http"/>
		#<operation name="createUser">
		#<SOAP:operation style="rpc" soapAction=""/>
		#<input>
		#<SOAP:body use="encoded" namespace="urn:userservice" encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"/>
		#</input>
		#<output>
		#<SOAP:body use="encoded" namespace="urn:userservice" encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"/>
		#</output>
		#</operation>

		binding = doc.createElement('binding')
		binding.setAttribute('name',servicename)
		binding.setAttribute('type',"tns:%sPortType" % servicename)
		transport = doc.createElement('SOAP:binding')
		transport.setAttribute('style','rpc')
		transport.setAttribute('transport','http://schemas.xmlsoap.org/soap/http')
		binding.appendChild(transport)
		definitions.appendChild(binding)

		for m in methodlist:
			operation = doc.createElement('operation')
			operation.setAttribute('name',m.name())
			binding.appendChild(operation)
			soapaction = doc.createElement('SOAP:operation')
			soapaction.setAttribute('style','rpc')
			soapaction.setAttribute('soapAction','')
			operation.appendChild(soapaction)
			input_tag = doc.createElement('input')
			input_soapbody = doc.createElement('SOAP:body')
			input_soapbody.setAttribute('use','encoded')
			input_soapbody.setAttribute('namespace','urn:%s' % servicename)
			input_soapbody.setAttribute('encodingStyle','http://schemas.xmlsoap.org/soap/encoding/')
			input_tag.appendChild(input_soapbody)
			operation.appendChild(input_tag)
			output_tag = doc.createElement('output')
			output_soapbody = doc.createElement('SOAP:body')
			output_soapbody.setAttribute('use','encoded')
			output_soapbody.setAttribute('namespace','urn:%s' % servicename)
			output_soapbody.setAttribute('encodingStyle','http://schemas.xmlsoap.org/soap/encoding/')
			output_tag.appendChild(output_soapbody)
			operation.appendChild(output_tag)


		#<service name="userservice">
		#<documentation>gSOAP 2.7.10 generated service definition</documentation>
		#<port name="userservice" binding="tns:userservice">
		#<SOAP:address location="http://127.0.0.1:8443/userservice"/>
		#</port>
		#</service>

		service = doc.createElement('service')
		service.setAttribute('name',servicename)
		documentation = doc.createElement('documentation')
		documentation.appendChild(doc.createTextNode('Ladon generated service definition'))
		service.appendChild(documentation)
		port = doc.createElement('port')
		port.setAttribute('name',servicename)
		port.setAttribute('binding','tns:%s' % servicename)
		service.appendChild(port)
		address = doc.createElement('SOAP:address')
		address.setAttribute('location',service_url)
		port.appendChild(address)
		definitions.appendChild(service)
		if sys.version_info[0]>=3:
			return doc.toxml()
		return doc.toxml(encoding)

class SOAPRequestHandler(BaseRequestHandler):

	def parse_request(self,soap_body,sinfo,encoding):
		import xml.dom.minidom as md
		doc = md.parseString(soap_body)
		soap_envelope = doc.getElementsByTagNameNS('*','Envelope')[0]
		soap_body = soap_envelope.getElementsByTagNameNS('*','Body')[0]
		EN = soap_body.ELEMENT_NODE
		soap_method = (node for node in soap_body.childNodes
				if node.nodeType == EN).next()
		soap_methodprefix = soap_method.prefix
		m = re.match("^ns(\d+)$",soap_methodprefix)
		servicenumber = None
		if m: servicenumber = int(m.groups()[0])
		soap_methodname = soap_method.localName
		soap_args = {'methodname': soap_methodname,'servicenumber':servicenumber}
		#LOG.debug('soap_method: %s %s', soap_method, dir(soap_method))
		TN = soap_method.TEXT_NODE
		soap_args['args'] = nodeListToDict(node
				for node in soap_method.childNodes if node.nodeType != TN)
		return soap_args



class SOAPResponseHandler(BaseResponseHandler):

	_content_type = 'text/xml'
	_stringify_res_dict = True

	@staticmethod
	def value_to_soapxml(value,parent,doc,is_toplevel=False):
		typ = type(value)
		if typ==dict:
			for attr_name,attr_val in value.items():
				xml_attr_name = attr_name.replace('_','-')
				attr_elem = doc.createElement(xml_attr_name)
				parent.appendChild(attr_elem)
				SOAPResponseHandler.value_to_soapxml(attr_val,attr_elem,doc)
		else:
			if is_toplevel:
				value_parent = doc.createElement('result')
				parent.appendChild(value_parent)
			else:
				value_parent = parent

			if typ in [list,tuple]:
				for item in value:
					item_element = doc.createElement('item')
					SOAPResponseHandler.value_to_soapxml(item,item_element,doc)
					value_parent.appendChild(item_element)
			else:
				value_parent.appendChild(doc.createTextNode(value))


	def build_response(self,res_dict,sinfo,encoding):
		import xml.dom.minidom as md
		doc = md.Document()
		envelope = doc.createElement('SOAP-ENV:Envelope')
		envelope.setAttribute('xmlns:SOAP-ENV','http://schemas.xmlsoap.org/soap/envelope/')
		envelope.setAttribute('xmlns:SOAP-ENC','http://schemas.xmlsoap.org/soap/encoding/')
		envelope.setAttribute('xmlns:xsi','http://www.w3.org/2001/XMLSchema-instance')
		envelope.setAttribute('xmlns:xsd','http://www.w3.org/2001/XMLSchema')
		envelope.setAttribute('xmlns:ns','urn:%s' % res_dict['servicename'])
		doc.appendChild(envelope)
		body_elem = doc.createElement('SOAP-ENV:Body')
		body_elem.setAttribute('SOAP-ENV:encodingStyle','http://schemas.xmlsoap.org/soap/encoding/')
		envelope.appendChild(body_elem)
		method_elem = doc.createElement("ns:%sResponse" % res_dict['method'])
		SOAPResponseHandler.value_to_soapxml(res_dict['result'],method_elem,doc,is_toplevel=True)
		body_elem.appendChild(method_elem)
		return doc.toxml(encoding=encoding)


@expose
class SOAPInterface(BaseInterface):

	def __init__(self,sinfo,**kw):
		def_kw = {
			'service_descriptor': SOAPServiceDescriptor,
			'request_handler': SOAPRequestHandler,
			'response_handler': SOAPResponseHandler}
		def_kw.update(kw)
		BaseInterface.__init__(self,sinfo,**def_kw)

	@staticmethod
	def _interface_name():
		return 'soap'

	@staticmethod
	def _accept_basetype(typ):
		return pytype_support.count(typ)>0

	@staticmethod
	def _accept_list():
		return True

	@staticmethod
	def _accept_dict():
		return False

