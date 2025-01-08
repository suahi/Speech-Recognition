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
//vk70xn output adc setting function
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
//return to the original condition or shape


int Def_Function_OUTfmt VK70xNMC_Get_ADCConfigParameter(int mci, int *sr, int *npoints, int *timeintervals, int *bitmode, int *para, int timeout)
{
	int i;
	if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开 
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -13;
	//----------------------------------------------
	VK[mci].UpdateFlag = -1;
	seNet_Send_ReadCommand(mci, vCOM_CMD_RW_ADC);
	//----------------------------------------------
	while ((timeout > 0) && (VK[mci].UpdateFlag < 0))
	{
		timeout--;
		Sleep(1);
	}
	if (VK[mci].UpdateFlag < 0)return (VK[mci].UpdateFlag);
	//---------------------------
	*sr = VK[mci].SampleRate;
	*npoints = VK[mci].Npoints;
	*timeintervals = VK[mci].Tintervals;
	*bitmode = VK[mci].SampleDataFormat;
	//------------------------
	for (i = 0; i < 4; i++)
	{
		*para++ = VK[mci].VolRange[i];
	}	
	//----------------------------
	return 0;// 
}

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
//vk70xn output function
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


//===================================================================
// 5、读取ADC采样数据(所有8通道）
//解释，前三个为设置值。缓冲区大小 与 采样设置单元中的设置一致，也可以小些。
//
//后2个为输出指向和数据量大小设置
//
// 函数原型：         
//Uint VC_DS_GetAllChannel(double *adcbuffer, int len,int waittime)
// Input: adcbuffer(double *) : input the buffer for save the ADC result 
//        len(int)    :         ready for read the array lenght
//        WaitTime(int)     :   waittime
// Output: result= int
//          > 0:  the fact read lenght
//          0: No datum, none
//===================================================================
int Def_Function_OUTfmt VK70xNMC_GetSrcDatumFromAllChannel(int mci, int *adcbuffer, int rsamplenum)//double(*adcbuffer)[4]
{
	int rfactnum, i;
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -3;
	//if (VK[mci].SaveShowPI == VK[mci].ReadShowPI)return 0;
	//--------------------------------------
	int timeout = ReadADCResultTimeout;
	if (timeout > 0)
	{
		while (1)
		{
			rfactnum = ((VK[mci].SaveShowPI + _DISP_MAX_LEN) - VK[mci].ReadShowPI) % _DISP_MAX_LEN;
#if (_DEBUG_VKUSBMC_LIB_>0)
			//printf("》》》》》》》》》》》读取阻塞数据量：%d)\n", rfactnum);
			//printf("--------------------------------------\n");
#endif
			if (rfactnum >= rsamplenum)break;
			Sleep(1);
			if (timeout>0)timeout--;
			else
			{
#if (_DEBUG_VKUSBMC_LIB_>0)
				//printf("timeout溢出：%d)\n", rfactnum);
#endif
				break;//return -2;
			}
		}
	}
	if (VK[mci].SaveShowPI == VK[mci].ReadShowPI)return 0;
	//=====================================
	rfactnum = 0;
	while (1)
	{
		for (i = 0; i < 8; i++)
		{
			*adcbuffer++ = VK[mci].CHSrcHexBuffer[i][VK[mci].ReadShowPI];
		}
		if (++VK[mci].ReadShowPI>_DISP_MAX_LEN)
			VK[mci].ReadShowPI = 0;
		//---------------
		rfactnum++;
		if (rfactnum >= rsamplenum)break;
		if (VK[mci].ReadShowPI == VK[mci].SaveShowPI)break;
		//-------------------
	}
	//--------------------------------------
	return rfactnum;
}


