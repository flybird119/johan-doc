# coding=utf-8

STAMPS={'Stamp':'log_stamp', 'OpStamp': 'oplog_stamp', 'FPImage':'FPImage', 'PhotoStamp':'photo_stamp'}

#post_urlPara_dic = {}
#
#class post_urlPara_handler(object):
#    def __init__(self,name,action=None,if_break=False):
#        self.name = name
#        self.value = ''
#        self.action = action
#        self.if_break = if_break
#    def do_action(self,request, device):
#        self.value = request.REQUEST.get(self.name, None)
#        if self.action:
#            self.action(request, device,self.value)