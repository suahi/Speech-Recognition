#if _MSC_VER > 1000
#pragma once
#endif 

#include "VK70xNMC_DAQ2.h"
#include "dvr_header.h"
#include <Windows.h>
#include <stdio.h>

static unsigned int  DLLInitializeFlag=0;  // $748167// 初始化了OK
//////////////////////////////////////////////////////

void IntializeVKinging_RXTaskBuffer(void)
{
	int i, j, r = 0;
	for (r = 0; r < MAX_TCP_CILENT_NUM; r++)
	{
		VK[r].SaveShowPI = 0;
		VK[r].ReadShowPI = 0;
		VK[r].Read4CHPI = 0;

		//for (i = 0; i < 4; i++)IOStaus[i] = -1;
		VK[r].IOUpdateFlag = -1;
		for (i = 0; i < 8; i++)VK[r].ReadCHPI[i] = 0;
		for (i = 0; i < 10; i++)// 增加2路IO
		{
			for (j = 0; j < _DISP_MAX_LEN; j++)
			{
				VK[r].CHShowBuffer[i][j] = 0;
				VK[r].CHSrcHexBuffer[i][j] = 0;				
			}
				
		}
		//--------------------------------------------
		if (VK[r].ReferenceVoltage == 0 || VK[r].ReferenceVoltage > 4)VK[r].ReferenceVoltage = 2.442;
		for (i = 0; i < 8; i++)
		{
			if (VK[r].PGAGainRange[i] == 0)VK[r].PGAGainRange[i] = 1; //check ERROR and reset
		}
		////////////////////////////////////////////////
		for (j = 0; j < MAX_RXLAN_LEN; j++)VK[r].RXLANDatum[j] = 0;
		VK[r].RXLANSavePI = 0;
		VK[r].RXLANReadPI = 0;
		VK[r].MaxBuffer_SaveedLen = 0;
		VK[r].MaxBuffer_OverFlag = 0;
		////////////////////////////////////////////////
		for (i = 0; i < 2048; i++)VK[r].PacketDatum[i] = 0;
		//==============================================
		seNet_DefaultAfterChangeModelType(r);
		//---------------------------------------------
		//---------------------------------------------------
		//VK[r].UpdateFlag;// 读取标志
		//VK[r].IO[4];//bytes(21-24)
		//VK[r].DAC[2];
		//VK[r].PWMFreq[2];
		//VK[r].PWMDuty[2];
		//VK[r].Excounter; //i = mbytes(25) * &H1000000 + mbytes(26) * &H10000 + mbytes(27) * &H100 + mbytes(28)	"计数器
		//VK[r].Temp; //i = mbytes(29) * &H100 + mbytes(30)摄氏度 ; i = i / 100
		//VK[r].ExFreq;
		//VK[r].ExTemp;
		//---------------------------------
		VK[r].CNP_Trig_Status = 0;   //  0: 空闲， 不触发；  1-准备触发， 2-正在触发数据
		VK[r].CNP_Trig_Channel = 0;  //  0: 无效通道，  1-8：对应电压值触发通道；  12/0x12：IO2，13/0x13：IO3 IO电平触发
		VK[r].CNP_Trig_Edge = 0;    //   0: 上升沿触发/高于电压值触发；  1： 下降沿触发/低于电压值触发
		VK[r].CNP_Trig_Value = 0;   //   触发的电压值，，，double        
		//-------------------------
		VK[r].CNP_Target_Len = 10000;    // 触发N点长度
		VK[r].CNP_Target_Neg_Len = 0;// 触发N点时前M点负采样
		//---------------
		VK[r].CNP_Counter = 0;	     // 触发N点计数器
		VK[r].CNP_Read_PI = 0;       // 读取数据指针，主要用于负采样点数
	}
}

