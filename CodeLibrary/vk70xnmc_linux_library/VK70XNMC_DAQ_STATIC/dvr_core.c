#if _MSC_VER > 1000
#pragma once
#endif 

#include "VK70xNMC_DAQ2.h"
#include "dvr_header.h"
#include <Windows.h>
#include <stdio.h>
//#include <WinSock2.h>  
//#pragma comment(lib, "WS2_32.lib")

/*#ifndef _OUT_ALL_DLL_//_OUT_CDCEL_DLL_
//---------------------------------
#ifdef _MANAGED
#pragma managed(push, off)
#endif

BOOL APIENTRY DllMain(HMODULE hModule,
	DWORD  ul_reason_for_call,
	LPVOID lpReserved
	)
{
	return TRUE;
}
//-------------------------------------
#endif*/


//void  DisposalDownloadRXTask_LEN(int mci, TypeDefVK70xNMCPara *vkmc, int len);


//=======================================================
//========================================================
//
//void MonitorUSBEvent(void)
DWORD WINAPI MonitorRXLANEvent(PVOID pvParam)
{
	char pluse_test_buffer[64];
	unsigned char i;
	int tlen;
	int threadslpflag;
	static int uc_timeout = 0;
	int errnum;
	//-------------------------------
	for (i = 0; i< sizeof(pluse_test_buffer); i++)pluse_test_buffer[i] = 0;
	//-------------------------------
	//TCPMonitor_ThreadRunningState = 0;
	//RXLANMonitor_ThreadRunningState = 0;
	RXLANMonitor_ThreadRunningState = 2;//开始读写
	while (RXLANMonitor_ThreadRunningState>0)// 
	{
		threadslpflag = 1;// 准备下一次睡眠
		//--------------------
		//int readout_flag = 0;
		//int readout_count;
		//factlen = recv(sockConn, recvBuf, 1032, 0);  //接收数据 
		for (i = 0; i< MAX_TCP_CILENT_NUM; i++)
		{
			if (VKTCPServer.ClientStatus[i]>0)
			{
				//readout_flag = 1;
				//debug_infor_status = 10000*(i+1);
				tlen = recv(VKTCPServer.SockClient[i], (char *)&VK[i].RXLANDatum[VK[i].RXLANSavePI], MAX_READ_TCP_UNIT, 0);
				//debug_infor_status = 10000 * (i + 1) + tlen;
				if (tlen>0)
				{
					VK[i].RXLANSavePI += tlen;
					if (VK[i].RXLANSavePI >= MAX_RXLAN_LEN)
					{
						VK[i].MaxBuffer_SaveedLen = VK[i].RXLANSavePI;
						VK[i].MaxBuffer_OverFlag = 1;
						VK[i].RXLANSavePI = 0;
					}
					//MultiCard_WirteBufferTask(i,(unsigned char *)datapbuffer,readout_count);
					VKTCPServer.RecievedBytes_Count += tlen;	  //计算流量
					uc_timeout = 0;
				}				
				else if (tlen == 0)
				{
					//printf("句柄【%d】接收到采集卡【%d】上【%d】个数据!\n", VKTCPServer.SockClient[i], i, tlen);
					//printf("实际发送的的数据或状态：%d；准备发送数据长度：%d\n", tlen, 1);
					//FD_CLR(VKTCPServer.fdSocket.fd_array[i], &VKTCPServer.fdSocket);
					VKTCPServer.ClientStatus[i] = 0;
					memset(&VKTCPServer.ClientAddr[i], 0, sizeof(VKTCPServer.ClientAddr[i]));
					if (VKTCPServer.Client_Num>0)VKTCPServer.Client_Num--;
					//printf("=======================================已断开连接：%d==========================================\n", VKTCPServer.Client_Num);
				}
				else
				{
					if (++uc_timeout > 20)
					{
						uc_timeout = send(VKTCPServer.SockClient[i], pluse_test_buffer, sizeof(pluse_test_buffer), 0);;//(char *)&
						if (uc_timeout < 0)
						{
							//printf("句柄【%d】接收到采集卡【%d】上【%d】个数据!\n", VKTCPServer.SockClient[i], i, tlen);
							//printf("实际发送的的数据或状态：%d；准备发送数据长度：%d\n", tlen, 1);
							//FD_CLR(VKTCPServer.fdSocket.fd_array[i], &VKTCPServer.fdSocket);
							VKTCPServer.ClientStatus[i] = 0;
							closesocket(VKTCPServer.SockClient[i]);
							VKTCPServer.SockClient[i] = INVALID_SOCKET;
							memset(&VKTCPServer.ClientAddr[i], 0, sizeof(VKTCPServer.ClientAddr[i]));
							if (VKTCPServer.Client_Num>0)VKTCPServer.Client_Num--;
							//printf("=======================================已断开连接：%d==========================================\n", VKTCPServer.Client_Num);
						}
						uc_timeout = 0;
					}
				}
			}
		}
		//if (readout_flag == 0)
		//{
		//	char datapbuffer[103200];		 // 其它采集卡，读出防止一直响应这个中断
		//	readout_count = ServerTCPRead(handle, datapbuffer, 103200, 1);
		//	if (readout_count>0)VKTCPServer.RecievedBytes_Count += readout_count;	  //计算流量
		//}
		//-------------------------------------
		for (i = 0; i < MAX_TCP_CILENT_NUM; i++)// 扫描16 通道 数据 
		{
			if (VK[i].RXLANSavePI == VK[i].RXLANReadPI)continue; // 无数据
			threadslpflag = 0;
			//--------------------------------- //处理溢出字节
			if (VK[i].MaxBuffer_OverFlag == 1)
			{
				if (VK[i].MaxBuffer_SaveedLen>VK[i].RXLANReadPI)
				{
					tlen = VK[i].MaxBuffer_SaveedLen - VK[i].RXLANReadPI;
					DisposalDownloadRXTask_LEN(i,&VK[i], tlen);
				}
				VK[i].RXLANReadPI = 0;
				VK[i].MaxBuffer_OverFlag = 0;
				VK[i].MaxBuffer_SaveedLen = 0;
			}
			//--------------------------------
			if (VK[i].RXLANSavePI>VK[i].RXLANReadPI)
			{
				tlen = VK[i].RXLANSavePI - VK[i].RXLANReadPI;
				DisposalDownloadRXTask_LEN(i,&VK[i], tlen);
				VK[i].RXLANReadPI = VK[i].RXLANSavePI;
			}
			//else if(VK[i].RXLANSavePI<VK[i].RXLANReadPI)// error 
		}
		//-----------------------
		if (threadslpflag == 1)Sleep(1); /// 休眠，防止CPU占用效率过高
		//-----------------------
	}
	/*
	unsigned char i;
	int threadslpflag;
	ThreadRunningState=2;//开始读写
	while(ThreadRunningState>0)//
	{
	threadslpflag = 1;// 准备下一次睡眠
	//--------------------
	for (i = 0; i < MAX_RX_CARD_NUM; i++)// 扫描16 通道 数据
	{
	if (VK[i].RXLANSavePI == VK[i].RXLANReadPI)continue; // 无数据
	threadslpflag = 0;
	//---------------------------------
	if(VK[i].MaxBuffer_OverFlag==1)
	{
	while (VK[i].RXLANSavePI != VK[i].RXLANReadPI)
	{
	DisposalDownloadRXTask(i,VK[i].RXLANDatum[VK[i].RXLANReadPI]);
	if (++VK[i].RXLANReadPI >= VK[i].MaxBuffer_SaveedLen)
	{
	VK[i].RXLANReadPI = 0;
	VK[i].MaxBuffer_OverFlag = 0;
	VK[i].MaxBuffer_SaveedLen = 0;
	break;
	}
	}
	}
	else
	{
	while (VK[i].RXLANSavePI != VK[i].RXLANReadPI)
	{
	DisposalDownloadRXTask(i,VK[i].RXLANDatum[VK[i].RXLANReadPI]);
	VK[i].RXLANReadPI++;
	//if (++VK[i].RXLANReadPI >= MAX_RXLAN_LEN)VK[i].RXLANReadPI = 0;
	}
	}
	//---------------------------------
	//while (VK[i].RXLANSavePI != VK[i].RXLANReadPI)
	//{
	//	  DisposalDownloadRXTask(i,VK[i].RXLANDatum[VK[i].RXLANReadPI]);
	//	  if (++VK[i].RXLANReadPI >= MAX_RXLAN_LEN)VK[i].RXLANReadPI = 0;
	//}
	//--------------------------------
	}
	//-----------------------
	if (threadslpflag == 1)Sleep(1); /// 休眠，防止CPU占用效率过高
	//-----------------------
	}
	*/
	/*
	unsigned char i;
	int threadslpflag;
	ThreadRunningState=2;//开始读写
	while(ThreadRunningState>0)//
	{
	threadslpflag = 1;// 准备下一次睡眠
	//--------------------
	for (i = 0; i < MAX_RX_CARD_NUM; i++)// 扫描16 通道 数据
	{
	if (VK[i].RXLANSavePI == VK[i].RXLANReadPI)continue; // 无数据
	threadslpflag = 0;
	while (VK[i].RXLANSavePI != VK[i].RXLANReadPI)
	{
	DisposalDownloadRXTask(i,VK[i].RXLANDatum[VK[i].RXLANReadPI]);
	if (++VK[i].RXLANReadPI >= MAX_RXLAN_LEN)VK[i].RXLANReadPI = 0;
	}
	}
	//-----------------------
	if (threadslpflag == 1)Sleep(1); /// 休眠，防止CPU占用效率过高
	//-----------------------
	}
	*/
	return 0;
}


double  GetGainValue_NOPGA(int volrange)
{
	if (volrange == 0)return 1;
	else if (volrange == 1)return 2;
	else if (volrange == 2)return 4;
	else if (volrange == 3)return 8;
	else if (volrange == 4)return 16;
	else return 1;
}


