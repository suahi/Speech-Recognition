#if _MSC_VER > 1000
#pragma once
#endif 
//#pragma comment(lib, "winmm.lib")
#include "VK70xNMC_DAQ2.h"
#include "dvr_header.h"
#include <Windows.h>
#include <stdio.h>
//#include <MMSystem.h> // 需要包含 Windows.h 头文件
#include <Ws2tcpip.h>

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//tcp/ip function
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//memset(&serv, 0, sizeof(serv));
//serv.sin_family = AF_INET;
//serv.sin_port = htons(80);
//serv.sin_addr.S_un.S_addr = inet_addr("115.239.210.26");
//SOCKET tcpclientport 
int DisposalTXDatum(SOCKET connectHandle, unsigned char cmd, unsigned char *txbuff, unsigned int txlen, unsigned char wrflag)
{
	char destpi[260];
	unsigned int  destlen, i, rawi;
	unsigned int temp;
	unsigned char checksum;
	int rii = -1;


	if (txlen > 250)return -1;// buffer 溢出

	destlen = txlen + 8;// 
	//destpi = (unsigned char *)malloc(destlen + 2);  // 多分配2字节，防止溢出

	//======================
	destpi[0] = vCOM_SYSNC_HEADER1;
	destpi[1] = vCOM_SYSNC_HEADER2;
	//------------------------
	temp = txlen + 4;// 1 byte cmd+ 1 byte checksum + 2bytes sn
	if (wrflag == 1) temp = temp | 0x8000;   // 高位置1，代表写命令
	destpi[2] = (unsigned char)(temp / 0x100);
	destpi[3] = (unsigned char)(temp);    // 长度
	//-------------------
	destpi[4] = vCOM_SYSNC_SN1;
	destpi[5] = vCOM_SYSNC_SN2;
	destpi[6] = cmd;
	if (txlen>0)
	{
		for (i = 0; i< txlen; i++)
		{
			destpi[i + 7] = *txbuff++;
		}
	}
	else i = 0;
	//=================
	rawi = i + 7;
	checksum = 0;
	for (i = 0; i< rawi; i++)
	{
		checksum = checksum + destpi[i];
	}
	destpi[rawi++] = checksum;
	//---------------------
	//if (connectHandle>0)
	//   rii = ServerTCPWrite (connectHandle,destpi,rawi,0);  //把数组发送出去
	//else //send(istcpclient, (char *)&ttxbuffer, rawi , 0); 
	rii = send(connectHandle, destpi, rawi, 0);
	//---------------------
	//Sleep(1);
	//free(destpi);
	return rii;
}


//VKTCPServer.PortNumber = 8234;
//	  VKTCPServer.RecievedBytes_Count=0;
//	  VKTCPServer.Client_Num=0;
//	  for(i = 0; i <= MAX_TCP_CILENT_NUM;i++)
//	  {
//		  VKTCPServer.ClientHandle[i]=0;  // 最大可以连接128个客户机
//		  VKTCPServer.ClientStatus[i]=0; 
//		  for(j = 0;j<128;j++)VKTCPServer.ClientIP[i][j]=0; 
//	  }
//static char datapbuffer[103200];
//static int  ThreadRunningReceiveFalg =0;
//static int  RunningTCPServer_handle=0;
//RXLANMonitor_Handle
//void MonitorUSBEvent(void)

