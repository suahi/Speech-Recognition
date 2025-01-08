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
// facotry  function
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// system mode function
//==========================================================================
int Def_Function_OUTfmt VK70xNMC_Set_SystemMode(int mci, int modelval, int samplemethod, int sdfilefmt)
{
	//unsigned short int tdac1=0xFFFF;
	int i, tstatus = 0;
	unsigned char trmode = 0;
	unsigned char trmethod = 0;
	unsigned char trfilrfmt = 0;
	//-------------------------
	unsigned char tempdatbuf[16];
	for (i = 0; i < 16; i++)tempdatbuf[i] = 0;
	//////////////////////////////////////////////////////////  
	if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开  

	//if (ThreadRunningState==0)return -11;  //服务未打开  
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端  
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -13;
	//////////////////////////////////////////////////////////
	//--------------------
	VK70xNMC_StopSampling(mci);
	//-------------------------
	//0x0000 ： 正常模式
	//0x8080 ： IO中断触发ADC采样模式
	//0x8199 ： 设置IO4做输入时钟作为ADC采样时钟
	//////////////////////////////////////////////////
	//temp = *usbdatpi++;
	//if ((temp == 0) || (temp == 0x80) || (temp == 0x81))tmode = SYS_MODE_TXDATUMBYLAN; // 正常采样模式， LAN/WIFI传输
	//else if (temp == 0x8A)tmode = SYS_MODE_SDSAVEDATUM;   // 正常采样模式， SD卡存储模式
	//else if (temp == 0x8B)tmode = SYS_MODE_DOWNLOADING;   // 下载数据模式
	//else if (temp == 0x8F)tmode = SYS_MODE_FACTORY;       // 保留，  工厂模式
	//else tmode = SYS_MODE_TXDATUMBYLAN; // 正常采样模式， LAN/WIFI传输
	////--------------------------------------
	//temp = *usbdatpi++;
	//if (temp == 0)tselADCCLK = FUNC_NORMAL_SAMPLING; // TIMERA时钟，通过TIMERA定时中断触发连续采样 

	//else if (temp == 0x80)tselADCCLK = FUNC_NPOTINT_SAMPLING;   // TIMERA时钟， 通过IO4触发采样N点采样
	//else if (temp == 0x99)tselADCCLK = FUNC_TRIGADC_FORMIO4CLOCKIN;   // IO4 作为时钟采样

	//else if (temp == 0x9A)tselADCCLK = FUNC_TIMERA_NPOTINT_SAMPLING;   // 定时采集
	//else tselADCCLK = FUNC_NORMAL_SAMPLING;    // TIMERA时钟，通过TIMERA定时中断触发连续采样 
	////-------------------------------------
	//temp = *usbdatpi++;
	//if (temp == 0x11)tselsaveMethod = FUNC_SAVEASVOLRESULT; // ADC采样计算后开始存储
	//else tselsaveMethod = FUNC_SAVEASRAWDATUM;    //ADC采样后直接存储 原始 RAW 数据
	//--------------------------
	//VkserailMode = 0;
	//0x00/0x80/0x81: LAN 发送数据模式
	//0x8A： SD 卡保存数据模式
	//0x8B：文件下载模式， 
	//0x8F：保留，工厂模式测试模式
	//其它： LAN 发送数据模式
	//GetCtrlVal(panelHandle,PANEL_RADIOBUTTON_SAMPING1,&tstatus);
	//if(tstatus==0){trmode = 0x8A; VkserailMode = 10; } //  1： 实时SD存储采集，
	//else {trmode = 0x80;VkserailMode = 0;}

	//0x00: 在线命令触发采样方式
	//0x80：IO4 中断触发 ADC 一次 N 点采样方式
	//0x99：以 IO4 中断作为 ADC 采样时钟的方式
	//0x9A：定时触发采集
	//其它： 在线命令触发采样方式
	//  VKxxx_MODE_RTTX_SAMPLING = 0x00,    //   real time 实时传输模式    直接命令、IO4中断触发以及IO4时钟同步触发采集数据或切换模式，开始连续采集、N点采集，停止采集等,
	//	VKxxx_MODE_RTSAVE_SAMPLING,      //   real time 保存到SD卡模式  直接命令、IO4中断触发以及IO4时钟同步触发采集数据或切换模式，开始连续采集、N点采集，停止采集等,
	//	VKxxx_MODE_DOWNLOADFILE,         //   离线文件下载模式                 ：下载文件或切换模式，需要命令下载存储的文件
	//	VKxxx_MODE_UDISK,                //    USB U盘文件模式                  :  下载文件或切换模式，所有总线交由USB文件系统
	//	VKxxx_MODE_FACOTRY,              //   工厂测试模式                     : 用于烧录工厂设置信息，工厂测试等等
	//	//------------------------------
	//--------------------------   //0x000
	if ((modelval == 0) || (modelval == 0x80) || (modelval == 0x81))
	{
		trmode = modelval;
		VK[mci].WorkMode = VKxxx_MODE_RTTX_SAMPLING;
	}
	else if ((modelval == 1) || (modelval == 0x8A))
	{
		trmode = 0x8A;
		VK[mci].WorkMode = VKxxx_MODE_RTSAVE_SAMPLING;
	}
	else if ((modelval == 2) || (modelval == 0x8B))
	{
		trmode = 0x8B;
		VK[mci].WorkMode = VKxxx_MODE_DOWNLOADFILE;
	}
	else if ((modelval == 3) || (modelval == 0x8F))
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

	//0x00/0x80/0x81: LAN 发送数据模式
	//0x8A： SD 卡保存数据模式
	//0x8B：文件下载模式， 
	//0x8F：保留，工厂模式测试模式
	//其它： LAN 发送数据模式
	//VKxxx_SAMLEMETHOD_IDLE = 0x00,    //  
	//	VKxxx_SAMLEMETHOD_CONTIMUE = 0x01,
	//	VKxxx_SAMLEMETHOD_NPOINTS = 0x02,
	//	VKxxx_SAMLEMETHOD_IO4_CONTIMUE = 0x11,
	//	VKxxx_SAMLEMETHOD_IO4_NPOINTS = 0x12,
	//	VKxxx_SAMLEMETHOD_IO4_ASADCCLOCK = 0x13,
	//	VKxxx_SAMLEMETHOD_TIMER_NPOINTS = 0x21,
	if ((samplemethod == 0) || (samplemethod == 0x01))
	{
		trmethod = 0;
		VK[mci].SampleComand = VKxxx_SAMLEMETHOD_CONTIMUE;
	}
	else if ((samplemethod == 12) || (samplemethod == 0x12) || (samplemethod == 0x80))
	{
		trmethod = 0x80;
		VK[mci].SampleComand = VKxxx_SAMLEMETHOD_IO4_NPOINTS;
	}
	else if ((samplemethod == 13) || (samplemethod == 0x13) || (samplemethod == 0x99))
	{
		trmethod = 0x99;
		VK[mci].SampleComand = VKxxx_SAMLEMETHOD_IO4_ASADCCLOCK;
	}
	else if ((samplemethod == 21) || (samplemethod == 0x21) || (samplemethod == 0x9A))
	{
		trmethod = 0x9A;
		VK[mci].SampleComand = VKxxx_SAMLEMETHOD_TIMER_NPOINTS;
	}
	else if (samplemethod == 0x7E)
	{
		trmethod = 0x7E;
		VK[mci].SampleComand = VKxxx_SAMLEMETHOD_CONTIMUE;
	}
	else
	{
		trmethod = 0;
		VK[mci].SampleComand = VKxxx_SAMLEMETHOD_CONTIMUE;
	}
	tempdatbuf[1] = trmethod; // 采样方式
	//0x00: 在线命令触发采样方式
	//0x80：IO4 中断触发 ADC 一次 N 点采样方式
	//0x99：以 IO4 中断作为 ADC 采样时钟的方式
	//其它： 在线命令触发采样方式					 
	//----------------------
	// VKxxx_SDFILEFMT_BIN = 0,
	//	VKxxx_SDFILEFMT_TEXT,
	//0x00：以 BIN 文件保存 RAW 数据
	//0x11：以 TXT 保存高精度电压信号的数据
	//其它：以 BIN 文件保存 RAW 数据
	if ((sdfilefmt == 11) || (sdfilefmt == 0x11) || (sdfilefmt == 0x01))
	{
		trfilrfmt = 0x11;
		VK[mci].SDFileFormat = VKxxx_SDFILEFMT_TEXT;
	}
	else
	{
		trfilrfmt = 0;
		VK[mci].SDFileFormat = VKxxx_SDFILEFMT_BIN;
	}
	tempdatbuf[2] = trfilrfmt;// VK[mci].SDFileFormat; //保存文件格式
	//---------------------------
	for (i = 3; i < 8; i++) tempdatbuf[i] = 0;
	//----------------------
	//DisposalTXDatum(vCOM_CMD_RW_MODE,tempdatbuf,13,true);  
	tstatus = DisposalTXDatum(VKTCPServer.SockClient[mci], vCOM_CMD_RW_MODE, tempdatbuf, 8, 1);  //vCOM_CMD_RW_IO
	return tstatus;
	//////////////////////////////////////////////////
}


