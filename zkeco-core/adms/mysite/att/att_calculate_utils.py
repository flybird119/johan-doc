# coding=utf-8

#from django.conf import settings
#from django.utils.translation import ugettext as _

from django.db import models
from dbapp.utils import save_tmp_file

def paging(item_count,offset,pagesize=None):
    '''
    实现标准的分页功能
    @param    item_count    记录总数
    @param    offset    当前页
    @param    pagesize 每页记录数
    @return    返回起止记录号、分页信息字典
    '''
    if pagesize:
        limit = pagesize
    else:
        limit = settings.PAGE_LIMIT
    if item_count % limit==0:
        page_count =item_count/limit
    else:
        page_count =int(item_count/limit)+1                        
    if offset>page_count and page_count:offset=page_count
    Result = {}
    Result['item_count']=item_count
    Result['page']=offset
    Result['limit']=limit
    Result['from']=(offset-1)*limit+1
    Result['page_count']=page_count
    begin = (offset-1)*limit
    end = offset*limit
    return   begin,end,Result


class AttCalculateBase(object):
    def __init__(self,dic,pagesize=30):
        self.current_page = 1
        self.pagesize = pagesize
        
        self.dic = dic
        self.__fieldcaptions= [e[1] for e in self.dic]
        self.__fieldnames =  [e[0] for e in self.dic]
        self.CalculateItem = {}
        self.CalculateItems = []
        self.result = {}
        self.ReItemObj()
        
    def NewItem(self):
        for e in self.CalculateItem.keys():
            self.CalculateItem[e]=''
        return self.CalculateItem
       
    def AddItem(self,obj):
        self.CalculateItems.append(obj.copy())
        
    def ReItemObj(self,dic = None):
        if dic:
            self.dic = dic
            self.__fieldcaptions= [e[1] for e in self.dic]
            self.__fieldnames =  [e[0] for e in self.dic]            
        for e in self.__fieldnames:
            self.CalculateItem[e]=None
            
    def SaveTmp(self):
        file_name="_tmp_%s"%id(self.result)
        attrs=dict([(str(k), models.CharField(max_length=1024, verbose_name=self.__fieldcaptions[self.__fieldnames.index(k)])) for k in self.__fieldnames])
        admin_attrs={"read_only":True, "cache": False, "log":False}
        save_tmp_file(file_name, (attrs, admin_attrs, self.CalculateItems))
        return file_name
    
    def paging(self,item_count=None,offset=None,pagesize=None):
        '''
        实现标准的分页功能
        @param    item_count    记录总数
        @param    offset    当前页
        @param    pagesize 每页记录数
        @return    返回起止记录号、分页信息字典
        '''
        if not item_count:
            item_count = len(self.CalculateItems)
        if not offset:
            offset = self .current_page
        if not pagesize:
            pagesize = self.pagesize
        
        if pagesize:
            limit = pagesize
        else:
            limit = 12#settings.PAGE_LIMIT
        if item_count % limit==0:
            page_count =item_count/limit
        else:
            page_count =int(item_count/limit)+1                        
        if offset>page_count and page_count:offset=page_count
        Result = {}
        Result['item_count']=item_count
        Result['page']=offset
        Result['limit']=limit
        Result['from']=(offset-1)*limit+1
        Result['page_count']=page_count
        begin = (offset-1)*limit
        end = offset*limit
        self.CalculateItems = self.CalculateItems[begin:end]
        self.result.update(Result)
    def ItemData(self):
        for e in self.CalculateItems:
            print e
    def ItemCount(self):
        return  len(self.CalculateItems)
    def GetDatas(self):
        dd = []
    def ResultDic(self,page=1):
        self.paging(offset=page)
        self.result['fieldcaptions'] = [e[1] for e in self.dic]
        self.result['fieldnames'] =  [e[0] for e in self.dic]
        self.result['disableCols'] = []
        self.result['tmp_name'] = self.SaveTmp()
        self.result['datas'] = self.CalculateItems
        return self.result
                
if __name__ == '__main__':
    dic = {'id':u'用户ID','pin':u'人员编号','username':u'姓名'}
    test = AttCalculateBase(dic)
    for i in range(1000):
        obj = test.NewItem()
        obj['id'] =str(i)
        test.AddItem(obj)
    print test.ResultDic(2)
    test.ItemData()
    
        
    