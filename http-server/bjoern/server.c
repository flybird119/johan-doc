//#include <sys/socket.h>
//#include <netinet/in.h>
//#include <arpa/inet.h>
#include <fcntl.h>
#ifdef WANT_SIGINT_HANDLING
# include <sys/signal.h>
#endif
//#include <sys/sendfile.h>
#include <uv.h>

#include "common.h"
#include "wsgi.h"
#include "server.h"

//#define LISTEN_BACKLOG  1024
//#define READ_BUFFER_SIZE 64*1024
//�ͷŶ���
#define Py_XCLEAR(obj) do { if(obj) { Py_DECREF(obj); obj = NULL; } } while(0)
#define GIL_LOCK(n) _gilstate_##n = PyGILState_Ensure()	//�߳�״̬����
#define GIL_UNLOCK(n) PyGILState_Release(_gilstate_##n)
//libuv�����ӡ
#define UVERR(err, msg) fprintf(stderr, "%s: %s\n", msg, uv_strerror(err))

//static int sockfd;	// �׽���ID	ȫ�ֱ���
static const char* http_error_messages[4] = {
  NULL, /* Error codes start at 1 because 0 means "no error" */
  "HTTP/1.1 400 Bad Request\r\n\r\n",
  "HTTP/1.1 406 Length Required\r\n\r\n",
  "HTTP/1.1 500 Internal Server Error\r\n\r\n"
};

#define RESPONSE \
  "HTTP/1.1 200 OK\r\n" \
  "Content-Type: text/plain\r\n" \
  "Content-Length: 12\r\n" \
  "\r\n" \
  "hello world\n"

//typedef void ev_io_callback(struct ev_loop*, ev_io*, const int);	// ����ص������ṹ��
#if WANT_SIGINT_HANDLING
typedef void ev_signal_callback(struct ev_loop*, ev_signal*, const int);
static ev_signal_callback ev_signal_on_sigint;
#endif
//static ev_io_callback ev_io_on_request;	//��дI/O ʱ�Ĵ�����	3����Ҫ�Ļص��¼�
//static ev_io_callback ev_io_on_read;
//static ev_io_callback ev_io_on_write;
static void on_connection(uv_stream_t* server, int status);
static void on_read(uv_stream_t* handle, ssize_t nread, uv_buf_t buf);
static void on_close(uv_handle_t* handle); 


static bool send_chunk(Request*);
static bool do_sendfile(Request*);
static bool handle_nonzero_errno(Request*);
static void after_write(uv_write_t* req, int status);
static void io_write(Request* request);

static void _http_uv__on_close__cb(uv_handle_t* handle);
static void _http_client__finish(Request *req);
static void _http_request__finish(Request *req);

//static uv_handle_t* server;
static uv_tcp_t tcpServer;	//����ȫ�ַ���ṹ��
static uv_loop_t* loop;	//����ȫ�ֵ��¼�ѭ��

static uv_buf_t resbuf_s;
PyGILState_STATE _gilstate_0;

static void _http_uv__on_close__cb(uv_handle_t* handle) {
    //LOGF("[ %5d ] connection closed", client->request_num);
    _http_client__finish((Request*) handle->data);
}

static void _http_client__finish(Request *req) {
    // TODO figure out uv_close and deletion of client / tcp connection
    if (req != NULL) {
        _http_request__finish(req);
    }
    free(req);
}

static void _http_request__finish(Request *req) {
	printf("�Ͽ��˴�����\n");
	Request_free(req);
    req = NULL;
	free(req);//����Ҫ,����loop�Զ��˳�
}