void seNet_Load_DefaultTCPIPConfigurationFile(void)
{
	//FILE *tfilehandle;
	int j;
	FILE *tfilehandle;
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
		return;
	}
	if (chdir(tempapppath) < 0)
	{
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
		printf("切换路径失败！\n");
#endif
		return;
	}
	//----------------------------------------
	if (_access("vk70xnmcdllconfig.ini", 0) == -1)//表示文件不存在。 函数int _access(const char *path, int mode); 可以判断文件或者文件夹的mode属性
	{
		//TypeDefTCPServerPara    *tvkinfor;
		//tvkinfor = &VKTCPServer;
		//char *pstr = NULL;

		tfilehandle = fopen("vk70xnmcdllconfig.ini", "wb");// in
		//memset(pstr, '\0', sizeof(pstr));//
		memset(tempstr, '\0', sizeof(tempstr));//
		//------------------------------------
		sprintf(tempstr, "[VK70xN Server Configuration]\n");
		fwrite(tempstr, 1, strlen(tempstr), tfilehandle);//
		memset(tempstr, '\0', sizeof(tempstr));//
		//------------------------------------
		sprintf(tempstr, "Server Port=8234\n");
		fwrite(tempstr, 1, strlen(tempstr), tfilehandle);//
		//------------------------------------
		for (j = 0; j < MAX_TCP_CILENT_NUM; j++)
		{
			sprintf(tempstr, "DAQ-%d=\"0.0.0.0\"\n", (j + 1));
			//strcat(pstr, tempstr);
			//strcat(pstr, "\\VK701NADCFile");//
			fwrite(tempstr, 1, strlen(tempstr), tfilehandle);// 
			//printf(tempstr);
		}
		//char buffer[] = { '\r', '\n' }; // 假定 用bai CRLF 为换行，(也可以 改成du 只用 LF)
		//pFile = fopen("myfile.bin", "wb");
		//这里写数据，然后写 CR LF：
		//fwrite(buffer, sizeof(char), sizeof(buffer), pFile);
		//fwrite(tvkinfor, sizeof(TypeDefTCPServerPara), 1, tfilehandle);// 
		//115.239.210.26
		//memset(&tvkinfor, 0, sizeof(TypeDefTCPServerPara));
		//fwrite(&tvkinfor, sizeof(TypeDefTCPServerPara), 1, tfilehandle);// 
		fclose(tfilehandle);
	}
	//=========================================
	tfilehandle = fopen("vk70xnmcdllconfig.ini", "r");// in
	//fread(&VKTCPServer, sizeof(TypeDefTCPServerPara), 1, tfilehandle);// 
	//fgets(s, 4, tfilehandle);
	//iihanlde = VKTCPServer.ClientAddr[mci].sin_port;
	//memcpy(bufpi, inet_ntoa(VKTCPServer.ClientAddr[mci].sin_addr), 128);
	//if (stricmp(inet_ntoa(tclientadr.sin_addr), inet_ntoa(VKTCPServer.ClientAddr[i].sin_addr)) == 0)
	char newstr[128];
	int tport = 0;
	//-------------[服务器配置]
	fgets(tempstr, 128, tfilehandle);// 先读取一行文件头=[服务器配置]
	memset(tempstr, '\0', sizeof(tempstr));//
	memset(newstr, '\0', sizeof(newstr));//
	//--------------服务器端口号=8234
	fgets(tempstr, 128, tfilehandle);
	if (CommStr_GetParameterUnintegerValueFromCongfigfile('=', tempstr, &tport) >= 0)
		VKTCPServer.PortNumber = tport;
	else
		VKTCPServer.PortNumber = 8234;
	//------------------------------------
	for (j = 0; j < MAX_TCP_CILENT_NUM; j++)
	{
		fgets(tempstr, 128, tfilehandle);
		memset(newstr, '\0', sizeof(newstr));//
		if (CommStr_GetNewStringsFromCongfigfile_RemoveSpecialCharacters('=', tempstr, newstr)>0)
			VKTCPServer.ClientAddr[j].sin_addr.s_addr = inet_addr(newstr);
		else
			VKTCPServer.ClientAddr[j].sin_addr.s_addr = inet_addr("0.0.0.0");
	}
	///---------------------------------------
	fclose(tfilehandle);
	//memset(&VKTCPServer.ClientStatus[0], 0, MAX_TCP_CILENT_NUM* sizeof(int));// sizeof(VKTCPServer.ClientStatus)
	//=========================================
	//tfilehandle = fopen("vk70xmcdllconfig", "wb+");// in
	//TypeDefTCPServerPara    VKTCPServer;
	/*
	FILE * fopen(const char * path,const char * mode);
	-- path: 文件路径，如："F:\Visual Stdio 2012\test.txt"
	-- mode: 文件打开方式，例如：
	"r" 以只读方式打开文件，该文件必须存在。
	"w" 打开只写文件，若文件存在则文件长度清为0，即该文件内容会消失。若文件不存在则建立该文件。
	"w+" 打开可读写文件，若文件存在则文件长度清为零，即该文件内容会消失。若文件不存在则建立该文件。
	"a" 以附加的方式打开只写文件。若文件不存在，则会建立该文件，如果文件存在，写入的数据会被加到文件尾，即文件原先的内容会被保留。（EOF符保留）
	"a+" 以附加方式打开可读写的文件。若文件不存在，则会建立该文件，如果文件存在，写入的数据会被加到文件尾后，即文件原先的内容会被保留。（原来的EOF符不保留）
	"wb" 只写打开或新建一个二进制文件，只允许写数据。
	"wb+" 读写打开或建立一个二进制文件，允许读和写。
	"ab" 追加打开一个二进制文件，并在文件末尾写数据。
	"ab+"读写打开一个二进制文件，允许读，或在文件末追加数据。
	--返回值: 文件顺利打开后，指向该流的文件指针就会被返回。如果文件打开失败则返回NULL
	*/
	//fwrite(VKTCPServer, sizeof(VKTCPServer), 1, tfilehandle);// 
	//size_t fwrite(const void* buffer, size_t size, size_t count, FILE* stream);
	//--buffer:指向数据块的指针
	//	-- size : 每个数据的大小，单位为Byte(例如：sizeof(int)就是4)
	//	--count : 数据个数
	//	-- stream : 文件指针
	//size_t fread(void *buffer, size_t size, size_t count, FILE *stream);
	//--buffer:指向数据块的指针
	///	-- size : 每个数据的大小，单位为Byte(例如：sizeof(int)就是4)
	//	--count : 数据个数
	//	-- stream : 文件指针
	//fclose(tfilehandle);
	//-----------------------------
	//memset(&VKTCPServer.ClientAddr, 0, sizeof(VKTCPServer.ClientAddr));
	//memset(&VKTCPServer.SockClient, 0, sizeof(VKTCPServer.SockClient));
	//memset(&serv, 0, sizeof(serv));
	//serv.sin_family = AF_INET;
	//serv.sin_port = htons(80);
	//serv.sin_addr.S_un.S_addr = inet_addr("115.239.210.26");
	//-----------------------------
	//ThreadRunningState=2;
	//RXLANMonitor_Handle = CreateThread(NULL, 0, MonitorRXLANEvent, NULL, 0, NULL);  
	//SetThreadPriority(RXLANMonitor_Handle,THREAD_PRIORITY_TIME_CRITICAL);
	///////////////////////////////////////////////////////
}