//int samplerate, int npoints, int timeintervals, int bitmode, int *para
int Def_Function_OUTfmt  VK70xNMC_Set_DeviceDefaultParameter(int mci, char *wrmodel, char *wrsn, int *para)
{   // 其它默认
	//char           ModelName[7]; // 采集卡的项目名称，保留 
	//char           SWVer[7];     // 采集卡的软件版本，保留 
	//char           HWVer[7];     // 采集卡的硬件版本，保留  
	//char           SN[11];       // 采集卡的序列号， 用于绑定采集卡
	int i, tempp;
	//time_t t;
	//struct tm *lt;
	//=====================================
	if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开  

	//if (ThreadRunningState==0)return -11;  //服务未打开  
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -13;
	//--------------------
	VK70xNMC_StopSampling(mci);
	//--------------------
	for (i = 0; i < 6; i++)
	{
		VK[mci].ModelName[i] = *wrmodel++;
	}
	VK[mci].ModelName[6] = '\0';

	for (i = 0; i < 16; i++)
	{
		VK[mci].SN[i] = *wrsn++;
	}
	VK[mci].SN[16] = '\0';
	//-----------------------------------
	///////////////////////////////////////
	//int volrange[4],
	//int iepefalg[8],
	//int samplerate, 
	//int npoints, 
	//int timeintervals, 
	//int bitmode,

	//int SelvCOM;//37//保留-通讯方式  VK[mci].SelvCOM
	//itn WorkMode; // 采样模式 38
	//int SampleComand; // 采样模式; 0x00:   停止/待采样模式 
	//int Channel;//USB_Fact_RX_CH_NUM; i++; // 传输通道， 1，2，4，8 
	//int IO4TrigEdge
	//int SDFileFormat; //保存文件格式 40
	//int SDFileIndex//
	//int Sysnctimeflag//[12]
	//int OffsetRatio[8]
	//int CalibrationRatio[8]
	//--------------------------------
	VK[mci].VolRange[0] = *(para + 0);//GetGainValue_NOPGA(volrg15);
	VK[mci].VolRange[1] = *(para + 1);// GetGainValue_NOPGA(volrg26);
	VK[mci].VolRange[2] = *(para + 2);// GetGainValue_NOPGA(volrg37);
	VK[mci].VolRange[3] = *(para + 3);// GetGainValue_NOPGA(volrg48);
	VK[mci].VolRange[4] = VK[mci].VolRange[0];
	VK[mci].VolRange[5] = VK[mci].VolRange[1];
	VK[mci].VolRange[6] = VK[mci].VolRange[2];
	VK[mci].VolRange[7] = VK[mci].VolRange[3];

	//for (i = 0; i < 8; i++)VK[mci].IEPEflag[i] = *(para + 4 + i);

	VK[mci].SampleRate = *(para + 4);
	VK[mci].Npoints = *(para + 5);
	VK[mci].Tintervals = *(para + 6);
	VK[mci].SampleDataFormat = *(para + 7);

	//-------------------------------
	if ((VK[mci].SampleDataFormat == 2) || (VK[mci].SampleDataFormat == 3) || (VK[mci].SampleDataFormat == 24) || (VK[mci].SampleDataFormat == 32))VK[mci].SampleDataFormat = 2;
	else VK[mci].SampleDataFormat = 1;

	if (VK[mci].SampleRate > 100000)VK[mci].SampleRate = 100000;
	if (VK[mci].SampleRate > 50000)
	{
		if (VK[mci].SampleDataFormat == 2) VK[mci].SampleDataFormat = 1;
	}
	//----------------------------------

	VK[mci].Channel = *(para + 8);//37//保留-通讯方式  VK[mci].SelvCOM	
	//--------------------------
	tempp = *(para + 9); // 系统模式， 不能出现工厂模式和文件下载模式
	if ((tempp == 0) || (tempp == 0x80) || (tempp == 0x81))
	{
		//tempp = tempp;
		VK[mci].WorkMode = VKxxx_MODE_RTTX_SAMPLING;
	}
	else if ((tempp == 1) || (tempp == 0x8A))
	{
		tempp = 0x8A;
		VK[mci].WorkMode = VKxxx_MODE_RTSAVE_SAMPLING;
	}
	//else if ((tempp == 2) || (tempp == 0x8B))
	//{
	//	tempp = 0x8B;
	//	//VK[mci].WorkMode = VKxxx_MODE_DOWNLOADFILE;
	//}
	//else if ((tempp == 3) || (tempp == 0x8F))
	//{
	//	tempp = 0x8F;
	///	//VK[mci].WorkMode = VKxxx_MODE_FACOTRY;
	//}
	else
	{
		tempp = 0;
		VK[mci].WorkMode = VKxxx_MODE_RTTX_SAMPLING;
		//VK[mci].WorkMode = VKxxx_MODE_RTTX_SAMPLING;
	}
	//--------------------------------
	//if (tmode == VKxxx_MODE_DOWNLOADFILE)
	//{
	//	sDFile_CheckSDCardDownloadCondition(mci);
	//	VK[mci].WorkMode = tmode;
	//#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
	//	printf("用户使用缺省函数重新设置采集卡[%d]sd下载模式=[%d]  \n", mci, VK[mci].WorkMode);
	//#endif
	//}
	//else VK[mci].WorkMode = tmode;
	//-----------------------------
	//VK[mci].SampleComand = *(para + 10); // 采样模式; 0x00:   停止/待采样模式 
	tempp = *(para + 10); // 采样模式; 0x00:   停止/待采样模式 
	if ((tempp == 0) || (tempp == 0x01))
	{
		tempp = 0;
		VK[mci].SampleComand = VKxxx_SAMLEMETHOD_CONTIMUE;
	}
	else if ((tempp == 12) || (tempp == 0x12) || (tempp == 0x80))
	{
		tempp = 0x80;
		VK[mci].SampleComand = VKxxx_SAMLEMETHOD_IO4_NPOINTS;
	}
	else if ((tempp == 13) || (tempp == 0x13) || (tempp == 0x99))
	{
		tempp = 0x99;
		VK[mci].SampleComand = VKxxx_SAMLEMETHOD_IO4_ASADCCLOCK;
	}
	else if ((tempp == 21) || (tempp == 0x21) || (tempp == 0x9A))
	{
		tempp = 0x9A;
		VK[mci].SampleComand = VKxxx_SAMLEMETHOD_TIMER_NPOINTS;
	}
	else if (tempp == 0x7E)
	{
		tempp = 0x7E;
		VK[mci].SampleComand = VKxxx_SAMLEMETHOD_CONTIMUE;
	}
	else
	{
		tempp = 0;
		VK[mci].SampleComand = VKxxx_SAMLEMETHOD_CONTIMUE;
	}
	//-----------------------------
	VK[mci].Channel = *(para + 11);//USB_Fact_RX_CH_NUM; i++; // 传输通道， 1，2，4，8 
	//VK[mci].SDFileFormat = *(para + 12); //保存文件格式 40
	tempp = *(para + 12); //保存文件格式 40
	if ((tempp == 11) || (tempp == 0x11) || (tempp == 0x01))
	{
		tempp = 0x11;
		VK[mci].SDFileFormat = VKxxx_SDFILEFMT_TEXT;
	}
	else
	{
		tempp = 0;
		VK[mci].SDFileFormat = VKxxx_SDFILEFMT_BIN;
	}
	VK[mci].SDFileIndex = *(para + 13);//
	//Sysnctimeflag = *(para + 14);// 
	//VK[mci].IO4TrigeEdage = *(para + 15);
	//for (i = 0; i < 8; i++)VK[mci].OffsetRatio[i] = *(para + 16 + i);
	//for (i = 0; i < 8; i++)VK[mci].CalibrationRatio[i] = *(para + 24 + i);
	// *(para + 14);// 
	// *(para + 15);
	for (i = 0; i < 8; i++)VK[mci].CVMode[i] = *(para + 16 + i);
	//------------------------------------	
	//i = subeNet_DisposalTXSockDatum(VKTCPServer.SockClient[mci], vCOM_CMD_RW_SG, wbuf, 16, 1);  //vCOM_CMD_RW_IO
	i = seNet_Send_WriteSystemParameterToDevice(mci, 0x33, 0x22);//&VKUSBDevice.Client[mci]
	return i;//
}




