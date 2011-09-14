from django.core.management.base import BaseCommand, CommandError
import os
import time
import sys

class Command(BaseCommand):
	option_list = BaseCommand.option_list + ()
	help = "Starts data comm center process."
	args = ''
 
	def handle(self, *args, **options):
		print "DataCommCenter starting... ..."

