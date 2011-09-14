#! /usr/bin/env python
#coding=utf-8

"""
$URL: svn+ssh://svn.mems-exchange.org/repos/trunk/durus/file.py $
$Id: file.py 31249 2008-10-28 21:49:21Z dbinger $
"""
import os, os.path
from os.path import exists
from tempfile import NamedTemporaryFile, _TemporaryFileWrapper

if os.name == 'nt':
    import win32con, win32file, pywintypes
else:
    import fcntl

class File (object):
    """
    文件对象的封装,排除一些平台相关的操作
    A file wrapper that smooths over some platform-specific
    operations.
    """
    def __init__(self, name=None, readonly=False, **kwargs):
        if name is None:
            self.file = NamedTemporaryFile(**kwargs)    #---临时文件对象
        else:
            if exists(name):
                if readonly:
                    self.file = open(name, 'rb')    #---只读
                else:
                    self.file = open(name, 'r+b')   #---可读可写
            else:
                if readonly:
                    raise OSError('No "%s" found.' % name)  #---OSError 的使用
                self.file = open(name, 'w+b')
        if readonly:
            assert self.is_readonly()
        self.has_lock = False   #----文件锁定状态

    def get_name(self):
        ''' 获取文件名 '''
        return self.file.name

    def is_temporary(self):
        ''' 是否为临时文件 '''
        return isinstance(self.file, _TemporaryFileWrapper)

    def is_readonly(self):  #---起验证作用
        ''' 是否为只读文件 '''
        return self.file.mode == 'rb'

    def seek(self, n, whence=0):
        self.file.seek(n, whence)
        if whence == 0:
            assert self.file.tell() == n

    def seek_end(self):
        self.file.seek(0, 2)

    def read(self, n=None):
        ''' 读取文件 '''
        self.seek(0)
        if n is None:
            return self.file.read()
        else:
            return self.file.read(n)

    def tell(self):
        ''' 当前位置 '''
        return self.file.tell()

    def stat(self):
        return os.stat(self.get_name())

    def __len__(self):
        return self.stat().st_size

    def rename(self, name):
        ''' 重命名文件 '''
        old_name = self.get_name()
        if name == old_name:
            return
        assert not self.is_temporary()  #---不能为临时文件
        self.obtain_lock()
        self.close()
        if exists(name):
            os.unlink(name)
        os.rename(old_name, name)
        self.file = open(name, 'r+b')
        self.obtain_lock()

    def obtain_lock(self):
        """
        给文件加上排他锁
        Make sure that we have an exclusive lock on self.file before
        doing a write.
        If the lock is not available, raise an exception.
        """
        assert not self.is_readonly()   #---不能为只读
        if not self.has_lock:
            if os.name == 'nt': #---如果是win32平台
                try:
                    win32file.LockFileEx(   #---os文件锁
                        win32file._get_osfhandle(self.file.fileno()),
                        (win32con.LOCKFILE_EXCLUSIVE_LOCK |
                         win32con.LOCKFILE_FAIL_IMMEDIATELY),
                        0, -65536, pywintypes.OVERLAPPED())
                except pywintypes.error:
                    raise IOError("Unable to obtain lock")
            else:
                fcntl.flock(self.file, fcntl.LOCK_EX | fcntl.LOCK_NB)   #---否则使用库函数来加锁
            self.has_lock = True

    def release_lock(self):
        """
        解除文件的排他锁
        Make sure that we do not retain an exclusive lock on self.file.
        """
        if self.has_lock:
            if os.name == 'nt':
                win32file.UnlockFileEx(
                    win32file._get_osfhandle(self.file.fileno()),
                    0, -65536, pywintypes.OVERLAPPED())
            else:
                fcntl.flock(self.file, fcntl.LOCK_UN)
            self.has_lock = False

    def write(self, s):
        self.seek(0)
        self.truncate()     #当1000->999时，写入时变成9990, 需清空
        self.file.write(s)
        if os.name == 'nt':
            #--- This flush helps the file knows where it ends.
            self.file.flush()

    def truncate(self):
        ''' 文件截取 '''
        self.file.truncate()

    def close(self):
        ''' 关闭文件 '''
        self.release_lock()
        self.file.close()

    def flush(self):
        ''' 刷新文件的内部缓冲区 '''
        self.file.flush()

    def fsync(self):
        ''' 强制将文件写入硬盘 '''
        if hasattr(os, 'fsync'):
            os.fsync(self.file)
