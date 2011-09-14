nginxConf="""
        listen %(PORT)s;
        server_name ADMS;
        location / {
            #fastcgi_pass 127.0.0.1:%(FCGI_PORT)s;
            #include        fastcgi.conf;
            proxy_pass  http://127.0.0.1:%(FCGI_PORT)s/;
            proxy_set_header Host $host:$server_port;
            proxy_redirect off;                                                                                                                              
            proxy_set_header X-Real-IP $remote_addr;                                                                                                         
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;             
        }
"""