//===================================================================
// 5、读取ADC采样数据(所有4通道）
//解释，前三个为设置值。缓冲区大小 与 采样设置单元中的设置一致，也可以小些。
//
//后2个为输出指向和数据量大小设置
//
// 函数原型：         
//Uint VC_DS_GetAllChannel(double *adcbuffer, int len,int waittime)
// Input: adcbuffer(double *) : input the buffer for save the ADC result 
//        len(int)    :         ready for read the array lenght
//        WaitTime(int)     :   waittime
// Output: result= int
//          > 0:  the fact read lenght
//          0: No datum, none
//===================================================================
int Def_Function_OUTfmt VK70xNMC_GetSrcDatumFromFourChannel(int mci, int *adcbuffer, int rsamplenum)//double(*adcbuffer)[4]
{
	int rfactnum, i;
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -3;
	//if (VK[mci].SaveShowPI == VK[mci].Read4CHPI)return 0;
	//--------------------------------------
	int timeout = ReadADCResultTimeout;
	if (timeout > 0)
	{
		while (1)
		{
			rfactnum = ((VK[mci].SaveShowPI + _DISP_MAX_LEN) - VK[mci].Read4CHPI) % _DISP_MAX_LEN;
#if (_DEBUG_VKUSBMC_LIB_>0)
			//printf("》》》》》》》》》》》读取阻塞数据量：%d)\n", rfactnum);
			//printf("--------------------------------------\n");
#endif
			if (rfactnum >= rsamplenum)break;
			Sleep(1);
			if (timeout>0)timeout--;
			else
			{
#if (_DEBUG_VKUSBMC_LIB_>0)
				//printf("timeout溢出：%d)\n", rfactnum);
#endif
				break;//return -2;
			}
		}
	}
	if (VK[mci].SaveShowPI == VK[mci].Read4CHPI)return 0;
	//=====================================
	rfactnum = 0;
	while (1)
	{
		for (i = 0; i < 4; i++)
		{
			*adcbuffer++ = VK[mci].CHSrcHexBuffer[i][VK[mci].Read4CHPI];
		}
		if (++VK[mci].Read4CHPI>_DISP_MAX_LEN)
			VK[mci].Read4CHPI = 0;
		//---------------
		rfactnum++;
		if (rfactnum >= rsamplenum)break;
		if (VK[mci].SaveShowPI == VK[mci].Read4CHPI)break;
		//if (ReadShowPI==Read4CHPI)break;
		//----------------
	}
	//--------------------------------------
	return rfactnum;
}
///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

//===================================================================
// 5、读取ADC采样数据(所有8通道）
//解释，前三个为设置值。缓冲区大小 与 采样设置单元中的设置一致，也可以小些。
//
//后2个为输出指向和数据量大小设置
//
// 函数原型：         
//Uint VC_DS_GetAllChannel(double *adcbuffer, int len,int waittime)
// Input: adcbuffer(double *) : input the buffer for save the ADC result 
//        len(int)    :         ready for read the array lenght
//        WaitTime(int)     :   waittime
// Output: result= int
//          > 0:  the fact read lenght
//          0: No datum, none
//===================================================================
int Def_Function_OUTfmt VK70xNMC_GetAllChannel(int mci, double *adcbuffer, int rsamplenum)//double(*adcbuffer)[4]
{
	int rfactnum, i;
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -3;
	//if (VK[mci].SaveShowPI == VK[mci].ReadShowPI)return 0;
	//--------------------------------------
	int timeout = ReadADCResultTimeout;
	if (timeout > 0)
	{
		while (1)
		{
			rfactnum = ((VK[mci].SaveShowPI + _DISP_MAX_LEN) - VK[mci].ReadShowPI) % _DISP_MAX_LEN;
#if (_DEBUG_VKUSBMC_LIB_>0)
			//printf("》》》》》》》》》》》读取阻塞数据量：%d)\n", rfactnum);
			//printf("--------------------------------------\n");
#endif
			if (rfactnum >= rsamplenum)break;
			Sleep(1);
			if (timeout>0)timeout--;
			else
			{
#if (_DEBUG_VKUSBMC_LIB_>0)
				//printf("timeout溢出：%d)\n", rfactnum);
#endif
				break;//return -2;
			}
		}
	}
	if (VK[mci].SaveShowPI == VK[mci].ReadShowPI)return 0;
	//=====================================
	rfactnum = 0;
	while (1)
	{
		for (i = 0; i < 8; i++)
		{
			*adcbuffer++ = VK[mci].CHShowBuffer[i][VK[mci].ReadShowPI];
		}
		if (++VK[mci].ReadShowPI>_DISP_MAX_LEN)
			VK[mci].ReadShowPI = 0;
		//---------------
		rfactnum++;
		if (rfactnum >= rsamplenum)break;
		if (VK[mci].ReadShowPI == VK[mci].SaveShowPI)break;
		//-------------------
	}
	//--------------------------------------
	return rfactnum;
}