/*
int TCPServerCB (unsigned handle, int xType, int errCode, void *callbackData)
{
int i;
switch (xType)
{
case TCP_CONNECT:
int  isexistconenctedflag = 0;
char tcpaddress[128];
memset(tcpaddress,0,128);
GetTCPPeerAddr (handle,tcpaddress, 128);
//当有客户连接时，获得TCP连接句柄
SetTCPDisconnectMode (handle, TCP_DISCONNECT_AUTO);
//-------------------------------
for(i=0; i < MAX_TCP_CILENT_NUM; i++)
{
if (stricmp(tcpaddress,VKTCPServer.ClientIP[i])==0)//(handle == VKTCPServer.ClientHandle[i])
{
VKTCPServer.ClientHandle[i] = handle;
VKTCPServer.ClientStatus[i] = 1;
//GetTCPPeerAddr (handle, VKTCPServer.ClientIP[i], 128);
memcpy(VKTCPServer.ClientIP[i],tcpaddress,128);
isexistconenctedflag = 1;
break;
}
}
//-----------------------------
if (isexistconenctedflag==0)
{
if(VKTCPServer.Client_Num>=MAX_TCP_CILENT_NUM)VKTCPServer.Client_Num=MAX_TCP_CILENT_NUM;
//--------------------------------
for(i=0; i < MAX_TCP_CILENT_NUM; i++)
{
if(VKTCPServer.ClientStatus[i]==0)
{
VKTCPServer.ClientHandle[i] = handle;
VKTCPServer.ClientStatus[i] = 1;
//GetTCPPeerAddr (handle, VKTCPServer.ClientIP[i], 128);
memcpy(VKTCPServer.ClientIP[i],tcpaddress,128);
VKTCPServer.Client_Num++;
break;
}
}
}
//-------------------------------------------
//char buffer[250];
//GetTCPPeerAddr (VKTCPServer.ClientHandle[VKTCPServer.Client_Num], tcpaddress, 250);  	//以下代码为获得客户机信息
//sprintf(buffer,"当前连接数：%d",VKTCPServer.Client_Num);
//////////////////////////////////////////////////////////////
break;

case TCP_DISCONNECT:		//TCP断开时产生的事件

for(i=0; i < MAX_TCP_CILENT_NUM; i++)
{
if (handle == VKTCPServer.ClientHandle[i])
{
VKTCPServer.ClientHandle[i] = 0;
VKTCPServer.ClientStatus[i] = 0;
memset(VKTCPServer.ClientIP[i],0,128);
break;
}
}
//---------------------------------------
if(VKTCPServer.Client_Num>0)VKTCPServer.Client_Num--;
//--------------------------------------
break;
case TCP_DATAREADY:

//----------------------
int readout_flag=0;
int readout_count;
for(i = 0; i< MAX_RX_CARD_NUM; i++)
{
if (handle == VKTCPServer.ClientHandle[i])
{
readout_flag=1;
readout_count =ServerTCPRead (handle,&VK[i].RXLANDatum[VK[i].RXLANSavePI],MAX_READ_TCP_UNIT,1);
if(readout_count>0)
{
VK[i].RXLANSavePI += readout_count;
if (VK[i].RXLANSavePI >= MAX_RXLAN_LEN)
{
VK[i].MaxBuffer_SaveedLen = VK[i].RXLANSavePI;
VK[i].MaxBuffer_OverFlag  = 1;
VK[i].RXLANSavePI=0;
}
//MultiCard_WirteBufferTask(i,(unsigned char *)datapbuffer,readout_count);
VKTCPServer.RecievedBytes_Count+=readout_count;	  //计算流量
}
break;
}
}
if (readout_flag == 0)
{
char datapbuffer[103200];		 // 其它采集卡，读出防止一直响应这个中断
readout_count =ServerTCPRead (handle,datapbuffer,103200,1);
if(readout_count>0)VKTCPServer.RecievedBytes_Count += readout_count;	  //计算流量
}
//------------------------------------
break;
}
return 0;
}
*/