double  GetGainValue_PGA(int volrange)
{
	//-10V~+10V	0.344
	//-5V~+5V	0.688
	//-2.5V~+2.5V	1.375
	//-1V~+1V	2.75
	//-500mV~+500mV	5.5
	//-100mV~+100mV	22
	//-20mV~+20mV	176
	//-1mV~+1mV	2816
	if (volrange == 0)return 0.344;
	else if (volrange == 1)return 0.688;
	else if (volrange == 2)return 1.375;
	else if (volrange == 3)return 2.75;
	else if (volrange == 4)return 5.5;
	else if (volrange == 5)return 22;
	else if (volrange == 6)return 176;
	else if (volrange == 7)return 2816;
	else return 0.344;
}
///////////////////////////////////////////////////////////////////////////////////////////
/*
void SaveAndDisplayInformation(unsigned char mci)
{
int packagelen;
//double tempvol;
short int sch;
int tempdat,tempCh,tempLine,ti,r,chindex;//,j
//////////////////////////////////////////////////////////////////////
if (VK[mci].ReferenceVoltage == 2.442)// 2.442 mode
{
///////////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////////
packagelen = VK[mci].PacketDatum[0] & 0x7F;
packagelen = (packagelen << 8) + VK[mci].PacketDatum[1];
//printf("数据格式16位,共[%d]通道,[%d]采样点\n",packagelen,PacketDatum[4]);
//----------------------
if ((VK[mci].PacketDatum[4] & 0xF0) == 0x10) // signal byte
{
tempCh = VK[mci].PacketDatum[4] & 0x0F; //PacketDatum
packagelen = packagelen - 4;
tempLine =  packagelen /  tempCh;
//if( UpdateDataFormatFlag==1 )    //  System_Channel <> tempCh
//{
//   printf("数据格式8位,共[%d]通道,[%d]采样点",tempCh,tempLine);
//	Sampling_Channel=tempCh;
//    UpdateDataFormatFlag=1;
//}
r = 5;
ti = 0;
VK[mci].IOUpdateFlag = -1;
while (ti < tempLine)
{
//==========================================
for(chindex = 0; chindex < tempCh; chindex++)
{
//sch= (short int)(PacketDatum[r]*256);//(~((PacketDatum[r]*256)))+1;
sch = (short int)(~((VK[mci].PacketDatum[r] * 256))) + 1;
tempdat=sch;
VK[mci].CHShowBuffer[chindex][VK[mci].SaveShowPI] = (((tempdat)*14.652) / 0x8000) / VK[mci].PGAGainRange[chindex];
r++;
}
while (chindex < 8)
{
VK[mci].CHShowBuffer[chindex][VK[mci].SaveShowPI] = 0;
chindex++;
}
/////////////////////////
ti++;
VK[mci].SaveShowPI++;
if (VK[mci].SaveShowPI>_DISP_MAX_LEN)
{
VK[mci].SaveShowPI = 0;
//exit;
}
}
}
else if ((VK[mci].PacketDatum[4] & 0xF0) == 0x20)  // double byte
{
tempCh = VK[mci].PacketDatum[4] & 0x0F;
packagelen = packagelen - 4;
tempLine =  packagelen /  tempCh;
tempLine = tempLine >> 1;   // div
//=================================
//if( UpdateDataFormatFlag==1 )
//{
// printf("数据格式16位,共[%d]通道,[%d]采样点",tempCh,tempLine);
//	Sampling_Channel=tempCh;
//    UpdateDataFormatFlag=0;
//}
r = 5;
ti = 0;
VK[mci].IOUpdateFlag = -1;
while ( ti <  tempLine )
{
//==========================================
for(chindex = 0; chindex< tempCh; chindex ++)
{
//sch= (short int)(PacketDatum[r]+ (PacketDatum[r+1]*256));//(~(PacketDatum[r]+ (PacketDatum[r+1]*256)))+1;
sch = (short int)(~(VK[mci].PacketDatum[r] + (VK[mci].PacketDatum[r + 1] * 256))) + 1;
tempdat=sch;
VK[mci].CHShowBuffer[chindex][VK[mci].SaveShowPI] = (((tempdat)*14.652) / 0x8000) / VK[mci].PGAGainRange[chindex];
r=r+2;
}
while (chindex < 8)
{
VK[mci].CHShowBuffer[chindex][VK[mci].SaveShowPI] = 0;
chindex++;
}
//=========================================
ti++;
VK[mci].SaveShowPI++;
if (VK[mci].SaveShowPI>_DISP_MAX_LEN)
{
VK[mci].SaveShowPI = 0;
//exit;
}
}
//--------------------
}
else if ((VK[mci].PacketDatum[4] & 0xF0) == 0x30) // 4 byte
{
tempCh = VK[mci].PacketDatum[4] & 0x0F;
packagelen = packagelen - 4;
tempLine =  packagelen /  tempCh;
tempLine = tempLine >> 2;
//if( UpdateDataFormatFlag==1 ) //  System_Channel <> tempCh
//{
// printf("数据格式24位,共[%d]通道,[%d]采样点",tempCh,tempLine);
///	Sampling_Channel=tempCh;
//    UpdateDataFormatFlag=0;
//}
r = 5;
ti = 0;
/////////////////////////////////////////////////////////////
//IOStaus[4];//PacketDatum[r+2]
//if ((PacketDatum[8] & 0x10) == 0x10)IOStaus[1] = 1;
//else IOStaus[1] = 0;
//------------------------------------------------------------
//if ((PacketDatum[8] & 0x20) == 0x20)IOStaus[2] = 1;
//else IOStaus[2] = 0;

VK[mci].IOUpdateFlag = 1;
/////////////////////////////////////////////////////////////
while(ti <  tempLine )
{
//IO2 固定在 8通道上， IO3固定9通道
if ((VK[mci].PacketDatum[r + 3] & 0x10) == 0x10)VK[mci].CHShowBuffer[8][VK[mci].SaveShowPI] = 1;
else VK[mci].CHShowBuffer[8][VK[mci].SaveShowPI] = 0;
if ((VK[mci].PacketDatum[r + 3] & 0x20) == 0x20)VK[mci].CHShowBuffer[9][VK[mci].SaveShowPI] = 1;
else VK[mci].CHShowBuffer[9][VK[mci].SaveShowPI] = 0;
//==========================================
for(chindex = 0; chindex< tempCh; chindex ++)
{
//tempdat=  PacketDatum[r]*0x100+ (PacketDatum[r+1]*0x10000)+ (PacketDatum[r+2]*0x1000000);//(~ (PacketDatum[r]*0x100+ (PacketDatum[r+1]*0x10000)+ (PacketDatum[r+2]*0x1000000)))+1;
tempdat = (~(VK[mci].PacketDatum[r] * 0x100 + (VK[mci].PacketDatum[r + 1] * 0x10000) + (VK[mci].PacketDatum[r + 2] * 0x1000000))) + 1;
tempdat= tempdat / 0x100;
VK[mci].CHShowBuffer[chindex][VK[mci].SaveShowPI] = (((tempdat)*14.652) / 0x800000) / VK[mci].PGAGainRange[chindex];
r=r+4;
}
while (chindex < 8)
{
VK[mci].CHShowBuffer[chindex][VK[mci].SaveShowPI] = 0;
chindex++;
}
//////////////////////////////////////////

//=========================================
ti++;
VK[mci].SaveShowPI++;
if (VK[mci].SaveShowPI>_DISP_MAX_LEN)
{
VK[mci].SaveShowPI = 0;
//exit;
}
}
}
else if ((VK[mci].PacketDatum[4] & 0xF0) == 0x40) // 4 byte
{
tempCh = VK[mci].PacketDatum[4] & 0x0F;
packagelen = packagelen - 4;
tempLine =  packagelen /  tempCh;
tempLine = tempLine >> 2;
//if( UpdateDataFormatFlag==1 )  //System_Channel <> tempCh
//{
// printf("数据格式32位,共[%d]通道,[%d]采样点",tempCh,tempLine);
//	Sampling_Channel=tempCh;
//    UpdateDataFormatFlag=0;
//}
////////////////
r = 5;
ti = 0;
VK[mci].IOUpdateFlag = -1;
while (ti <  tempLine)
{
if (VK[mci].SaveShowPI>_DISP_MAX_LEN)
{
VK[mci].SaveShowPI = 0;
}
//==========================================
for(chindex = 0; chindex < tempCh; chindex ++)
{
//tempdat= (PacketDatum[r+1]*0x100)+ (PacketDatum[r+2]*0x10000)+ (PacketDatum[r+3]*0x1000000);//(~ ((PacketDatum[r+1]*0x100)+ (PacketDatum[r+2]*0x10000)+ (PacketDatum[r+3]*0x1000000)))+1;
tempdat = (~((VK[mci].PacketDatum[r + 1] * 0x100) + (VK[mci].PacketDatum[r + 2] * 0x10000) + (VK[mci].PacketDatum[r + 3] * 0x1000000))) + 1;
tempdat= tempdat / 0x100;
VK[mci].CHShowBuffer[chindex][VK[mci].SaveShowPI] = (((tempdat)*14.652) / 0x800000) / VK[mci].PGAGainRange[chindex];
r=r+4;
}
while (chindex < 8)
{
VK[mci].CHShowBuffer[chindex][VK[mci].SaveShowPI] = 0;
chindex++;
}
//==========================================
ti++;
VK[mci].SaveShowPI++;
if (VK[mci].SaveShowPI>_DISP_MAX_LEN)
{
VK[mci].SaveShowPI = 0;
}
}
}
///////////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////////
}
else // 4.00 mode
{
///////////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////////
packagelen = VK[mci].PacketDatum[0] & 0x7F;
packagelen = (packagelen << 8) + VK[mci].PacketDatum[1];
//printf("数据格式16位,共[%d]通道,[%d]采样点\n",packagelen,PacketDatum[4]);
//----------------------
if ((VK[mci].PacketDatum[4] & 0xF0) == 0x10) // signal byte
{
tempCh = VK[mci].PacketDatum[4] & 0x0F; //PacketDatum
packagelen = packagelen - 4;
tempLine =  packagelen /  tempCh;
//if( UpdateDataFormatFlag==1 )    //  System_Channel <> tempCh
//{
//   printf("数据格式8位,共[%d]通道,[%d]采样点",tempCh,tempLine);
//	Sampling_Channel=tempCh;
//    UpdateDataFormatFlag=1;
//}
r = 5;
ti = 0;
VK[mci].IOUpdateFlag = -1;
while (ti < tempLine)
{
//==========================================
for(chindex = 0; chindex < tempCh; chindex++)
{
sch = (short int)(VK[mci].PacketDatum[r] * 256);//(~((PacketDatum[r]*256)))+1;
//sch= (short int)(~((PacketDatum[r]*256)))+1;
tempdat=sch;
//CHShowBuffer[chindex][SaveShowPI]= (((tempdat)*14.652)/0x8000)/PGAGainRange[chindex];
VK[mci].CHShowBuffer[chindex][VK[mci].SaveShowPI] = (((tempdat)*4.000) / 0x8000) / VK[mci].PGAGainRange[chindex];
r++;
}
while (chindex < 8)
{
VK[mci].CHShowBuffer[chindex][VK[mci].SaveShowPI] = 0;
chindex++;
}
/////////////////////////
ti++;
VK[mci].SaveShowPI++;
if (VK[mci].SaveShowPI>_DISP_MAX_LEN)
{
VK[mci].SaveShowPI = 0;
//exit;
}
}
}
else if ((VK[mci].PacketDatum[4] & 0xF0) == 0x20)  // double byte
{
tempCh = VK[mci].PacketDatum[4] & 0x0F;
packagelen = packagelen - 4;
tempLine =  packagelen /  tempCh;
tempLine = tempLine >> 1;   // div
//=================================
//if( UpdateDataFormatFlag==1 )
//{
// printf("数据格式16位,共[%d]通道,[%d]采样点",tempCh,tempLine);
//	Sampling_Channel=tempCh;
//    UpdateDataFormatFlag=0;
//}
r = 5;
ti = 0;
VK[mci].IOUpdateFlag = -1;
while ( ti <  tempLine )
{
//==========================================
for(chindex = 0; chindex< tempCh; chindex ++)
{
sch = (short int)(VK[mci].PacketDatum[r] + (VK[mci].PacketDatum[r + 1] * 256));//(~(PacketDatum[r]+ (PacketDatum[r+1]*256)))+1;
//sch= (short int)(~(PacketDatum[r]+ (PacketDatum[r+1]*256)))+1;
tempdat=sch;
//CHShowBuffer[chindex][SaveShowPI]= (((tempdat)*14.652)/0x8000)/PGAGainRange[chindex];
VK[mci].CHShowBuffer[chindex][VK[mci].SaveShowPI] = (((tempdat)*4.000) / 0x8000) / VK[mci].PGAGainRange[chindex];
r=r+2;
}
while (chindex < 8)
{
VK[mci].CHShowBuffer[chindex][VK[mci].SaveShowPI] = 0;
chindex++;
}
//=========================================
ti++;
VK[mci].SaveShowPI++;
if (VK[mci].SaveShowPI>_DISP_MAX_LEN)
{
VK[mci].SaveShowPI = 0;
//exit;
}
}
//--------------------
}
else if ((VK[mci].PacketDatum[4] & 0xF0) == 0x30) // 4 byte
{
tempCh = VK[mci].PacketDatum[4] & 0x0F;
packagelen = packagelen - 4;
tempLine =  packagelen /  tempCh;
tempLine = tempLine >> 2;
//if( UpdateDataFormatFlag==1 ) //  System_Channel <> tempCh
//{
// printf("数据格式24位,共[%d]通道,[%d]采样点",tempCh,tempLine);
///	Sampling_Channel=tempCh;
//    UpdateDataFormatFlag=0;
//}
r = 5;
ti = 0;
VK[mci].IOUpdateFlag = 1;
while(ti <  tempLine )
{
//==========================================
if (tempCh == 4)
{
//------------------------------------------
//IO2 固定在 8通道上， IO3固定9通道
if ((VK[mci].PacketDatum[r] & 0x10) == 0x10)VK[mci].CHShowBuffer[8][VK[mci].SaveShowPI] = 1;
else VK[mci].CHShowBuffer[8][VK[mci].SaveShowPI] = 0;
if ((VK[mci].PacketDatum[r] & 0x20) == 0x20)VK[mci].CHShowBuffer[9][VK[mci].SaveShowPI] = 1;
else VK[mci].CHShowBuffer[9][VK[mci].SaveShowPI] = 0;
//----------------------------------------------------
//00 22 FF 00 D0 F8 F2 FF FF F4 9F F3 FA FF FF 2F
//      FFF8D0      FFF2F4     FFF39F FFFA2F
r=r+2;
tempdat = VK[mci].PacketDatum[r] * 0x1000000 + (VK[mci].PacketDatum[r + 3] * 0x10000) + (VK[mci].PacketDatum[r + 2] * 0x100);//(~(PacketDatum[r]*0x1000000+ (PacketDatum[r+3]*0x10000)+ (PacketDatum[r+2]*0x100)))+1;
//tempdat= (~(PacketDatum[r]*0x1000000+ (PacketDatum[r+3]*0x10000)+ (PacketDatum[r+2]*0x100)))+1;
tempdat= tempdat / 0x100;
VK[mci].CHShowBuffer[0][VK[mci].SaveShowPI] = (((tempdat)*4.00) / 0x800000) / VK[mci].PGAGainRange[0];
r=r+4;
//---------------------
tempdat = VK[mci].PacketDatum[r + 3] * 0x100 + (VK[mci].PacketDatum[r] * 0x10000) + (VK[mci].PacketDatum[r + 1] * 0x1000000);//(~ (PacketDatum[r+3]*0x100+ (PacketDatum[r]*0x10000)+ (PacketDatum[r+1]*0x1000000)))+1;
//tempdat= (~ (PacketDatum[r+3]*0x100+ (PacketDatum[r]*0x10000)+ (PacketDatum[r+1]*0x1000000)))+1;
tempdat= tempdat / 0x100;
VK[mci].CHShowBuffer[1][VK[mci].SaveShowPI] = (((tempdat)*4.00) / 0x800000) / VK[mci].PGAGainRange[1];
r=r+2;
//------------------
tempdat = VK[mci].PacketDatum[r + 2] * 0x100 + (VK[mci].PacketDatum[r + 3] * 0x10000) + (VK[mci].PacketDatum[r] * 0x1000000);//(~ (PacketDatum[r+2]*0x100+ (PacketDatum[r+3]*0x10000)+ (PacketDatum[r]*0x1000000)))+1;
//tempdat= (~ (PacketDatum[r+2]*0x100+ (PacketDatum[r+3]*0x10000)+ (PacketDatum[r]*0x1000000)))+1;
tempdat= tempdat / 0x100;
VK[mci].CHShowBuffer[2][VK[mci].SaveShowPI] = (((tempdat)*4.00) / 0x800000) / VK[mci].PGAGainRange[2];
r=r+4;
//------------------
tempdat = VK[mci].PacketDatum[r + 3] * 0x100 + (VK[mci].PacketDatum[r] * 0x10000) + (VK[mci].PacketDatum[r + 1] * 0x1000000);//(~ (PacketDatum[r+2]*0x100+ (PacketDatum[r+3]*0x10000)+ (PacketDatum[r]*0x1000000)))+1;
//tempdat= (~ (PacketDatum[r+3]*0x100+ (PacketDatum[r]*0x10000)+ (PacketDatum[r+1]*0x1000000)))+1;
tempdat= tempdat / 0x100;
VK[mci].CHShowBuffer[3][VK[mci].SaveShowPI] = (((tempdat)*4.00) / 0x800000) / VK[mci].PGAGainRange[3];
r=r+4;
}
else
{
//IO2 固定在 8通道上， IO3固定9通道
if ((VK[mci].PacketDatum[r + 3] & 0x10) == 0x10)VK[mci].CHShowBuffer[8][VK[mci].SaveShowPI] = 1;
else VK[mci].CHShowBuffer[8][VK[mci].SaveShowPI] = 0;
if ((VK[mci].PacketDatum[r + 3] & 0x20) == 0x20)VK[mci].CHShowBuffer[9][VK[mci].SaveShowPI] = 1;
else VK[mci].CHShowBuffer[9][VK[mci].SaveShowPI] = 0;
//====================================================
for(chindex = 0; chindex< tempCh; chindex ++)
{
tempdat = VK[mci].PacketDatum[r] * 0x100 + (VK[mci].PacketDatum[r + 1] * 0x10000) + (VK[mci].PacketDatum[r + 2] * 0x1000000);//(~ (PacketDatum[r]*0x100+ (PacketDatum[r+1]*0x10000)+ (PacketDatum[r+2]*0x1000000)))+1;
//tempdat=  (~ (PacketDatum[r]*0x100+ (PacketDatum[r+1]*0x10000)+ (PacketDatum[r+2]*0x1000000)))+1;
tempdat= tempdat / 0x100;
//CHShowBuffer[chindex][SaveShowPI]= (((tempdat)*14.652)/0x800000)/PGAGainRange[chindex];
VK[mci].CHShowBuffer[chindex][VK[mci].SaveShowPI] = (((tempdat)*4.000) / 0x800000) / VK[mci].PGAGainRange[chindex];
r=r+4;
}
while (chindex < 8)
{
VK[mci].CHShowBuffer[chindex][VK[mci].SaveShowPI] = 0;
chindex++;
}
}
//=========================================
ti++;
VK[mci].SaveShowPI++;
if (VK[mci].SaveShowPI>_DISP_MAX_LEN)
{
VK[mci].SaveShowPI = 0;
//exit;
}
}
}
else if ((VK[mci].PacketDatum[4] & 0xF0) == 0x40) // 4 byte
{
tempCh = VK[mci].PacketDatum[4] & 0x0F;
packagelen = packagelen - 4;
tempLine =  packagelen /  tempCh;
tempLine = tempLine >> 2;
//if( UpdateDataFormatFlag==1 )  //System_Channel <> tempCh
//{
// printf("数据格式32位,共[%d]通道,[%d]采样点",tempCh,tempLine);
//	Sampling_Channel=tempCh;
//    UpdateDataFormatFlag=0;
//}
r = 5;
ti = 0;
VK[mci].IOUpdateFlag = -1;
while (ti <  tempLine )
{
//==========================================
for(chindex = 0; chindex< tempCh; chindex ++)
{
tempdat = (VK[mci].PacketDatum[r + 1] * 0x100) + (VK[mci].PacketDatum[r + 2] * 0x10000) + (VK[mci].PacketDatum[r + 3] * 0x1000000);//(~ ((PacketDatum[r+1]*0x100)+ (PacketDatum[r+2]*0x10000)+ (PacketDatum[r+3]*0x1000000)))+1;
//tempdat= (~ ((PacketDatum[r+1]*0x100)+ (PacketDatum[r+2]*0x10000)+ (PacketDatum[r+3]*0x1000000)))+1;
tempdat= tempdat / 0x100;
//CHShowBuffer[chindex][SaveShowPI]= (((tempdat)*14.652)/0x800000)/PGAGainRange[chindex];
VK[mci].CHShowBuffer[chindex][VK[mci].SaveShowPI] = (((tempdat)*4.000) / 0x800000) / VK[mci].PGAGainRange[chindex];
r=r+4;
}
while (chindex < 8)
{
VK[mci].CHShowBuffer[chindex][VK[mci].SaveShowPI] = 0;
chindex++;
}
//==========================================
ti++;
VK[mci].SaveShowPI++;
if (VK[mci].SaveShowPI>_DISP_MAX_LEN)
{
VK[mci].SaveShowPI = 0;
}
}
}
///////////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////////
///////////////////////////////////////////////////////////////////////////////////////////
}
}
*/