//===================================================================
// 5、读取ADC采样数据(所有4通道）
//解释，前三个为设置值。缓冲区大小 与 采样设置单元中的设置一致，也可以小些。
//
//后2个为输出指向和数据量大小设置
//
// 函数原型：         
//Uint VC_DS_GetAllChannel(double *adcbuffer, int len,int waittime)
// Input: adcbuffer(double *) : input the buffer for save the ADC result 
//        len(int)    :         ready for read the array lenght
//        WaitTime(int)     :   waittime
// Output: result= int
//          > 0:  the fact read lenght
//          0: No datum, none
//===================================================================
int Def_Function_OUTfmt VK70xNMC_GetFourChannel(int mci, double *adcbuffer, int rsamplenum)//double(*adcbuffer)[4]
{
	int rfactnum, i;
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -3;
	//if (VK[mci].SaveShowPI == VK[mci].Read4CHPI)return 0;
	//--------------------------------------
	int timeout = ReadADCResultTimeout;
	if (timeout > 0)
	{
		while (1)
		{
			rfactnum = ((VK[mci].SaveShowPI + _DISP_MAX_LEN) - VK[mci].Read4CHPI) % _DISP_MAX_LEN;
#if (_DEBUG_VKUSBMC_LIB_>0)
			//printf("》》》》》》》》》》》读取阻塞数据量：%d)\n", rfactnum);
			//printf("--------------------------------------\n");
#endif
			if (rfactnum >= rsamplenum)break;
			Sleep(1);
			if (timeout>0)timeout--;
			else
			{
#if (_DEBUG_VKUSBMC_LIB_>0)
				//printf("timeout溢出：%d)\n", rfactnum);
#endif
				break;//return -2;
			}
		}
	}
	if (VK[mci].SaveShowPI == VK[mci].Read4CHPI)return 0;
	//=====================================
	rfactnum = 0;
	while (1)
	{
		for (i = 0; i < 4; i++)
		{
			*adcbuffer++ = VK[mci].CHShowBuffer[i][VK[mci].Read4CHPI];
		}
		if (++VK[mci].Read4CHPI>_DISP_MAX_LEN)
			VK[mci].Read4CHPI = 0;
		//---------------
		rfactnum++;
		if (rfactnum >= rsamplenum)break;
		if (VK[mci].SaveShowPI == VK[mci].Read4CHPI)break;
		//if (ReadShowPI==Read4CHPI)break;
		//----------------
	}
	//--------------------------------------
	return rfactnum;
}
//=======================================================
// 4、读取ADC采样数据(单通道）,函数原型：   
// int  VC_DS_GetOneChannel(int CHNum, double *adcbuffer, int len,int waittime)
// Input: CHNum(int):  ready to read the channel number
//        adcbuffer(double *) : input the buffer for save the ADC result 
//        len(int)    :         ready for read the array lenght
//        WaitTime(int)     :   waittime
// Output: result= int
//          > 0:  the fact read lenght
//          0: No datum, none
//         -1: USB disconnect
//===================================================================
int Def_Function_OUTfmt VK70xNMC_GetOneChannel(int mci, int CHno, double *adcbuffer, int rsamplenum)
{
	int rfactnum;
	int tchpi;
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -3;
	tchpi = VK[mci].ReadCHPI[CHno];
	//--------------------------------------
	int timeout = ReadADCResultTimeout;
	if (timeout > 0)
	{
		while (1)
		{
			rfactnum = ((VK[mci].SaveShowPI + _DISP_MAX_LEN) - tchpi) % _DISP_MAX_LEN;
#if (_DEBUG_VKUSBMC_LIB_>0)
			//printf("》》》》》》》》》》》读取阻塞数据量：%d)\n", rfactnum);
			//printf("--------------------------------------\n");
#endif
			if (rfactnum >= rsamplenum)break;
			Sleep(1);
			if (timeout>0)timeout--;
			else
			{
#if (_DEBUG_VKUSBMC_LIB_>0)
				//printf("timeout溢出：%d)\n", rfactnum);
#endif
				break;//return -2;
			}
		}
	}
	if (tchpi == VK[mci].SaveShowPI)return 0;
	//=====================================
	rfactnum = 0;
	while (1)
	{
		*adcbuffer++ = VK[mci].CHShowBuffer[CHno][tchpi];
		if (++tchpi>_DISP_MAX_LEN)
			tchpi = 0;
		//-----------------------
		rfactnum++;
		if (rfactnum >= rsamplenum)
		{
			VK[mci].ReadCHPI[CHno] = tchpi;
			break;
		}
		//if (ReadShowPI==SaveShowPI）
		if (tchpi == VK[mci].SaveShowPI)
		{
			VK[mci].ReadCHPI[CHno] = tchpi;
			break;
		}
		//-----------------------
	}
	//--------------------------------------
	return rfactnum;
}