//////////////////////////////////////////////////////////////////////////////////////////////////////////////
DWORD WINAPI TCPRecieveThreadEvent(PVOID pvParam)
{
	unsigned char i;
	int len;
	SOCKET      tclientsock;
	SOCKADDR_IN tclientadr;
	//-----------------------------
	memset(&VKTCPServer.ClientStatus, 0, sizeof(VKTCPServer.ClientStatus));
	//memset(&VKTCPServer.ClientAddr, 0, sizeof(VKTCPServer.ClientAddr));
	//memset(&VKTCPServer.SockClient, 0, sizeof(VKTCPServer.SockClient));
	//memset(&serv, 0, sizeof(serv));
	//serv.sin_family = AF_INET;
	//serv.sin_port = htons(80);
	//serv.sin_addr.S_un.S_addr = inet_addr("115.239.210.26");
	//SOCKET tcpclientport 
	//------------------------------
	//int threadslpflag=0;
	//debug_infor_status = 100;
	//TCPMonitor_ThreadRunningState = 0;
	//RXLANMonitor_ThreadRunningState = 0;
	TCPMonitor_ThreadRunningState = 2;//开始读写
	len = sizeof(SOCKADDR);//SOCKET sockConn
	while (TCPMonitor_ThreadRunningState > 0)//
	{
		//等待客户请求到来  		
		tclientsock = accept(VKTCPServer.SockServer, (SOCKADDR*)&tclientadr, &len); // 阻塞式

		if (tclientsock == INVALID_SOCKET)
		{
			Sleep(10);
			//debug_infor_status = 1000;
		}
		else
		{
			ULONG NonBlock = 1;
			ioctlsocket(tclientsock, FIONBIO, &NonBlock);
			int  isexistconenctedflag = 0;
			char tempchar[128] = { 0 };// inet_ntoa(VKTCPServer.ClientAddr[i].sin_addr)
			char destchar[128] = { 0 };// inet_ntoa(tclientadr.sin_addr)
			//debug_infor_status += 100;
			//printf("客户端已连接 [%s,%d]\n", inet_ntoa(TCPIP_ClientAddr.sin_addr), TCPIP_ClientAddr.sin_port);   //打印接收到的数据  
			//-------------------------------
			for (i = 0; i < MAX_TCP_CILENT_NUM; i++)
			{
				//if (tclientadr.sin_addr == VKTCPServer.ClientAddr[i].sin_addr)//(handle == VKTCPServer.ClientHandle[i])
				//char dest[50] = { 0 };
				//char src[50] = { "888" };
				//strcpy(dest, src);				
				memcpy(tempchar, inet_ntoa(tclientadr.sin_addr), 128);
				memcpy(destchar, inet_ntoa(VKTCPServer.ClientAddr[i].sin_addr), 128);
				//printf("客户端已连接 [%s,%d]\n", inet_ntoa(TCPIP_ClientAddr.sin_addr), TCPIP_ClientAddr.sin_port);
				//if (stricmp(inet_ntoa(tclientadr.sin_addr), inet_ntoa(VKTCPServer.ClientAddr[i].sin_addr)) == 0)
				if (stricmp(tempchar, destchar) == 0)
				{
					//VKTCPServer.ClientHandle[i] = handle;
					VKTCPServer.ClientAddr[i] = tclientadr;
					VKTCPServer.SockClient[i] = tclientsock;
					if (VKTCPServer.ClientStatus[i] == 0)
					{
						VKTCPServer.ClientStatus[i] = 1;
						VKTCPServer.Client_Num++;
					}
					//VKTCPServer.ClientAddr[i] = tclientadr;
					//GetTCPPeerAddr (handle, VKTCPServer.ClientIP[i], 128);
					//memcpy(VKTCPServer.ClientIP[i], tcpaddress, 128);
					isexistconenctedflag = 1;
					//debug_infor_status = 999;					
					break;
				}
			}
			//-----------------------------
			if (isexistconenctedflag == 0)
			{
				//debug_infor_status = 1000;
				if (VKTCPServer.Client_Num >= MAX_TCP_CILENT_NUM)VKTCPServer.Client_Num = MAX_TCP_CILENT_NUM;
				//--------------------------------
				for (i = 0; i < MAX_TCP_CILENT_NUM; i++)
				{
					//debug_infor_status++;
					memset(destchar, 0, sizeof(destchar));
					memcpy(destchar, inet_ntoa(VKTCPServer.ClientAddr[i].sin_addr), 128);
					if ((VKTCPServer.ClientStatus[i] == 0) && (stricmp(destchar, "0.0.0.0") == 0))
					{
						//VKTCPServer.ClientHandle[i] = handle;
						VKTCPServer.ClientStatus[i] = 1;
						VKTCPServer.ClientAddr[i] = tclientadr;
						VKTCPServer.SockClient[i] = tclientsock;
						//SOCKET SockClient[MAX_TCP_CILENT_NUM + 1];
						//SOCKADDR_IN ClientAddr[MAX_TCP_CILENT_NUM + 1];
						//GetTCPPeerAddr (handle, VKTCPServer.ClientIP[i], 128);
						//memcpy(VKTCPServer.ClientIP[i], tcpaddress, 128);
						VKTCPServer.Client_Num++;
						break;
					}
				}
			}
			//-------------------------------------------
			//char buffer[250];
			//GetTCPPeerAddr (VKTCPServer.ClientHandle[VKTCPServer.Client_Num], tcpaddress, 250);  	//以下代码为获得客户机信息
			//sprintf(buffer,"当前连接数：%d",VKTCPServer.Client_Num);
			//////////////////////////////////////////////////////////////
		}
	}
	//---------------------------------------
	for (i = 0; i < MAX_TCP_CILENT_NUM; i++)
	{
		if (VKTCPServer.ClientStatus[i]>0)
		{
			closesocket(VKTCPServer.SockClient[i]);
			VKTCPServer.ClientStatus[i] = 0;
		}
	}
	closesocket(VKTCPServer.SockServer);
	//----------------------------------------
	//memset(&VKTCPServer.ClientStatus, 0, sizeof(VKTCPServer.ClientStatus));
	//memset(&VKTCPServer.ClientAddr, 0, sizeof(VKTCPServer.ClientAddr));
	//memset(&VKTCPServer.SockClient, 0, sizeof(VKTCPServer.SockClient));
	//----------------------------------------
	//debug_infor_status = 0;
	return 0;
}