void SaveAndDisplayInformation_LEN(TypeDefVK70xNMCPara *vknextmc)
{
	int packagelen;
	//double tempvol;
	short int sch;
	int tempdat, tempCh, tempLine, ti, r, chindex;//,j  
	//////////////////////////////////////////////////////////////////////
	if (vknextmc->ReferenceVoltage == 2.442)// 2.442 mode
	{//VK702N,VK702N, VK701S
		///////////////////////////////////////////////////////////////////////////////////////////
		///////////////////////////////////////////////////////////////////////////////////////////
		///////////////////////////////////////////////////////////////////////////////////////////
		packagelen = vknextmc->PacketDatum[0] & 0x7F;
		packagelen = (packagelen << 8) + vknextmc->PacketDatum[1];
		//printf("数据格式16位,共[%d]通道,[%d]采样点\n",packagelen,PacketDatum[4]);
		//----------------------
		if ((vknextmc->PacketDatum[4] & 0xF0) == 0x10) // signal byte
		{
			tempCh = vknextmc->PacketDatum[4] & 0x0F; //PacketDatum
			packagelen = packagelen - 4;
			tempLine = packagelen / tempCh;
			//if( UpdateDataFormatFlag==1 )    //  System_Channel <> tempCh
			//{
			//   printf("数据格式8位,共[%d]通道,[%d]采样点",tempCh,tempLine);
			//	Sampling_Channel=tempCh;
			//    UpdateDataFormatFlag=1;
			//}
			r = 5;
			ti = 0;
			vknextmc->IOUpdateFlag = -1;
			while (ti < tempLine)
			{
				//==========================================
				for (chindex = 0; chindex < tempCh; chindex++)
				{
					//sch= (short int)(PacketDatum[r]*256);//(~((PacketDatum[r]*256)))+1;
					sch = (short int)(~((vknextmc->PacketDatum[r] * 256))) + 1;
					tempdat = sch;					
					vknextmc->CHSrcHexBuffer[chindex][vknextmc->SaveShowPI] = tempdat;
					vknextmc->CHShowBuffer[chindex][vknextmc->SaveShowPI] = (((tempdat)*14.652) / 0x8000) / vknextmc->PGAGainRange[chindex];
					r++;
				}
				while (chindex < 8)
				{
					vknextmc->CHSrcHexBuffer[chindex][vknextmc->SaveShowPI] = 0;
					vknextmc->CHShowBuffer[chindex][vknextmc->SaveShowPI] = 0;
					chindex++;
				}
				/////////////////////////
				ti++;
				vknextmc->SaveShowPI++;
				if (vknextmc->SaveShowPI>_DISP_MAX_LEN)
				{
					vknextmc->SaveShowPI = 0;
					//exit;
				}
			}
		}
		else if ((vknextmc->PacketDatum[4] & 0xF0) == 0x20)  // double byte
		{
			tempCh = vknextmc->PacketDatum[4] & 0x0F;
			packagelen = packagelen - 4;
			tempLine = packagelen / tempCh;
			tempLine = tempLine >> 1;   // div
			//=================================
			//if( UpdateDataFormatFlag==1 )
			//{
			// printf("数据格式16位,共[%d]通道,[%d]采样点",tempCh,tempLine);
			//	Sampling_Channel=tempCh;
			//    UpdateDataFormatFlag=0;
			//}
			r = 5;
			ti = 0;
			vknextmc->IOUpdateFlag = -1;
			while (ti <  tempLine)
			{
				//==========================================
				for (chindex = 0; chindex< tempCh; chindex++)
				{
					//sch= (short int)(PacketDatum[r]+ (PacketDatum[r+1]*256));//(~(PacketDatum[r]+ (PacketDatum[r+1]*256)))+1;
					sch = (short int)(~(vknextmc->PacketDatum[r] + (vknextmc->PacketDatum[r + 1] * 256))) + 1;
					tempdat = sch;
					vknextmc->CHSrcHexBuffer[chindex][vknextmc->SaveShowPI] = tempdat;
					vknextmc->CHShowBuffer[chindex][vknextmc->SaveShowPI] = (((tempdat)*14.652) / 0x8000) / vknextmc->PGAGainRange[chindex];
					r = r + 2;
				}
				while (chindex < 8)
				{
					vknextmc->CHSrcHexBuffer[chindex][vknextmc->SaveShowPI] = 0;
					vknextmc->CHShowBuffer[chindex][vknextmc->SaveShowPI] = 0;
					chindex++;
				}
				//=========================================
				ti++;
				vknextmc->SaveShowPI++;
				if (vknextmc->SaveShowPI>_DISP_MAX_LEN)
				{
					vknextmc->SaveShowPI = 0;
					//exit;
				}
			}
			//--------------------
		}
		else if ((vknextmc->PacketDatum[4] & 0xF0) == 0x30) // 4 byte
		{
			tempCh = vknextmc->PacketDatum[4] & 0x0F;
			packagelen = packagelen - 4;
			tempLine = packagelen / tempCh;
			tempLine = tempLine >> 2;
			//if( UpdateDataFormatFlag==1 ) //  System_Channel <> tempCh
			//{
			// printf("数据格式24位,共[%d]通道,[%d]采样点",tempCh,tempLine);
			///	Sampling_Channel=tempCh;
			//    UpdateDataFormatFlag=0;
			//}
			r = 5;
			ti = 0;
			/////////////////////////////////////////////////////////////
			//IOStaus[4];//PacketDatum[r+2]
			//if ((PacketDatum[8] & 0x10) == 0x10)IOStaus[1] = 1;
			//else IOStaus[1] = 0;
			//------------------------------------------------------------
			//if ((PacketDatum[8] & 0x20) == 0x20)IOStaus[2] = 1;
			//else IOStaus[2] = 0;

			vknextmc->IOUpdateFlag = 1;
			/////////////////////////////////////////////////////////////
			while (ti <  tempLine)
			{
				//IO2 固定在 8通道上， IO3固定9通道
				if ((vknextmc->PacketDatum[r + 3] & 0x10) == 0x10)vknextmc->CHShowBuffer[8][vknextmc->SaveShowPI] = 1;
				else vknextmc->CHShowBuffer[8][vknextmc->SaveShowPI] = 0;
				if ((vknextmc->PacketDatum[r + 3] & 0x20) == 0x20)vknextmc->CHShowBuffer[9][vknextmc->SaveShowPI] = 1;
				else vknextmc->CHShowBuffer[9][vknextmc->SaveShowPI] = 0;
				//==========================================
				for (chindex = 0; chindex< tempCh; chindex++)
				{
					//tempdat=  PacketDatum[r]*0x100+ (PacketDatum[r+1]*0x10000)+ (PacketDatum[r+2]*0x1000000);//(~ (PacketDatum[r]*0x100+ (PacketDatum[r+1]*0x10000)+ (PacketDatum[r+2]*0x1000000)))+1;
					tempdat = (~(vknextmc->PacketDatum[r] * 0x100 + (vknextmc->PacketDatum[r + 1] * 0x10000) + (vknextmc->PacketDatum[r + 2] * 0x1000000))) + 1;
					tempdat = tempdat / 0x100;
					vknextmc->CHSrcHexBuffer[chindex][vknextmc->SaveShowPI] = tempdat;
					vknextmc->CHShowBuffer[chindex][vknextmc->SaveShowPI] = (((tempdat)*14.652) / 0x800000) / vknextmc->PGAGainRange[chindex];
					r = r + 4;
				}
				while (chindex < 8)
				{
					vknextmc->CHSrcHexBuffer[chindex][vknextmc->SaveShowPI] = 0;
					vknextmc->CHShowBuffer[chindex][vknextmc->SaveShowPI] = 0;
					chindex++;
				}
				//////////////////////////////////////////

				//=========================================
				ti++;
				vknextmc->SaveShowPI++;
				if (vknextmc->SaveShowPI>_DISP_MAX_LEN)
				{
					vknextmc->SaveShowPI = 0;
					//exit;
				}
			}
		}
		else if ((vknextmc->PacketDatum[4] & 0xF0) == 0x40) // 4 byte
		{
			tempCh = vknextmc->PacketDatum[4] & 0x0F;
			packagelen = packagelen - 4;
			tempLine = packagelen / tempCh;
			tempLine = tempLine >> 2;
			//if( UpdateDataFormatFlag==1 )  //System_Channel <> tempCh
			//{
			// printf("数据格式32位,共[%d]通道,[%d]采样点",tempCh,tempLine);
			//	Sampling_Channel=tempCh;
			//    UpdateDataFormatFlag=0;
			//}	
			////////////////
			r = 5;
			ti = 0;
			vknextmc->IOUpdateFlag = -1;
			while (ti <  tempLine)
			{
				if (vknextmc->SaveShowPI>_DISP_MAX_LEN)
				{
					vknextmc->SaveShowPI = 0;
				}
				//==========================================
				for (chindex = 0; chindex < tempCh; chindex++)
				{
					//tempdat= (PacketDatum[r+1]*0x100)+ (PacketDatum[r+2]*0x10000)+ (PacketDatum[r+3]*0x1000000);//(~ ((PacketDatum[r+1]*0x100)+ (PacketDatum[r+2]*0x10000)+ (PacketDatum[r+3]*0x1000000)))+1;
					tempdat = (~((vknextmc->PacketDatum[r + 1] * 0x100) + (vknextmc->PacketDatum[r + 2] * 0x10000) + (vknextmc->PacketDatum[r + 3] * 0x1000000))) + 1;
					tempdat = tempdat / 0x100;
					vknextmc->CHSrcHexBuffer[chindex][vknextmc->SaveShowPI] = tempdat;
					vknextmc->CHShowBuffer[chindex][vknextmc->SaveShowPI] = (((tempdat)*14.652) / 0x800000) / vknextmc->PGAGainRange[chindex];
					r = r + 4;
				}
				while (chindex < 8)
				{
					vknextmc->CHSrcHexBuffer[chindex][vknextmc->SaveShowPI] = 0;
					vknextmc->CHShowBuffer[chindex][vknextmc->SaveShowPI] = 0;
					chindex++;
				}
				//==========================================
				ti++;
				vknextmc->SaveShowPI++;
				if (vknextmc->SaveShowPI>_DISP_MAX_LEN)
				{
					vknextmc->SaveShowPI = 0;
				}
			}
		}
		///////////////////////////////////////////////////////////////////////////////////////////
		///////////////////////////////////////////////////////////////////////////////////////////
		///////////////////////////////////////////////////////////////////////////////////////////
	}
	else // 4.00 mode,  VK701N,VK701, VK701NSD
	{
		///////////////////////////////////////////////////////////////////////////////////////////
		///////////////////////////////////////////////////////////////////////////////////////////
		///////////////////////////////////////////////////////////////////////////////////////////
		packagelen = vknextmc->PacketDatum[0] & 0x7F;
		packagelen = (packagelen << 8) + vknextmc->PacketDatum[1];
		//printf("数据格式16位,共[%d]通道,[%d]采样点\n",packagelen,PacketDatum[4]);
		//----------------------
		if ((vknextmc->PacketDatum[4] & 0xF0) == 0x10) // signal byte
		{
			tempCh = vknextmc->PacketDatum[4] & 0x0F; //PacketDatum
			packagelen = packagelen - 4;
			tempLine = packagelen / tempCh;
			//if( UpdateDataFormatFlag==1 )    //  System_Channel <> tempCh
			//{
			//   printf("数据格式8位,共[%d]通道,[%d]采样点",tempCh,tempLine);
			//	Sampling_Channel=tempCh;
			//    UpdateDataFormatFlag=1;
			//}
			r = 5;
			ti = 0;
			vknextmc->IOUpdateFlag = -1;
			while (ti < tempLine)
			{
				//==========================================
				for (chindex = 0; chindex < tempCh; chindex++)
				{
					sch = (short int)(vknextmc->PacketDatum[r] * 256);//(~((PacketDatum[r]*256)))+1;
					//sch= (short int)(~((PacketDatum[r]*256)))+1;
					tempdat = sch;
					vknextmc->CHSrcHexBuffer[chindex][vknextmc->SaveShowPI] = tempdat;
					//CHShowBuffer[chindex][SaveShowPI]= (((tempdat)*14.652)/0x8000)/PGAGainRange[chindex];
					vknextmc->CHShowBuffer[chindex][vknextmc->SaveShowPI] = (((tempdat)*4.000) / 0x8000) / vknextmc->PGAGainRange[chindex];
					r++;
				}
				while (chindex < 8)
				{
					vknextmc->CHSrcHexBuffer[chindex][vknextmc->SaveShowPI] = 0;
					vknextmc->CHShowBuffer[chindex][vknextmc->SaveShowPI] = 0;
					chindex++;
				}
				/////////////////////////
				ti++;
				vknextmc->SaveShowPI++;
				if (vknextmc->SaveShowPI>_DISP_MAX_LEN)
				{
					vknextmc->SaveShowPI = 0;
					//exit;
				}
			}
		}
		else if ((vknextmc->PacketDatum[4] & 0xF0) == 0x20)  // double byte
		{
			tempCh = vknextmc->PacketDatum[4] & 0x0F;
			packagelen = packagelen - 4;
			tempLine = packagelen / tempCh;
			tempLine = tempLine >> 1;   // div
			//=================================
			//if( UpdateDataFormatFlag==1 )
			//{
			// printf("数据格式16位,共[%d]通道,[%d]采样点",tempCh,tempLine);
			//	Sampling_Channel=tempCh;
			//    UpdateDataFormatFlag=0;
			//}
			r = 5;
			ti = 0;
			vknextmc->IOUpdateFlag = -1;
			while (ti <  tempLine)
			{
				//==========================================
				for (chindex = 0; chindex< tempCh; chindex++)
				{
					sch = (short int)(vknextmc->PacketDatum[r] + (vknextmc->PacketDatum[r + 1] * 256));//(~(PacketDatum[r]+ (PacketDatum[r+1]*256)))+1;
					//sch= (short int)(~(PacketDatum[r]+ (PacketDatum[r+1]*256)))+1;
					tempdat = sch;
					vknextmc->CHSrcHexBuffer[chindex][vknextmc->SaveShowPI] = tempdat;
					//CHShowBuffer[chindex][SaveShowPI]= (((tempdat)*14.652)/0x8000)/PGAGainRange[chindex];
					vknextmc->CHShowBuffer[chindex][vknextmc->SaveShowPI] = (((tempdat)*4.000) / 0x8000) / vknextmc->PGAGainRange[chindex];
					r = r + 2;
				}
				while (chindex < 8)
				{
					vknextmc->CHSrcHexBuffer[chindex][vknextmc->SaveShowPI] = 0;
					vknextmc->CHShowBuffer[chindex][vknextmc->SaveShowPI] = 0;
					chindex++;
				}
				//=========================================
				ti++;
				vknextmc->SaveShowPI++;
				if (vknextmc->SaveShowPI>_DISP_MAX_LEN)
				{
					vknextmc->SaveShowPI = 0;
					//exit;
				}
			}
			//--------------------
		}
		else if ((vknextmc->PacketDatum[4] & 0xF0) == 0x30) // 4 byte
		{
			tempCh = vknextmc->PacketDatum[4] & 0x0F;
			packagelen = packagelen - 4;
			tempLine = packagelen / tempCh;
			tempLine = tempLine >> 2;
			//if( UpdateDataFormatFlag==1 ) //  System_Channel <> tempCh
			//{
			// printf("数据格式24位,共[%d]通道,[%d]采样点",tempCh,tempLine);
			///	Sampling_Channel=tempCh;
			//    UpdateDataFormatFlag=0;
			//}
			r = 5;
			ti = 0;
			vknextmc->IOUpdateFlag = 1;
			while (ti <  tempLine)
			{
				//==========================================
				if (tempCh == 4)
				{
					//------------------------------------------
					//IO2 固定在 8通道上， IO3固定9通道
					if ((vknextmc->PacketDatum[r] & 0x10) == 0x10)vknextmc->CHShowBuffer[8][vknextmc->SaveShowPI] = 1;
					else vknextmc->CHShowBuffer[8][vknextmc->SaveShowPI] = 0;
					if ((vknextmc->PacketDatum[r] & 0x20) == 0x20)vknextmc->CHShowBuffer[9][vknextmc->SaveShowPI] = 1;
					else vknextmc->CHShowBuffer[9][vknextmc->SaveShowPI] = 0;
					//----------------------------------------------------
					//00 22 FF 00 D0 F8 F2 FF FF F4 9F F3 FA FF FF 2F
					//      FFF8D0      FFF2F4     FFF39F FFFA2F
					r = r + 2;
					tempdat = vknextmc->PacketDatum[r] * 0x1000000 + (vknextmc->PacketDatum[r + 3] * 0x10000) + (vknextmc->PacketDatum[r + 2] * 0x100);//(~(PacketDatum[r]*0x1000000+ (PacketDatum[r+3]*0x10000)+ (PacketDatum[r+2]*0x100)))+1;
					//tempdat= (~(PacketDatum[r]*0x1000000+ (PacketDatum[r+3]*0x10000)+ (PacketDatum[r+2]*0x100)))+1;
					tempdat = tempdat / 0x100;
					vknextmc->CHSrcHexBuffer[0][vknextmc->SaveShowPI] = tempdat;
					vknextmc->CHShowBuffer[0][vknextmc->SaveShowPI] = (((tempdat)*4.00) / 0x800000) / vknextmc->PGAGainRange[0];
					r = r + 4;
					//---------------------
					tempdat = vknextmc->PacketDatum[r + 3] * 0x100 + (vknextmc->PacketDatum[r] * 0x10000) + (vknextmc->PacketDatum[r + 1] * 0x1000000);//(~ (PacketDatum[r+3]*0x100+ (PacketDatum[r]*0x10000)+ (PacketDatum[r+1]*0x1000000)))+1;
					//tempdat= (~ (PacketDatum[r+3]*0x100+ (PacketDatum[r]*0x10000)+ (PacketDatum[r+1]*0x1000000)))+1;
					tempdat = tempdat / 0x100;
					vknextmc->CHSrcHexBuffer[1][vknextmc->SaveShowPI] = tempdat;
					vknextmc->CHShowBuffer[1][vknextmc->SaveShowPI] = (((tempdat)*4.00) / 0x800000) / vknextmc->PGAGainRange[1];
					r = r + 2;
					//------------------
					tempdat = vknextmc->PacketDatum[r + 2] * 0x100 + (vknextmc->PacketDatum[r + 3] * 0x10000) + (vknextmc->PacketDatum[r] * 0x1000000);//(~ (PacketDatum[r+2]*0x100+ (PacketDatum[r+3]*0x10000)+ (PacketDatum[r]*0x1000000)))+1;
					//tempdat= (~ (PacketDatum[r+2]*0x100+ (PacketDatum[r+3]*0x10000)+ (PacketDatum[r]*0x1000000)))+1;
					tempdat = tempdat / 0x100;
					vknextmc->CHSrcHexBuffer[2][vknextmc->SaveShowPI] = tempdat;
					vknextmc->CHShowBuffer[2][vknextmc->SaveShowPI] = (((tempdat)*4.00) / 0x800000) / vknextmc->PGAGainRange[2];
					r = r + 4;
					//------------------
					tempdat = vknextmc->PacketDatum[r + 3] * 0x100 + (vknextmc->PacketDatum[r] * 0x10000) + (vknextmc->PacketDatum[r + 1] * 0x1000000);//(~ (PacketDatum[r+2]*0x100+ (PacketDatum[r+3]*0x10000)+ (PacketDatum[r]*0x1000000)))+1;
					//tempdat= (~ (PacketDatum[r+3]*0x100+ (PacketDatum[r]*0x10000)+ (PacketDatum[r+1]*0x1000000)))+1;
					tempdat = tempdat / 0x100;
					vknextmc->CHSrcHexBuffer[3][vknextmc->SaveShowPI] = tempdat;
					vknextmc->CHShowBuffer[3][vknextmc->SaveShowPI] = (((tempdat)*4.00) / 0x800000) / vknextmc->PGAGainRange[3];
					r = r + 4;
				}
				else
				{
					//IO2 固定在 8通道上， IO3固定9通道
					if ((vknextmc->PacketDatum[r + 3] & 0x10) == 0x10)vknextmc->CHShowBuffer[8][vknextmc->SaveShowPI] = 1;
					else vknextmc->CHShowBuffer[8][vknextmc->SaveShowPI] = 0;
					if ((vknextmc->PacketDatum[r + 3] & 0x20) == 0x20)vknextmc->CHShowBuffer[9][vknextmc->SaveShowPI] = 1;
					else vknextmc->CHShowBuffer[9][vknextmc->SaveShowPI] = 0;
					//====================================================
					for (chindex = 0; chindex< tempCh; chindex++)
					{
						tempdat = vknextmc->PacketDatum[r] * 0x100 + (vknextmc->PacketDatum[r + 1] * 0x10000) + (vknextmc->PacketDatum[r + 2] * 0x1000000);//(~ (PacketDatum[r]*0x100+ (PacketDatum[r+1]*0x10000)+ (PacketDatum[r+2]*0x1000000)))+1;
						//tempdat=  (~ (PacketDatum[r]*0x100+ (PacketDatum[r+1]*0x10000)+ (PacketDatum[r+2]*0x1000000)))+1;
						tempdat = tempdat / 0x100;
						//CHShowBuffer[chindex][SaveShowPI]= (((tempdat)*14.652)/0x800000)/PGAGainRange[chindex];
						vknextmc->CHSrcHexBuffer[chindex][vknextmc->SaveShowPI] = tempdat;
						vknextmc->CHShowBuffer[chindex][vknextmc->SaveShowPI] = (((tempdat)*4.000) / 0x800000) / vknextmc->PGAGainRange[chindex];
						r = r + 4;
					}
					while (chindex < 8)
					{
						vknextmc->CHSrcHexBuffer[chindex][vknextmc->SaveShowPI] = 0;
						vknextmc->CHShowBuffer[chindex][vknextmc->SaveShowPI] = 0;
						chindex++;
					}
				}
				//=========================================
				ti++;
				vknextmc->SaveShowPI++;
				if (vknextmc->SaveShowPI>_DISP_MAX_LEN)
				{
					vknextmc->SaveShowPI = 0;
					//exit;
				}
			}
		}
		else if ((vknextmc->PacketDatum[4] & 0xF0) == 0x40) // 4 byte
		{
			tempCh = vknextmc->PacketDatum[4] & 0x0F;
			packagelen = packagelen - 4;
			tempLine = packagelen / tempCh;
			tempLine = tempLine >> 2;
			//if( UpdateDataFormatFlag==1 )  //System_Channel <> tempCh
			//{
			// printf("数据格式32位,共[%d]通道,[%d]采样点",tempCh,tempLine);
			//	Sampling_Channel=tempCh;
			//    UpdateDataFormatFlag=0;
			//}
			r = 5;
			ti = 0;
			vknextmc->IOUpdateFlag = -1;
			while (ti <  tempLine)
			{
				//==========================================
				for (chindex = 0; chindex< tempCh; chindex++)
				{
					tempdat = (vknextmc->PacketDatum[r + 1] * 0x100) + (vknextmc->PacketDatum[r + 2] * 0x10000) + (vknextmc->PacketDatum[r + 3] * 0x1000000);//(~ ((PacketDatum[r+1]*0x100)+ (PacketDatum[r+2]*0x10000)+ (PacketDatum[r+3]*0x1000000)))+1;
					//tempdat= (~ ((PacketDatum[r+1]*0x100)+ (PacketDatum[r+2]*0x10000)+ (PacketDatum[r+3]*0x1000000)))+1;
					tempdat = tempdat / 0x100;
					vknextmc->CHSrcHexBuffer[chindex][vknextmc->SaveShowPI] = tempdat;
					//CHShowBuffer[chindex][SaveShowPI]= (((tempdat)*14.652)/0x800000)/PGAGainRange[chindex];
					vknextmc->CHShowBuffer[chindex][vknextmc->SaveShowPI] = (((tempdat)*4.000) / 0x800000) / vknextmc->PGAGainRange[chindex];
					r = r + 4;
				}
				while (chindex < 8)
				{
					vknextmc->CHSrcHexBuffer[chindex][vknextmc->SaveShowPI] = 0;
					vknextmc->CHShowBuffer[chindex][vknextmc->SaveShowPI] = 0;
					chindex++;
				}
				//==========================================
				ti++;
				vknextmc->SaveShowPI++;
				if (vknextmc->SaveShowPI>_DISP_MAX_LEN)
				{
					vknextmc->SaveShowPI = 0;
				}
			}
		}
		///////////////////////////////////////////////////////////////////////////////////////////
		///////////////////////////////////////////////////////////////////////////////////////////
		///////////////////////////////////////////////////////////////////////////////////////////
	}
}