//=======================================================
// 4、读取IO状态,函数原型：   
// int VK70xNMC_GetIOStatus(int *iostatus)
// Input:  iostatus(double *) : input the buffer for save the ADC result 
// Output: result= int
//          0: IO1和IO2状态信息
//         -1: 采集卡工作在8或16或32位模式下，无法返回IO状态信息
//         -2： 该采集卡不支持返回IO状态
//===================================================================
int Def_Function_OUTfmt VK70xNMC_GetIOStatus(int mci, int *iostatus)
{
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -3;
	//if (ReferenceVoltage == 2.442)// 2.442 mode
	if (VK[mci].IOUpdateFlag == 1)
	{
		if (VK[mci].IOUpdateFlag < 0)
			return -1;
		/////////////////////////////////////
		//if ((PacketDatum[r + 3] & 0x10) == 0x10)CHShowBuffer[8][SaveShowPI] = 1;
		//else CHShowBuffer[8][SaveShowPI] = 0;
		//if ((PacketDatum[r + 3] & 0x20) == 0x20)CHShowBuffer[9][SaveShowPI] = 1;
		//else CHShowBuffer[9][SaveShowPI] = 0;
		*iostatus++ = -1;
		*iostatus++ = (int)VK[mci].CHShowBuffer[8][VK[mci].ReadShowPI];//IOStaus[1];
		*iostatus++ = (int)VK[mci].CHShowBuffer[9][VK[mci].ReadShowPI];//IOStaus[2];
		*iostatus = -1;
		return 0;
	}
	//--------------------------------------
	return -2;
}



//===================================================================
// 5、读取ADC采样数据(所有8通道）带IO2，IO3
//解释，前三个为设置值。缓冲区大小 与 采样设置单元中的设置一致，也可以小些。
//
//后2个为输出指向和数据量大小设置
//
// 函数原型：         
//Uint VC_DS_GetAllChannel(double *adcbuffer, int len,int waittime)
// Input: adcbuffer(double *) : input the buffer for save the ADC result 
//        len(int)    :         ready for read the array lenght
//        ioenable(int)     :   1:IO2, 2: IO3; 3:IO2和IO3， 其它无效
// Output: result= int
//          > 0:  the fact read lenght
//          0: No datum, none
//===================================================================
int Def_Function_OUTfmt VK70xNMC_GetAllChannel_WithIOStatus(int mci, double *adcbuffer, int rsamplenum, int ioenable)//double(*adcbuffer)[4]
{
	int rfactnum, i;
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -3;
	//--------------------------------------
	int timeout = ReadADCResultTimeout;
	if (timeout > 0)
	{
		while (1)
		{
			rfactnum = ((VK[mci].SaveShowPI + _DISP_MAX_LEN) - VK[mci].ReadShowPI) % _DISP_MAX_LEN;
#if (_DEBUG_VKUSBMC_LIB_>0)
			//printf("》》》》》》》》》》》读取阻塞数据量：%d)\n", rfactnum);
			//printf("--------------------------------------\n");
#endif
			if (rfactnum >= rsamplenum)break;
			Sleep(1);
			if (timeout>0)timeout--;
			else
			{
#if (_DEBUG_VKUSBMC_LIB_>0)
				//printf("timeout溢出：%d)\n", rfactnum);
#endif
				break;//return -2;
			}
		}
	}
	if (VK[mci].SaveShowPI == VK[mci].ReadShowPI)return 0;
	//=====================================
	rfactnum = 0;
	while (1)
	{
		for (i = 0; i < 8; i++)
		{
			*adcbuffer++ = VK[mci].CHShowBuffer[i][VK[mci].ReadShowPI];
		}
		//////////////////////////////////////
		if (ioenable == 1)*adcbuffer++ = VK[mci].CHShowBuffer[8][VK[mci].ReadShowPI];
		else if (ioenable == 2)*adcbuffer++ = VK[mci].CHShowBuffer[9][VK[mci].ReadShowPI];
		else if (ioenable == 3)
		{
			*adcbuffer++ = VK[mci].CHShowBuffer[8][VK[mci].ReadShowPI];
			*adcbuffer++ = VK[mci].CHShowBuffer[9][VK[mci].ReadShowPI];
		}
		//////////////////////////////////////
		if (++VK[mci].ReadShowPI>_DISP_MAX_LEN)
			VK[mci].ReadShowPI = 0;
		//---------------
		rfactnum++;
		if (rfactnum >= rsamplenum)break;
		if (VK[mci].ReadShowPI == VK[mci].SaveShowPI)break;
		//-------------------
	}
	//--------------------------------------
	return rfactnum;
}