//////////////////////////////////////////////////////
// TCP server intialize functions
// input:
//     int TCP server port number, be fixed 8234
// Output:
//     int error: 0=ok, normal
//                -1=WSAStartup() called failed!\n
//                -2=若不是所请求的版本号2.2，则终止WinSock库的使用
//                -3=printf("socket() called failed! ,error code is: %d", WSAGetLastError());
//                -4=printf("bind() called failed! The error code is: %d\n", WSAGetLastError());
//                -5=printf("listen() called failed! The error code is: %d\n", WSAGetLastError());
/////////////////////////////////////////////////////
int TCPServer_Intialize(int LocalPortNo)
{
	//加载套接字库  
//	WORD wVersionRequested;//用于保存WinSock库的版本号
//	WSADATA wsaData;
	int err = 0;
/*
	//InitDLL();
	//printf("This is a Server side application!\n");

	wVersionRequested = MAKEWORD(2, 2);

	err = WSAStartup(wVersionRequested, &wsaData);
	if (err != 0)
	{
		//printf("WSAStartup() called failed!\n");
		return -1;
	}
	//else
	//{
	//	printf("WSAStartup() called successful!\n");
	//}

	if (LOBYTE(wsaData.wVersion) != 2 ||
		HIBYTE(wsaData.wVersion) != 2)
	{
		//若不是所请求的版本号2.2，则终止WinSock库的使用  
		WSACleanup();
		return -2;
	}
*/
	//创建用于监听的套接字  
	VKTCPServer.SockServer = socket(AF_INET, SOCK_STREAM, 0);
	if (VKTCPServer.SockServer == INVALID_SOCKET)
	{
		//printf("socket() called failed! ,error code is: %d", WSAGetLastError());
		return -3;
	}
	//else
	//{
	//	printf("socket() called successful!\n");
	//}
	//在linux终止一个程序之后不回立即释放端口，因端口上有处于TIME_WAIT的连接。需要等到一定的时间才能自动释放，
	//如果有重启服务的要求，服务是无法启动的。解决办法就是端口复用，配置socket端口为SO_REUSEADDR模式。用以下代码：
	//在创建socket 之后执行这段代码即可。
	int opt = 1;
	setsockopt(VKTCPServer.SockServer, SOL_SOCKET, SO_REUSEADDR, (const void *)&opt, sizeof(opt));
	// 设置为非阻塞模式
	//-------------------------------------------------
	ULONG NonBlock = 1;
	if (ioctlsocket(VKTCPServer.SockServer, FIONBIO, &NonBlock) == SOCKET_ERROR)
	{
		//	//printf("ioctlsocket() failed with error %d\n", WSAGetLastError());
		closesocket(VKTCPServer.SockServer);
		return -1;
	}
	int nNetTimeout = 1000;//1秒
	//发送时限
	setsockopt(VKTCPServer.SockServer, SOL_SOCKET, SO_SNDTIMEO, (char *)&nNetTimeout, sizeof(int));
	//接收时限
	setsockopt(VKTCPServer.SockServer, SOL_SOCKET, SO_RCVTIMEO, (char *)&nNetTimeout, sizeof(int));

	// 接收缓冲区
	//int nRecvBuf = 32 * 1024;//设置为32K
	//setsockopt(VKTCPServer.SockServer, SOL_SOCKET, SO_RCVBUF, (const char*)&nRecvBuf, sizeof(int));
	//发送缓冲区
	//int nSendBuf = 32 * 1024;//设置为32K
	//setsockopt(VKTCPServer.SockServer, SOL_SOCKET, SO_SNDBUF, (const char*)&nSendBuf, sizeof(int));
	//------------------------------------------------
	//static SOCKADDR_IN TCPIP_LocalAddr;
	//static SOCKADDR_IN TCPIP_ClientAddr;
	//填充服务器端套接字结构  
	//SOCKADDR_IN addrServer;
	VKTCPServer.LocalAddr.sin_addr.s_addr = htonl(INADDR_ANY);//将主机字节顺序转换成TCP/IP网络字节顺序  
	VKTCPServer.LocalAddr.sin_family = AF_INET;
	VKTCPServer.LocalAddr.sin_port = htons(LocalPortNo);//htons(SERVERPORT);

	//将套接字绑定到一个本地地址和端口上  
	err = bind(VKTCPServer.SockServer, (SOCKADDR*)&VKTCPServer.LocalAddr, sizeof(SOCKADDR));
	if (err == SOCKET_ERROR)
	{
		//printf("bind() called failed! The error code is: %d\n", WSAGetLastError());
		closesocket(VKTCPServer.SockServer);
		return -4;
	}
	//else
	//{
	//	printf("bind() called successful\n");
	//}
	////////////////////////////////////////////
	//printf("TCP Server Address is [%s]\n", inet_ntoa(TCPIP_LocalAddr.sin_addr));
	//printf("TCP Server Port is [%d]\n", SERVERPORT);
	/////////////////////////////////////////////
	//将套接字设置为监听模式，准备接收客户请求  
	err = listen(VKTCPServer.SockServer, 8);
	if (err == SOCKET_ERROR)
	{
		//printf("listen() called failed! The error code is: %d\n", WSAGetLastError());
		closesocket(VKTCPServer.SockServer);
		return -5;
	}
	//else
	//{
	//	printf("listen() called successful!\n");
	//}
	//debug_infor_status = 5;
	return 0;
}
//////////////////////////////////////////////////////////////////////////////////////////////////////////////
int Def_Function_OUTfmt Server_TCPOpen(int portnumber)
{
	int status;
	unsigned int i, j = 0;
	InitDLL(); // 濡傛灉鍑芥暟绗竴鍒濆鍖栵紝鍑嗗寮€鍚嚎绋?
	//==============================
	timeBeginPeriod(1); //  设置高精度定时器，1ms
	//====================================================
	if (TCPMonitor_ThreadRunningState > 0)  // 已打开
	{
		if (VKTCPServer.PortNumber == portnumber)return 1; //服务器已经打开， 未连接客户端  
		else if (VKTCPServer.Client_Num>0)return 2;// 服务器已有连接的客服端
		else   // 不同的IP 端口， 
		{
			//若TCP连接句柄存在，则断开 
			//TCPMonitor_ThreadRunningState = 0;
			//RXLANMonitor_ThreadRunningState = 0;
			//-------------------------------
			if (RXLANMonitor_ThreadRunningState>0)
			{
				RXLANMonitor_ThreadRunningState = 0;  // 退出线程
				for (j = 0; j < MAX_TCP_CILENT_NUM; j++)
				{
					VK[j].SaveShowPI = 0;
					VK[j].ReadShowPI = 0;
					VK[j].Read4CHPI = 0;
					for (i = 0; i < 8; i++)VK[j].ReadCHPI[i] = 0;
				}
			} //
			//注销TCP服务器
			closesocket(VKTCPServer.SockServer);
			//  UnregisterTCPServer (VKTCPServer.PortNumber); ////////// 先注销tCP 服务器后再重
			TCPMonitor_ThreadRunningState = 0;// 打开状态服务器   
			Sleep(10);
		}
	}
	//----------------------------------------------------
	//Select_conversation_NO=0;  //  被选择的客户机序号 
	//Count_conversation_NO=0;  //  连接的客户机数量
	for (i = 0; i < MAX_TCP_CILENT_NUM; i++)
	{
		if (VKTCPServer.ClientStatus[i]>0)closesocket(VKTCPServer.SockClient[i]);//DisconnectTCPClient(VKTCPServer.ClientHandle[i]);
		//VKTCPServer.ClientHandle[i] = 0;
		VKTCPServer.ClientStatus[i] = 0;
		//memset(VKTCPServer.ClientIP[i], 0, 128);
	}
	//Select_conversation_NO=0;  //  被选择的客户机序号 
	VKTCPServer.PortNumber = portnumber;
	VKTCPServer.RecievedBytes_Count = 0;
	VKTCPServer.Client_Num = 0;
	//-----------------------------------
	//ThreadRunningState=1;// 打开状态服务器 
	//TCPMonitor_Handle = CreateThread(NULL, 0, TCPRecieveThreadEvent, NULL, 0, NULL);
	////SetThreadPriority(RXLANMonitor_Handle,THREAD_PRIORITY_TIME_CRITICAL); //20200528 hide thread // 
	//return 0;
	//TCPMonitor_ThreadRunningState = 1;// 打开状态服务器 	  
	// status = RegisterTCPServer (portnumber, TCPServerCB, 0);   //注册TCP服务器 
	status = TCPServer_Intialize(VKTCPServer.PortNumber);
	Sleep(500);
	if (status == 0)
	{
		Sleep(500);
		TCPMonitor_Handle = CreateThread(NULL, 0, TCPRecieveThreadEvent, NULL, 0, NULL);
		//SetThreadPriority(TCPMonitor_Handle, THREAD_PRIORITY_TIME_CRITICAL); //20200528 hide thread //

		RXLANMonitor_Handle = CreateThread(NULL, 0, MonitorRXLANEvent, NULL, 0, NULL); //20200528 hide thread // 
		//SetThreadPriority(RXLANMonitor_Handle,THREAD_PRIORITY_TIME_CRITICAL); //20200528 hide thread //
		return 0;
	}

	//if (ThreadRunningState < 2) // 閲嶆柊鎵撳紑鎺ユ敹绾跨▼   //20200528 hide thread //
	//{								//20200528 hide thread //
	//	ThreadRunningState = 2;   //20200528 hide thread //
	///	RXLANMonitor_Handle = CreateThread(NULL, 0, MonitorRXLANEvent, NULL, 0, NULL); //20200528 hide thread // 
	//	//SetThreadPriority(RXLANMonitor_Handle,THREAD_PRIORITY_TIME_CRITICAL); //20200528 hide thread //
	//}		//20200528 hide thread //

	TCPMonitor_ThreadRunningState = 0;// 服务器打开异常 	
	return -13;
	//-------------------------------
	//注销TCP服务器		
	//status = RegisterTCPServer (portnumber, TCPServerCB, 0);  // 重新尝试打开服务器
	//if (status == 0)return 0;
	//-------------------------------
	//{
	//  SetCtrlAttribute (panelHandle, PANEL_CMD_CONNECT, ATTR_DIMMED, 1);
	//  SetCtrlAttribute (panelHandle, PANEL_CMD_DISCONNECT, ATTR_DIMMED, 0);
	//		    // sprintf (linestr, "系统文件丢失！vk701nconfig.ini = %d", tfilesize);    
	//}
	//else MessagePopup("警告！","服务器端口已被占用！"); 
}