int server_run(const char* hostaddr, const int port)	//���з���
{
  int r;
  struct sockaddr_in addr;
  //sockaddr_in addr;
  loop = uv_default_loop();	

  resbuf_s.base = RESPONSE;
  resbuf_s.len = sizeof(RESPONSE);

  addr = uv_ip4_addr(hostaddr, port);	//�����׽��ֵ�ַ

  r = uv_tcp_init(loop, &tcpServer);	//��ʼ������handler�����׽���
  if (r) {
    /* TODO: Error codes */
    fprintf(stderr, "Socket creation error\n");
    return 1;
  }

  r = uv_tcp_bind(&tcpServer, addr);	//���׽��ֵ�ַ
  if (r) {
    /* TODO: Error codes */
    fprintf(stderr, "Bind error\n");
    return 1;
  }

  Py_BEGIN_ALLOW_THREADS
  r = uv_listen((uv_stream_t*)&tcpServer, SOMAXCONN, on_connection);	//�����˿�
  Py_END_ALLOW_THREADS
  if (r) {
    /* TODO: Error codes */
    fprintf(stderr, "Listen error %s\n",
        uv_err_name(uv_last_error(loop)));
    return 1;
  }
  uv_run(loop);

#if WANT_SIGINT_HANDLING
  ev_signal signal_watcher;
  ev_signal_init(&signal_watcher, ev_signal_on_sigint, SIGINT);
  ev_signal_start(mainloop, &signal_watcher);
#endif
  return 0;
}


uv_buf_t on_alloc(uv_handle_t* client, size_t suggested_size) {
  uv_buf_t buf;
  buf.base = malloc(suggested_size);
  buf.len = suggested_size;
  return buf;
}

static void on_connection(uv_stream_t* server, int status) {	//���пͻ�������ʱ����
	int r;
	uv_stream_t* stream;
	Request* request;
	struct sockaddr_in sockaddr;	//�����׽��ֵ�ַ
	socklen_t addrlen;

	if (status != 0) {				//״̬�ж�, ״̬����Ϊ0
	fprintf(stderr, "Connect error %d\n",
		uv_last_error(loop).code);
	}
	ASSERT(status == 0);

	GIL_LOCK(0);
	request = Request_init();
	GIL_UNLOCK(0);

	r = uv_tcp_init(loop, &request->ev_watcher);//��ʼ���������ṹ��
	ASSERT(r == 0);

	request->ev_watcher.data = request;

	r = uv_accept(server, (uv_stream_t*)&request->ev_watcher);
	ASSERT(r == 0);

	//-----------------�õ��ͻ�����Ϣ
	addrlen = sizeof(struct sockaddr_in);
	//socket = (int)(((uv_tcp_t*) stream)->socket);
	r = uv_tcp_getpeername(&request->ev_watcher, (struct sockaddr *)&sockaddr, &addrlen);
	ASSERT(r == 0);
	
	request->client_addr = PyString_FromString(inet_ntoa(sockaddr.sin_addr));
	request->client_fd = request->ev_watcher.socket;

	DBG_REQ(request, "Accepted client %s:%d on fd %d",
		  inet_ntoa(sockaddr.sin_addr), ntohs(sockaddr.sin_port), (int)((request->ev_watcher).socket));
	free(&sockaddr);
	//-----------------���¼�ѭ��
	r = uv_read_start((uv_stream_t*)&request->ev_watcher, on_alloc, on_read);
	ASSERT(r == 0);
}


#if WANT_SIGINT_HANDLING
static void
ev_signal_on_sigint(struct ev_loop* mainloop, ev_signal* watcher, const int events)
{
  /* Clean up and shut down this thread.
   * (Shuts down the Python interpreter if this is the main thread) */
  ev_unloop(mainloop, EVUNLOOP_ALL);
  PyErr_SetInterrupt();
}
#endif



static void after_write(uv_write_t* req, int status) {
  printf("after_write\n");
  if (status) {
    uv_err_t err = uv_last_error(loop);
	printf("after_write status erro\n");
    fprintf(stderr, "uv_write error: %s\n", uv_strerror(err));
	//ASSERT(0);
  }

  //uv_tcp_keepalive((uv_tcp_t*)req->handle, 1, 200);
  //uv_close((uv_handle_t*)req->handle, on_close);
  /* Free the read/write buffer and the request */
  free(req);
}