//int samplerate, int npoints, int timeintervals, int bitmode, int *para
int Def_Function_OUTfmt  VK70xNMC_Set_DefaultParameter(int mci, int *para)
{   // 其它默认
	//char           ModelName[7]; // 采集卡的项目名称，保留 
	//char           SWVer[7];     // 采集卡的软件版本，保留 
	//char           HWVer[7];     // 采集卡的硬件版本，保留  
	//char           SN[11];       // 采集卡的序列号， 用于绑定采集卡
	int i, tempp;
	//time_t t;
	//struct tm *lt;
	//=====================================
	if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开  

	//if (ThreadRunningState==0)return -11;  //服务未打开  
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -13;
	//--------------------
	VK70xNMC_StopSampling(mci);
	//----------------------------------

	//for (i = 0; i < 6; i++)
	//{
	//	VK[mci].ModelName[i] = *wrmodel++;
	//}
	//VK[mci].ModelName[6] = '\0';
	//
	//for (i = 0; i < 16; i++)
	//{
	//	VK[mci].SN[i] = *wrsn++;
	//}
	//VK[mci].SN[16] = '\0';
	//-----------------------------------
	///////////////////////////////////////
	//int volrange[4],
	//int iepefalg[8],
	//int samplerate, 
	//int npoints, 
	//int timeintervals, 
	//int bitmode,

	//int SelvCOM;//37//保留-通讯方式  VK[mci].SelvCOM
	//itn WorkMode; // 采样模式 38
	//int SampleComand; // 采样模式; 0x00:   停止/待采样模式 
	//int Channel;//USB_Fact_RX_CH_NUM; i++; // 传输通道， 1，2，4，8 
	//int IO4TrigEdge
	//int SDFileFormat; //保存文件格式 40
	//int SDFileIndex//
	//int Sysnctimeflag//[12]
	//int OffsetRatio[8]
	//int CalibrationRatio[8]
	//--------------------------------
	VK[mci].VolRange[0] = *(para + 0);//GetGainValue_NOPGA(volrg15);
	VK[mci].VolRange[1] = *(para + 1);// GetGainValue_NOPGA(volrg26);
	VK[mci].VolRange[2] = *(para + 2);// GetGainValue_NOPGA(volrg37);
	VK[mci].VolRange[3] = *(para + 3);// GetGainValue_NOPGA(volrg48);
	VK[mci].VolRange[4] = VK[mci].VolRange[0];
	VK[mci].VolRange[5] = VK[mci].VolRange[1];
	VK[mci].VolRange[6] = VK[mci].VolRange[2];
	VK[mci].VolRange[7] = VK[mci].VolRange[3];

	//for (i = 0; i < 8; i++)VK[mci].IEPEflag[i] = *(para + 4 + i);


	

	VK[mci].SampleRate = *(para + 4);
	VK[mci].Npoints = *(para + 5);
	VK[mci].Tintervals = *(para + 6);
	VK[mci].SampleDataFormat = *(para + 7);

	//-------------------------------
	if ((VK[mci].SampleDataFormat == 2) || (VK[mci].SampleDataFormat == 3) || (VK[mci].SampleDataFormat == 24) || (VK[mci].SampleDataFormat == 32))VK[mci].SampleDataFormat = 2;
	else VK[mci].SampleDataFormat = 1;

	if (VK[mci].SampleRate > 100000)VK[mci].SampleRate = 100000;
	if (VK[mci].SampleRate > 50000)
	{
		if (VK[mci].SampleDataFormat == 2) VK[mci].SampleDataFormat = 1;
	}
	//----------------------------------

	VK[mci].Channel = *(para + 8);//37//保留-通讯方式  VK[mci].SelvCOM	
	//--------------------------
	tempp = *(para + 9); // 系统模式， 不能出现工厂模式和文件下载模式
	if ((tempp == 0) || (tempp == 0x80) || (tempp == 0x81))
	{
		//tempp = tempp;
		VK[mci].WorkMode = VKxxx_MODE_RTTX_SAMPLING;
	}
	else if ((tempp == 1) || (tempp == 0x8A))
	{
		tempp = 0x8A;
		VK[mci].WorkMode = VKxxx_MODE_RTSAVE_SAMPLING;
	}
	//else if ((tempp == 2) || (tempp == 0x8B))
	//{
	//	tempp = 0x8B;
	//	//VK[mci].WorkMode = VKxxx_MODE_DOWNLOADFILE;
	//}
	//else if ((tempp == 3) || (tempp == 0x8F))
	//{
	//	tempp = 0x8F;
	///	//VK[mci].WorkMode = VKxxx_MODE_FACOTRY;
	//}
	else
	{
		tempp = 0;
		VK[mci].WorkMode = VKxxx_MODE_RTTX_SAMPLING;
		//VK[mci].WorkMode = VKxxx_MODE_RTTX_SAMPLING;
	}
	//--------------------------------
	//if (tmode == VKxxx_MODE_DOWNLOADFILE)
	//{
	//	sDFile_CheckSDCardDownloadCondition(mci);
	//	VK[mci].WorkMode = tmode;
	//#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
	//	printf("用户使用缺省函数重新设置采集卡[%d]sd下载模式=[%d]  \n", mci, VK[mci].WorkMode);
	//#endif
	//}
	//else VK[mci].WorkMode = tmode;
	//-----------------------------
	//VK[mci].SampleComand = *(para + 10); // 采样模式; 0x00:   停止/待采样模式 
	tempp = *(para + 10); // 采样模式; 0x00:   停止/待采样模式 
	if ((tempp == 0) || (tempp == 0x01))
	{
		tempp = 0;
		VK[mci].SampleComand = VKxxx_SAMLEMETHOD_CONTIMUE;
	}
	else if ((tempp == 12) || (tempp == 0x12) || (tempp == 0x80))
	{
		tempp = 0x80;
		VK[mci].SampleComand = VKxxx_SAMLEMETHOD_IO4_NPOINTS;
	}
	else if ((tempp == 13) || (tempp == 0x13) || (tempp == 0x99))
	{
		tempp = 0x99;
		VK[mci].SampleComand = VKxxx_SAMLEMETHOD_IO4_ASADCCLOCK;
	}
	else if ((tempp == 21) || (tempp == 0x21) || (tempp == 0x9A))
	{
		tempp = 0x9A;
		VK[mci].SampleComand = VKxxx_SAMLEMETHOD_TIMER_NPOINTS;
	}
	else if (tempp == 0x7E)
	{
		tempp = 0x7E;
		VK[mci].SampleComand = VKxxx_SAMLEMETHOD_CONTIMUE;
	}
	else
	{
		tempp = 0;
		VK[mci].SampleComand = VKxxx_SAMLEMETHOD_CONTIMUE;
	}
	//-----------------------------
	VK[mci].Channel = *(para + 11);//USB_Fact_RX_CH_NUM; i++; // 传输通道， 1，2，4，8 
	//VK[mci].SDFileFormat = *(para + 12); //保存文件格式 40
	tempp = *(para + 12); //保存文件格式 40
	if ((tempp == 11) || (tempp == 0x11) || (tempp == 0x01))
	{
		tempp = 0x11;
		VK[mci].SDFileFormat = VKxxx_SDFILEFMT_TEXT;
	}
	else
	{
		tempp = 0;
		VK[mci].SDFileFormat = VKxxx_SDFILEFMT_BIN;
	}
	VK[mci].SDFileIndex = *(para + 13);//
	//Sysnctimeflag = *(para + 14);// 
	//VK[mci].IO4TrigeEdage = *(para + 15);
	//for (i = 0; i < 8; i++)VK[mci].OffsetRatio[i] = *(para + 16 + i);
	//for (i = 0; i < 8; i++)VK[mci].CalibrationRatio[i] = *(para + 24 + i);
	// *(para + 14);// 
	// *(para + 15);//
	for (i = 0; i < 8; i++)VK[mci].CVMode[i] = *(para + 16 + i);//
	//------------------------------------	
	//i = subeNet_DisposalTXSockDatum(VKTCPServer.SockClient[mci], vCOM_CMD_RW_SG, wbuf, 16, 1);  //vCOM_CMD_RW_IO
	i = seNet_Send_WriteSystemParameterToDevice(mci, 0x33, 0);//&VKUSBDevice.Client[mci]
	return i;//
}

