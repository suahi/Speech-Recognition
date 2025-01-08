#if _MSC_VER > 1000
#pragma once
#endif 

#include "VK70xNMC_DAQ2.h"
#include "dvr_header.h"
#include <Windows.h>
#include <stdio.h>

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
// adc sampling function
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

//char StarSample[9]={0x55,0XEE,0X00,0X05,0X10,0X01,0X24,0X10,0X8D}; 
int Def_Function_OUTfmt  VK70xNMC_StartSampling(int mci)
{
	unsigned char txbuf[2];
	int  tstatus, i = 0;
	if (TCPMonitor_ThreadRunningState == 0)   // 未打开服务器
	{
		InitDLL(); // 濡傛灉鍑芥暟绗竴鍒濆鍖栵紝鍑嗗寮€鍚嚎绋?
		Server_TCPOpen(8234);//打开默认的服务器
		Sleep(10);
		return -11;
	}
	//if (ThreadRunningState==1)return -2;
	//if (ThreadRunningState==0)return -11;  //服务未打开  
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端 
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -13;
	//-----------------------------------
	VK[mci].SaveShowPI = 0;
	VK[mci].ReadShowPI = 0;
	VK[mci].Read4CHPI = 0;
	for (i = 0; i < 8; i++)VK[mci].ReadCHPI[i] = 0;
	//------------------------------------
	if (RXLANMonitor_ThreadRunningState == 0) // 閲嶆柊鎵撳紑鎺ユ敹绾跨▼   //20200528 hide thread //
	{								//20200528 hide thread //
		RXLANMonitor_ThreadRunningState = 2;   //20200528 hide thread //
		RXLANMonitor_Handle = CreateThread(NULL, 0, MonitorRXLANEvent, NULL, 0, NULL); //20200528 hide thread // 
		//SetThreadPriority(RXLANMonitor_Handle,THREAD_PRIORITY_TIME_CRITICAL); //20200528 hide thread //
	}		//20200528 hide thread //
	//------------------------------------
	txbuf[0] = 0x10;
	txbuf[1] = 0;
	tstatus = DisposalTXDatum(VKTCPServer.SockClient[mci], 0x24, txbuf, 1, 0);
	return  tstatus;
}


int Def_Function_OUTfmt VK70xNMC_StartSampling_NPoints(int mci, int Npointsnums)
{
	unsigned char txbuf[6];
	unsigned int  tmpNp = 0;
	int  tstatus, i = 0;
	if (TCPMonitor_ThreadRunningState == 0)   // 未打开服务器
	{
		InitDLL(); // 濡傛灉鍑芥暟绗竴鍒濆鍖栵紝鍑嗗寮€鍚嚎绋?
		Server_TCPOpen(8234);//打开默认的服务器
		Sleep(10);
		return -11;
	}
	//if (ThreadRunningState==1)return -2;
	//if (ThreadRunningState==0)return -11;  //服务未打开  
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端 
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -13;
	//-----------------------------------
	VK[mci].SaveShowPI = 0;
	VK[mci].ReadShowPI = 0;
	VK[mci].Read4CHPI = 0;
	for (i = 0; i < 8; i++)VK[mci].ReadCHPI[i] = 0;
	//------------------------------------
	if (RXLANMonitor_ThreadRunningState == 0) // 閲嶆柊鎵撳紑鎺ユ敹绾跨▼   //20200528 hide thread //
	{								//20200528 hide thread //
		RXLANMonitor_ThreadRunningState = 2;   //20200528 hide thread //
		RXLANMonitor_Handle = CreateThread(NULL, 0, MonitorRXLANEvent, NULL, 0, NULL); //20200528 hide thread // 
		//SetThreadPriority(RXLANMonitor_Handle,THREAD_PRIORITY_TIME_CRITICAL); //20200528 hide thread //
	}		//20200528 hide thread //
	//------------------------------------
	tmpNp = (unsigned int)Npointsnums;
	txbuf[0] = 0x33;
	txbuf[1] = (unsigned char)(tmpNp / 0x1000000);
	txbuf[2] = (unsigned char)(tmpNp / 0x10000);
	txbuf[3] = (unsigned char)(tmpNp / 0x100);
	txbuf[4] = (unsigned char)(tmpNp);
	txbuf[5] = 0;
	tstatus = DisposalTXDatum(VKTCPServer.SockClient[mci], 0x24, txbuf, 5, 1);
	return  tstatus;
}