/*
typedef struct VK70xNMC_AdddtionalFeature
{   //mbytes(6) = vCOM_CMD_RW_IO
//len = mbytes(2) * 256 + mbytes(3) + 4
//If (ReadTaskIndex = NEXTTASK_TEMP) And (len > 24) Then
unsigned char UpdateFlag;
unsigned int IO[4];//bytes(21-24)
double DAC[2];
unsigned int PWMFreq[2];
double PWMDuty[2];
unsigned int Excounter; //i = mbytes(25) * &H1000000 + mbytes(26) * &H10000 + mbytes(27) * &H100 + mbytes(28)	"计数器
double Temp; //i = mbytes(29) * &H100 + mbytes(30)摄氏度 ; i = i / 100
//mbytes(7) = &H22 设置成功
}TypeDefVK70xNMCAdddtionalFeature;//TypeDefVK70xNMCAdddtionalFeature     VKFuntionPara[MAX_RX_CARD_NUM];
*/


unsigned char Set_ChannelVoltageRange(unsigned char refvol, unsigned char pga, unsigned char adc)
{
	if ((refvol == 1) || (refvol == 4) || (refvol == 0x10))
	{
		if ((pga == 1) && (adc == 0)) return 0;
		if ((pga == 2) && (adc == 0)) return 1;
		if ((pga == 3) && (adc == 0)) return 2;
		if ((pga == 4) && (adc == 0)) return 3;
		if ((pga == 5) && (adc == 0)) return 4;
		if ((pga == 7) && (adc == 0)) return 5;
		if ((pga == 10) && (adc == 0)) return 6;
		if ((pga == 10) && (adc == 4)) return 7;
	}
	else
	{
		if ((adc == 0)) return 0;
		if ((adc == 1)) return 1;
		if ((adc == 2)) return 2;
		if ((adc == 3)) return 3;
	}
	return 0;
}