//===================================================================
int Def_Function_OUTfmt VK70xNMC_Set_eNetParameter(int mci, char *para, int len)		//VK702HU_StopSampling
{
	unsigned char wbuf[64];  //128
	//unsigned short int tvol;
	int i = 0;
	int len1;
	//---------------------
	// 采集卡如果MAC设置需要  len>=50  ;  小于50， MAC设置将会忽略。
	//---------------------

	len1 = len;
	if (len1<23)return -5;// 参数错误或参数过少
	//-----------------------------
	if (len1 > 64)len1 = 64;
	for (i = 0; i< 64; i++)wbuf[i] = 0;
	//----------------------------
	for (i = 0; i< len1; i++)wbuf[i] = *para++;   // 请求读取操作
	////////////////////////////////////////////////////
	i = DisposalTXDatum(VKTCPServer.SockClient[mci], vCOM_CMD_RW_WIFIPARA, wbuf, len1, 1);
	return i;
}



////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// factory  function
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

int Def_Function_OUTfmt VK70xNMC_Get_SystemMode(int mci, int *sysmode, int *samplecmd, int *sdfilefmt, int timeout)
{
	if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开 
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -13;
	//----------------------------------------------
	VK[mci].UpdateFlag = -1;
	seNet_Send_ReadCommand(mci, vCOM_CMD_RW_MODE);
	//----------------------------------------------
	while ((timeout > 0) && (VK[mci].UpdateFlag < 0))
	{
		timeout--;
		Sleep(1);
	}
	if (VK[mci].UpdateFlag < 0)return (VK[mci].UpdateFlag);
	//---------------------------
	*sysmode = VK[mci].WorkMode;
	*samplecmd = VK[mci].SampleComand;
	*sdfilefmt = VK[mci].SDFileFormat;
	//---------------------------------------------
	return (VK[mci].UpdateFlag);// 
}



