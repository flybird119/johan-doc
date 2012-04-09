/*
 * Copyright (C) Eric Zhang
 */
#include <ngx_config.h>
#include <ngx_core.h>
#include <ngx_http.h>
/* Module config 模块配置结构 */
typedef struct {
    ngx_str_t  ed;	//用于存储echo指令指定的需要输出的字符串
} ngx_http_echo_loc_conf_t;

static char *ngx_http_echo(ngx_conf_t *cf, ngx_command_t *cmd, void *conf);
static void *ngx_http_echo_create_loc_conf(ngx_conf_t *cf);
static char *ngx_http_echo_merge_loc_conf(ngx_conf_t *cf, void *parent, void *child);
/* Directives 定义指令数组 */
static ngx_command_t  ngx_http_echo_commands[] = {
    { ngx_string("echo"),
      NGX_HTTP_LOC_CONF|NGX_CONF_TAKE1,	//精确接受一个参数
      ngx_http_echo,	//函数指针	参数转化函数
      NGX_HTTP_LOC_CONF_OFFSET,	//指定Nginx相应配置文件内存其实地址，一般可以通过内置常量指定
      offsetof(ngx_http_echo_loc_conf_t, ed),	//指定此条指令的参数的偏移量
      NULL },
      ngx_null_command
};
/* Http context of the module 定义模块上下文Contexts 主要用于定义各个Hook函数*/
static ngx_http_module_t  ngx_http_echo_module_ctx = {
    NULL,                                  /* preconfiguration */
    NULL,                                  /* postconfiguration */
    NULL,                                  /* create main configuration */
    NULL,                                  /* init main configuration */
    NULL,                                  /* create server configuration */
    NULL,                                  /* merge server configuration */
    ngx_http_echo_create_loc_conf,         /* create location configration */
    ngx_http_echo_merge_loc_conf           /* merge location configration */
};
/* Module 模块被定义为一个ngx_module_t结构 */
ngx_module_t  ngx_http_echo_module = {
    NGX_MODULE_V1,
    &ngx_http_echo_module_ctx,             /* module context */
    ngx_http_echo_commands,                /* module directives */
    NGX_HTTP_MODULE,                       /* module type */
    NULL,                                  /* init master 若干特定事件的回调处理函数（不需要可以置为NULL）*/
    NULL,                                  /* init module */
    NULL,                                  /* init process */
    NULL,                                  /* init thread */
    NULL,                                  /* exit thread */
    NULL,                                  /* exit process */
    NULL,                                  /* exit master */
    NGX_MODULE_V1_PADDING
};
/* Handler function 可以说是模块中真正干活的代码：读入模块配置。处理功能业务。产生HTTP header。产生HTTP body。*/
static ngx_int_t
ngx_http_echo_handler(ngx_http_request_t *r)
{
    ngx_int_t rc;
    ngx_buf_t *b;
    ngx_chain_t out;
    ngx_http_echo_loc_conf_t *elcf;
    elcf = ngx_http_get_module_loc_conf(r, ngx_http_echo_module);	//获取模块配置信息
    if(!(r->method & (NGX_HTTP_HEAD|NGX_HTTP_GET|NGX_HTTP_POST)))
    {
        return NGX_HTTP_NOT_ALLOWED;
    }
    r->headers_out.content_type.len = sizeof("text/html") - 1;	//设置response header。Header内容可以通过填充headers_out实现
    r->headers_out.content_type.data = (u_char *) "text/html";
    r->headers_out.status = NGX_HTTP_OK;
    r->headers_out.content_length_n = elcf->ed.len;
    if(r->method == NGX_HTTP_HEAD)
    {
        rc = ngx_http_send_header(r);	//设置好头信息后使用ngx_http_send_header就可以将头信息输出
        if(rc != NGX_OK)
        {
            return rc;
        }
    }
    b = ngx_pcalloc(r->pool, sizeof(ngx_buf_t));
    if(b == NULL)
    {
        ngx_log_error(NGX_LOG_ERR, r->connection->log, 0, "Failed to allocate response buffer.");
        return NGX_HTTP_INTERNAL_SERVER_ERROR;
    }
    out.buf = b;	//某个数据缓冲区的指针
    out.next = NULL;	//指向下一个链表节点
    b->pos = elcf->ed.data;	//缓冲区数据在内存中的起始地址和结尾地址
    b->last = elcf->ed.data + (elcf->ed.len);
    b->memory = 1;
    b->last_buf = 1;	//一个位域，设为1表示此缓冲区是链表中最后一个元素，为0表示后面还有元素
    rc = ngx_http_send_header(r);
    if(rc != NGX_OK)
    {
        return rc;
    }
    return ngx_http_output_filter(r, &out);	//输出了（会送到filter进行各种过滤处理）。	第二个为输出链表的起始地址
}
static char *//调用ngx_conf_set_str_slot转化echo指令的参数外，还将修改了核心模块配置（也就是这个location的配置），将其handler替换为我们编写的handler：ngx_http_echo_handler。这样就屏蔽了此location的默认handler
ngx_http_echo(ngx_conf_t *cf, ngx_command_t *cmd, void *conf)
{
    ngx_http_core_loc_conf_t  *clcf;
    clcf = ngx_http_conf_get_module_loc_conf(cf, ngx_http_core_module);
    clcf->handler = ngx_http_echo_handler;
    ngx_conf_set_str_slot(cf,cmd,conf);
    return NGX_CONF_OK;
}
static void *//初始化一个配置结构体，如为配置结构体分配内存
ngx_http_echo_create_loc_conf(ngx_conf_t *cf)
{
    ngx_http_echo_loc_conf_t  *conf;
    conf = ngx_pcalloc(cf->pool, sizeof(ngx_http_echo_loc_conf_t));
    if (conf == NULL) {
        return NGX_CONF_ERROR;
    }
    conf->ed.len = 0;
    conf->ed.data = NULL;
    return conf;
}
static char *	//将其父block的配置信息合并到此结构体中
ngx_http_echo_merge_loc_conf(ngx_conf_t *cf, void *parent, void *child)
{
    ngx_http_echo_loc_conf_t *prev = parent;
    ngx_http_echo_loc_conf_t *conf = child;
    ngx_conf_merge_str_value(conf->ed, prev->ed, "");
    return NGX_CONF_OK;
}