int ConvertSystemMode2DLLDefine(int modeval)
{
	int trmode;
	if ((modeval == 0) || (modeval == 0x80) || (modeval == 0x81))
	{
		trmode = VKxxx_MODE_RTTX_SAMPLING;
	}
	else if ((modeval == 1) || (modeval == 0x8A))
	{
		trmode = VKxxx_MODE_RTSAVE_SAMPLING;
	}
	else if ((modeval == 2) || (modeval == 0x8B))
	{
		trmode = VKxxx_MODE_DOWNLOADFILE;
	}
	else if ((modeval == 3) || (modeval == 0x8F))
	{
		trmode = VKxxx_MODE_FACOTRY;
	}
	else
	{
		trmode = VKxxx_MODE_RTTX_SAMPLING;
	}
	return trmode;
}


int ConvertSampleMethod2DLLDefine(int samplemethod)
{
	int trmethod;
	if ((samplemethod == 0) || (samplemethod == 0x01))
	{
		trmethod = VKxxx_SAMLEMETHOD_CONTIMUE;
	}
	else if ((samplemethod == 12) || (samplemethod == 0x12) || (samplemethod == 0x80))
	{
		trmethod = VKxxx_SAMLEMETHOD_IO4_NPOINTS;
	}
	else if ((samplemethod == 13) || (samplemethod == 0x13) || (samplemethod == 0x99))
	{
		trmethod = VKxxx_SAMLEMETHOD_IO4_ASADCCLOCK;
	}
	else if ((samplemethod == 21) || (samplemethod == 0x21) || (samplemethod == 0x9A))
	{
		trmethod = VKxxx_SAMLEMETHOD_TIMER_NPOINTS;
	}
	else
	{
		trmethod = VKxxx_SAMLEMETHOD_CONTIMUE;
	}
	return trmethod;
}