int Def_Function_OUTfmt VK70xNMC_Get_DeviceDefaultParameter(int mci, char *rdmodol, char *rdswver, char *rdhdver, char *rdsn, int *para, int timeout)
{
	int i;
	if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开 
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -13;
	//----------------------------------------------
	VK[mci].UpdateFlag = -1;
	seNet_Send_ReadCommand(mci, vCOM_CMD_RW_SYSTEM);
	//----------------------------------------------
	while ((timeout > 0) && (VK[mci].UpdateFlag < 0))
	{
		timeout--;
		Sleep(1);
	}
	if (VK[mci].UpdateFlag < 0)return (VK[mci].UpdateFlag);
	//----------------------------------
	for (i = 0; i < 6; i++)
	{
		*rdmodol++ = VK[mci].ModelName[i];
		*rdswver++ = VK[mci].SWVer[i];
		*rdhdver++ = VK[mci].HWVer[i];
	}
	*rdmodol = '\0';
	*rdswver = '\0';
	*rdhdver = '\0';
	for (i = 0; i < 16; i++)
	{
		*rdsn++ = VK[mci].SN[i];
	}
	*rdsn = '\0';
	//-----------------------------------
	*(para + 0) = VK[mci].VolRange[0];
	*(para + 1) = VK[mci].VolRange[1];
	*(para + 2) = VK[mci].VolRange[2];
	*(para + 3) = VK[mci].VolRange[3];

	*(para + 4) = VK[mci].SampleRate;
	*(para + 5) = VK[mci].Npoints;
	*(para + 6) = VK[mci].Tintervals;
	*(para + 7) = VK[mci].SampleDataFormat;

	*(para + 8) = VK[mci].Channel;//37//保留-通讯方式  VK[mci].SelvCOM
	*(para + 9) = VK[mci].WorkMode; // 采样模式 38
	*(para + 10) = VK[mci].SampleComand; // 采样模式; 0x00:   停止/待采样模式 
	*(para + 11) = VK[mci].Channel;//USB_Fact_RX_CH_NUM; i++; // 传输通道， 1，2，4，8 
	*(para + 12) = VK[mci].SDFileFormat; //保存文件格式 40
	*(para + 13) = VK[mci].SDFileIndex;//
    *(para + 14) = 0;
    *(para + 15) = 0;
	for (i = 0; i < 4; i++)*(para + 16 + i) = VK[mci].CVMode[i];//
	//---------------------------------------------
	return (VK[mci].UpdateFlag);// 
}