//char StopSample[13]={0x55,0XEE,0X80,0X09,0X10,0X01,0X24,0X33,0X00,0X00,0X00,0X01,0x35}; 
int Def_Function_OUTfmt  VK70xNMC_StopSampling(int mci)
{
	unsigned char txbuf[6];
	int  tstatus = 0;
	int i = 0;
	//InitDLL(); // 濡傛灉鍑芥暟绗竴鍒濆鍖栵紝鍑嗗寮€鍚嚎绋?
	//=====================================
	//if (ThreadRunningState==0)return -11;  //服务未打开  
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端 
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -13;
	//if (ThreadRunningState==0)return -11;   // 未打开服务器
	//if ((ThreadRunningState==1)||(Count_conversation_NO == 0))return -12;   // 未监测已连接的客户端 
	//if(mci >= Count_conversation_NO)return -13;   // 请求非法客户端
	//------------------------------------
	txbuf[0] = 0x33;
	txbuf[1] = 0;
	txbuf[2] = 0;
	txbuf[3] = 0;
	txbuf[4] = 0x1;
	txbuf[5] = 0;
	tstatus = DisposalTXDatum(VKTCPServer.SockClient[mci], 0x24, txbuf, 5, 1);
	//--------------------------
	//IntializeVKinging_RXTaskBuffer();
	//////////////////////////////////////////////
	//ThreadRunningState = 1;   //
	//-------------------------------------------
	VK[mci].SaveShowPI = 0;
	VK[mci].ReadShowPI = 0;
	VK[mci].Read4CHPI = 0;
	for (i = 0; i < 8; i++)VK[mci].ReadCHPI[i] = 0;
	return  tstatus;
}