void InitDLL(void)
{
	int y = 0;
	if (DLLInitializeFlag != DS_DLL_INTIALIZEOK)
	{
		DLLInitializeFlag = DS_DLL_INTIALIZEOK;  // 代表已经初始化
		//ReadADCResultTimeout = 0;
		//ThreadRunningState = 0;
		//IntializeVKinging_RXTaskBuffer();
		Load_DefaultCommonConfigurationFile();
		//----------------------------
		VKTCPServer.PortNumber = 8234;
		VKTCPServer.RecievedBytes_Count = 0;
		VKTCPServer.Client_Num = 0;
		for (y = 0; y <= MAX_TCP_CILENT_NUM; y++)
		{
			//VKTCPServer.ClientHandle[i]C语言检查文件是否存在 = 0;  // 最大可以连接128个客户机
			VKTCPServer.ClientStatus[y] = 0;
			//memset(VKTCPServer.ClientIP[y], 0, 128);
			//for(j = 0;j<128;j++)VKTCPServer.ClientIP[y][j]=0; 
		}
		seNet_Load_DefaultTCPIPConfigurationFile();
		TCPMonitor_ThreadRunningState = 0;
		RXLANMonitor_ThreadRunningState = 0;
		//ThreadRunningState = 0;		
		//======================================================= 
		//ADCFilePIHandle = NULL;
		//SaveADCNumCount = 0;
		//TnewADCFileName
		///////////////////////////////////////////////////////
		//20200528 hide thread //ThreadRunningState = 0;
		IntializeVKinging_RXTaskBuffer();
		//20200528 hide thread //ThreadRunningState=2;
		//20200528 hide thread //RXLANMonitor_Handle = CreateThread(NULL, 0, MonitorRXLANEvent, NULL, 0, NULL);  
		//SetThreadPriority(RXLANMonitor_Handle,THREAD_PRIORITY_TIME_CRITICAL);
		//UnregisterTCPServer (VKTCPServer.PortNumber); ////////// 注销tCP 服务器后再重  
		//=====================================
		sDFile_LoadDefaultSDConfigurationFile();
		sDFile_IntializeVKinging_SdFileRxBuffer();
		//------------------------------------
	}
}
