#include <Python.h>
#include <object.h>
#include "server.h"
#include "wsgi.h"
#include "bjoernmodule.h"	//PyObject* wsgi_app;
#include "filewrapper.h"


PyDoc_STRVAR(listen_doc,
"listen(application, host, port) -> None\n\n \
\
Makes bjoern listen to host:port and use application as WSGI callback. \
(This does not run the server mainloop.)");	//---------------------�ĵ��ַ���
static PyObject* listens(PyObject* self, PyObject* args)
{
  const char* host;
  int port;

  if(wsgi_app) {
    PyErr_SetString(
      PyExc_RuntimeError,
      "Only one bjoern server per Python interpreter is allowed"
    );
    return NULL;
  }

  if(!PyArg_ParseTuple(args, "Osi:run/listen", &wsgi_app, &host, &port))
    return NULL;

  _initialize_request_module(host, port);	//��ʼ�� wsgi ��һЩ������Ϣ


  //PyRun_SimpleString("import os\n"	//����һ�δ���
  //"print os\n");

  if(server_run(host, port)) {	//��ʼ���׽���
    PyErr_Format(
      PyExc_RuntimeError,
      "Could not start server on %s:%d", host, port
    );
    return NULL;
  }

  Py_RETURN_NONE;	// python ���ؿ�ֵ
}

PyDoc_STRVAR(run_doc,
"run(application, host, port) -> None\n \
Calls listen(application, host, port) and starts the server mainloop.\n \
\n\
run() -> None\n \
Starts the server mainloop. listen(...) has to be called before calling \
run() without arguments.");

static PyObject* run(PyObject* self, PyObject* args)
{
  if(PyTuple_GET_SIZE(args) == 0) {	//�����������ж�
    /* bjoern.run() */
    if(!wsgi_app) {
      PyErr_SetString(
        PyExc_RuntimeError,
        "Must call bjoern.listen(app, host, port) before "
        "calling bjoern.run() without arguments."
      );
      return NULL;
    }
  }
  else {
    /* bjoern.run(app, host, port) */
    if(!listens(self, args))
      return NULL;
  }
//  PyRun_SimpleString("def wsgi_app(environ, start_response):\n"
//							  "\tstart_response('200 OK', [])\n"
//							  "\tyield 'Hello world'\n"
//							  "\tyield ''\n");	//����һ�δ���
//  PyRun_SimpleString("print wsgi_app\n");	//����һ�δ���
//  server_run();	//���з�����ѭ��
  wsgi_app = NULL;
  Py_RETURN_NONE;
}
	//----------------------------------------------------------------------------------------------------cģ�麯������ӳ���
static PyMethodDef Bjoern_FunctionTable[] = {	// python ��չģ��funtion����
  {"run", run, METH_VARARGS, run_doc},	//bjoern.run(wsgi_application, host, port)
  {"listens", listens, METH_VARARGS, listen_doc}, //bjoern.listen(wsgi_application, host, port)
  {NULL, NULL, 0, NULL}
};

PyMODINIT_FUNC initbjoern()	//cģ��ĳ�ʼ������
{
  PyObject* bjoern_module;
  _init_common();
  _init_filewrapper();

  PyType_Ready(&FileWrapper_Type);
  assert(FileWrapper_Type.tp_flags & Py_TPFLAGS_READY);
  PyType_Ready(&StartResponse_Type);
  assert(StartResponse_Type.tp_flags & Py_TPFLAGS_READY);

  bjoern_module = Py_InitModule("bjoern", Bjoern_FunctionTable);
  PyModule_AddObject(bjoern_module, "version", Py_BuildValue("(ii)", 1, 2));
}


