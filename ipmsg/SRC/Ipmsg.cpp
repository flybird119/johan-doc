static char *ipmsg_id = 
	"@(#)Copyright (C) H.Shirouzu 1996-2002   ipmsg.cpp	Ver2.00";
/* ========================================================================
	Project  Name			: IP Messenger for Win32
	Module Name				: IP Messenger Application Class
	Create					: 1996-06-01(Sat)
	Update					: 2002-11-03(Sun)
	Copyright				: H.Shirouzu
	Reference				: 
	======================================================================== */

#include <time.h>
#include "tlib.h"
#include "resource.h"
#include "ipmsg.h"

#define IPMSG_CLASS	"ipmsg_class"

TMsgApp::TMsgApp(HINSTANCE _hI, LPSTR _cmdLine, int _nCmdShow) : TApp(_hI, _cmdLine, _nCmdShow)
{
	srand((UINT)Time());	//随机数发生器 参数为随机数种子
}

TMsgApp::~TMsgApp()
{
}
//初始化主窗体
void TMsgApp::InitWindow(void)
{
	WNDCLASS	wc;
	HWND		hWnd;
	char		class_name[MAX_PATH] = IPMSG_CLASS, *tok, *msg, *p;
	ULONG		nicAddr = 0;
	int			port_no = atoi(cmdLine);//从命令行中读取端口

	if (port_no == 0)
		port_no = IPMSG_DEFAULT_PORT;

	if ((tok = strchr(cmdLine, '/')) && separate_token(tok, ' ', &p))
	{
		BOOL	diag = TRUE;
		DWORD	status = 0xffffffff;

		if (stricmp(tok, "/NIC") == 0)	// NIC 巜掕
		{
			if (tok = separate_token(NULL, ' ', &p))
				nicAddr = ResolveAddr(tok);
		}
		else if (stricmp(tok, "/MSG") == 0)	// 僐儅儞僪儔僀儞儌乕僪
		{
			MsgMng	msgMng(nicAddr, port_no);
			ULONG	command = IPMSG_SENDMSG|IPMSG_NOADDLISTOPT|IPMSG_NOLOGOPT, destAddr;

			while ((tok = separate_token(NULL, ' ', &p)) != NULL && *tok == '/') {
				if (stricmp(tok, "/LOG") == 0)
					command &= ~IPMSG_NOLOGOPT;
				else if (stricmp(tok, "/SEAL") == 0)
					command |= IPMSG_SECRETOPT;
			}

			if ((msg = separate_token(NULL, 0, &p)) != NULL)
			{
				diag = FALSE;
				 if ((destAddr = ResolveAddr(tok)) != NULL)
					status = msgMng.Send(destAddr, htons(port_no), command, msg) ? 0 : -1;
			}
		}
		if (nicAddr == 0)
		{
			if (diag)
				MessageBox(0, "ipmsg.exe [portno] [/MSG [/LOG] [/SEAL] <hostname or IP addr> <message>]\r\nipmsg.exe [portno] [/NIC nic_addr]", MSG_STR, MB_OK);
			::ExitProcess(status);
			return;
		}
	}

	if (port_no != IPMSG_DEFAULT_PORT || nicAddr)
		wsprintf(class_name, nicAddr ? "%s_%d_%s" : "%s_%d", IPMSG_CLASS, port_no, inet_ntoa(*(in_addr *)&nicAddr));

	memset(&wc, 0, sizeof(wc));
	wc.style			= CS_DBLCLKS;
	wc.lpfnWndProc		= TApp::WinProc;
	wc.cbClsExtra 		= 0;
	wc.cbWndExtra		= 0;
	wc.hInstance		= hI;
	wc.hIcon			= ::LoadIcon(hI, (LPCSTR)IPMSG_ICON);	//设置logo图片
	wc.hCursor			= ::LoadCursor(NULL, IDC_ARROW);
	wc.hbrBackground	= NULL;
	wc.lpszMenuName		= NULL;
	wc.lpszClassName	= class_name;

	HANDLE	hMutex = ::CreateMutex(NULL, FALSE, class_name);
	::WaitForSingleObject(hMutex, INFINITE);

	if ((hWnd = ::FindWindow(class_name, NULL)) != NULL || ::RegisterClass(&wc) == 0)////防止同时运行两个程序实例
	{
		if (hWnd != NULL)
			::SetForegroundWindow(hWnd);
		::ExitProcess(0xffffffff);
		return;
	}

	mainWnd = new TMainWin(nicAddr, port_no);//创建一个新的TMainWin窗口
	mainWnd->Create(class_name, IP_MSG, WS_OVERLAPPEDWINDOW | (IsNewShell() ? WS_MINIMIZE : 0));//创建TMainWin的CWnd窗口，启动时最小化
	::ReleaseMutex(hMutex);
	::CloseHandle(hMutex);
}
//程序入口
int WINAPI WinMain(HINSTANCE hI, HINSTANCE, LPSTR cmdLine, int nCmdShow)
{
	TMsgApp	app(hI, cmdLine, nCmdShow);

	return	app.Run();
}