//----------------------------------------------

int Def_Function_OUTfmt Server_TCPClose(int portnumber)
{
	unsigned int i, j = 0;
	if (TCPMonitor_ThreadRunningState == 0)  // 服务器未打开
		return -11;
	if ((VKTCPServer.PortNumber != portnumber) && (portnumber != 0)) // 服务器端口不存在
		return -12;
	//-------------------------------
	timeEndPeriod(1);/// 还原高精度定时器
	//-------------------------------
	VKTCPServer.RecievedBytes_Count = 0;
	if (RXLANMonitor_ThreadRunningState>0)
	{
		RXLANMonitor_ThreadRunningState = 0;  // 退出线程
		for (j = 0; j < MAX_TCP_CILENT_NUM; j++)
		{
			VK[j].SaveShowPI = 0;
			VK[j].ReadShowPI = 0;
			VK[j].Read4CHPI = 0;
			for (i = 0; i < 8; i++)VK[j].ReadCHPI[i] = 0;
		}
	} //ThreadRunningState
	//--------------------------------
	//若TCP连接句柄存在，则断开  
	for (i = 0; i < MAX_TCP_CILENT_NUM; i++)
	{
		//if (VKTCPServer.ClientHandle[i]>0)DisconnectTCPClient (VKTCPServer.ClientHandle[i]);
		if (VKTCPServer.ClientStatus[i]>0)closesocket(VKTCPServer.SockClient[i]);//DisconnectTCPClient(VKTCPServer.ClientHandle[i]);
		//VKTCPServer.ClientHandle[i] = 0;
		VKTCPServer.ClientStatus[i] = 0;
		//memset(VKTCPServer.ClientIP[i], 0, 128);
	}
	VKTCPServer.Client_Num = 0;  //  连接的客户机数量 
	//------------------------------
	TCPMonitor_ThreadRunningState = 0;// 打开状态服务器  
	//	UnregisterTCPServer (VKTCPServer.PortNumber);  //注销TCP服务器 
	//closesocket(VKTCPServer.SockServer);
	seNet_Load_DefaultTCPIPConfigurationFile();// 复位TCP/IP地址文件。清除已连接的缓存中IP
	return 0;
}