static void on_read(uv_stream_t* handle, ssize_t nread, uv_buf_t buf) {

	int i;
	Request* request;
	//uv_shutdown_t* req;
	uv_err_t err;

	request =(Request*)handle->data;
	GIL_LOCK(0);
	if (nread < 0) {
		/* Error or EOF */
		printf("Error or EOF %d\n",uv_last_error(loop).code);
		//--------------------hhhhhhh-------------------ASSERT (uv_last_error(loop).code == UV_EOF);

		if (buf.base) {
		  free(buf.base);
		}
		err = uv_last_error(loop);
        if (err.code != UV_EOF) {
            UVERR(err, "read");
        }
		//req = (uv_shutdown_t*) malloc(sizeof *req);
		//uv_shutdown(req, handle, after_shutdown);
		return;
	}

	if (nread == 0) {
		/* Everything OK, but nothing read. */
		free(buf.base);
		return;
	}
    Request_parse(request, buf.base, nread);	//����Request����
	free(buf.base);
    if(request->state.error_code) {
      DBG_REQ(request, "Parse error");
      request->current_chunk = PyString_FromString(
        http_error_messages[request->state.error_code]);
	  assert(request->iterator == NULL);
	  uv_close((uv_handle_t*) &request->ev_watcher, on_close);
	  goto out;
    }
    else if(request->state.parse_finished) {	// ׼����
	  printf("ִ��wsgi���� >>>\n");
      if(!wsgi_call_application(request)) {	// ִ��wsgi
	    printf("wsgiִ�а�������\n");
        assert(PyErr_Occurred());
        PyErr_Print();
        assert(!request->state.chunked_response);
        Py_XCLEAR(request->iterator);
        request->current_chunk = PyString_FromString(
          http_error_messages[HTTP_SERVER_ERROR]);
      }
	  printf("��ʼ�ͻ������ݷ��� >>>\n");
	  while(request->current_chunk){
		io_write(request);
	  }
    } else {
      /* Wait for more data */
      goto out;
    }
    //request = (Request*) parser->data;
    //io_write(request);
//	if (uv_write(&wr->req, handle, &wr->buf, 1, after_write)) {
//	FATAL("uv_write failed");
//	}

	out:
	  GIL_UNLOCK(0);
	  return;
}

static void on_close(uv_handle_t* handle) {
  Request* request =(Request*)handle->data;
  DBG_REQ(request, "done, close");
  Request_free(request);
  printf("gone.........\n");
  //free(request);
}

static void io_write(Request* request)
{
  GIL_LOCK(0);

  if(request->state.use_sendfile) {//�ͻ��˷����ļ�ʱ
	printf("�����ļ����ͻ���\n");
    /* sendfile */
    if(request->current_chunk && send_chunk(request))
      goto out;
    /* abuse current_chunk_p to store the file fd */
    request->current_chunk_p = PyObject_AsFileDescriptor(request->iterable);
    if(do_sendfile(request))
      goto out;
  } else {
    printf("�����ַ�\n");
    /* iterable */
	if(send_chunk(request)){
	  printf("��Ӧ�ɹ�,׼������...\n");
	  //uv_close((uv_handle_t*) &request->ev_watcher, _http_uv__on_close__cb);
      goto out;
	}

    if(request->iterator) {
      PyObject* next_chunk;
	  printf("request����\n");
      next_chunk = wsgi_iterable_get_next_chunk(request);
      if(next_chunk) {
		printf("��һ��chunk����\n");
        if(request->state.chunked_response) {
          request->current_chunk = wrap_http_chunk_cruft_around(next_chunk);
          Py_DECREF(next_chunk);
        } else {
          request->current_chunk = next_chunk;
        }
        assert(request->current_chunk_p == 0);
		//io_write(request);
        goto out;
      } else {
	    printf("û����һ��chunk\n");
        if(PyErr_Occurred()) {
		  uv_err_t err;
          PyErr_Print();
          /* We can't do anything graceful here because at least one
           * chunk is already sent... just close the connection */
          DBG_REQ(request, "Exception in iterator, can not recover");
		  uv_close((uv_handle_t*) &request->ev_watcher, on_close);
//          ev_io_stop(mainloop, &request->ev_watcher);
//          close(request->client_fd);	// �رտͻ����׽���

			//free(wr->buf.base);
			//free(wr);

		  err = uv_last_error(loop);
		  //Request_free(request);
		  fprintf(stderr, "uv_write error: %s\n", uv_strerror(err));
		  ASSERT(0);
		  printf("��������\n");
          goto out;
        }
        Py_CLEAR(request->iterator);
      }
    }

    if(request->state.chunked_response) {
      printf("�����chunked_response ������β����,���ÿ�chunked_response\n");
      /* We have to send a terminating empty chunk + \r\n */
      request->current_chunk = PyString_FromString("0\r\n\r\n");
      assert(request->current_chunk_p == 0);
	  //io_write(request);
      request->state.chunked_response = false;
      goto out;
    }
  }
  printf("��Ӧȫ�����\n");
  //ev_io_stop(mainloop, &request->ev_watcher);

  if(request->state.keep_alive) {
    int r;
    DBG_REQ(request, "done, keep-alive");
    Request_clean(request);
    Request_reset(request);
  } else {
    //DBG_REQ(request, "done, close");
	uv_close((uv_handle_t*) &request->ev_watcher, on_close);
    //Request_free(request);
  }


out:
  printf("����hander�������\n");
  GIL_UNLOCK(0);
}

