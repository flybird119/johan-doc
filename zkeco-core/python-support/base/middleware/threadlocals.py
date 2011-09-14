#coding=utf-8
'''
主体：当前线程当前请求的本地信息 threading.local
重要API：
    get_current_user()：得到当前请求的 用户
    get_current_request()：得到当前请求的 request
    ThreadLocals().process_request(req) 处理 req请求
'''
try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local

_thread_locals = local()
def get_current_user():
    return getattr(_thread_locals, 'user', None)

def get_current_request():
    return getattr(_thread_locals, 'req', None)

class ThreadLocals(object):
    """Middleware that gets various objects from the
    request object and saves them in thread local storage."""
    def process_request(self, request):
        _thread_locals.req = request
        _thread_locals.user = getattr(request, 'user', None)

