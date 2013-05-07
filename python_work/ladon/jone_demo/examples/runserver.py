# -*- coding: utf-8 -*-
from ladon.server.wsgi import LadonWSGIApplication
import wsgiref.simple_server
from os.path import abspath,dirname,join

scriptdir = dirname(abspath(__file__))
service_modules = ['calculator','albumservice','transferservice','shopservice']
print [join(scriptdir,'services'),join(scriptdir,'appearance')] 
# Create the WSGI Application
application = LadonWSGIApplication(
	service_modules,
	[join(scriptdir,'services'),join(scriptdir,'appearance')],
	catalog_name = 'Ladon Service Examples',
	catalog_desc = 'The services in this catalog serve as examples to how Ladon is used')

if __name__=='__main__':
	# Starting the server from command-line will create a stand-alone server on port 8080
	port = 8090
	print("\nExample services are running on port %(port)s.\nView browsable API at http://localhost:%(port)s\n" % {'port':port})

	server = wsgiref.simple_server.make_server('', port , application)
	server.serve_forever()
