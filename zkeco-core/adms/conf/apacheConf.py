apacheConf="""
ServerName ADMS
Listen %(address)s

# ThreadsPerChild 100
ThreadsPerChild %(numthreads)s

# MaxRequestsPerChild  0
MaxRequestsPerChild %(request_queue_size)s

KeepAlive On
KeepAliveTimeout 2

Timeout 600

LoadModule python_module modules/mod_python.so
#LoadModule access_module modules/mod_access.so
LoadModule actions_module modules/mod_actions.so
LoadModule alias_module modules/mod_alias.so
LoadModule asis_module modules/mod_asis.so
LoadModule autoindex_module modules/mod_autoindex.so
LoadModule dir_module modules/mod_dir.so
LoadModule env_module modules/mod_env.so
LoadModule file_cache_module modules/mod_file_cache.so
LoadModule log_config_module modules/mod_log_config.so
LoadModule mime_module modules/mod_mime.so

AddType text/css        css
TypesConfig conf/mime.types

<Location "/">
        SetHandler python-program
        PythonHandler django.core.handlers.modpython
        SetEnv DJANGO_SETTINGS_MODULE mysite.settings
        PythonDebug On
        Options All
</Location>

Alias /media/ "%(path)s/mysite/media/"
<Location "/media">
        SetHandler None
</Location>
Alias /iclock/media/ "%(path)s/mysite/media/"
<Location "/media">
        SetHandler None
</Location>

Alias /iclock/file/ "%(path)s/mysite/files/"
<Location "/iclock/file">
        SetHandler None
</Location>

Alias /iclock/tmp/ "%(path)s/mysite/tmp/"
<Location "/iclock/tmp">
        SetHandler None
</Location>

# LogFormat "%%h %%l %%u %%t \\"%%r\\" %%>s %%b" common
# CustomLog %(path)s/mysite/tmp/apache_access.log common
ErrorLog %(path)s/mysite/tmp/apache_error.log
"""