static bool
send_chunk(Request* request)
{
  Py_ssize_t chunk_length;
  Py_ssize_t bytes_sent;
  static uv_buf_t resbuf;
  //printf("send_chunk:\n%s\n",PyString_AS_STRING(request->current_chunk) + request->current_chunk_p);
  printf("���ʹ�С:%d\n",PyString_GET_SIZE(request->current_chunk) - request->current_chunk_p);
  assert(request->current_chunk != NULL);
  assert(!(request->current_chunk_p == PyString_GET_SIZE(request->current_chunk)
         && PyString_GET_SIZE(request->current_chunk) != 0));
					  //-----------------------------------------ϵͳ����--------------------
//  bytes_sent = write(
//    request->client_fd,
//    PyString_AS_STRING(request->current_chunk) + request->current_chunk_p,
//    PyString_GET_SIZE(request->current_chunk) - request->current_chunk_p
//  );
  resbuf = uv_buf_init(PyString_AS_STRING(request->current_chunk) + request->current_chunk_p, PyString_GET_SIZE(request->current_chunk) - request->current_chunk_p);
  bytes_sent = uv_write(
		   &request->write_req,
		   (uv_stream_t*)&request->ev_watcher,
		   &resbuf,
		   1,
		   after_write);

  if(bytes_sent == -1){
    printf("�������ݳ���\n");
	printf("send_chunk:\n%s\n",PyString_AS_STRING(request->current_chunk) + request->current_chunk_p);
    return handle_nonzero_errno(request);
  }
  request->current_chunk_p += resbuf.len;
  if(request->current_chunk_p == PyString_GET_SIZE(request->current_chunk)) {
    Py_CLEAR(request->current_chunk);
    request->current_chunk_p = 0;
    return false;
  }
  Py_CLEAR(request->current_chunk);
  free(resbuf.base);
  return true;
}

#define SENDFILE_CHUNK_SIZE 16*1024

static bool
do_sendfile(Request* request)
{
  Py_ssize_t bytes_sent = 1;
	 // sendfile(
  //  request->client_fd,
  //  request->current_chunk_p, /* current_chunk_p stores the file fd */
  //  NULL, SENDFILE_CHUNK_SIZE
  //);
  if(bytes_sent == -1)
    return handle_nonzero_errno(request);
  return bytes_sent != 0;
}

static bool
handle_nonzero_errno(Request* request)
{
  if(errno == EAGAIN || errno == WSAEWOULDBLOCK) {	//EWOULDBLOCK
    /* Try again later */
    return true;
  } else {
    /* Serious transmission failure. Hang up. */
    fprintf(stderr, "Client %d hit errno %d\n", request->client_fd, errno);
    Py_XDECREF(request->current_chunk);
    Py_XCLEAR(request->iterator);
    request->state.keep_alive = false;
    Request_clean(request);
    Request_reset(request);
    return false;
  }
}