int Def_Function_OUTfmt VK70xNMC_Get_eNetParameter(int mci, char *tvalue, int timeout)
{
	int i;
	if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开 
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -13;
	//----------------------------------------------
	VK[mci].UpdateFlag = -1;
#if (_DEBUG_VK70xxMC_LIB_>0)
	printf("--------------------------------------\n");
	printf("发送到连接采集卡【%d】数据包长度：%d\n", mci, vCOM_CMD_RW_WIFIPARA);
	printf("--------------------------------------\n");
#endif
	seNet_Send_ReadCommand(mci, vCOM_CMD_RW_WIFIPARA);//vCOM_CMD_RW_WIFIPARA
	//----------------------------------------------
	while ((timeout > 0) && (VK[mci].UpdateFlag < 0))
	{
		timeout--;
		Sleep(1);
	}
	if (VK[mci].UpdateFlag < 0)return (VK[mci].UpdateFlag);
	//---------------------------
	for (i = 0; i<4; i++)
	{
		*(tvalue + i) = VK[mci].ServerIP[i];   // 请求读取操作
		*(tvalue + i + 4) = VK[mci].VKIP[i];   // 请求读取操作
		*(tvalue + i + 8) = VK[mci].VKGateWay[i];   // 请求读取操作
		*(tvalue + i + 12) = VK[mci].VKNetMask[i];   // 请求读取操作
	}
	i = 16;
	*(tvalue + 16) = (unsigned char)(VK[mci].ServerPort / 0x100);
	*(tvalue + 17) = (unsigned char)(VK[mci].ServerPort);

	*(tvalue + 18) = (unsigned char)(VK[mci].VKPort / 0x100);
	*(tvalue + 19) = (unsigned char)(VK[mci].VKPort);

	*(tvalue + 20) = VK[mci].enetProtocol;
	*(tvalue + 21) = VK[mci].enetdisconectTime;
	*(tvalue + 22) = VK[mci].maxecacheTime;

	for (i = 0; i<6; i++)
	{
		*(tvalue + i + 23) = VK[mci].VKMac[i];
	}
	//---------------------------------------------
	return (VK[mci].UpdateFlag);// 
}


