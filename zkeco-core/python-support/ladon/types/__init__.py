# -*- coding: utf-8 -*-

def validate_type(typ,val):
	if [tuple,list].count(type(typ)):
		if not [tuple,list].count(type(val)):
			return False
		for i in val:
			if type(i)!=typ[0]:
				return False
	else:
		if typ!=type(val):
			return False
	return True

def get_type_info(typ):
	"""
	Convert a type to ladon type dict. If the type is a LadonType and contained in the service being processed
	the type dict will be returned, otherwise None is returned.
	"""
	from ladon.types.typemanager import TypeManager
	if not [list,tuple].count(type(typ)) and typ in TypeManager.global_type_dict:
		return TypeManager.global_type_dict[typ]
	else:
		return None