int Def_Function_OUTfmt VK70xNMC_Initialize(int mci, double refvol, int bitmode, int sr, int volrg15, int volrg26, int volrg37, int volrg48)
{
	int i = 0;
	unsigned char vkmode = 0;
	unsigned char tempbitmode = 1;
	int tempsr;
	InitDLL(); // 濡傛灉鍑芥暟绗竴鍒濆鍖栵紝鍑嗗寮€鍚嚎绋?
	//20200528 hide thread //if (ThreadRunningState > 0)
	//20200528 hide thread //{
	//20200528 hide thread //   ThreadRunningState=0;
	//20200528 hide thread //	 Sleep(2); // 寤舵椂1ms锛岀瓑寰呯嚎绋嬮€€鍑?
	//20200528 hide thread //}  
	//--------------------
	if (TCPMonitor_ThreadRunningState == 0)   // 未打开服务器
	{
		i = Server_TCPOpen(8234);//打开默认的服务器
		if (i<0)return i;
		Sleep(100);
	}
	//if (ThreadRunningState==1)return -2;
	//if (ThreadRunningState==0)return -11;  //服务未打开  
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -13;
	//--------------------
	VK70xNMC_StopSampling(mci);
	//-------------------- 
	VK[mci].SaveShowPI = 0;
	VK[mci].ReadShowPI = 0;
	VK[mci].Read4CHPI = 0;
	for (i = 0; i < 8; i++)VK[mci].ReadCHPI[i] = 0;
	//-------------------- 
	if ((refvol == 4.000) || (refvol == 1))
	{
		VK[mci].ReferenceVoltage = 4.000;//VK701N with PGA, VK701NSD
		vkmode = 1;
	}
	else
	{
		VK[mci].ReferenceVoltage = 2.442;//VK701S,VK702N with no pGA
		vkmode = 0;
	}
	//ReferenceVoltage = 4.000;
	//--------------------
	if (VK[mci].ReferenceVoltage == 2.442)
	{
		VK[mci].PGAGainRange[0] = GetGainValue_NOPGA(volrg15);
		VK[mci].PGAGainRange[1] = GetGainValue_NOPGA(volrg26);
		VK[mci].PGAGainRange[2] = GetGainValue_NOPGA(volrg37);
		VK[mci].PGAGainRange[3] = GetGainValue_NOPGA(volrg48);
		VK[mci].PGAGainRange[4] = VK[mci].PGAGainRange[0];
		VK[mci].PGAGainRange[5] = VK[mci].PGAGainRange[1];
		VK[mci].PGAGainRange[6] = VK[mci].PGAGainRange[2];
		VK[mci].PGAGainRange[7] = VK[mci].PGAGainRange[3];
	}
	else
	{
		VK[mci].PGAGainRange[0] = GetGainValue_PGA(volrg15);
		VK[mci].PGAGainRange[1] = GetGainValue_PGA(volrg26);
		VK[mci].PGAGainRange[2] = GetGainValue_PGA(volrg37);
		VK[mci].PGAGainRange[3] = GetGainValue_PGA(volrg48);
		VK[mci].PGAGainRange[4] = VK[mci].PGAGainRange[0];
		VK[mci].PGAGainRange[5] = VK[mci].PGAGainRange[1];
		VK[mci].PGAGainRange[6] = VK[mci].PGAGainRange[2];
		VK[mci].PGAGainRange[7] = VK[mci].PGAGainRange[3];
	}
	//---------------------------
	//for(j = 0; j < _DISP_MAX_LEN;j++)RXLANDatum[j]=0;
	VK[mci].RXLANSavePI = 0;
	VK[mci].RXLANReadPI = 0;
	//-------------------------
	//char SetVinRangeValue[18]={0x55,0xEE,0x80,0x0E,0x10,0x01,0x81,
	//0x00,0x00,0x00,0x00,
	//0x00,
	//0x01,
	///0x00,0x03,0xE8,
	//0x00,0x4F};
	unsigned char txbuf[10];

	txbuf[0] = (unsigned char)(volrg15);// (char)SysInfor.CH_CS[0];	//设置通道1的输入范围   
	txbuf[1] = (unsigned char)(volrg26);   	//设置通道2的输入范围  
	txbuf[2] = (unsigned char)(volrg37);   	//设置通道3的输入范围   
	txbuf[3] = (unsigned char)(volrg48);   	//设置通道4的输入范围   
	txbuf[4] = vkmode; 
	//--------------------------------
	if ((bitmode == 2) || (bitmode == 3) || (bitmode == 24) || (bitmode == 32))tempbitmode = 2;
	else tempbitmode = 1;
	
	tempsr = sr;
	if (tempsr > 102400)tempsr = 102400;
	//------------------
	if (tempsr > 51200)
	{
		if (tempbitmode == 2) tempbitmode = 1;
	}	
	//--------------------

	//if (tempbitmode == 2)
	//{
	//	if (tempsr > 50000)tempsr = 50000;
	//}
	//else
	//{
	//	if (tempsr > 100000)tempsr = 100000;
	//}
	txbuf[5] = tempbitmode;  	//设置传输的数据格式8/16/24/32位    
	txbuf[6] = (unsigned char)(tempsr / 0x10000);	   //把KPS采样率分解为三个数据写入相应数组   
	txbuf[7] = (unsigned char)(tempsr / 0x100);
	txbuf[8] = (unsigned char)(tempsr);
	txbuf[9] = 0; // 发送 所有的 通道
	//---------------------------------
	VK[mci].Npoints;
	//---------------------------------
	i = DisposalTXDatum(VKTCPServer.SockClient[mci], 0x81, txbuf, 10, 1);
	//--------------------------
	if (RXLANMonitor_ThreadRunningState == 0) // 閲嶆柊鎵撳紑鎺ユ敹绾跨▼	 //20200528 hide thread //
	{				  //20200528 hide thread //
		RXLANMonitor_ThreadRunningState = 2;	   //20200528 hide thread //
		RXLANMonitor_Handle = CreateThread(NULL, 0, MonitorRXLANEvent, NULL, 0, NULL);	  //20200528 hide thread //
		//SetThreadPriority(RXLANMonitor_Handle,THREAD_PRIORITY_TIME_CRITICAL);   //20200528 hide thread //
	}
	return i;
}