int Def_Function_OUTfmt Server_DisconnectedClient(int mci)
{
	if (TCPMonitor_ThreadRunningState == 0)  // 服务器未打开
		return -11;
	if (VKTCPServer.ClientStatus[mci] > 0)
	{
		closesocket(VKTCPServer.SockClient[mci]);
		VKTCPServer.ClientStatus[mci] = 0;
		VKTCPServer.ClientAddr[mci].sin_addr.s_addr = inet_addr("0.0.0.0");
		if (VKTCPServer.Client_Num > 0)VKTCPServer.Client_Num--;
		return 0;
	}
	return -1;
}
////////////////////////////////////////////////////////////


int  Def_Function_OUTfmt Server_Get_ServerPort(int *iport)
{
	if (TCPMonitor_ThreadRunningState == 0)return -11;
	//if (ThreadRunningState==1)return -2; 
	*iport = VKTCPServer.PortNumber;
	return 0;
}


//==========================================
int Def_Function_OUTfmt Server_Get_ConnectedClientNumbers(int *clientnum)
{
	if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开  
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; 	 //未连接客户端    
	//if(mci >= Count_conversation_NO)return -13;   // 请求非法客户端 
	*clientnum = VKTCPServer.Client_Num;
	return 0;//Count_conversation_NO;
}
//==========================================