int Def_Function_OUTfmt VK70xNMC_Get_DeviceUDI(int mci, char *rdmodol, char *rdswver, char *rdhdver, char *devudi, int timeout)
{
	//vCOM_CMD_RW_UDI
	int i;
	if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开 
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -13;
	//----------------------------------------------
	VK[mci].UpdateFlag = -2;

	int tstatus = 0;
	tstatus = seNet_Send_ReadCommand(mci, vCOM_CMD_RW_UDI);
	if (tstatus<0)return tstatus;
	//----------------------------------------------
	while ((timeout > 0) && (VK[mci].UpdateFlag < 0))
	{
		timeout--;
		Sleep(1);
	}
	if (VK[mci].UpdateFlag < 0)return (VK[mci].UpdateFlag);
	//----------------------------------
	for (i = 0; i < 6; i++)
	{
		*rdmodol++ = VK[mci].ModelName[i];
		*rdswver++ = VK[mci].SWVer[i];
		*rdhdver++ = VK[mci].HWVer[i];
	}
	*rdmodol = '\0';
	*rdswver = '\0';
	*rdhdver = '\0';
	for (i = 0; i < 16; i++)
	{
		*devudi++ = VK[mci].UDI[i];
	}
	return (VK[mci].UpdateFlag);// 
}

////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// debug  function
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


int Def_Function_OUTfmt  VK70xNMC_debug_infor(int mci, double *backpara, int len)
{
	if (len < 1)return 0;
	*backpara++ = (double)VK[mci].VolRange[0];// ThreadRunningState;
	if (len < 2)return 1;
	*backpara++ = (double)VK[mci].VolRange[2];//(int)VKTCPServer.SockServer;
	if (len < 3)return 2;
	*backpara++ = (double)VK[mci].PGAGainRange[0];//;VK[mci]
	if (len < 4)return 3;
	*backpara++ = (double)VK[mci].PGAGainRange[2];
	if (len < 5)return 4;
	*backpara++ = (double)VK[mci].PGAGainRange[4];
	if (len < 6)return 5;
	*backpara++ = (double)VKTCPServer.SockClient[1];
	if (len < 7)return 6;
	return len;
}