int ConvertSdFileFormat2DLLDefine(int sdfilefmt)
{
	int trfilrfmt;
	if ((sdfilefmt == 11) || (sdfilefmt == 0x11) || (sdfilefmt == 0x01))
	{
		trfilrfmt = VKxxx_SDFILEFMT_TEXT;
	}
	else
	{
		trfilrfmt = VKxxx_SDFILEFMT_BIN;
	}
	return trfilrfmt;
}
//////////////////////////////////////////////////////////////////////////////////
//void SaveAndDisplayInformation_LEN(TypeDefVK70xNMCPara *vknextmc)
void DisposalExternalFunctionInformation(TypeDefVK70xNMCPara *vknextmc)
{
	int tlen = 0;
	int i, tindex = 0;
	int  stempval = 0;
	unsigned char cmd, tempb, tempu8;
	unsigned int  tempval = 0;
	double tempdbval = 0;
	tlen = vknextmc->PacketDatum[0] & 0x7F;
	tlen = (tlen << 8) + vknextmc->PacketDatum[1];
	//PacketDatum[2] ans PacketDatum[3]  == [10 01] 固定编码
	cmd = vknextmc->PacketDatum[4];// Command
	//#define vCOM_CMD_RW_ADC        0x81  //
	//#define vCOM_CMD_RW_IO         0x90  // write and read the IO,pWM, DAC, counter, temperature   
	//#define vCOM_CMD_RW_MODE       0x91  // write and read mode  
	//#define vCOM_CMD_RW_SYSTEM     0xA0  //
	//TypeDefVK70xNMCAdddtionalFeature;//TypeDefVK70xNMCAdddtionalFeature     VKFuntionPara[MAX_RX_CARD_NUM];
	//mbytes(6) = vCOM_CMD_RW_IO
	//len = mbytes(2) * 256 + mbytes(3) + 4
	//If (ReadTaskIndex = NEXTTASK_TEMP) And (len > 24) Then
	//mbytes(7) = &H22 设置成功
	//-----------------------------------------------------------
	//unsigned char UpdateFlag;
	//unsigned int IO[4];//bytes(21-24)
	//double DAC[2];
	//unsigned int PWMFreq[2];
	//double PWMDuty[2];
	//unsigned int Excounter; //i = mbytes(25) * &H1000000 + mbytes(26) * &H10000 + mbytes(27) * &H100 + mbytes(28)	"计数器
	//double Temp; //i = mbytes(29) * &H100 + mbytes(30)摄氏度 ; i = i / 100
	//////////////////////////////////////////////////////
	switch (cmd)
	{
	case vCOM_CMD_RW_ADC:// 
		if (tlen > 20)
		{
			vknextmc->UpdateFlag = 0;
			tindex = 5;
			tempb = vknextmc->PacketDatum[13];//
			for (i = 0; i < 8; i++)
			{
				//第 16 字节是参考电源，其中 VK702N 固定为 0，表示 2.442V；
				vknextmc->VolRange[i] = Set_ChannelVoltageRange(tempb, vknextmc->PacketDatum[5 + i], vknextmc->PacketDatum[9 + i]);
			}
			vknextmc->ReferenceVoltage = tempb;
			//---------------------			
			tindex = 14;//14
			// 第 17 字节为保留位，数据无意义;
			vknextmc->SampleDataFormat = vknextmc->PacketDatum[tindex];//
			//--------------------- 15-18
			tindex = 15;//15~17
			stempval = (int)vknextmc->PacketDatum[tindex] * 0x10000 + (int)vknextmc->PacketDatum[tindex + 1] * 0x100 + vknextmc->PacketDatum[tindex + 2];
			vknextmc->SampleRate = stempval;
			tindex = 18;
			//stempval = (int)vknextmc->PacketDatum[tindex] * 0x1000000 + (int)vknextmc->PacketDatum[tindex + 1] * 0x10000 + (int)vknextmc->PacketDatum[tindex + 2] * 0x100 + vknextmc->PacketDatum[tindex + 3];
			//vknextmc->Npoints = stempval;//15-18
			// 采样模式; 0x00: 停止/待采样模式 
			//           0x01： 连续采样模式；0x02：单次N点采样模式  
			//           0x11： IO4触发连续采样模式；0x12：IO4触发单次N点采样模式  0x13： IO4作为采样时钟采样模式; 
			//           0x21： 定时进行一次N点采样
			//if (stempval == 0)vknextmc->SampleComand = 0x01;
			//else if (stempval == 1)vknextmc->SampleComand = 0x00;
			//else vknextmc->SampleComand = 0x02;
			//-----------------------------------
		}
		break;
	case vCOM_CMD_RW_IO://len 大于24
		if (tlen > 24)
		{
			vknextmc->UpdateFlag = 0;
			//unsigned int tempval = 0;
			//double tempdbval = 0;
			//----------------------PWM
			//tempval=
			vknextmc->PWMFreq[0] = (unsigned int)vknextmc->PacketDatum[5] * 0x10000 + vknextmc->PacketDatum[6] * 0x100 + vknextmc->PacketDatum[7];
			tempval = (unsigned int)vknextmc->PacketDatum[8] * 0x100 + vknextmc->PacketDatum[9];
			tempdbval = (double)tempval / 10;//实际占空比 * 10， 0.0~100.0%
			vknextmc->PWMDuty[0] = tempdbval;
			vknextmc->PWMFreq[1] = (unsigned int)vknextmc->PacketDatum[10] * 0x10000 + vknextmc->PacketDatum[11] * 0x100 + vknextmc->PacketDatum[12];
			tempval = (unsigned int)vknextmc->PacketDatum[13] * 0x100 + vknextmc->PacketDatum[14];
			tempdbval = (double)tempval / 10;//实际占空比 * 10， 0.0~100.0%
			vknextmc->PWMDuty[1] = tempdbval;
			//------------------------DAC
			tempval = (unsigned int)vknextmc->PacketDatum[15] * 0x100 + vknextmc->PacketDatum[16];
			tempdbval = (double)tempval * 33;//DAC * 3.3/1024
			tempdbval = tempdbval / 10240;// unit = v
			vknextmc->DAC[0] = tempdbval;
			tempval = (unsigned int)vknextmc->PacketDatum[17] * 0x100 + vknextmc->PacketDatum[18];
			tempdbval = (double)tempval * 33;//DAC * 3.3/1024
			tempdbval = tempdbval / 10240;// unit = v
			vknextmc->DAC[1] = tempdbval;
			//-----------------------IO
			vknextmc->IO[0] = vknextmc->PacketDatum[19];
			vknextmc->IO[1] = vknextmc->PacketDatum[20];
			vknextmc->IO[2] = vknextmc->PacketDatum[21];
			vknextmc->IO[3] = vknextmc->PacketDatum[22];
			//----------------------Counter
			vknextmc->Excounter = (unsigned int)vknextmc->PacketDatum[23] * 0x1000000 + vknextmc->PacketDatum[24] * 0x10000 + vknextmc->PacketDatum[25] * 0x100 + vknextmc->PacketDatum[26];
			//---------------------temperature
			tempval = (unsigned int)vknextmc->PacketDatum[27] * 0x100 + vknextmc->PacketDatum[28];
			tempdbval = (double)tempval / 100;//12.34
			vknextmc->Temp = tempdbval;
			//-------------------------
			stempval = (int)vknextmc->PacketDatum[29] * 0x1000000 + vknextmc->PacketDatum[30] * 0x10000 + vknextmc->PacketDatum[31] * 0x100 + vknextmc->PacketDatum[32];
			vknextmc->ExTemp = (double)stempval / 10;
			stempval = (int)vknextmc->PacketDatum[33] * 0x1000000 + vknextmc->PacketDatum[34] * 0x10000 + vknextmc->PacketDatum[35] * 0x100 + vknextmc->PacketDatum[36];
			vknextmc->ExHumidity = (double)stempval / 10;
		}
		else
		{
			//if (vknextmc->PacketDatum[5] ==0x22)
			//else if (vknextmc->PacketDatum[5] == 0x44)
		}
		break;
	case vCOM_CMD_RW_MODE:
		vknextmc->UpdateFlag = 0;
		tindex = 5;
		if (tlen > 6)
		{
			vknextmc->WorkMode = ConvertSystemMode2DLLDefine((int)vknextmc->PacketDatum[tindex++]);
			vknextmc->SampleComand = ConvertSampleMethod2DLLDefine((int)vknextmc->PacketDatum[tindex++]);// function select mode, 0 : normal,  0x80(0x80): IO trig ADC Mode, 0x81(7E)	= 	SysInfor.Mode
			vknextmc->SDFileFormat = ConvertSdFileFormat2DLLDefine((int)vknextmc->PacketDatum[tindex++]);//1-8
			if (vknextmc->PacketDatum[tindex++] == 0x22)
			{
				// return time
			}
		}
		break;
	case vCOM_CMD_RW_SYSTEM:
		if (tlen >= 18)
		{
			vknextmc->UpdateFlag = 0;
			tindex = 5;
			//----------------------
			//// 6+6+6+1+16+1=36
			for (i = 0; i < 6; i++)vknextmc->ModelName[i] = vknextmc->PacketDatum[tindex++];// 6bytes ,model number 1-6	
			vknextmc->ModelName[6] = '\0';
			for (i = 0; i < 6; i++)vknextmc->HWVer[i] = vknextmc->PacketDatum[tindex++];// 6 bytes , HW 7-12
			vknextmc->HWVer[6] = '\0';
			for (i = 0; i < 6; i++)vknextmc->SWVer[i] = vknextmc->PacketDatum[tindex++];// 6 bytes, SW 13-18
			vknextmc->SWVer[6] = '\0';			
			if (tlen >= 72)
			{
				//------------------------
				tindex++;// fixed byte  19, 0x22
				//-----------------------
				for (i = 0; i < 16; i++)vknextmc->SN[i] = vknextmc->PacketDatum[tindex++];// 16 bytes, sn 20-15
				vknextmc->SN[16] = '\0';
				tindex++;// checksum
				//--------------------- 37
				vknextmc->CommucanitionProtocol = vknextmc->PacketDatum[tindex++];////通讯方式  
				//----------------------
				//// 13+37=50
				vknextmc->WorkMode = ConvertSystemMode2DLLDefine((int)vknextmc->PacketDatum[tindex++]);
				vknextmc->SampleComand = ConvertSampleMethod2DLLDefine((int)vknextmc->PacketDatum[tindex++]);
				vknextmc->SDFileFormat = ConvertSdFileFormat2DLLDefine((int)vknextmc->PacketDatum[tindex++]);//1-8
				//  *txpi++ = (unsigned char)SysInfor.Mode;// = tmode;  38
				//  *txpi++ =  (unsigned char)SysInfor.FuncSel_ADCCLK;// = tselADCCLK; 39
				//  *txpi++ =  (unsigned char)SysInfor.FuncSel_SDSaveMethod;// = tselsaveMethod; 40
				//  RTC_GetFullTime(LPC_RTC,&tptime);	
				//  *txpi++ = 0x22;//41
				//  temp = tptime.YEAR;
				//  *txpi++ = (unsigned char)(temp>>8);//42
				//  *txpi++ = (unsigned char)(temp);//43  
				//  *txpi++ = tptime.MONTH;//44
				//  *txpi++ = tptime.DOM;//45  
				//  *txpi++ = tptime.HOUR;	//46
				//  *txpi++ = tptime.MIN;//47
				//  *txpi++ = tptime.SEC;//48  
				//  *txpi++ = tptime.DOW;//49  
				//  *txpi++ = 0;//50，checksum
				tindex += 10;  // 时间值，先空着
				//================================= 33+3(空白)
				for (i = 0; i < 4; i++)
				{
					vknextmc->VolRange[i] = vknextmc->PacketDatum[tindex++];//1-8
					vknextmc->VolRange[i + 4] = vknextmc->VolRange[i];
				}					
				//---------------------
				vknextmc->ReferenceVoltage = vknextmc->PacketDatum[tindex++];//9
				vknextmc->SampleDataFormat = vknextmc->PacketDatum[tindex++];//10 采样精度
				//--------------------- 11-13
				//(int)vknextmc->ParaDatum[7] * 0x100000 + 
				stempval = (int)vknextmc->PacketDatum[tindex] * 0x10000 + (int)vknextmc->PacketDatum[tindex + 1] * 0x100 + vknextmc->PacketDatum[tindex + 2];
				vknextmc->SampleRate = stempval;
				tindex += 3;
				vknextmc->Channel = vknextmc->PacketDatum[tindex++];//14采集卡上传通道设置（暂保留）
				//------------------- 
				stempval = (int)vknextmc->PacketDatum[tindex] * 0x1000000 + (int)vknextmc->PacketDatum[tindex + 1] * 0x10000 + (int)vknextmc->PacketDatum[tindex + 2] * 0x100 + vknextmc->PacketDatum[tindex + 3];
				vknextmc->Npoints = stempval;//15-18
				tindex += 4;
				stempval = (int)vknextmc->PacketDatum[tindex] * 0x1000000 + (int)vknextmc->PacketDatum[tindex + 1] * 0x10000 + (int)vknextmc->PacketDatum[tindex + 2] * 0x100 + vknextmc->PacketDatum[tindex + 3];
				vknextmc->SDFileIndex = stempval;
				tindex += 4;				
				//=================================
				//vknextmc->ParaDatum[23]=0x22  固定值;//19
				tindex++;
				//char           Cal_RTC_Direction;
				//unsigned int   Cal_RTC_Value;
				vknextmc->Cal_RTC_Direction = vknextmc->PacketDatum[tindex++];
				stempval = (unsigned int)vknextmc->PacketDatum[tindex] * 0x100 + vknextmc->PacketDatum[tindex + 1];
				vknextmc->Cal_RTC_Value = stempval;
				tindex += 2;
				//==============================
			}			
		}
		break;
	case vCOM_CMD_RW_WIFIPARA://        0xA1
		vknextmc->UpdateFlag = 0;
		tindex = 5;
		if (tlen >= 25)
		{
			for (i = 0; i < 4; i++)vknextmc->ServerIP[i] = vknextmc->PacketDatum[tindex++];
			for (i = 0; i < 4; i++)vknextmc->VKIP[i] = vknextmc->PacketDatum[tindex++];
			for (i = 0; i < 4; i++)vknextmc->VKGateWay[i] = vknextmc->PacketDatum[tindex++];
			for (i = 0; i < 4; i++)vknextmc->VKNetMask[i] = vknextmc->PacketDatum[tindex++];

			stempval = (int)vknextmc->PacketDatum[tindex] * 0x100 + vknextmc->PacketDatum[tindex + 1];
			vknextmc->ServerPort = stempval;
			tindex += 2;

			stempval = (int)vknextmc->PacketDatum[tindex] * 0x100 + vknextmc->PacketDatum[tindex + 1];
			vknextmc->VKPort = stempval;
			tindex += 2;

			vknextmc->enetProtocol = vknextmc->PacketDatum[tindex++];
			vknextmc->enetdisconectTime = vknextmc->PacketDatum[tindex++];
			vknextmc->maxecacheTime = vknextmc->PacketDatum[tindex++];

			for (i = 0; i < 6; i++)vknextmc->VKMac[i] = vknextmc->PacketDatum[tindex++];
		}
		break;
	case vCOM_CMD_RW_UDI:
		//unsig////ned char tempu8=0;
		if (tlen > 24)
		{
			vknextmc->UpdateFlag = 0;
			tindex = 5;
			//6bytes model name + 6 bytes sw ver + +6 bytes hw ver + 'SN=['hhhh, hhhh'”'
			//"701NS140119EH10800SN=[xxxxxxxxx]"
			//----------------------
			//// 6+6+6+1+16+1=36
			for (i = 0; i < 6; i++)vknextmc->ModelName[i] = vknextmc->PacketDatum[tindex++];// 6bytes ,model number 1-6	
			vknextmc->ModelName[6] = '\0';
			for (i = 0; i < 6; i++)vknextmc->HWVer[i] = vknextmc->PacketDatum[tindex++];// 6 bytes , HW 7-12
			vknextmc->HWVer[6] = '\0';
			for (i = 0; i < 6; i++)vknextmc->SWVer[i] = vknextmc->PacketDatum[tindex++];// 6 bytes, SW 13-18
			vknextmc->SWVer[6] = '\0';
			//------------------------
			if ((vknextmc->PacketDatum[tindex] == 'S') && (vknextmc->PacketDatum[tindex + 1] == 'N') && (vknextmc->PacketDatum[tindex + 2] == '=') && (vknextmc->PacketDatum[tindex + 3] == '['))
			{
				tindex += 4;
				i = 0;
				while (i < 16)
				{
					tempu8 = vknextmc->PacketDatum[tindex++];
					if (tempu8 == ']')break;
					vknextmc->UDI[i] = tempu8;
					i++;
				}
			}
			//---------------------------
#if (_DEBUG_VK70xxMC_LIB_>0)
			printf("============================================================================\n");
			printf("接收到UDI数据包\n");
			printf("解析项目名称：%s\n", vknextmc->ModelName);
			printf("解析硬件版本号：%s\n", vknextmc->HWVer);
			printf("解析软件版本号：%s\n", vknextmc->SWVer);
			printf("[[[[[[[[[[[[[[[[[[[[[[[");
			for (i = 0; i <= 16; i++)
			{
				printf("%02X ", vknextmc->UDI[i]);
			}
			printf("]]]]]]]]]]]]]]]]]]]]]]]]]]\n");

			for (i = 0; i <= (tlen >> 4); i++)
			{
				for (int j = 0; j < 16; j++)
				{
					printf("%02X ", vknextmc->PacketDatum[i * 16 + j]);
				}
				printf("\n");
			}
			printf("============================================================================\n");
#endif
			//----------------------------
		}
		break;
	default:
		break;
	}
}
//-------------------------------------------------------------------------------

