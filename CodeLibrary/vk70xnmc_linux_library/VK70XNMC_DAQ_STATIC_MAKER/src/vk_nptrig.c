#if _MSC_VER > 1000
#pragma once
#endif 

#include "VK70xNMC_DAQ2.h"
#include "dvr_header.h"
#include <Windows.h>
#include <stdio.h>



/////////////////////////////////////////////////
// 设置触发模式

//VK[mci].CNP_Trig_Status;   //  0: 空闲， 不触发；  1-准备触发， 2-正在触发数据
//VK[mci].CNP_Trig_Channel;  //  0-7：对应电压值触发通道；  8：IO2，9：IO3 IO电平触发;  大于9或小于0: 无效通道，  
//VK[mci].CNP_Trig_Edge;    //   0: 上升沿触发/高于电压值触发；  1： 下降沿触发/低于电压值触发
//VK[mci].CNP_Trig_Value;   //   触发的电压值，，，double        
//-------------------------
//VK[mci].CNP_Target_Len;    // 触发N点长度(包括负采样数目，所以此设置采样点数一定大于负采样数目)
//VK[mci].CNP_Target_Neg_Len;// 触发N点时前M点负采样
//---------------
//VK[mci].CNP_Counter;	     // 触发N点计数器
//VK[mci].CNP_Read_PI;       // 读取数据指针，主要用于负采样点数


int Def_Function_OUTfmt VK70xNMC_Set_SimulationTriggerMode(int mci, int status, int trigch, int trigedge, int rdnpoints, int rdnegnpoints, double trigval)
{
	int resi = 0;
	if ((status == 0) || (status == 1))VK[mci].CNP_Trig_Status = status;   //  0: 空闲， 不触发；  1-准备触发， 2-正在触发数据
	else
	{
		VK[mci].CNP_Trig_Status = 0;
		resi = -1;
	}
	//-----------------------
	if ((trigch >= 0) && (trigch<10))VK[mci].CNP_Trig_Channel = trigch;  //  0-7：对应电压值触发通道；  8：IO2，9：IO3 IO电平触发;  大于9或小于0: 无效通道， 
	else
	{
		VK[mci].CNP_Trig_Channel = 0;
		resi = -2;
	}

	if ((trigedge >= 0) && (trigedge < 4))VK[mci].CNP_Trig_Edge = trigedge;
	else
	{
		VK[mci].CNP_Trig_Edge = 0;    //   0: 上升沿触发/高于电压值触发；  1： 下降沿触发/低于电压值触发； 2： 高电平触发/高于电压值触发；3： 低电平触发/低于电压值触发
		resi = -3;
	}

	if (trigch > 7)
	{
		//if (trigval>0)VK[mci].CNP_Trig_Value = 1;
		//else VK[mci].CNP_Trig_Value = 0;
		VK[mci].CNP_Trig_Value = 0.5;// 由于电平判断时0/1，所有固定中间电平来判断
	}
	else VK[mci].CNP_Trig_Value = trigval;   //   触发的电压值，，，double    
	//-------------------------
	if ((rdnpoints > rdnegnpoints) && (rdnegnpoints >= 0))
	{
		VK[mci].CNP_Target_Len = rdnpoints;    // 触发N点长度(包括负采样数目，所以此设置采样点数一定大于负采样数目)
		VK[mci].CNP_Target_Neg_Len = rdnegnpoints;// 触发N点时前M点负采样
	}
	else
	{
		VK[mci].CNP_Target_Len = rdnpoints;    // 触发N点长度(包括负采样数目，所以此设置采样点数一定大于负采样数目)
		VK[mci].CNP_Target_Neg_Len = rdnpoints;// 触发N点时前M点负采样
		resi = -4;
	}
	//---------------
	VK[mci].CNP_Counter = 0;	     // 触发N点计数器
	VK[mci].CNP_Read_PI = 0;;       // 读取数据指针，主要用于负采样点数
	return resi;
}




//int Def_Function_OUTfmt VK70xNMC_Get_SimulationTriggerMode(int mci, int status, int trigch, int trigedge, int rdnpoints, int rdnegnpoints, double trigval)