//===================================================================
// 5、读取ADC采样数据(所有4通道）
//解释，前三个为设置值。缓冲区大小 与 采样设置单元中的设置一致，也可以小些。
//
//后2个为输出指向和数据量大小设置
//
// 函数原型：         
//Uint VC_DS_GetAllChannel(double *adcbuffer, int len,int waittime)
// Input: adcbuffer(double *) : input the buffer for save the ADC result 
//        len(int)    :         ready for read the array lenght
//        ioenable(int)     :   1:IO2, 2: IO3; 3:IO2和IO3， 其它无效
// Output: result= int
//          > 0:  the fact read lenght
//          0: No datum, none
//===================================================================
int Def_Function_OUTfmt VK70xNMC_GetFourChannel_WithIOStatus(int mci, double *adcbuffer, int rsamplenum, int ioenable)//double(*adcbuffer)[4]
{
	int rfactnum, i;
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -3;
	//--------------------------------------
	int timeout = ReadADCResultTimeout;
	if (timeout > 0)
	{
		while (1)
		{
			rfactnum = ((VK[mci].SaveShowPI + _DISP_MAX_LEN) - VK[mci].Read4CHPI) % _DISP_MAX_LEN;
#if (_DEBUG_VKUSBMC_LIB_>0)
			//printf("》》》》》》》》》》》读取阻塞数据量：%d)\n", rfactnum);
			//printf("--------------------------------------\n");
#endif
			if (rfactnum >= rsamplenum)break;
			Sleep(1);
			if (timeout>0)timeout--;
			else
			{
#if (_DEBUG_VKUSBMC_LIB_>0)
				//printf("timeout溢出：%d)\n", rfactnum);
#endif
				break;//return -2;
			}
		}
	}
	if (VK[mci].SaveShowPI == VK[mci].Read4CHPI)return 0;
	//=====================================
	rfactnum = 0;
	while (1)
	{
		for (i = 0; i < 4; i++)
		{
			*adcbuffer++ = VK[mci].CHShowBuffer[i][VK[mci].Read4CHPI];
		}
		//////////////////////////////////////
		if (ioenable == 1)*adcbuffer++ = VK[mci].CHShowBuffer[8][VK[mci].Read4CHPI];
		else if (ioenable == 2)*adcbuffer++ = VK[mci].CHShowBuffer[9][VK[mci].Read4CHPI];
		else if (ioenable == 3)
		{
			*adcbuffer++ = VK[mci].CHShowBuffer[8][VK[mci].Read4CHPI];
			*adcbuffer++ = VK[mci].CHShowBuffer[9][VK[mci].Read4CHPI];
		}
		//////////////////////////////////////
		if (++VK[mci].Read4CHPI>_DISP_MAX_LEN)
			VK[mci].Read4CHPI = 0;
		//---------------
		rfactnum++;
		if (rfactnum >= rsamplenum)break;
		if (VK[mci].SaveShowPI == VK[mci].Read4CHPI)break;
		//if (ReadShowPI==Read4CHPI)break;
		//----------------
	}
	//--------------------------------------
	return rfactnum;
}


