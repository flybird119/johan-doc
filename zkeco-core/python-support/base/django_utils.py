# coding=utf-8

from django.db import connection

def get_db_type():
    '''
    获取当前站点数据库类型
    '''
    db_select=1
    if 'mysql' in connection.__module__:#mysql 数据库
        db_select=1
    elif 'sqlserver_ado' in connection.__module__:#sqlserver 2005 数据库 
        db_select=2
    elif 'oracle' in connection.__module__: #oracle 数据库 
        db_select=3
    elif 'postgresql_psycopg2' in connection.__module__: # postgresql 数据库
        db_select=4
    return db_select