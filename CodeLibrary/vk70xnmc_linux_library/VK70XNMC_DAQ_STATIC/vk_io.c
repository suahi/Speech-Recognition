
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
// IO function
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

int Def_Function_OUTfmt VK70xNMC_Set_AdditionalFeature(int mci, int funcNo, int para1, double para2)
{
	int tstatus;
	int temp = 0xFFFFFFFF;
	unsigned char txbuf[40];
	//////////////////////////////////////////////////////////  
	if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开  

	//if (ThreadRunningState==0)return -11;  //服务未打开  
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -13;
	//////////////////////////////////////////////////////////
	//第1,2字节	同步头	[55 EE]	同步头字节
	//第3,4字节	数据包长度	[80 1D]	数据包长度，高字节在前，低字节在后
	//第5,6字节	机身编号	[10 01]	保留，固定为0x1001机身编号
	//第7字节	命令	[90]	命令
	//---------------------------
	// 功能1
	// pwm freq = 0-100000
	// duty     = 0.1%~100.0%
	//----------------------------
	//  VKxxx_IOFUNCTION_PWM1 = 0x1,//功能1-PWM1
	//	VKxxx_IOFUNCTION_PWM2 = 0x2,//功能2-PWM2
	//	VKxxx_IOFUNCTION_DAC1 = 0x11,//功能11-DAC1
	//	VKxxx_IOFUNCTION_DAC2 = 0x12,//功能12-DAC2
	//	VKxxx_IOFUNCTION_IO = 0x20,//
	//	VKxxx_IOFUNCTION_IO1 = 0x21,//功能21~24-IO1-IO4
	//	VKxxx_IOFUNCTION_IO2 = 0x22,
	//	VKxxx_IOFUNCTION_IO3 = 0x23,
	//	VKxxx_IOFUNCTION_IO4 = 0x24,
	//	VKxxx_IOFUNCTION_COUNTER = 0x31,//功能31 - Counter+Freq
	//	VKxxx_IOFUNCTION_FREQ = 0x32,//功能31 - Counter+Freq
	//	VKxxx_IOFUNCTION_INTMEP = 0x41,//功能41 - temp+humiduty
	//	VKxxx_IOFUNCTION_EXTEMP = 0x42,//功能41 - temp+humiduty
	//第1,2字节	同步头	[55 EE]	同步头字节
	//第3,4字节	数据包长度	[80 1D]	数据包长度，高字节在前，低字节在后
	//第5,6字节	机身编号	[10 01]	保留，固定为0x1001机身编号
	//第7字节	命令	[90]	命令
	//---------------------------
	// 功能1
	// pwm freq = 0-100000
	// duty     = 0.1%~100.0%
	//----------------------------
	if (funcNo == VKxxx_IOFUNCTION_PWM1)
	{
		txbuf[0] = (unsigned char)(para1 / 0x10000);
		txbuf[1] = (unsigned char)(para1 / 0x100);
		txbuf[2] = (unsigned char)(para1);//第8-10字节	PWM1频率	[?? ?? ??]	PWM通道1频率0~1000 000Hz, 高字节在前，低字节在后。
		//---------------------
		temp = (unsigned int)(para2 * 10);
		if (temp>1000) temp = 1000;
		//---------------------
		txbuf[3] = (unsigned char)(temp / 0x100);
		txbuf[4] = (unsigned char)(temp); //第11-12字节	PWM1占空比	[?? ??]	PWM通道1占空比，范围0~1000（对应百分比是0.1%~100.0%）,0xFFFF无效, 高字节在前，低字节在后。
	}
	else
	{
		txbuf[0] = 0xFF;
		txbuf[1] = 0xFF;
		txbuf[2] = 0xFF;//第8-10字节	PWM1频率	[?? ?? ??]	PWM通道1频率0~1000 000Hz, 高字节在前，低字节在后。
		txbuf[3] = 0xFF;
		txbuf[4] = 0xFF;//第11-12字节	PWM1占空比	[?? ??]	PWM通道1占空比，范围0~1000（对应百分比是0.1%~100.0%）,0xFFFF无效, 高字节在前，低字节在后。
	}

	//---------------------------
	// 功能2
	// pwm freq = 0-100000
	// duty     = 0.1%~100.0%
	//----------------------------
	if (funcNo == VKxxx_IOFUNCTION_PWM2)
	{
		txbuf[5] = (unsigned char)(para1 / 0x10000);
		txbuf[6] = (unsigned char)(para1 / 0x100);
		txbuf[7] = (unsigned char)(para1);//第13-15字节	PWM2频率	[?? ?? ??]	PWM通道2频率0~1000 000Hz, 高字节在前，低字节在后。
		temp = (unsigned int)(para2 * 10);
		if (temp>1000) temp = 1000;
		//---------------------
		txbuf[8] = (unsigned char)(temp / 0x100);
		txbuf[9] = (unsigned char)(temp);//第16-17字节	PWM3占空比	[?? ??]	PWM通道2占空比，范围0~1000（对应百分比是0.1%~100.0%）,0xFFFF无效, 高字节在前，低字节在后。
	}
	else
	{
		txbuf[5] = 0xFF;
		txbuf[6] = 0xFF;
		txbuf[7] = 0xFF;//第13-15字节	PWM2频率	[?? ?? ??]	PWM通道2频率0~1000 000Hz, 高字节在前，低字节在后。
		txbuf[8] = 0xFF;
		txbuf[9] = 0xFF;//第16-17字节	PWM3占空比	[?? ??]	PWM通道2占空比，范围0~1000（对应百分比是0.1%~100.0%）,0xFFFF无效, 高字节在前，低字节在后。
	}

	//---------------------------
	// 功能11
	//----------------------------
	if ((funcNo == VKxxx_IOFUNCTION_DAC1) || (funcNo == 11))//11//17
	{
		temp = (unsigned int)((para2 * 1000 * 1024) / 3300);
		if (temp>1023) temp = 1023;
		txbuf[10] = (unsigned char)(temp / 0x100);
		txbuf[11] = (unsigned char)temp;//第18-19字节	DAC通道1	[?? ??]	DAC通道1，范围0~1023对应电压0~3.3V,0xFFFF无效, 高字节在前，低字节在后。
	}
	else
	{
		txbuf[10] = 0xFF;
		txbuf[11] = 0xFF;
	}


	//---------------------------
	// 功能12
	//----------------------------
	if ((funcNo == VKxxx_IOFUNCTION_DAC2) || (funcNo == 12))//12//18
	{
		temp = (unsigned int)((para2 * 1000 * 1024) / 3300);
		if (temp>1023) temp = 1023;
		txbuf[12] = (unsigned char)(temp / 0x100);
		txbuf[13] = (unsigned char)temp;//第18-19字节	DAC通道1	[?? ??]	DAC通道1，范围0~1023对应电压0~3.3V,0xFFFF无效, 高字节在前，低字节在后。
	}
	else
	{
		txbuf[12] = 0xFF;//(unsigned char)(tdac1/0x100);
		txbuf[13] = 0xFF;//(unsigned char)(tdac1/0x100);//第20-21字节	DAC通道2	[?? ??]	DAC通道2，范围0~1023对应电压0~3.3V,0xFFFF无效, 高字节在前，低字节在后。
	}

	//---------------------------
	// 功能21~24  - VKxxx_IOFUNCTION_IO
	//----------------------------
	if (funcNo == 20) //32//20//(funcNo == VKxxx_IOFUNCTION_IO) || 
	{
		txbuf[14] = (unsigned char)(para1 & 0x1);
		txbuf[15] = (unsigned char)((para1 >> 1) & 0x1);
		txbuf[16] = (unsigned char)((para1 >> 2) & 0x1);
		txbuf[17] = (unsigned char)((para1 >> 3) & 0x1);
	}
	else
	{
		if ((funcNo == VKxxx_IOFUNCTION_IO1) || (funcNo == 21))//33//21
		{
			txbuf[14] = (unsigned char)(para1 & 0x3);
		}
		else  txbuf[14] = 0xFF;//第22字节	IO1电平	[??]	IO1电平,0为低，1为高，0xFF无效 


		if ((funcNo == VKxxx_IOFUNCTION_IO2) || (funcNo == 22))//34//22
		{
			txbuf[15] = (unsigned char)(para1 & 0x3);
			if (txbuf[14] > 4)txbuf[14] = 4;//  由于下位限制 用IO1判断小于5才可以设置其它IO
		}
		else  txbuf[15] = 0xFF;//第23字节	IO1电平	[??]	IO2电平,0为低，1为高，0xFF无效 

		if ((funcNo == VKxxx_IOFUNCTION_IO3) || (funcNo == 23))//35//23
		{
			txbuf[16] = (unsigned char)(para1 & 0x3);
			if (txbuf[14] > 4)txbuf[14] = 4;//  由于下位限制 用IO1判断小于5才可以设置其它IO
		}
		else  txbuf[16] = 0xFF;//第24字节	IO1电平	[??]	IO3电平,0为低，1为高，0xFF无效 

		if ((funcNo == VKxxx_IOFUNCTION_IO4) || (funcNo == 24))//36//24
		{
			txbuf[17] = (unsigned char)(para1 & 0x3);
			if (txbuf[14] > 4)txbuf[14] = 4;//  由于下位限制 用IO1判断小于5才可以设置其它IO
		}
		else  txbuf[17] = 0xFF;//第25字节	IO1电平	[??]	IO4电平,0为低，1为高，0xFF无效 
	}
	//---------------------------
	// 功能31
	//----------------------------
	if ((funcNo == VKxxx_IOFUNCTION_COUNTER) || (funcNo == 31))//31//49  // 复位
	{
		txbuf[18] = 0;
		txbuf[19] = 0;
		txbuf[20] = 0;
		txbuf[21] = 0;//第26-29字节	IO计数器	[?? ?? ?? ??]	32位计数器，0~0xFFFF FFFF, 高字节在前，低字节在后。
	}
	else if ((funcNo == VKxxx_IOFUNCTION_FREQ) || (funcNo == 32))  //50  32
	{
		if (para1 >= 100)// 频率计
		{
			txbuf[18] = 0x01;
			txbuf[19] = (unsigned char)(para1 / 0x10000);
			txbuf[20] = (unsigned char)(para1 / 0x100);
			txbuf[21] = (unsigned char)(para1);//
		}
		else // 100,200,500,1000,  设置频率
		{
			txbuf[18] = 0x01;
			txbuf[19] = 0;
			txbuf[20] = 0x03;
			txbuf[21] = 0xE8;//第26-29字节	IO计数器	[?? ?? ?? ??]	32位计数器，0~0xFFFF FFFF, 高字节在前，低字节在后。  
		}
	}
	else
	{
		txbuf[18] = 0xFF;
		txbuf[19] = 0xFF;
		txbuf[20] = 0xFF;
		txbuf[21] = 0xFF;//第26-29字节	IO计数器	[?? ?? ?? ??]	32位计数器，0~0xFFFF FFFF, 高字节在前，低字节在后。
	}
	//---------------------------
	// 功能41
	//----------------------------
	if ((funcNo == VKxxx_IOFUNCTION_INTMEP) || (funcNo == 41))//41//65
	{
		txbuf[22] = 0;//
		txbuf[23] = (unsigned char)(para1 & 0xF);//第30-31字节	温度传感器	[?? ??]	温度传感器值, 高字节在前，低字节在后。
	}
	else
	{
		txbuf[22] = 0xFF;//
		txbuf[23] = 0xFF;//第30-31字节	温度传感器	[?? ??]	温度传感器值, 高字节在前，低字节在后。
	}
	//第32字节	校验码	[??]	校验码
	//---------------------------
	// 功能42
	//----------------------------
	int index = 24;
	if ((funcNo == VKxxx_IOFUNCTION_EXTEMP) || (funcNo == 42))//42//66
	{
		txbuf[index++] = (unsigned char)(para1 / 0x1000000);
		txbuf[index++] = (unsigned char)(para1 / 0x10000);
		txbuf[index++] = (unsigned char)(para1 / 0x100);
		txbuf[index++] = (unsigned char)(para1);
		txbuf[index++] = (unsigned char)(para1 / 0x1000000);
		txbuf[index++] = (unsigned char)(para1 / 0x10000);
		txbuf[index++] = (unsigned char)(para1 / 0x100);
		txbuf[index++] = (unsigned char)(para1);
	}
	else
	{
		txbuf[index++] = 0xFF;
		txbuf[index++] = 0xFF;
		txbuf[index++] = 0xFF;
		txbuf[index++] = 0xFF;
		txbuf[index++] = 0xFF;
		txbuf[index++] = 0xFF;
		txbuf[index++] = 0xFF;
		txbuf[index++] = 0xFF;
	}
	//DisposalTXDatum(vCOM_CMD_RW_IO,txbuf,24,true); 
	//sprintf(tstrrr,"设置tsetdac1=%lf, tdac1=%d,%d,%d",tsetdac1,tdac1,txbuf[10],txbuf[11]);
	tstatus = DisposalTXDatum(VKTCPServer.SockClient[mci], vCOM_CMD_RW_IO, txbuf, 32, 1);  //vCOM_CMD_RW_IO
	return tstatus;
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
// IO function strings function
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//#define vCOM_CMD_RW_IO         0x90  // write and read the IO,pWM, DAC, counter, temperature   
//#define vCOM_CMD_RW_MODE       0x91  // write and read mode  
//附加功能， Additional features

/*
/////////////////////////////////////////////////////////////////////////////////////////////////////////////
int Def_Function_OUTfmt VK70xNMC_Command_ReadAdditionalFeature(int mci)
{
int tstatus;
unsigned char txbuf[2];
//////////////////////////////////////////////////////////
if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开
//if (ThreadRunningState==0)return -11;  //服务未打开
if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误
if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
if ((mci < 0) || (mci >(MAX_RX_CARD_NUM - 1)))return -13;
//////////////////////////////////////////////////////////
VK[mci].UpdateFlag = -1;
txbuf[0] = 0x10;
txbuf[1] = 0;
//========================================================
tstatus = DisposalTXDatum(VKTCPServer.SockClient[mci], vCOM_CMD_RW_IO, txbuf, 1, 0);  //vCOM_CMD_RW_IO
return tstatus;
}

int Def_Function_OUTfmt VK70xNMC_Get_AllIOS(int mci, unsigned int *iobuffer)
{
if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开
if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误
if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
if ((mci < 0) || (mci >(MAX_RX_CARD_NUM - 1)))return -13;
//----------------------------------------------
*iobuffer++ = VK[mci].IO[0];
*iobuffer++ = VK[mci].IO[1];
*iobuffer++ = VK[mci].IO[2];
*iobuffer = VK[mci].IO[3];
//----------------------------------------
//if (VKFuntionPara[mci].UpdateFlag == 0)return 0;
//----------------------------------------
return (VK[mci].UpdateFlag);//
}

int Def_Function_OUTfmt VK70xNMC_Get_IO1(int mci, unsigned int *iovalue)
{
if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开
if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误
if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
if ((mci < 0) || (mci >(MAX_RX_CARD_NUM - 1)))return -13;
//----------------------------------------------
*iovalue = VK[mci].IO[0];
//---------------------------------------------
return (VK[mci].UpdateFlag);//
}

int Def_Function_OUTfmt VK70xNMC_Get_IO2(int mci, unsigned int *iovalue)
{
if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开
if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误
if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
if ((mci < 0) || (mci >(MAX_RX_CARD_NUM - 1)))return -13;
//----------------------------------------------
*iovalue = VK[mci].IO[1];
//---------------------------------------------
return (VK[mci].UpdateFlag);//
}

int Def_Function_OUTfmt VK70xNMC_Get_IO3(int mci, unsigned int *iovalue)
{
if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开
if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误
if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
if ((mci < 0) || (mci >(MAX_RX_CARD_NUM - 1)))return -13;
//----------------------------------------------
*iovalue = VK[mci].IO[2];
//---------------------------------------------
return (VK[mci].UpdateFlag);//
}
int Def_Function_OUTfmt VK70xNMC_Get_IO4(int mci, unsigned int *iovalue)
{
if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开
if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误
if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
if ((mci < 0) || (mci >(MAX_RX_CARD_NUM - 1)))return -13;
//----------------------------------------------
*iovalue = VK[mci].IO[3];
//---------------------------------------------
return (VK[mci].UpdateFlag);//
}


int Def_Function_OUTfmt VK70xNMC_Get_Counter(int mci, unsigned int *countervalue)
{
if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开
if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误
if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
if ((mci < 0) || (mci >(MAX_RX_CARD_NUM - 1)))return -13;
//----------------------------------------------
*countervalue = VK[mci].Excounter;
//---------------------------------------------
return (VK[mci].UpdateFlag);//
}


int Def_Function_OUTfmt VK70xNMC_Get_PWM(int mci, double *dutyval, unsigned int *freqval)
{
if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开
if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误
if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
if ((mci < 0) || (mci >(MAX_RX_CARD_NUM - 1)))return -13;
//----------------------------------------------
*dutyval++ = VK[mci].PWMDuty[0];
*dutyval = VK[mci].PWMDuty[1];

*freqval++ = VK[mci].PWMFreq[0];
*freqval = VK[mci].PWMFreq[1];
//---------------------------------------------
return (VK[mci].UpdateFlag);//
}

int Def_Function_OUTfmt VK70xNMC_Get_DAC(int mci, double *dacvalue)
{
if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开
if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误
if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
if ((mci < 0) || (mci >(MAX_RX_CARD_NUM - 1)))return -13;
//----------------------------------------------
*dacvalue++ = VK[mci].DAC[0];
*dacvalue = VK[mci].DAC[1];
//---------------------------------------------
return (VK[mci].UpdateFlag);//
}

int Def_Function_OUTfmt VK70xNMC_Get_Temperature(int mci, double *tempvalue)
{
if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开
if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误
if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
if ((mci < 0) || (mci >(MAX_RX_CARD_NUM - 1)))return -13;
//----------------------------------------------
*tempvalue = VK[mci].Temp;
//---------------------------------------------
return (VK[mci].UpdateFlag);//
}
*/
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// Blocking
//==============================================================================================================


int sub_Command_ReadAdditionalFeature(int mci)
{
	int tstatus;
	unsigned char txbuf[2];
	VK[mci].UpdateFlag = -1;
	txbuf[0] = 0x10;
	txbuf[1] = 0;
	tstatus = DisposalTXDatum(VKTCPServer.SockClient[mci], vCOM_CMD_RW_IO, txbuf, 1, 0);  //vCOM_CMD_RW_IO
	return tstatus;
}


int Def_Function_OUTfmt VK70xNMC_Get_AllIOS_Blocking(int mci, int *iobuffer, int timeout)
{
	if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开 
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -13;
	//----------------------------------------------
	sub_Command_ReadAdditionalFeature(mci);
	while ((timeout > 0) && (VK[mci].UpdateFlag < 0))
	{
		timeout--;
		Sleep(1);
	}
	if (VK[mci].UpdateFlag < 0)return (VK[mci].UpdateFlag);
	*iobuffer++ = VK[mci].IO[0];
	*iobuffer++ = VK[mci].IO[1];
	*iobuffer++ = VK[mci].IO[2];
	*iobuffer = VK[mci].IO[3];
	//----------------------------------------
	//if (VKFuntionPara[mci].UpdateFlag == 0)return 0;
	//----------------------------------------
	return (VK[mci].UpdateFlag);// 
}

int Def_Function_OUTfmt VK70xNMC_Get_IO1_Blocking(int mci, int *iovalue, int timeout)
{
	if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开 
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -13;
	//----------------------------------------------
	sub_Command_ReadAdditionalFeature(mci);
	while ((timeout > 0) && (VK[mci].UpdateFlag < 0))
	{
		timeout--;
		Sleep(1);
	}
	if (VK[mci].UpdateFlag < 0)return (VK[mci].UpdateFlag);
	*iovalue = VK[mci].IO[0];
	//---------------------------------------------
	return (VK[mci].UpdateFlag);// 
}

int Def_Function_OUTfmt VK70xNMC_Get_IO2_Blocking(int mci, int *iovalue, int timeout)
{
	if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开 
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -13;
	//----------------------------------------------
	sub_Command_ReadAdditionalFeature(mci);
	while ((timeout > 0) && (VK[mci].UpdateFlag < 0))
	{
		timeout--;
		Sleep(1);
	}
	if (VK[mci].UpdateFlag < 0)return (VK[mci].UpdateFlag);
	*iovalue = VK[mci].IO[1];
	//---------------------------------------------
	return (VK[mci].UpdateFlag);// 
}

int Def_Function_OUTfmt VK70xNMC_Get_IO3_Blocking(int mci, int *iovalue, int timeout)
{
	if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开 
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -13;
	//----------------------------------------------
	sub_Command_ReadAdditionalFeature(mci);
	while ((timeout > 0) && (VK[mci].UpdateFlag < 0))
	{
		timeout--;
		Sleep(1);
	}
	if (VK[mci].UpdateFlag < 0)return (VK[mci].UpdateFlag);
	*iovalue = VK[mci].IO[2];
	//---------------------------------------------
	return (VK[mci].UpdateFlag);// 
}
int Def_Function_OUTfmt VK70xNMC_Get_IO4_Blocking(int mci, int *iovalue, int timeout)
{
	if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开 
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -13;
	//----------------------------------------------
	sub_Command_ReadAdditionalFeature(mci);
	while ((timeout > 0) && (VK[mci].UpdateFlag < 0))
	{
		timeout--;
		Sleep(1);
	}
	if (VK[mci].UpdateFlag < 0)return (VK[mci].UpdateFlag);
	*iovalue = VK[mci].IO[3];
	//---------------------------------------------
	return (VK[mci].UpdateFlag);// 
}


int Def_Function_OUTfmt VK70xNMC_Get_Counter_Blocking(int mci, int *countervalue, int timeout)
{
	if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开 
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -13;
	//----------------------------------------------
	sub_Command_ReadAdditionalFeature(mci);
	while ((timeout > 0) && (VK[mci].UpdateFlag < 0))
	{
		timeout--;
		Sleep(1);
	}
	if (VK[mci].UpdateFlag < 0)return (VK[mci].UpdateFlag);
	*countervalue = VK[mci].Excounter;
	//---------------------------------------------
	return (VK[mci].UpdateFlag);// 
}


int Def_Function_OUTfmt VK70xNMC_Get_PWM_Blocking(int mci, double *dutyval, int *freqval, int timeout)
{
	if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开 
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -13;
	//----------------------------------------------
	sub_Command_ReadAdditionalFeature(mci);
	while ((timeout > 0) && (VK[mci].UpdateFlag < 0))
	{
		timeout--;
		Sleep(1);
	}
	if (VK[mci].UpdateFlag < 0)return (VK[mci].UpdateFlag);
	*dutyval++ = VK[mci].PWMDuty[0];
	*dutyval = VK[mci].PWMDuty[1];

	*freqval++ = VK[mci].PWMFreq[0];
	*freqval = VK[mci].PWMFreq[1];
	//---------------------------------------------
	return (VK[mci].UpdateFlag);// 
}

int Def_Function_OUTfmt VK70xNMC_Get_DAC_Blocking(int mci, double *dacvalue, int timeout)
{
	if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开 
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -13;
	//----------------------------------------------
	sub_Command_ReadAdditionalFeature(mci);
	while ((timeout > 0) && (VK[mci].UpdateFlag < 0))
	{
		timeout--;
		Sleep(1);
	}
	if (VK[mci].UpdateFlag < 0)return (VK[mci].UpdateFlag);
	*dacvalue++ = VK[mci].DAC[0];
	*dacvalue = VK[mci].DAC[1];
	//---------------------------------------------
	return (VK[mci].UpdateFlag);// 
}



int Def_Function_OUTfmt VK70xNMC_Get_Temperature_Blocking(int mci, double *tempvalue, int timeout)
{
	if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开 
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -13;
	//----------------------------------------------
	sub_Command_ReadAdditionalFeature(mci);
	while ((timeout > 0) && (VK[mci].UpdateFlag < 0))
	{
		timeout--;
		Sleep(1);
	}
	if (VK[mci].UpdateFlag < 0)return (VK[mci].UpdateFlag);
	*tempvalue = VK[mci].Temp;
	//---------------------------------------------
	return (VK[mci].UpdateFlag);// 
}