//===================================================================
// 5、读取ADC采样数据(所有4通道）
//解释，前三个为设置值。缓冲区大小 与 采样设置单元中的设置一致，也可以小些。
//
//后2个为输出指向和数据量大小设置
//
// 函数原型：         
//Uint VC_DS_GetAllChannel(double *adcbuffer, int len,int waittime)
// Input: adcbuffer(double *) : input the buffer for save the ADC result 
//        len(int)    :         ready for read the array lenght
//        ioenable(int)     :   1:IO2, 2: IO3; 3:IO2和IO3， 其它无效
// Output: result= int
//          > 0:  the fact read lenght
//          0: No datum, none
//===================================================================
int Def_Function_OUTfmt VK70xNMC_GetFixedFourChannel_CH1CH2_IO2IO3(int mci, double *adcbuffer, int rsamplenum)//double(*adcbuffer)[4]
{
	int rfactnum, i;
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -3;
	//--------------------------------------
	int timeout = ReadADCResultTimeout;
	if (timeout > 0)
	{
		while (1)
		{
			rfactnum = ((VK[mci].SaveShowPI + _DISP_MAX_LEN) - VK[mci].Read4CHPI) % _DISP_MAX_LEN;
#if (_DEBUG_VKUSBMC_LIB_>0)
			//printf("》》》》》》》》》》》读取阻塞数据量：%d)\n", rfactnum);
			//printf("--------------------------------------\n");
#endif
			if (rfactnum >= rsamplenum)break;
			Sleep(1);
			if (timeout>0)timeout--;
			else
			{
#if (_DEBUG_VKUSBMC_LIB_>0)
				//printf("timeout溢出：%d)\n", rfactnum);
#endif
				break;//return -2;
			}
		}
	}
	if (VK[mci].SaveShowPI == VK[mci].Read4CHPI)return 0;
	//=====================================
	rfactnum = 0;
	while (1)
	{
		for (i = 0; i < 2; i++)
		{
			*adcbuffer++ = VK[mci].CHShowBuffer[i][VK[mci].Read4CHPI];
		}
		//////////////////////////////////////
		*adcbuffer++ = VK[mci].CHShowBuffer[8][VK[mci].Read4CHPI];
		*adcbuffer++ = VK[mci].CHShowBuffer[9][VK[mci].Read4CHPI];
		//////////////////////////////////////
		if (++VK[mci].Read4CHPI>_DISP_MAX_LEN)
			VK[mci].Read4CHPI = 0;
		//---------------
		rfactnum++;
		if (rfactnum >= rsamplenum)break;
		if (VK[mci].SaveShowPI == VK[mci].Read4CHPI)break;
		//if (ReadShowPI==Read4CHPI)break;
		//----------------
	}
	//--------------------------------------
	return rfactnum;
}




//===================================================================
// 5、读取ADC采样数据(所有4通道）
//解释，前三个为设置值。缓冲区大小 与 采样设置单元中的设置一致，也可以小些。
//
//后2个为输出指向和数据量大小设置
//
// 函数原型：         
//Uint VC_DS_GetAllChannel(double *adcbuffer, int len,int waittime)
// Input: adcbuffer(double *) : input the buffer for save the ADC result 
//        len(int)    :         ready for read the array lenght
//        ioenable(int)     :   1:IO2, 2: IO3; 3:IO2和IO3， 其它无效
// Output: result= int
//          > 0:  the fact read lenght
//          0: No datum, none
//===================================================================
int Def_Function_OUTfmt VK70xNMC_GetFixedFourChannel_CH3CH4_IO2IO3(int mci, double *adcbuffer, int rsamplenum)//double(*adcbuffer)[4]
{
	int rfactnum, i;
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -3;
	//--------------------------------------
	int timeout = ReadADCResultTimeout;
	if (timeout > 0)
	{
		while (1)
		{
			rfactnum = ((VK[mci].SaveShowPI + _DISP_MAX_LEN) - VK[mci].Read4CHPI) % _DISP_MAX_LEN;
#if (_DEBUG_VKUSBMC_LIB_>0)
			//printf("》》》》》》》》》》》读取阻塞数据量：%d)\n", rfactnum);
			//printf("--------------------------------------\n");
#endif
			if (rfactnum >= rsamplenum)break;
			Sleep(1);
			if (timeout>0)timeout--;
			else
			{
#if (_DEBUG_VKUSBMC_LIB_>0)
				//printf("timeout溢出：%d)\n", rfactnum);
#endif
				break;//return -2;
			}
		}
	}
	if (VK[mci].SaveShowPI == VK[mci].Read4CHPI)return 0;
	//=====================================
	rfactnum = 0;
	while (1)
	{
		for (i = 2; i < 4; i++)
		{
			*adcbuffer++ = VK[mci].CHShowBuffer[i][VK[mci].Read4CHPI];
		}
		//////////////////////////////////////
		*adcbuffer++ = VK[mci].CHShowBuffer[8][VK[mci].Read4CHPI];
		*adcbuffer++ = VK[mci].CHShowBuffer[9][VK[mci].Read4CHPI];
		//////////////////////////////////////
		if (++VK[mci].Read4CHPI>_DISP_MAX_LEN)
			VK[mci].Read4CHPI = 0;
		//---------------
		rfactnum++;
		if (rfactnum >= rsamplenum)break;
		if (VK[mci].SaveShowPI == VK[mci].Read4CHPI)break;
		//if (ReadShowPI==Read4CHPI)break;
		//----------------
	}
	//--------------------------------------
	return rfactnum;
}

