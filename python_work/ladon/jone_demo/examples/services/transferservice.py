# -*- coding: utf-8 -*-
from ladon.ladonizer import ladonize
from ladon.types.ladontype import LadonType
from ladon.types.attachment import attachment
from ladon.compat import PORTABLE_STRING
from os.path import dirname,abspath,join
import os

upload_dir = join(dirname(abspath(__file__)),'upload')

class File(LadonType):
	data = attachment
	name = PORTABLE_STRING

class TransferService(object):
	"""
	TransferService demonstrates how easy it is to write a service that can transport
	files forth and back between server and clients.
	"""

	@ladonize([File],rtype=int)
	def upload(self,incomming):
		"""
		Upload multiple files at once. Files are stored in the folder services/upload.
		
		@param incomming: A list of File objects containing file data and name
		@rtype: Returns 1 on success
		"""
		global upload_dir
		if not os.path.exists(upload_dir):
			os.mkdir(upload_dir)
		for upload_item in incomming:
			f = open(join(upload_dir,upload_item.name),'wb')
			f.write(upload_item.data.read())
			f.close()
		return 1

	@ladonize([PORTABLE_STRING], rtype=[File])
	def download(self,names):
		"""
		Download multiple files at once. For each name in the <b>names</b> the service
		attempts to find a file in service/upload that matches it. If a name does not
		have a matching file it is ignored.
		
		@param names: A list of the file names
		@rtype: Returns a list of File objects
		"""
		global upload_dir
		response = []
		for name in names:
			f = File()
			f.name = name
			f.data = attachment(open(join(upload_dir,name),'rb'))
			response += [f]
		return response