void  DisposalDownloadRXTask_LEN(int mci, TypeDefVK70xNMCPara *vkmc, int len)
{
	//static unsigned int PacketCount=0; 
	unsigned char rxdat;
	unsigned char *bufferpi;
	int i = 0;
	//int templen,trlen=0;
	//----------------------------
	bufferpi = &vkmc->RXLANDatum[vkmc->RXLANReadPI];
	//---------------------------
	if (vkmc->WorkMode == VKxxx_MODE_DOWNLOADFILE)
	{  // 数据下载模式
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
		printf("sDFile_WriteReadSDCardTask采集卡【%d】收到数据长度【%d】[%d]！！\n", mci, vkmc->RXLANReadPI, vkmc->RXLANSavePI);
		printf("sDFile_WriteReadSDCardTask采集卡【%d】收到数据长度【%d】[%d]！！\n", mci, (int)&vkmc->RXLANDatum[vkmc->RXLANReadPI], (int)&vkmc->RXLANDatum[vkmc->RXLANSavePI]);
		printf("sDFile_WriteReadSDCardTask采集卡【%d】收到数据长度【%d】[%d]！！\n", mci, len, (int)bufferpi);
#endif
		sDFile_WriteReadSDCardTask(mci, bufferpi, len);
		// 目前只能支持同时一个sd在线下载， 不同同时支持N采集卡同时下载
	}
	else  // ADC 采样模式
	{
		//while(i<len)
		for (i = 0; i<len; i++)
		{
			if (vkmc->PacketState == 4)
			{
				vkmc->PacketDatum[vkmc->PacketCount++] = *bufferpi++;
				//--------------------
				if (vkmc->PacketCount >= vkmc->PacketLen)
				{
					if (vkmc->PacketDatum[4] < 0x80)
						SaveAndDisplayInformation_LEN(vkmc);
					else
					{
						DisposalExternalFunctionInformation(vkmc);
						//--------------------
						if (vkmc->WorkMode == VKxxx_MODE_DOWNLOADFILE)// 如果模式发生变化， 检查一下sd下载环境
							sDFile_CheckSDCardDownloadCondition(mci);
						//--------------------
					}						
					//-------------------
					//////////////////////	   
					vkmc->PacketState = 0;
					vkmc->PacketLen = 0;
					vkmc->PacketCount = 0;
					//--------------------
				}
				//else 
				//{
				//	vkmc->PacketCheckSum = vkmc->PacketCheckSum + rxdat;   // 校验码
				//}	
				//---------------------
			}
			else //if (vkmc->PacketState<5)
			{
				rxdat = *bufferpi++;//i++;  
				//---------------------
				switch (vkmc->PacketState)
				{
				case 0:	  // 55
					if (rxdat == vCOM_SYSNC_HEADER1)
						vkmc->PacketState = 1;
					break;
				case 1:   // EE
					if (rxdat == vCOM_SYSNC_HEADER2)vkmc->PacketState = 2;
					else if (rxdat == vCOM_SYSNC_HEADER1)vkmc->PacketState = 1;
					else vkmc->PacketState = 0;
					break;
				case 2:	   // len0
					//vkmc->PacketCheckSum = vCOM_SYSNC_HEADER1;
					//vkmc->PacketCheckSum = vkmc->PacketCheckSum + vCOM_SYSNC_HEADER2;
					//vkmc->PacketCheckSum = vkmc->PacketCheckSum + rxdat;
					vkmc->PacketLen = rxdat * 256;
					vkmc->PacketLen = vkmc->PacketLen & 0x7FFF;
					vkmc->PacketState = 3;
					vkmc->PacketDatum[0] = rxdat;//
					//vkmc->PacketCount = 1;
					////////////////////////////////////////
					break;
				case 3:	 //  len 1
					//if DebugSwitch ) TestString=TestString+inttohex(rxdat,2)+' ';
					//vkmc->PacketCheckSum = vkmc->PacketCheckSum + rxdat; 
					vkmc->PacketLen = vkmc->PacketLen + rxdat + 2;  // 128+2 增加自身长度 
					vkmc->PacketState = 4;
					vkmc->PacketDatum[1] = rxdat;
					vkmc->PacketCount = 2;                         // 2  已经包括长度2个字节
					break;
				default:
					vkmc->PacketState = 0;
					vkmc->PacketLen = 0;
					break;
				}
			}
		}// for mulita card
	}// mode
}