int Def_Function_OUTfmt VK70xNMC_Initialize_2(int mci, double refvol, int bitmode, int sr, int npoints, int tinterval, int *volrg)
{
	int i = 0;
	unsigned char txbuf[32];
	unsigned char vkmode = 0;
	unsigned char tempbitmode = 1;
	int tempsr;
	InitDLL(); // 濡傛灉鍑芥暟绗竴鍒濆鍖栵紝鍑嗗寮€鍚嚎绋?
	//20200528 hide thread //if (ThreadRunningState > 0)
	//20200528 hide thread //{
	//20200528 hide thread //   ThreadRunningState=0;
	//20200528 hide thread //	 Sleep(2); // 寤舵椂1ms锛岀瓑寰呯嚎绋嬮€€鍑?
	//20200528 hide thread //}  
	//--------------------
	if (TCPMonitor_ThreadRunningState == 0)   // 未打开服务器
	{
		i = Server_TCPOpen(8234);//打开默认的服务器
		if (i<0)return i;
		Sleep(100);
	}
	//if (ThreadRunningState==1)return -2;
	//if (ThreadRunningState==0)return -11;  //服务未打开  
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -13;
	//--------------------
	VK70xNMC_StopSampling(mci);
	//-------------------- 
	VK[mci].SaveShowPI = 0;
	VK[mci].ReadShowPI = 0;
	VK[mci].Read4CHPI = 0;
	for (i = 0; i < 8; i++)VK[mci].ReadCHPI[i] = 0;
	//-------------------- 
	if ((refvol == 4.000) || (refvol == 1))
	{
		VK[mci].ReferenceVoltage = 4.000;//VK701N with PGA, VK701NSD
		vkmode = 1;
	}
	else
	{
		VK[mci].ReferenceVoltage = 2.442;//VK701S,VK702N with no pGA
		vkmode = 0;
	}
	//ReferenceVoltage = 4.000;
	//--------------------
	if (VK[mci].ReferenceVoltage == 2.442)
	{
		VK[mci].PGAGainRange[0] = GetGainValue_NOPGA(*volrg);
		VK[mci].PGAGainRange[1] = GetGainValue_NOPGA(*(volrg + 1));
		VK[mci].PGAGainRange[2] = GetGainValue_NOPGA(*(volrg + 2));
		VK[mci].PGAGainRange[3] = GetGainValue_NOPGA(*(volrg + 3));
		VK[mci].PGAGainRange[4] = VK[mci].PGAGainRange[0];
		VK[mci].PGAGainRange[5] = VK[mci].PGAGainRange[1];
		VK[mci].PGAGainRange[6] = VK[mci].PGAGainRange[2];
		VK[mci].PGAGainRange[7] = VK[mci].PGAGainRange[3];
	}
	else
	{
		VK[mci].PGAGainRange[0] = GetGainValue_PGA(*volrg);
		VK[mci].PGAGainRange[1] = GetGainValue_PGA(*(volrg + 1));
		VK[mci].PGAGainRange[2] = GetGainValue_PGA(*(volrg + 2));
		VK[mci].PGAGainRange[3] = GetGainValue_PGA(*(volrg + 3));
		VK[mci].PGAGainRange[4] = VK[mci].PGAGainRange[0];
		VK[mci].PGAGainRange[5] = VK[mci].PGAGainRange[1];
		VK[mci].PGAGainRange[6] = VK[mci].PGAGainRange[2];
		VK[mci].PGAGainRange[7] = VK[mci].PGAGainRange[3];
	}
	//---------------------------
	//for(j = 0; j < _DISP_MAX_LEN;j++)RXLANDatum[j]=0;
	VK[mci].RXLANSavePI = 0;
	VK[mci].RXLANReadPI = 0;
	//-------------------------
	//char SetVinRangeValue[18]={0x55,0xEE,0x80,0x0E,0x10,0x01,0x81,
	//0x00,0x00,0x00,0x00,
	//0x00,
	//0x01,
	///0x00,0x03,0xE8,
	//0x00,0x4F};	
	for (i = 0; i < 32; i++)txbuf[i] = 0;
	txbuf[0] = (unsigned char)(*(volrg + 0));// (char)SysInfor.CH_CS[0];	//设置通道1的输入范围   
	txbuf[1] = (unsigned char)(*(volrg + 1));   	//设置通道2的输入范围  
	txbuf[2] = (unsigned char)(*(volrg + 2));   	//设置通道3的输入范围   
	txbuf[3] = (unsigned char)(*(volrg + 3));   	//设置通道4的输入范围    
	txbuf[4] = vkmode;

	//if (VK[mci].ReferenceVoltage == 2.442)

	if ((bitmode == 2) || (bitmode == 3) || (bitmode == 24) || (bitmode == 32))tempbitmode = 2;
	else tempbitmode = 1;

	tempsr = sr;
	if (tempsr > 100000)tempsr = 100000;
	//------------------
	if (tempsr > 50000)
	{
		if (tempbitmode == 2) tempbitmode = 1;
	}
	//if (tempbitmode == 2)
	//{
	//	if (tempsr > 50000)tempsr = 50000;
	//}
	//else
	//{
	//	if (tempsr > 100000)tempsr = 100000;
	//}
	txbuf[5] = (unsigned char)tempbitmode;  	//设置传输的数据格式8/16/24/32位    
	txbuf[6] = (unsigned char)(tempsr / 0x10000);	   //把KPS采样率分解为三个数据写入相应数组   
	txbuf[7] = (unsigned char)(tempsr / 0x100);
	txbuf[8] = (unsigned char)(tempsr);
	txbuf[9] = 0; // 发送 所有的 通道,  第17字节
	VK[mci].SampleRate = sr;
	//---------------------------------
	
	//wpi = wpifromlan + 74;
	//VK[mci].CVMode[0] = *(wpifromlan + 74);//75 
	//VK[mci].CVMode[1] = *(wpifromlan + 75);//76 
	//VK[mci].CVMode[2] = *(wpifromlan + 76);//77 
	//VK[mci].CVMode[3] = *(wpifromlan + 77);//78 
	//wbuf[i++] = (unsigned char)VK[mci].CVMode[0];
	//wbuf[i++] = (unsigned char)VK[mci].CVMode[1];
	//wbuf[i++] = (unsigned char)VK[mci].CVMode[2];
	//wbuf[i++] = (unsigned char)VK[mci].CVMode[3];

	if ((npoints > 0) && (tinterval>0))
	{
		VK[mci].Npoints = npoints;
		VK[mci].Tintervals = tinterval;
		txbuf[10] = (unsigned char)(npoints / 0x1000000);//N采样数据
		txbuf[11] = (unsigned char)(npoints / 0x10000);	    
		txbuf[12] = (unsigned char)(npoints / 0x100);
		txbuf[13] = (unsigned char)(npoints);
		txbuf[14] = 0x22;
		txbuf[15] = (unsigned char)(tinterval / 0x1000000);//定时采样间隔 
		txbuf[16] = (unsigned char)(tinterval / 0x10000);	     
		txbuf[17] = (unsigned char)(tinterval / 0x100);
		txbuf[18] = (unsigned char)(tinterval);
		// 兼容， VK701NSD 采集卡
		i = DisposalTXDatum(VKTCPServer.SockClient[mci], 0x81, txbuf, 19, 1);
	}
	else
	{
		i = DisposalTXDatum(VKTCPServer.SockClient[mci], 0x81, txbuf, 10, 1);
	}
	//--------------------------
	if (RXLANMonitor_ThreadRunningState == 0) // 閲嶆柊鎵撳紑鎺ユ敹绾跨▼	 //20200528 hide thread //
	{				  //20200528 hide thread //
		RXLANMonitor_ThreadRunningState = 2;	   //20200528 hide thread //
		RXLANMonitor_Handle = CreateThread(NULL, 0, MonitorRXLANEvent, NULL, 0, NULL);	  //20200528 hide thread //
		//SetThreadPriority(RXLANMonitor_Handle,THREAD_PRIORITY_TIME_CRITICAL);   //20200528 hide thread //
	}
	return i;
}