//=======================================================
// 4、读取ADC采样数据(单通道）,函数原型：   
// int  VC_DS_GetOneChannel(int CHNum, double *adcbuffer, int len,int waittime)
// Input: CHNum(int):  ready to read the channel number
//        adcbuffer(double *) : input the buffer for save the ADC result 
//        len(int)    :         ready for read the array lenght
//        ioenable(int)     :   1:IO2, 2: IO3; 3:IO2和IO3， 其它无效
// Output: result= int
//          > 0:  the fact read lenght
//          0: No datum, none
//         -1: USB disconnect
//===================================================================
int Def_Function_OUTfmt VK70xNMC_GetOneChannel_WithIOStatus(int mci, int CHno, double *adcbuffer, int rsamplenum, int ioenable)
{
	int rfactnum;
	int tchpi;
	tchpi = VK[mci].ReadCHPI[CHno];
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -3;
	//--------------------------------------
	int timeout = ReadADCResultTimeout;
	if (timeout > 0)
	{
		while (1)
		{
			rfactnum = ((VK[mci].SaveShowPI + _DISP_MAX_LEN) - tchpi) % _DISP_MAX_LEN;
#if (_DEBUG_VKUSBMC_LIB_>0)
			//printf("》》》》》》》》》》》读取阻塞数据量：%d)\n", rfactnum);
			//printf("--------------------------------------\n");
#endif
			if (rfactnum >= rsamplenum)break;
			Sleep(1);
			if (timeout>0)timeout--;
			else
			{
#if (_DEBUG_VKUSBMC_LIB_>0)
				//printf("timeout溢出：%d)\n", rfactnum);
#endif
				break;//return -2;
			}
		}
	}
	if (tchpi == VK[mci].SaveShowPI)return 0;
	//=====================================
	rfactnum = 0;
	while (1)
	{
		*adcbuffer++ = VK[mci].CHShowBuffer[CHno][tchpi];
		//////////////////////////////////////
		if (ioenable == 1)*adcbuffer++ = VK[mci].CHShowBuffer[8][tchpi];
		else if (ioenable == 2)*adcbuffer++ = VK[mci].CHShowBuffer[9][tchpi];
		else if (ioenable == 3)
		{
			*adcbuffer++ = VK[mci].CHShowBuffer[8][tchpi];
			*adcbuffer++ = VK[mci].CHShowBuffer[9][tchpi];
		}
		//////////////////////////////////////
		if (++tchpi>_DISP_MAX_LEN)
			tchpi = 0;
		//-----------------------
		rfactnum++;
		if (rfactnum >= rsamplenum)
		{
			VK[mci].ReadCHPI[CHno] = tchpi;
			break;
		}
		//if (ReadShowPI==SaveShowPI）
		if (tchpi == VK[mci].SaveShowPI)
		{
			VK[mci].ReadCHPI[CHno] = tchpi;
			break;
		}
		//-----------------------
	}
	//--------------------------------------
	return rfactnum;
}


