/*
 * Compile with:
 * cc -I/usr/local/include -o time-test time-test.c -L/usr/local/lib -levent
 */

#include <sys/types.h>

#ifdef HAVE_CONFIG_H
#include "config.h"
#endif

#include <sys/stat.h>
#ifndef WIN32
#include <sys/queue.h>
#include <unistd.h>
#include <sys/time.h>
#else
#include <windows.h>
#endif
#include <signal.h>
#include <fcntl.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>

#include <event.h>

int called = 0;

static void
signal_cb(int fd, short event, void *arg)
{
	struct event *signal = arg;

	printf("%s: got signal %d\n", __func__, EVENT_SIGNAL(signal));

	if (called >= 2)
		event_del(signal);

	called++;
}

int
main (int argc, char **argv)
{
	struct event signal_int;	//定义事件

	/* Initalize the event library */
	event_init();

	/* Initalize one event */
	event_set(&signal_int, SIGINT, EV_SIGNAL|EV_PERSIST, signal_cb,
	    &signal_int);
	// 添加事件监听
	event_add(&signal_int, NULL);
	// 开始循环
	event_dispatch();

	return (0);
}