int Def_Function_OUTfmt  Server_Get_ConnectedClientHandle(int mci, int *iihanlde, char *ipadr)
{
	char *bufpi;//tempch[0];
	bufpi = (char *)malloc(sizeof (char)* (128));  // 50000
	memset(bufpi, '\0', 128);
	//------------------------------
	if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开  
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端 
	//------------------------
	//printf("客户端已连接 [%s,%d]\n", inet_ntoa(TCPIP_ClientAddr.sin_addr), TCPIP_ClientAddr.sin_port);   //打印接收到的数据 
	*iihanlde = VKTCPServer.ClientAddr[mci].sin_port;
	memcpy(bufpi, inet_ntoa(VKTCPServer.ClientAddr[mci].sin_addr), 128);
	//if (stricmp(inet_ntoa(tclientadr.sin_addr), inet_ntoa(VKTCPServer.ClientAddr[i].sin_addr)) == 0)
	memcpy(ipadr, bufpi, 128);
	//ipadr = VKTCPServer.ClientIP[mci][0];
	//////////////////////////
	//GetTCPPeerAddr (conversationHandle[mci], ipadr, 250);
	//=======================
	free(bufpi);
	return 0;
}

//memset(&serv, 0, sizeof(serv));
//serv.sin_family = AF_INET;
//serv.sin_port = htons(80);
//serv.sin_addr.S_un.S_addr = inet_addr("115.239.210.26");
//========================================================


int Def_Function_OUTfmt Server_Get_RxTotoalBytes(int *totalbytesnum, int clrflag)
{
	*totalbytesnum = VKTCPServer.RecievedBytes_Count;
	if (clrflag > 0) VKTCPServer.RecievedBytes_Count = 0;
	return 0;
}