//===================================================================
// 0、读取ADC采样数据(所有8通道）
//客户定制负误差模式
//客户定制负误差模式
//	Customized negative error mode
//VK[mci].CNP_Trig_Status;   //  0: 空闲， 不触发；  1-准备触发， 2-正在触发数据
//VK[mci].CNP_Trig_Channel;  //  0-7：对应电压值触发通道；  8：IO2，9：IO3 IO电平触发;  大于9或小于0: 无效通道，  
//VK[mci].CNP_Trig_Edge;    //   0: 上升沿触发/高于电压值触发；  1： 下降沿触发/低于电压值触发
//VK[mci].CNP_Trig_Value;   //   触发的电压值，，，double        
//-------------------------
//VK[mci].CNP_Target_Len;    // 触发N点长度(包括负采样数目，所以此设置采样点数一定大于负采样数目)
//VK[mci].CNP_Target_Neg_Len;// 触发N点时前M点负采样
//---------------
//VK[mci].CNP_Counter;	     // 触发N点计数器
//VK[mci].CNP_Read_PI;       // 读取数据指针，主要用于负采样点数
///////////////////////////////////////////////////////////////
//
// 函数原型：         
//int Def_Function_OUTfmt VK70xNMC_GetSelectChannels_FromSimulationTriger(int mci, int readdchnum, double *adcbuffer, int rsamplenum)
// Input: adcbuffer(double *) : input the buffer for save the ADC result 
//        readdchnum(int)     : read channel number
//        rsamplenum(int)    :  ready for read the array lenght

// Output: result= int
//          > 0:  the fact read lenght
//          0: No datum, none
//===================================================================