int Def_Function_OUTfmt VK70xNMC_InitializeAll(int mci, int *para,int len)
{
	int i = 0;
	int temp = 0;
	unsigned char txbuf[32];
	unsigned char vkmode = 0;
	unsigned char tempbitmode = 2;
	int tempsr;

	//printf("--------------------------------------\n");
	//printf("VKTCPServer.Client_Num：%d\n", VKTCPServer.Client_Num);
    //printf("TCPMonitor_ThreadRunningState：%d\n", TCPMonitor_ThreadRunningState);
	//printf("DLLInitializeFlag：%d\n", DLLInitializeFlag);	
	//printf("--------------------------------------\n");	
	InitDLL(); 
	//printf("VKTCPServer.Client_Num：%d\n", VKTCPServer.Client_Num);
	//printf("TCPMonitor_ThreadRunningState：%d\n", TCPMonitor_ThreadRunningState);
	//printf("DLLInitializeFlag：%d\n", DLLInitializeFlag);
	//--------------------
	if (TCPMonitor_ThreadRunningState == 0)   // 未打开服务器
	{
		i = Server_TCPOpen(8234);//打开默认的服务器
		if (i<0)return i;
		Sleep(100);
		//printf("3456789754323456776：%d\n", VKTCPServer.Client_Num);
	}
	//if (ThreadRunningState==1)return -2;
	//if (ThreadRunningState==0)return -11;  //服务未打开  
	//printf("--------------------------------------\n");
	//printf("VKTCPServer.Client_Num：%d\n", VKTCPServer.Client_Num);
	//printf("TCPMonitor_ThreadRunningState：%d\n", TCPMonitor_ThreadRunningState);
	//printf("--------------------------------------\n");

	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -13;
	//--------------------
	VK70xNMC_StopSampling(mci);
	//-------------------- 
	VK[mci].SaveShowPI = 0;
	VK[mci].ReadShowPI = 0;
	VK[mci].Read4CHPI = 0;
	for (i = 0; i < 8; i++)VK[mci].ReadCHPI[i] = 0;
	//-------------------- 
	// [0]: sr
	// [1]: refer vol
	// [2]: bit mode
	// [3]: n points
	// [4~7]/1:电压输入范围
	// [8~11]/4: CV mode
	//-------------------------------
	VK[mci].SampleRate = *(para);
	if (VK[mci].SampleRate > 102400)VK[mci].SampleRate = 102400;

	temp = *(para + 1);
	if ((temp == 1) || (temp == 4))VK[mci].ReferenceVoltage = 4.000;
	else VK[mci].ReferenceVoltage = 2.442;

	temp = *(para + 2);
	if ((temp == 2) || (temp == 3) || (temp == 24) || (temp == 32)) tempbitmode = 2;
	else  tempbitmode = 1;
	if (VK[mci].SampleRate > 51200)
	{
		if (tempbitmode == 2) tempbitmode = 1;
	}
	VK[mci].Npoints = *(para + 3);
	//---------------------
	if (VK[mci].ReferenceVoltage == 2.442)
	{
		VK[mci].PGAGainRange[0] = GetGainValue_NOPGA(*(para + 4));
		VK[mci].PGAGainRange[1] = GetGainValue_NOPGA(*(para + 5));
		VK[mci].PGAGainRange[2] = GetGainValue_NOPGA(*(para + 6));
		VK[mci].PGAGainRange[3] = GetGainValue_NOPGA(*(para + 7));
		VK[mci].PGAGainRange[4] = VK[mci].PGAGainRange[0];
		VK[mci].PGAGainRange[5] = VK[mci].PGAGainRange[1];
		VK[mci].PGAGainRange[6] = VK[mci].PGAGainRange[2];
		VK[mci].PGAGainRange[7] = VK[mci].PGAGainRange[3];
	}
	else
	{
		VK[mci].PGAGainRange[0] = GetGainValue_PGA(*(para + 4));
		VK[mci].PGAGainRange[1] = GetGainValue_PGA(*(para + 5));
		VK[mci].PGAGainRange[2] = GetGainValue_PGA(*(para + 6));
		VK[mci].PGAGainRange[3] = GetGainValue_PGA(*(para + 7));
		VK[mci].PGAGainRange[4] = VK[mci].PGAGainRange[0];
		VK[mci].PGAGainRange[5] = VK[mci].PGAGainRange[1];
		VK[mci].PGAGainRange[6] = VK[mci].PGAGainRange[2];
		VK[mci].PGAGainRange[7] = VK[mci].PGAGainRange[3];
	}

	for (i = 0; i < 4; i++)VK[mci].CVMode[i] = *(para + 8 + i);

	//-----------------------------
	VK[mci].RXLANSavePI = 0;
	VK[mci].RXLANReadPI = 0;
	//-------------------- 
	// [0~3]/1:
	// [4]/1: 1,VK[mci].ReferenceVoltage
	// [5]/1: data format 16/24bit
	// [6~8]/3: sr
	// [9]/1: channels
	// [10~13]/4: 保留/n points
	// [14~17]/4: 保留/file index
	// [18]/1:  0x00,无效，0x22=晶振校对参数 ,0x33=intervals
	// [19~21]/3: 保留/intervals/晶振校对参数 
	// [22~23]/2: 保留
	// [24~27]/4: CV mode
	// [28~31]/4: 保留
	//------------------------
	for (i = 0; i < 32; i++)txbuf[i] = 0;
	txbuf[0] = (unsigned char)(*(para + 4));// (char)SysInfor.CH_CS[0];	//设置通道1的输入范围   
	txbuf[1] = (unsigned char)(*(para + 5));   	//设置通道2的输入范围  
	txbuf[2] = (unsigned char)(*(para + 6));   	//设置通道3的输入范围   
	txbuf[3] = (unsigned char)(*(para + 7));   	//设置通道4的输入范围

	if (VK[mci].ReferenceVoltage == 2.442)txbuf[4] = 0;
	else txbuf[4] = 1;

	temp = VK[mci].SampleRate;
	txbuf[5] = (unsigned char)tempbitmode;  	//设置传输的数据格式8/16/24/32位    
	txbuf[6] = (unsigned char)(temp / 0x10000);	   //把KPS采样率分解为三个数据写入相应数组   
	txbuf[7] = (unsigned char)(temp / 0x100);
	txbuf[8] = (unsigned char)(temp);
	txbuf[9] = 0; // 发送 所有的 通道,  第17字节

	//---------------------------------
	temp = VK[mci].Npoints;// n points for vk701nsd
	txbuf[10] = (unsigned char)(temp / 0x1000000);//N采样数据
	txbuf[11] = (unsigned char)(temp / 0x10000);
	txbuf[12] = (unsigned char)(temp / 0x100);
	txbuf[13] = (unsigned char)(temp);

	temp = 1;// file index for vk701nsd
	txbuf[14] = (unsigned char)(temp / 0x1000000);//定时采样间隔 
	txbuf[15] = (unsigned char)(temp / 0x10000);
	txbuf[16] = (unsigned char)(temp / 0x100);
	txbuf[17] = (unsigned char)(temp);

	txbuf[18] = 0x33;
	txbuf[19] = 0;
	txbuf[20] = 0;
	txbuf[21] = 0;

	txbuf[22] = 0;
	txbuf[23] = 0;//
	txbuf[24] = (unsigned char)VK[mci].CVMode[0];
	txbuf[25] = (unsigned char)VK[mci].CVMode[1];
	txbuf[26] = (unsigned char)VK[mci].CVMode[2];
	txbuf[27] = (unsigned char)VK[mci].CVMode[3];
	txbuf[28] = 0;
	txbuf[29] = 0;
	txbuf[30] = 0;
	txbuf[31] = 0;
	//-------------------------
	i = DisposalTXDatum(VKTCPServer.SockClient[mci], 0x81, txbuf, 32, 1);
	//--------------------------
	if (RXLANMonitor_ThreadRunningState == 0) // 閲嶆柊鎵撳紑鎺ユ敹绾跨▼	 //20200528 hide thread //
	{				  //20200528 hide thread //
		RXLANMonitor_ThreadRunningState = 2;	   //20200528 hide thread //
		RXLANMonitor_Handle = CreateThread(NULL, 0, MonitorRXLANEvent, NULL, 0, NULL);	  //20200528 hide thread //
		//SetThreadPriority(RXLANMonitor_Handle,THREAD_PRIORITY_TIME_CRITICAL);   //20200528 hide thread //
	}
	return i;
}