int Def_Function_OUTfmt Server_Bind_ConnectedClientIP(int tflag)
{
	FILE *tfilehandle;
	int i = 0;
	char tempstr[128];
	//---------------------------------------
	char *ptr;
	char tempapppath[MAX_PATHNAME_LEN];
	ptr = (char *)getcwd(tempapppath, MAX_PATHNAME_LEN);
	if (ptr == NULL)
	{
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
		printf("获取路径失败！\n");
#endif
		return -1;
	}
	if (chdir(tempapppath) < 0)
	{
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
		printf("切换路径失败！\n");
#endif
		return -1;
	}
	if (tflag == 0)
	{
		tfilehandle = fopen("vk70xmcdllconfig.ini", "wb");// in
		//memset(pstr, '\0', sizeof(pstr));// 
		memset(tempstr, '\0', sizeof(tempstr));//
		//------------------------------------
		sprintf(tempstr, "[VK70xN Server Configuration]\n");
		fwrite(tempstr, 1, strlen(tempstr), tfilehandle);//
		//-------------------------------------
		memset(tempstr, '\0', sizeof(tempstr));//
		sprintf(tempstr, "Server Port=8234\n");
		fwrite(tempstr, 1, strlen(tempstr), tfilehandle);//
		//------------------------------------
		for (i = 0; i < MAX_TCP_CILENT_NUM; i++)
		{
			sprintf(tempstr, "DAQ-%d=\"0.0.0.0\"\n", (i + 1));
			//strcat(pstr, tempstr);
			//strcat(pstr, "\\VK701NADCFile");//
			fwrite(tempstr, 1, strlen(tempstr), tfilehandle);// 
			//printf(tempstr);
		}
		//memset(&tvkinfor, 0, sizeof(TypeDefTCPServerPara));
		//fwrite(&tvkinfor, sizeof(TypeDefTCPServerPara), 1, tfilehandle);// 
		fclose(tfilehandle);
	}
	else
	{
		tfilehandle = fopen("vk70xmcdllconfig.ini", "wb");// in
		//memset(pstr, '\0', sizeof(pstr));// 
		memset(tempstr, '\0', sizeof(tempstr));//
		sprintf(tempstr, "[VK70xN Server Configuration]\n");
		fwrite(tempstr, 1, strlen(tempstr), tfilehandle);//
		//-------------------------------------
		memset(tempstr, '\0', sizeof(tempstr));//
		sprintf(tempstr, "Server Port=%d\n", VKTCPServer.PortNumber);
		fwrite(tempstr, 1, strlen(tempstr), tfilehandle);//
		//------------------------------------
		for (i = 0; i < MAX_TCP_CILENT_NUM; i++)
		{
			sprintf(tempstr, "DAQ-%d=\"%s\"\n", (i + 1), inet_ntoa(VKTCPServer.ClientAddr[i].sin_addr));
			//strcat(pstr, tempstr);
			//strcat(pstr, "\\VK701NADCFile");//
			fwrite(tempstr, 1, strlen(tempstr), tfilehandle);// 
			//printf(tempstr);
		}
		sprintf(tempstr, "DAQ-%d=\"0.0.0.0\"\n", (i + 1));
		fwrite(tempstr, 1, strlen(tempstr), tfilehandle);// 
		//memset(&tvkinfor, 0, sizeof(TypeDefTCPServerPara));
		//fwrite(&tvkinfor, sizeof(TypeDefTCPServerPara), 1, tfilehandle);// 
		fclose(tfilehandle);
	}
	return 0;
}

int Def_Function_OUTfmt Server_debug_infor(int *backpara, int len)
{
	if (len < 1)return 0;
	*backpara++ = TCPMonitor_ThreadRunningState;
	if (len < 2)return 1;
	*backpara++ = (int)VKTCPServer.SockServer;
	if (len < 3)return 2;
	*backpara++ = (int)VKTCPServer.LocalAddr.sin_port;
	if (len < 4)return 3;
	*backpara++ = (int)VKTCPServer.SockClient[0];
	if (len < 5)return 4;
	*backpara++ = VKTCPServer.ClientStatus[0];
	if (len < 6)return 5;
	*backpara++ = (int)VKTCPServer.SockClient[0];
	if (len < 7)return 6;
	return len;
}
