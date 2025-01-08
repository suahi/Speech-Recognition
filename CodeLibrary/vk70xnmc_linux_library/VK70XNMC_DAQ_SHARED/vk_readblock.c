#if _MSC_VER > 1000
#pragma once
#endif 

#include "VK70xNMC_DAQ2.h"
#include "dvr_header.h"
#include <Windows.h>
#include <stdio.h>


//int  ReadADCResultTimeout;

///========================================

void Save_DefaultCommonConfigurationFile(void)
{
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
	tfilehandle = fopen("vk70xncommonconfig.ini", "wb");// in
	//memset(pstr, '\0', sizeof(pstr));//
	memset(tempstr, '\0', sizeof(tempstr));//
	//------------------------------------
	sprintf(tempstr, "[Default Configuration]\n");
	fwrite(tempstr, 1, strlen(tempstr), tfilehandle);//
	memset(tempstr, '\0', sizeof(tempstr));//
	//------------------------------------
	sprintf(tempstr, "Read ADC result Blocking Timeout=%d\n", ReadADCResultTimeout);
	fwrite(tempstr, 1, strlen(tempstr), tfilehandle);//
	//==========================================
	fclose(tfilehandle);
}


void Load_DefaultCommonConfigurationFile(void)
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
	if (_access("vk70xncommonconfig.ini", 0) == -1)//
	{
		ReadADCResultTimeout = 500;
		Save_DefaultCommonConfigurationFile();
	}
	//=========================================
	tfilehandle = fopen("vk70xncommonconfig.ini", "r");// in
	char newstr[128];
	int timeout = 0;
	//-------------[系统缺省配置配置]
	fgets(tempstr, 128, tfilehandle);// 先读取一行文件头=[服务器配置]
	memset(tempstr, '\0', sizeof(tempstr));//
	memset(newstr, '\0', sizeof(newstr));//
	//--------------
	fgets(tempstr, 128, tfilehandle);
	if (CommStr_GetParameterUnintegerValueFromCongfigfile('=', tempstr, &timeout) >= 0)
		ReadADCResultTimeout = timeout;
	else
		ReadADCResultTimeout = 0;
	///---------------------------------------
	fclose(tfilehandle);
}


//===================================================================
// 设置读取阻塞模式或阻塞timeout
//===================================================================
int Def_Function_OUTfmt  VK70xNMC_Set_BlockingMethodtoReadADCResult(int tmode, int timeout)
{
	//int timeout;
	if ((tmode < 0) || (tmode > 1))return -1;// 设置模式错误
	//=========================
	if (tmode == 0)
	{
		if (0 != ReadADCResultTimeout)
		{
			ReadADCResultTimeout = 0;
			//--------------------------  更新配置文件
			Save_DefaultCommonConfigurationFile();
			//--------------------------
		}
	}
	else
	{
		if ((timeout < 0) || (timeout > 10000))
		{
			return -2;// timeout 参数错误， 设置0或大于10秒
		}
		if (timeout != ReadADCResultTimeout)
		{
			ReadADCResultTimeout = timeout;
			//--------------------------  更新配置文件
			Save_DefaultCommonConfigurationFile();
			//--------------------------
		}
		//-----------------------------
	}
	return 0;
}