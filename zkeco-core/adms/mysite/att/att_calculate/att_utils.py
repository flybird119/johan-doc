# coding=utf-8

def getworktype_byuserdate(currentday,checkty,isholiday):
    '''
    节假日可覆盖休息日
    '''
#    isholiday = 
    empworktype = 0  #0为平日，1为平时加班,2为休息日,3为节假日。
    for h in isholiday:
        if todatetime(h['start_time'])<=currentday and (todatetime(h['start_time'])+datetime.timedelta(days=h['duration']))>currentday:#---当前日期在假期时间段内
           empworktype = 3 #---节假日
           break
        else:
            empworktype =0  #----非节假日
            
    if empworktype == 0 and checkty ==True:     #----非节假日且为系统初始的弹性时段日时则为 休息日
       empworktype=2
    return empworktype

def safeindex(val,li):
    try:
        index = li.index(val)
    except:
        index = None
    return index

def filattercord(currentday,attrecord):
    ii=0
    for a in attrecord:
        if (a.TTime).day == currentday.day:
           ii =ii +1
    return ii

def intdata(source,min,flag=0):
    '''
    数字的舍入控制
    '''
    if min==0:
       min =1
    if flag==0:
       try:
          if min!=1:
             if min>1:
                ret = int(source)/int(min)*min
             else:
                ret = float(source)/min*min
          else:
             ret = int(source) 
       except:
          import traceback;traceback.print_exc()
          ret = source
    if flag==1:   #四舍五入
        if min!=1:
           if min>1:
              if int(source)%int(min)>=(min/2 - 0.0000001):
                 ret = int(source)/int(min)*min+min
              else:
                 ret = int(source)/int(min)*min
           else:
              if int(source*100)%int(min*100)>=((min*100)/2 - 0.0000001):
                 ret = (int(source*100)/int(min*100)*min)+min
              else:
                 ret = (int(source*100)/int(min*100)*min) 
        else:
           if (source*100)%100>=50:
              ret = int(source) +1
           else:
              ret = int(source)
    if flag==2:    #向上取整，如果是最小单位大于20并且不是10的倍数则认为是大于20分钟向上取整成30分钟的情况。
        if min!=1:
           if min>1:
              if int(min)>20 and int(min)%10!=0:
                  if int(source)%(int(30 - min)+int(min))>=int(min):
                     ret = int(source)%30+30
                  else:
                     ret = int(source)%30
              else:  
                  if int(source)%int(min)>0:
                     ret = int(source)/int(min)*min+min
                  else:
                     ret = int(source)/int(min)*min
           else:
              if int(source*100)%int(min*100)>0:
                 ret = (int(source*100)/int(min*100)*min)+min
              else:
                 ret = (int(source*100)/int(min*100)*min) 
        else:
           if (source*100)%100>0:
              ret = int(source) +1
           else:
              ret = int(source)            
    return ret

def decquan(d,leng=1,flag=1):
    from decimal import Decimal,ROUND_HALF_UP,ROUND_DOWN
    if leng==1:     
       if flag==0:
          return Decimal(str(d)).quantize(Decimal('0.0'),ROUND_HALF_UP)
       else:
          return Decimal(str(d)).quantize(Decimal('0.0'),ROUND_DOWN) 
    else:
       if flag==0:
          return Decimal(str(d)).quantize(Decimal('0.000'),ROUND_HALF_UP)
       else:
          return Decimal(str(d)).quantize(Decimal('0.000'),ROUND_DOWN)           