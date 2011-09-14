import datetime

def todatetime(idate):
    return datetime.datetime(idate.year,idate.month,idate.day,0,0,0)

def todatetime2(t):
    return datetime.datetime(1900,1,1,t.hour,t.minute,t.second)
def todatetime3(d,t):
    return datetime.datetime(d.year,d.month,d.day,t.hour,t.minute,t.second)

def dtconvertint(t):
    if t.year>1900:
       return (todatetime(t) - datetime.datetime(1900,1,1,0,0,0)).days * 24*60 + t.hour*60 + t.minute
    else:
       if t.day==1:
          return t.hour*60 + t.minute
       else:
          return t.hour*60 + t.minute +1440