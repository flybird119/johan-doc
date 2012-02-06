/*
 * Compile with:
 * cc -I/usr/local/include -o event-test event-test.c -L/usr/local/lib -levent
 */

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <sys/types.h>
#include <sys/stat.h>

#ifndef WIN32	//如果没有定义
#include <sys/queue.h>
#include <unistd.h>
#include <sys/time.h>
#else
#include <windows.h>
#endif

#include <fcntl.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>

#include <event.h>	//	/usr/local/include/event.h

static void
fifo_read(int fd, short event, void *arg)	//回调函数
{
	char buf[255];
	int len;
	struct event *ev = arg;
#ifdef WIN32
	DWORD dwBytesRead;
#endif

	/* Reschedule this event */		//事件调度
	event_add(ev, NULL);

	fprintf(stderr, "管道文件 fifo_read called with 文件标志fd: %d, event: %d, arg: %p\n",
		fd, event, arg);
#ifdef WIN32
	len = ReadFile((HANDLE)fd, buf, sizeof(buf) - 1, &dwBytesRead, NULL);

	// Check for end of file.
	if(len && dwBytesRead == 0) {
		fprintf(stderr, "End Of File");
		event_del(ev);
		return;
	}

	buf[dwBytesRead] = '\0';
#else
	//------------读取文件对象 开始
	len = read(fd, buf, sizeof(buf) - 1);

	if (len == -1) {
		perror("read");
		return;
	} else if (len == 0) {
		fprintf(stderr, "Connection closed\n");
		return;
	}

	buf[len] = '\0';	//字符串尾处理
	//-----------读取文件结束
#endif
	fprintf(stdout, "读取到 Read: %s\n", buf);
}

int
main (int argc, char **argv)
{
	struct event evfifo;	//定义事件-----------------------------------------------
#ifdef WIN32
	HANDLE socket;
	// Open a file.
	socket = CreateFile("test.txt",     // open File
			GENERIC_READ,                 // open for reading
			0,                            // do not share
			NULL,                         // no security
			OPEN_EXISTING,                // existing file only
			FILE_ATTRIBUTE_NORMAL,        // normal file
			NULL);                        // no attr. template

	if(socket == INVALID_HANDLE_VALUE)
		return 1;

#else
	struct stat st; 	//文件属性结构体
	const char *fifo = "event.fifo";
	int socket;

	if (lstat (fifo, &st) == 0) {	//Get file attributes 获取文件属性
		if ((st.st_mode & S_IFMT) == S_IFREG) {
			errno = EEXIST;
			perror("lstat");
			exit (1);
		}
	}

	unlink (fifo);	//Remove the link	移除文件链接
	if (mkfifo (fifo, 0600) == -1) {	//Create a new FIFO  创建一个命名管道
		perror("mkfifo");
		exit (1);
	}

	/* Linux pipes are broken, we need O_RDWR instead of O_RDONLY */
#ifdef __linux
	socket = open (fifo, O_RDWR | O_NONBLOCK, 0);	//打开对象
#else
	socket = open (fifo, O_RDONLY | O_NONBLOCK, 0);
#endif

	if (socket == -1) {
		perror("open");
		exit (1);
	}

	fprintf(stderr, "Write data to %s\n", fifo);
#endif
	/* Initalize the event library */
	event_init();//------------------------------------------------------

	/* Initalize one event */
#ifdef WIN32
	event_set(&evfifo, (int)socket, EV_READ, fifo_read, &evfifo);
#else
	event_set(&evfifo, socket, EV_READ, fifo_read, &evfifo);//-----------
#endif

	/* Add it to the active events, without a timeout */
	event_add(&evfifo, NULL);//-----------------------------------------

	event_dispatch();//--------------------------------------------------
#ifdef WIN32
	CloseHandle(socket);
#endif
	return (0);
}

