#if _MSC_VER > 1000
#pragma once
#endif 

#include "VK70xNMC_DAQ2.h"
#include "dvr_header.h"
#include <Windows.h>
#include <stdio.h>
#include <time.h>


int seNet_DefaultAfterChangeModelType(int mci)
{
	VK[mci].WorkMode = VKxxx_MODE_RTTX_SAMPLING;// 初始化采样模式
	VK[mci].LastWorkMode = VKxxx_MODE_RTTX_SAMPLING;
	//---------------------
	VK[mci].Channel = 8;// 固定4通道
	VK[mci].ReferenceVoltage = 4.000;//VK701N with PGA, 
	//--------------------
	if (VK[mci].SampleRate>100000) VK[mci].SampleRate = 100000;
	else if (VK[mci].SampleRate<1) VK[mci].SampleRate = 1;
	//---------------------
	if (VK[mci].SampleRate > 50000)
	{
		//VK[mci].DataFormat = 16;
		VK[mci].SampleDataFormat = VKxxx_DATAFORMAT_16BIT;
	}
	else
	{
		//VK[mci].DataFormat = 32;
		VK[mci].SampleDataFormat = VKxxx_DATAFORMAT_24BIT; // 
	}
	//------------------------
	//VK[mci].PackageSize = Get_USB_TXLen(VK[mci].SampleRate);
	VK[mci].SampleComand = 0;
	//------------------------
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
	printf("采集卡 [%d] 重新复位参数，其模式[VK[mci].WorkMode=%d] \n", mci, VK[mci].WorkMode);
#endif
	return 0;
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
//vk70xN disposal function
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////





int seNet_Send_ReadCommand(int mci, unsigned char cmd)//vCOM_CMD_RW_IO
{
	//#define vCOM_CMD_RW_IO         0x90  // write and read the IO,pWM, DAC, counter, temperature   
	//附加功能， Additional features//
	//功能1-PWM1
	//功能2-PWM2
	//功能11-DAC1
	//功能12-DAC2
	//功能21~24-IO1-IO4
	//功能31 - Counter+Freq
	//功能41 - temp+humiduty
	//VK[mci].UpdateFlag = funcflag;
	int i;
	unsigned char destpi[2];//防止buffer溢出
	i = 0;
	destpi[0] = vCOM_STATUS_REPONSE_START; // 固定
	destpi[1] = 0;
	//while (i < EP0_TXBUFLEN){ destpi[i++] = 0;};

	//i = tx_onedatumpackage_to_usbport(VKTCPServer.SockClient[mci], cmd, destpi, EP0_TXBUFLEN, 0);  // vCOM_CMD_RW_IO
	i = DisposalTXDatum(VKTCPServer.SockClient[mci], cmd, destpi, 2, 0);
	//Sleep(1);// 固定等待1ms 
	return i;
}
/*
---------------------------------------------------------------------------------------
命令0xA0: 设置读取系统参数
名称	内容	描述
同步头	0x55,0xEE	同步头字节
数据包长度	0x----	数据包长度
机身编号	0x0001	通用：任意数据，
验证是否设置仪器编号：数据等于仪器标编号的10字节之和，16bit，说明可以设置仪器编号。
命令	0xA0	命令
1-6	0x??	读“VK702NS”6字节, 写无效
7-12	0x??	读“S30x11” 软件版本 6字节, 写无效
13-18	0x??	读“H10001” 硬件版本6字节, 写无效
19	0x22	读，保留；写固定0x22，其它数据，不改序列号
20-35	0x??	R/W: 16字节，仪器编号
36	0x??	读，保留；写时，第20-35字节的时间数据的校验码
37	0x??	保留
38	0x??	0x00/0x80/0x81: 正常采样，LAN发送数据模式
0x8A：正常采样，SD卡保存数据
0x8B：文件下载模式，LAN/USB发SD卡的文件到服务器。
0x8F：保留，工厂模式测试模式
其它：正常采样，LAN发送数据模式
39	0x??	0x00: TimerA定时采样连续或PC发送N点命令（0x0000）
0x80：IO4中断触发ADC一次N点采样方式（0x8080）
0x99：以IO4中断作为ADC采样时钟的方式（0x8199）
其它：TimerA定时采样连续或PC发送N点命令（0x0000）
40	0x??	0x00：以BIN文件保存RAW数据
0x11：以TXT保存高精度电压信号的数据
其它：以BIN文件保存RAW数据
41	0x22	固定，其它数据，不改写时钟
42-49:	0x??	W/R: YYYY-MM-DD-HH-MM-SS-Week（8字节）
50	0x??	第42-49字节的时间数据的校验码
//------------
55-86:adc parameter
//------------
校验	0x--	校验码
---------------------------------------------------------------------------------------
*/
int seNet_Send_WriteSystemParameterToDevice(int mci,unsigned char flagswitchsetpara,unsigned char wrsnflag)
{
	unsigned char wbuf[128];
	//double rtp;
	int i, j, len;
	unsigned char checksum;
	int temp;
	time_t tmtime;
	struct tm *pitime;

	//--------------------
	for (j = 0; j < 128; j++)
	{
		wbuf[j] = 0;
	};
	//-------------------
	i = 0;
	//-------------------
	for (j = 0; j < 6; j++)wbuf[i++] = VK[mci].ModelName[j];//5
	for (j = 0; j < 6; j++)wbuf[i++] = VK[mci].HWVer[j];// 11
	for (j = 0; j < 6; j++)wbuf[i++] = VK[mci].SWVer[j];//17
	wbuf[i++] = wrsnflag;//18
	checksum = 0;
	for (j = 0; j < 16; j++)
	{
		wbuf[i++] = VK[mci].SN[j];//34
		checksum += VK[mci].SN[j];
	}
	wbuf[i++] = checksum;//35
	// 6+6+6+1+16+1=36
	//--------------------
	wbuf[i++] = VK[mci].Channel;//36//保留-通讯方式 
	//-------------------------
	if (VK[mci].WorkMode == VKxxx_MODE_RTTX_SAMPLING)wbuf[i++] = 0x00; // 采样模式 37
	else if (VK[mci].WorkMode == VKxxx_MODE_RTSAVE_SAMPLING)wbuf[i++] = 0x8A; // 采样模式 37
	else if (VK[mci].WorkMode == VKxxx_MODE_DOWNLOADFILE)wbuf[i++] = 0x8B; // 采样模式 37
	else if (VK[mci].WorkMode == VKxxx_MODE_FACOTRY)wbuf[i++] = 0x8F; // 采样模式 37
	else wbuf[i++] = 0x00; // 采样模式 37	
    //-------------------------
	if (VK[mci].SampleComand == VKxxx_SAMLEMETHOD_IDLE)wbuf[i++] = 0; // 采样方式 38
	else if (VK[mci].SampleComand == VKxxx_SAMLEMETHOD_CONTIMUE)wbuf[i++] = 0; // 采样方式 38
	else if (VK[mci].SampleComand == VKxxx_SAMLEMETHOD_NPOINTS)wbuf[i++] = 0; // 采样方式 38
	else if (VK[mci].SampleComand == VKxxx_SAMLEMETHOD_IO4_CONTIMUE)wbuf[i++] = 0x80; // 采样方式 38
	else if (VK[mci].SampleComand == VKxxx_SAMLEMETHOD_IO4_NPOINTS)wbuf[i++] = 0x80; // 采样方式 38
	else if (VK[mci].SampleComand == VKxxx_SAMLEMETHOD_IO4_ASADCCLOCK)wbuf[i++] = 0x99; // 采样方式 38
	else if (VK[mci].SampleComand == VKxxx_SAMLEMETHOD_TIMER_NPOINTS)wbuf[i++] = 0x9A; // 采样方式 38
	else wbuf[i++] = 0; // 采样方式 38	
	//----------------------
	if (VK[mci].SDFileFormat == VKxxx_SDFILEFMT_TEXT)wbuf[i++] = 0x11; //保存文件格式 39
	else wbuf[i++] = 0; //保存文件格式 39
	//-------------------
	wbuf[i++] = 0x22;// 固定 40
	//--------------------
	//time_t tmtime;
	//struct tm *tmltime;
	time(&tmtime);//获取Unix时间戳。 
	pitime = localtime(&tmtime);//转为时间结构。

	temp = pitime->tm_year + 1900;
	wbuf[i++] = (unsigned char)(temp / 256);//41
	wbuf[i++] = (unsigned char)(temp % 256);//42
	temp = (pitime->tm_mon) + 1;
	if (temp > 12)temp = 12;
	if (temp < 1)temp = 1;
	wbuf[i++] = (unsigned char)temp;////43
	wbuf[i++] = (unsigned char)pitime->tm_mday;//44
	wbuf[i++] = (unsigned char)pitime->tm_hour;//45
	wbuf[i++] = (unsigned char)pitime->tm_min;//46
	wbuf[i++] = (unsigned char)pitime->tm_sec;//47
	wbuf[i++] = 0;//48
	checksum = 0;
	for (j = 41; j < 49; j++)
	{
		checksum += wbuf[j];
	}
	wbuf[i++] = checksum;//49
	//===========================================
	//通道x采集电压输入范围
	//1-8 bytes
	//-------------------------------------------
	wbuf[i] = VK[mci].VolRange[0]; i++; //50 Get_SetupPGAGains(uSet_VolRange[0]);
	wbuf[i] = VK[mci].VolRange[1]; i++;  //51
	wbuf[i] = VK[mci].VolRange[2]; i++;  // 52
	wbuf[i] = VK[mci].VolRange[3]; i++;  // 53	
	//------------------------
	wbuf[i] = (unsigned char)VK[mci].ReferenceVoltage; i++;//54
	//------------------------
	//采样模式：1/16：16bit， 2/24:24bit； 其它无效
	//60 bytes
	//-----------------------
	wbuf[i] = VK[mci].SampleDataFormat; i++;//55,采样模式  采样模式：1/16：16bit， 2/24:24bit； 其它无效 
	//------------------------
	// 采样率设置（默认1KHz）
	//61-63 bytes
	//------------------------
	temp = VK[mci].SampleRate;
	if (temp>125000)temp = 125000;
	wbuf[i] = (temp >> 16) & 0xFF; i++;//56
	wbuf[i] = (temp >> 8) & 0xFF; i++;//57
	wbuf[i] = (temp)& 0xFF; i++;//58
	//------------------------
	// 采集卡上传通道设置（暂保留），0/8： 8通道
	//------------------------
	// wbuf[i] = USB_Fact_RX_CH_NUM; i++; // 传输通道， 1，2，4，8 
	////64 bytes
	wbuf[i] = VK[mci].Channel; i++;//59
	//------------------------
	// N点采样点数默认值；设置参数为第11-14字节，高字节在前，注意第15字节必须固定0x22，才能设置N点采样数目；否则此设置参数无意义；
	//注意第15字节必须固定0x22
	//65-69 bytes
	//-------------------------------------
	temp = VK[mci].Npoints;
	wbuf[i] = (temp >> 24) & 0xFF; i++;//60
	wbuf[i] = (temp >> 16) & 0xFF; i++;//61
	wbuf[i] = (temp >> 8) & 0xFF; i++;//62
	wbuf[i] = (temp)& 0xFF; i++;//63

	//---------------------------   文件索引
	temp = VK[mci].SDFileIndex;   // 1000=1000ms
	wbuf[i] = (temp >> 24) & 0xFF; i++;//64
	wbuf[i] = (temp >> 16) & 0xFF; i++;//65
	wbuf[i] = (temp >> 8) & 0xFF; i++;//66
	wbuf[i] = (temp)& 0xFF; i++;//67

	//==========================================
	if (flagswitchsetpara == 0x22)
	{
		wbuf[i] = 0x22; i++;//68
		wbuf[i] = VK[mci].Cal_RTC_Direction; i++;//69
		temp = VK[mci].Cal_RTC_Value;   // 
		wbuf[i] = (temp >> 8) & 0xFF; i++;//70
		wbuf[i] = (temp)& 0xFF; i++;//71	
	}
	else // //0x33
	{
		if (VK[mci].Tintervals > 1) { wbuf[i] = 0x33; i++; }// 68
		else { wbuf[i] = 0x0; i++; }

		temp = VK[mci].Tintervals;   // 
		wbuf[i] = (temp >> 16) & 0xFF; i++;//69
		wbuf[i] = (temp >> 8) & 0xFF; i++;//70
		wbuf[i] = (temp)& 0xFF; i++;//71		
	}
	//----------------------------
	wbuf[i++] = 0;//72
	wbuf[i++] = 0;//73
	//wpi = wpifromlan + 74;
	//VK[mci].CVMode[0] = *(wpifromlan + 74);//75 
	//VK[mci].CVMode[1] = *(wpifromlan + 75);//76 
	//VK[mci].CVMode[2] = *(wpifromlan + 76);//77 
	//VK[mci].CVMode[3] = *(wpifromlan + 77);//78 
	wbuf[i++] = (unsigned char)VK[mci].CVMode[0];
	wbuf[i++] = (unsigned char)VK[mci].CVMode[1];
	wbuf[i++] = (unsigned char)VK[mci].CVMode[2];
	wbuf[i++] = (unsigned char)VK[mci].CVMode[3];
	//----------------------------
	len = DisposalTXDatum(VKTCPServer.SockClient[mci], vCOM_CMD_RW_SYSTEM, wbuf, i, 1);  // 
	//----------------------------
	return len;
}




int seNet_Swtich_SystemMode(int mci, unsigned char modeval)
{
	int i, tstatus = 0;
	unsigned char trmode = 0;
	unsigned char tempdatbuf[16];
	for (i = 0; i < 16; i++)tempdatbuf[i] = 0;	
	//--------------------------   //0x000
	if ((modeval == 0) || (modeval == 0x80) || (modeval == 0x81))
	{
		trmode = modeval;
		VK[mci].WorkMode = VKxxx_MODE_RTTX_SAMPLING;
	}
	else if ((modeval == 1) || (modeval == 0x8A))
	{
		trmode = 0x8A;
		VK[mci].WorkMode = VKxxx_MODE_RTSAVE_SAMPLING;
	}
	else if ((modeval == 2) || (modeval == 0x8B))
	{
		trmode = 0x8B;
		VK[mci].WorkMode = VKxxx_MODE_DOWNLOADFILE;
	}
	else if ((modeval == 3) || (modeval == 0x8F))
	{
		trmode = 0x8F;
		VK[mci].WorkMode = VKxxx_MODE_FACOTRY;
	}
	else
	{
		trmode = 0;
		VK[mci].WorkMode = VKxxx_MODE_RTTX_SAMPLING;
	}
	tempdatbuf[0] = trmode; // 采样模式
	tempdatbuf[1] = 0x80; // 采样方式
	tempdatbuf[2] = 0; // 
	//---------------------------
	for (i = 3; i < 8; i++) tempdatbuf[i] = 0;
	//---------------------- 
	tstatus = DisposalTXDatum(VKTCPServer.SockClient[mci], vCOM_CMD_RW_MODE, tempdatbuf, 8, 1);  //vCOM_CMD_RW_IO
	return tstatus;
	//----------------------
}