int Def_Function_OUTfmt VK70xNMC_Get_SelectChannelsFromSimulationTrigger(int mci, int readdchnum, double *adcbuffer, int rsamplenum)
{
	static double lasttrigvalue = 0;
	int rfactnum, i, tstatus;
	int tchno;
	double trigvalue;
	tstatus = VK[mci].CNP_Trig_Status;
	//----------------------------
	if (tstatus == 0)return -4;//当前采集卡不工作采样模式
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
	tchno = VK[mci].CNP_Trig_Channel;
	if ((tchno<0) || (tchno>9))return -5;//当前采集卡设置触发通道错误
	//-------------------------------------
	rfactnum = 0;
	if (tstatus == 1)//待采样N点模式下
	{
		i = 0;
		while (1)
		{
			trigvalue = VK[mci].CHShowBuffer[tchno][VK[mci].ReadShowPI];//lasttrigvalue
			if (VK[mci].CNP_Trig_Edge == 0)//   0: 上升沿触发/高于电压值触发；  1： 下降沿触发/低于电压值触发； 2： 高电平触发/高于电压值触发；3： 低电平触发/低于电压值触发
			{
				if ((trigvalue > VK[mci].CNP_Trig_Value) && (trigvalue > lasttrigvalue))
				{
					VK[mci].CNP_Trig_Status = 2;
					tstatus = 2;
					VK[mci].CNP_Counter = 0;
					if ((VK[mci].CNP_Target_Neg_Len >= 0) && (VK[mci].CNP_Target_Neg_Len < VK[mci].CNP_Target_Len))
					{
						VK[mci].CNP_Read_PI = (VK[mci].ReadShowPI + _DISP_MAX_LEN - VK[mci].CNP_Target_Neg_Len) % _DISP_MAX_LEN;
						// 修改读取指针
						VK[mci].ReadShowPI = VK[mci].CNP_Read_PI;
					}
					else
					{
						VK[mci].CNP_Read_PI = VK[mci].ReadShowPI;
					}
					i = rsamplenum;// 检查道触发条件了， 强行退出检查条件，准读取数据
					break;
				}
				lasttrigvalue = trigvalue;// 为了判定边沿触发条件
			}
			else if (VK[mci].CNP_Trig_Edge == 1)//   0: 上升沿触发/高于电压值触发；  1： 下降沿触发/低于电压值触发； 2： 高电平触发/高于电压值触发；3： 低电平触发/低于电压值触发
			{
				if ((trigvalue < VK[mci].CNP_Trig_Value) && (trigvalue<lasttrigvalue))
				{
					VK[mci].CNP_Trig_Status = 2;
					tstatus = 2;
					VK[mci].CNP_Counter = 0;
					if ((VK[mci].CNP_Target_Neg_Len >= 0) && (VK[mci].CNP_Target_Neg_Len < VK[mci].CNP_Target_Len))
					{
						VK[mci].CNP_Read_PI = (VK[mci].ReadShowPI + _DISP_MAX_LEN - VK[mci].CNP_Target_Neg_Len) % _DISP_MAX_LEN;
						//  修改读取指针
						VK[mci].ReadShowPI = VK[mci].CNP_Read_PI;
					}
					else
					{
						VK[mci].CNP_Read_PI = VK[mci].ReadShowPI;
					}
					i = rsamplenum;// 检查道触发条件了， 强行退出检查条件，准读取数据
					break;
				}
				lasttrigvalue = trigvalue;// 为了判定边沿触发条件
			}
			else if (VK[mci].CNP_Trig_Edge == 2)//   0: 上升沿触发/高于电压值触发；  1： 下降沿触发/低于电压值触发； 2： 高电平触发/高于电压值触发；3： 低电平触发/低于电压值触发
			{
				if (trigvalue > VK[mci].CNP_Trig_Value)
				{
					VK[mci].CNP_Trig_Status = 2;
					tstatus = 2;
					VK[mci].CNP_Counter = 0;
					if ((VK[mci].CNP_Target_Neg_Len >= 0) && (VK[mci].CNP_Target_Neg_Len < VK[mci].CNP_Target_Len))
					{
						VK[mci].CNP_Read_PI = (VK[mci].ReadShowPI + _DISP_MAX_LEN - VK[mci].CNP_Target_Neg_Len) % _DISP_MAX_LEN;
						// 修改读取指针
						VK[mci].ReadShowPI = VK[mci].CNP_Read_PI;
					}
					else
					{
						VK[mci].CNP_Read_PI = VK[mci].ReadShowPI;
					}
					i = rsamplenum;// 检查道触发条件了， 强行退出检查条件，准读取数据
					break;
				}
			}
			else //if (VK[mci].CNP_Trig_Edge ==1)//   0: 上升沿触发/高于电压值触发；  1： 下降沿触发/低于电压值触发； 2： 高电平触发/高于电压值触发；3： 低电平触发/低于电压值触发
			{
				if (trigvalue < VK[mci].CNP_Trig_Value)
				{
					VK[mci].CNP_Trig_Status = 2;
					tstatus = 2;
					VK[mci].CNP_Counter = 0;
					if ((VK[mci].CNP_Target_Neg_Len >= 0) && (VK[mci].CNP_Target_Neg_Len < VK[mci].CNP_Target_Len))
					{
						VK[mci].CNP_Read_PI = (VK[mci].ReadShowPI + _DISP_MAX_LEN - VK[mci].CNP_Target_Neg_Len) % _DISP_MAX_LEN;
						//  修改读取指针
						VK[mci].ReadShowPI = VK[mci].CNP_Read_PI;
					}
					else
					{
						VK[mci].CNP_Read_PI = VK[mci].ReadShowPI;
					}
					i = rsamplenum;// 检查道触发条件了， 强行退出检查条件，准读取数据
					break;
				}
			}
			//---------------
			if (++VK[mci].ReadShowPI>_DISP_MAX_LEN)
				VK[mci].ReadShowPI = 0;
			//---------------
			i++;
			if (i >= rsamplenum)break;
			if (VK[mci].ReadShowPI == VK[mci].SaveShowPI)break;
			//-------------------
		}
	}
	//-------------------------------------

	///////////////////////////////////////
	if (tstatus == 2) // 正在等待N点完成
	{
		tchno = readdchnum;
		if (tchno > 10)tchno = 10;
		if (tchno < 1)tchno = 1;
		//rfactnum = 0;
		while (1)
		{
			for (i = 0; i < tchno; i++)
			{
				*adcbuffer++ = VK[mci].CHShowBuffer[i][VK[mci].ReadShowPI];
			}
			//=====================
			rfactnum++;
			VK[mci].CNP_Counter++;
			if (VK[mci].CNP_Counter >= VK[mci].CNP_Target_Len)// 退出N读取， 重新检查下一个N点周期
			{
				//////////////////////////////////
				tchno = VK[mci].CNP_Trig_Channel;
				lasttrigvalue = VK[mci].CHShowBuffer[tchno][VK[mci].ReadShowPI];//
				VK[mci].CNP_Trig_Status = 1; // 停止触发， 重新检查触发条件
				tstatus = 1;
				//-------------------------------
				if (++VK[mci].ReadShowPI>_DISP_MAX_LEN)// 退出之前要更新指针
					VK[mci].ReadShowPI = 0;
				//-------------------------------
				break;
			}
			//--------------
			if (++VK[mci].ReadShowPI>_DISP_MAX_LEN)
				VK[mci].ReadShowPI = 0;
			//----------------------------------------
			if (rfactnum >= rsamplenum)break;
			if (VK[mci].ReadShowPI == VK[mci].SaveShowPI)break;
			//-------------------
		}
	}
	//--------------------------------------
	return rfactnum;
}

