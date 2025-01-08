#if _MSC_VER > 1000
#pragma once
#endif 

#include "VK70xNMC_DAQ2.h"
#include "dvr_header.h"
#include <Windows.h>
#include <stdio.h>
#include<stdlib.h>
#include<string.h>
//#include<direct.h>
#include <sys/stat.h>
#include <sys/types.h>

//static unsigned char TaskState = 0;
const char  SYSNCHANDER_START[] = { "\x16\x16\x16\x16\x16\x16\x16\x16\x16\x16" };//先发送10个<SYN>作为开始
const char  SYSNCHANDER_END[] = { "\x17\x17\x17\x17\x17\x17\x17\x17\x17\x17" }; ////发送10个<ETB>数据包结束
//----------------------------------
const char  SYSNC_CRLF[] = { "\x13\x10" };
const char  TASK_STREAM_START[] = { "STREAM_START=" };//<CR><LF>STREAM_START=1,A000000001,123,<CR><LF>
const char  TASK_INFOR_START[] = { "INFOR_START=" };   //(开始发一条数据流，机身编号长度为10，机身编号为:A000000001，文件号为123)
const char  TASK_FILE_START[] = { "FILE_START=" };//<CR><LF>TXT_START=2,12,<CR><LF>           (开始发txt文件，大小为12 bytes)
const char  TASK_FILE_END[] = { "FILE_END=" };

//-----------------------------------------------
const char  SEGINFOR_END[] = { "]" };
const char  SEGINFOR_SN_ST[] = { "sn[" };
const char  SEGINFOR_STATUS_ST[] = { "status[" };
//const char  SEGINFOR_INFORHEADER_ST[]={"INFOR_START="};  
//const char  SEGINFOR_FILEHEADER_ST[] ={"FILE_START="}; 
const char  SEGINFOR_MARK_SF[] = { "," };// separted file 文件分隔符号
const char  SEGINFOR_MARK_FSH[] = { "<" }; // mark file size header
const char  SEGINFOR_MARK_FSE[] = { ">" }; // mark file size end   

//unsigned char VkserailMode;//  0 ：  实时在线采集；  1： 实时SD存储采集，    10：下载sd文件 
//-------------------------
//size_t  TotalusedSDSize;//  0 bytes
//size_t  RxSDBytesCount;//  0 bytes  
//========================================
typedef struct _SDFILESYSTEM_DOWNLAODSTATUS {
	intptr_t  TotalusedSDSize;
	intptr_t  RxSDBytesCount;//  0 bytes
	//============================
	int tsdfileStatus;// 当前采集的文件数量
	int tsdfileNum;// 当前采集的文件数量
	//===========================
	int tNextTask; // 0: idle,  1: download one file  ; 2: downloading multi-files（主要用于多文件下载事件，其它命令为0）
	int tsdfileCount; // 0:all, 1-n files，  下载或删除文件位置计数器
	//==========================
	unsigned char  FileOpenFlag;//0: close;  1: open
	FILE  *TempADCFileHandle;  //  临时存储的文件句柄
	char TempADCFilePath[MAX_PATHNAME_LEN];// 文件路径
	char TempADCFilePathandFilename[MAX_PATHNAME_LEN];// 文件名全路径
} SDFILESYSTEM_DOWNLAODSTATUS;

SDFILESYSTEM_DOWNLAODSTATUS   sDFile[MAX_TCP_CILENT_NUM + 1]; // 
/////////////////////////////////////////////////////////////
int   DisapolDatapackage(int mci);
//void  uset_DisposalSettingRXTask(unsigned char rxdat);
//void  uset_DispasalComamndsAndDisplayInformation(void);
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
// disposal sd file driver function
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

void Format_Max256Bytes2HexChar_OutputListBox(const char *ttbuf, unsigned int len)
{
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
	unsigned int i;	
	char ttchar[1024];
	char tthex[16];
	memset(tthex, '\0', 16);
	memset(ttchar, '\0', 1024);
	sprintf(ttchar, "当前信息：");
	for (i = 0; i < len; i++)
	{
		sprintf(tthex, "%02x,", (unsigned char)(*ttbuf++));
		strcat(ttchar, tthex);// 
	}
	//InsertTextBoxLine(panelHandle, PANEL_TEXTBOX, 0, ttchar);
	printf("采集卡输出数据长度【%d】：%s\n", len, ttchar);
#endif
}



////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////  
////////////////////////////////////////////////////////////////////////////////////  
////////////////////////////////////////////////////////////////////////////////////
// sd 文件 解析
////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////  
////////////////////////////////////////////////////////////////////////////////////  
//////////////////////////////////////////////////////////////////////////////////// 

////////////////////////////////////////////////////////////////////////////////////
// sd 文件 内部函数
////////////////////////////////////////////////////////////////////////////////////

int ExtractCmpStrsEndPosFromL2R_FirstFound(const char *cmpbuf, intptr_t cmplen, const char *adata, intptr_t sumlen)
{
	intptr_t i, j;
	char temp;
	char *temcmpbuf;
	//---------------------
	temcmpbuf = (char *)cmpbuf;//(char *)
	temp = *temcmpbuf++;
	j = 0;
	//--------------------
	for (i = 0; i < sumlen; i++)
	{
		if (temp == *adata++)
		{
			j++;
			if (j >= cmplen)return (int)i;//  
			//----------------
			temp = *temcmpbuf++;
			//adata ++;
		}
		else if (j != 0)
		{
			j = 0;
			temcmpbuf = (char *)cmpbuf;  // 复位比较字符(char *)
			temp = *temcmpbuf++;
		}
	}
	return -1;
}


int PosExTbytes(const char *cmpbuf, intptr_t len, const char *adata, intptr_t startpos, intptr_t endpos)
{
	intptr_t i, j;
	char temp;
	char *temcmpbuf;
	j = 0;
	temcmpbuf = (char *)cmpbuf;
	temp = *temcmpbuf;
	for (i = startpos; i < endpos; i++)
	{
		if (temp == *adata++)
		{
			j++;
			if (j >= len)return (int)i;//返回对比字符最后的一个字符的位置。 
			temcmpbuf++;
			temp = *temcmpbuf;
		}
		else if (j != 1)
		{
			j = 1;//  restart
			temcmpbuf = (char *)cmpbuf;
			temp = *temcmpbuf;
		}
	}
	return -1;
}

/*
char* textFileRead(char* filename)
{
char* text;
FILE *pf = fopen(filename, "r");
fseek(pf, 0, SEEK_END);
long lSize = ftell(pf);
// 用完后需要将内存free掉
text = (char*)malloc(lSize + 1);
rewind(pf);
fread(text, sizeof(char), lSize, pf);
text[lSize] = '\0';
return text;
}
*/

int  FindString(char *data, char *fchar, char len)
{
	char i, tflag = 0;
	char *chpi = fchar;
	while (*data != '\0')
	{
		if (*data == *chpi)
		{
			tflag = 1;
			for (i = 0; i < len; i++)
			{
				if (*data++ != *chpi++)
				{
					chpi = fchar;// reset;
					tflag = 0;
					break;
				}
			}
			if (tflag == 1)return 1;
		}
		data++;
	}
	return -1;// 没找相同字符串
}


////////////////////////////////////////////////////////////////////////////////////
// sd 文件 外部函数
////////////////////////////////////////////////////////////////////////////////////


void sDFile_LoadDefaultSDConfigurationFile(void)
{
	//int j;
	FILE *tfilehandle;
	char tempstr[MAX_PATHNAME_LEN];
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
	if (_access("vk70xnmcsdconfig.ini", 0) == -1)//表示文件不存在。 函数int _access(const char *path, int mode); 可以判断文件或者文件夹的mode属性
	{
		tfilehandle = fopen("vk70xnmcsdconfig.ini", "wb");// in
		memset(tempstr, '\0', sizeof(tempstr));//
		//------------------------------------
		sprintf(tempstr, "[SD Default Configuration]\n");
		fwrite(tempstr, 1, strlen(tempstr), tfilehandle);//
		///////////////////////////////////////
		memset(tempstr, '\0', sizeof(tempstr));//
		sprintf(tempstr, "Default DIR=\"");
		fwrite(tempstr, 1, strlen(tempstr), tfilehandle);//
		memset(tempstr, '\0', sizeof(tempstr));//		
		if (getcwd(tempstr, MAX_PATHNAME_LEN) == NULL)
		{
			sprintf(tempstr, "D:");
		}
		fwrite(tempstr, 1, strlen(tempstr), tfilehandle);//
		memset(tempstr, '\0', sizeof(tempstr));//
		sprintf(tempstr, "\"\n");
		fwrite(tempstr, 1, strlen(tempstr), tfilehandle);//
		//====================================
		fclose(tfilehandle);
	}
	//=========================================
	tfilehandle = fopen("vk70xnmcsdconfig.ini", "r");// in
	//-------------[服务器配置]
	fgets(tempstr, MAX_PATHNAME_LEN, tfilehandle);// 先读取一行文件头=[服务器配置]
	memset(tempstr, '\0', sizeof(tempstr));//
	//--------------服务器端口号=8234
	fgets(tempstr, MAX_PATHNAME_LEN, tfilehandle);
#if (_DEBUG_VK70xxMC_LIB_>0)
	printf("--------------------------------------\n");
	printf("采集卡默认路径0：%s  [tempstr]\n", tempstr);
	printf("--------------------------------------\n");
#endif 
	memset(SD_DefaultFilePath, '\0', sizeof(SD_DefaultFilePath));
	if (CommStr_GetNewStringsWithBlankFromCongfigfile_RemoveSpecialCharacters('=', tempstr, SD_DefaultFilePath) > 0)
	{
#if (_DEBUG_VK70xxMC_LIB_>0)
		printf("--------------------------------------\n");
		printf("采集卡默认路径（正确）：%s\n", SD_DefaultFilePath);
		printf("--------------------------------------\n");
#endif 
	}
	else
	{
		sprintf(SD_DefaultFilePath, "D:");
#if (_DEBUG_VK70xxMC_LIB_>0)
		printf("--------------------------------------\n");
		printf("采集卡默认路径（错误）：%s\n", SD_DefaultFilePath);
		printf("--------------------------------------\n");
#endif 
	}
	///---------------------------------------
	fclose(tfilehandle);
}

void sDFile_IntializeVKinging_SdFileRxBuffer(void)
{
	int i, j;
	for (i = 0; i < 8; i++)
	{
		//VK[mci].LastWorkMode = VKxxx_MODE_RTTX_SAMPLING;
		sDFile[i].TotalusedSDSize = 0;
		sDFile[i].RxSDBytesCount = 0;//  0 bytes
		sDFile[i].tsdfileNum = 0;// 当前采集的文件数量
		sDFile[i].tNextTask = 0; // 0: idle,  1: download one file  ; 2: downloading multi-files（主要用于多文件下载事件，其它命令为0）
		sDFile[i].tsdfileCount = 0; // 0:all, 1-n files，  下载或删除文件位置计数器
		sDFile[i].FileOpenFlag = 0;//0: close;  1: open
		sDFile[i].TempADCFileHandle = NULL;  //  临时存储的文件句柄
		for (j = 0; j < MAX_PATHNAME_LEN; j++)
		{
			sDFile[i].TempADCFilePath[j] = 0;// 文件路径
			sDFile[i].TempADCFilePathandFilename[j] = 0;// 文件名全路径
		}
	}
}

int sDFile_CheckSDCardDownloadCondition(int mci)
{
	if (sDFile[mci].FileOpenFlag == 0)
	{
        sDFile_Intializetempsdcardfile(mci);
		return 0;
	}		
	return 1;
}


//-------------------------------------------------------------------
void sDFile_CheckSdTempFileWhetherisClosed(void)
{
	int i;
	for (i = 0; i < 8; i++)
	{
		if (sDFile[i].FileOpenFlag>0)
		{
			if (sDFile[i].TempADCFileHandle == NULL)continue; //file error
			fclose(sDFile[i].TempADCFileHandle);  // close file
			sDFile[i].FileOpenFlag = 0;
		}

	}
}

///////////////////////////////////////////////////////////////////////////
//int  CommStr_GetNewStringsFromCongfigfile_RemoveSpecialCharacters(const char tkeychar, const char *tsrcstring, char *deststr);

int  sDFile_SendtheNextFileComamnd(int mci)
{
	unsigned char tempdatbuf[8];
	int i = 0;

	for (i = 0; i < 8; i++)tempdatbuf[i] = 0;
	tempdatbuf[0] = vCOM_STATUS_REPONSE_START;
	tempdatbuf[1] = 0x11;
	tempdatbuf[2] = (unsigned char)(sDFile[mci].tsdfileCount / 0x100);
	tempdatbuf[3] = (unsigned char)sDFile[mci].tsdfileCount;
	i = DisposalTXDatum(VKTCPServer.SockClient[mci], vCOM_CMD_RW_SDCARD_FILES, tempdatbuf, 4, 0);  //vCOM_CMD_RW_IO
	//-----------------------------------------------
	return i;
}
/////////////////////////////////////////////////
//  temp file
/////////////////////////////////////////////////

void sDFile_Intializetempsdcardfile(int mci)//char *tempfiledir
{
	int dwAttr = 0;
	char tstr[32];

	//=======================================================
	memset(sDFile[mci].TempADCFilePath, '\0', sizeof(sDFile[mci].TempADCFilePath));
	if (SD_DefaultFilePath[0] == '\0')
	{
		if (getcwd(SD_DefaultFilePath, MAX_PATHNAME_LEN) == NULL)
		{
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
			printf("获取路径失败！\n");
#endif
			return;
		}
		else sprintf(tstr, "D:");
		//memcpy(sDFile[mci].TempADCFilePath, SD_DefaultFilePath, MAX_PATHNAME_LEN);
		strcat(sDFile[mci].TempADCFilePath, SD_DefaultFilePath);//创建目录
	}
	else strcat(sDFile[mci].TempADCFilePath, SD_DefaultFilePath);//创建目录
	//memcpy(sDFile[mci].TempADCFilePath, SD_DefaultFilePath, MAX_PATHNAME_LEN);
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
	printf("获取路径0【%s】！\n", SD_DefaultFilePath);
	printf("获取路径1【%s】！\n", sDFile[mci].TempADCFilePathandFilename);
#endif
	/////////////////////////////////////////////////	
	memset(tstr, '\0', sizeof(tstr));
	sprintf(tstr, "\\vk70xx_card%dfiles", mci);
	strcat(sDFile[mci].TempADCFilePath, tstr);//创建目录
	dwAttr = GetFileAttributes(sDFile[mci].TempADCFilePath);// 绗竴绾х洰褰曪紝
	if (dwAttr == 0xFFFFFFFF)  //鐩綍涓嶅瓨鍦ㄥ垯鍒涘缓   
		CreateDirectory(sDFile[mci].TempADCFilePath, NULL);
	//------------------------------------
	memset(sDFile[mci].TempADCFilePathandFilename, '\0', sizeof(sDFile[mci].TempADCFilePathandFilename));
	strcat(sDFile[mci].TempADCFilePathandFilename, sDFile[mci].TempADCFilePath);
	memset(tstr, '\0', sizeof(tstr));
	sprintf(tstr,"\\rxtemp_%d.vktmp", mci);
	strcat(sDFile[mci].TempADCFilePathandFilename, tstr);// 创立临时的文件路径
	//-------------------------------------------
	if (sDFile[mci].TempADCFileHandle != NULL)fclose(sDFile[mci].TempADCFileHandle);  // close file  
	//TempADCFileHandle = OpenFile(TempADCFilePathandFilename, VAL_WRITE_ONLY, VAL_TRUNCATE, VAL_BINARY);
	//OpenFile (txtfilename, VAL_WRITE_ONLY, VAL_TRUNCATE,VAL_BINARY);
	sDFile[mci].TempADCFileHandle = fopen(sDFile[mci].TempADCFilePathandFilename, "wb+");// in
	//TempADCFileHandle = fopen("vk70xmcdllconfig.ini", "r");// in
	sDFile[mci].FileOpenFlag = 1;
	//------------------------------------

#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
	printf("已打开一个新文件【%s】！【%d】\n", sDFile[mci].TempADCFilePathandFilename, (int)sDFile[mci].TempADCFileHandle);
#endif
	
}



////////////////////////////////////////////////////////////////////////////////////
// sd 文件 处理函数
////////////////////////////////////////////////////////////////////////////////////

int sDFile_WriteReadSDCardTask(int mci,const char *rxdat, int len)
{
	int i;
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
	//printf("开始写文件。。。。。。。。采集卡【%d】收到数据长度【%d】[%d][%d]！！\n", mci, len, (int)rxdat, (int)sDFile[mci].TempADCFileHandle);
#endif
	fwrite(rxdat, 1, (intptr_t)len, sDFile[mci].TempADCFileHandle);//
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
	//printf("开始处理。。。。。。。。采集卡【%d】收到数据长度【%d】[%d]！！\n", mci, len, (int)rxdat);
#endif
	i = ExtractCmpStrsEndPosFromL2R_FirstFound(SYSNCHANDER_END, 10, (const char *)rxdat, len);
	if (i>0)
	{
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
		printf("收到一个新文件！！\n");
#endif
		i = DisapolDatapackage(mci);		
		if (sDFile[mci].tNextTask>0) // 下载多个文件
		{
			//char tbuf[4];
			if (i >= 0)
			{
				sDFile[mci].tsdfileCount++;
				//-------------------------------
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
				if (sDFile[mci].tsdfileNum>0)
				{
					i = sDFile[mci].tsdfileCount * 100 / sDFile[mci].tsdfileNum;
					if (i>100)i = 100;
					printf("文件下载进度[%d%%]\n", i); //SetCtrlVal(panel2_sdfileHandle, PANEL_SF_NUMERICSLIDE, i);
				}
				else printf("文件下载进度[%d%%]\n", 0); //SetCtrlVal(panel2_sdfileHandle, PANEL_SF_NUMERICSLIDE, 0);// 显示文件下载进度
#endif
				//-------------------------------
				if (sDFile[mci].tsdfileCount>sDFile[mci].tsdfileNum)
				{
					sDFile[mci].tsdfileCount = 0;
					sDFile[mci].tNextTask = 0;		 // 清除下载文件任务
					sDFile[mci].tsdfileStatus = 0;
				}
				else   // 准备发送下一个文件
				{
					sDFile[mci].tsdfileStatus = 1;
					sDFile_SendtheNextFileComamnd(mci);
				}
			}
			else // 重新传送文件
			{
				sDFile[mci].tsdfileStatus = 1;
				sDFile_SendtheNextFileComamnd(mci);
			}
		}
		else sDFile[mci].tsdfileStatus = 0;
	}
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
	//printf("退出处理。。。。。。。。采集卡【%d】收到数据长度【%d】！！\n", mci, len);
#endif
	return 0;
}


int GetFileInfo(const char *filename, intptr_t *size)
{
	FILE *fp = fopen(filename, "r");
	if (!fp)return -1;
	fseek(fp, 0L, SEEK_END);
	int tsize = ftell(fp);
	fclose(fp);
	*size = (intptr_t)tsize;
	return tsize;
}
//=====================================
int DisapolDatapackage(int mci)
{
	char packageflag;
	char *filedata, *tempstr;
	intptr_t i, filelen = 0;//intptr_t	
	char printoutstr[256];
	//char Tag[32];
	intptr_t pos1, pos2, packageindex, templen;  // 文件位置信息
	memset(printoutstr, '\0', 256);
	//==========================================
	if (sDFile[mci].TempADCFileHandle == NULL)return -1; //file error
	//fclose(sDFile[mci].TempADCFileHandle);  // close file
	//----------------------
	//FILE *pf = fopen(sDFile[mci].TempADCFilePathandFilename, "r");
	fseek(sDFile[mci].TempADCFileHandle, 0, SEEK_END);
	filelen = ftell(sDFile[mci].TempADCFileHandle);
	filedata = (char*)malloc(filelen + 1);
	fseek(sDFile[mci].TempADCFileHandle, 0, SEEK_SET);
	fread(filedata, 1, filelen, sDFile[mci].TempADCFileHandle);
	filedata[filelen] = '\0';
	fclose(sDFile[mci].TempADCFileHandle);


	//char loginformationpathname[256];
	//memset(loginformationpathname, '\0', 256);
	//strcat(loginformationpathname, sDFile[mci].TempADCFilePath);
	//strcat(loginformationpathname, "\\vk70xnh_log_information.bin");

	//FILE *fplog = fopen(loginformationpathname, "wb");// in
	//fwrite(filedata, 1, filelen, fplog);// 
	//fclose(fplog);

	//---------------------------
	//InsertTextBoxLine(panel2_sdfileHandle, PANEL_SF_TEXTBOX, -1,"打开 rxsdcardtempfiles.bin"); 
	//GetFileInfo(TempADCFilePathandFilename, &filelen);
	//filedata = malloc((sizeof (char)) * (filelen+1));
	//------------------
	//FILE *pfile = fopen(TempADCFilePathandFilename, "r");
	//if (pfile == NULL)return -1;
	//while (!feof(pfile))
	//{
	//	fgets(filedata, (filelen*(sizeof (char))), pfile);
	//}
	//fclose(pfile);
	//-------------------
	//tempfilehandle = fopen(TempADCFilePathandFilename, "r");// in
	//tempfilehandle = OpenFile(TempADCFilePathandFilename, VAL_READ_ONLY, VAL_OPEN_AS_IS, VAL_BINARY);
	//fgets(filedata, (filelen*(sizeof (char))), tempfilehandle);
	//ReadFile(tempfilehandle, filedata, (filelen*(sizeof (char))));
	//fclose(tempfilehandle);
#if (_DEBUG_VK70xxMC_LIB_>0)//(0)// 
	printf("收到临时性文件! filelen=%d\n", filelen);
	//sprintf(printoutstr, "收到临时性文件! filelen=%d", (int)filelen);
	//InsertTextBoxLine(panel2_sdfileHandle, PANEL_SF_TEXTBOX, -1, printoutstr);
#endif
	//--------------------------------------
	sDFile[mci].TempADCFileHandle = fopen(sDFile[mci].TempADCFilePathandFilename, "wb+");// in
	//TempADCFileHandle = OpenFile(TempADCFilePathandFilename, VAL_WRITE_ONLY, VAL_TRUNCATE, VAL_BINARY);  // 重写
	//InsertTextBoxLine(panel2_sdfileHandle, PANEL_SF_TEXTBOX, -1,"重写 rxsdcardtempfiles.bin");
	//--------------------------------------
#if (_DEBUG_VK70xxMC_LIB_>0)//(0)// 
	printf("----------------------------------------\n");
	//InsertTextBoxLine(panel2_sdfileHandle, PANEL_SF_TEXTBOX, -1, "----------------------------------------");
	//InsertTextBoxLine(panel2_sdfileHandle, PANEL_SF_TEXTBOX, -1,filedata); 
#endif	
	//pos_start=0;
	//pos_end=filelen;
	pos1 = PosExTbytes(SYSNCHANDER_START, 10, filedata, 0, filelen);
	if (pos1<1)
	{
#if (_DEBUG_VK70xxMC_LIB_>0)//(0)// 
		printf("警告:数据包头错误【%d】【%d】!\n", pos1, filelen);
		printf("free(filedata)=%d\n", filelen);
#endif	
		free(filedata);
		//sDFile[mci].TempADCFileHandle = fopen(sDFile[mci].TempADCFilePathandFilename, "wb+");// in
		return -2;
	}
	//sDFile[mci].TempADCFileHandle = fopen(sDFile[mci].TempADCFilePathandFilename, "wb+");// in
	//======================== length( Edit1.text )
	packageindex = pos1;  // 下一个位置开始搜索
	pos1 = PosExTbytes(SEGINFOR_SN_ST, 3, (const char *)&filedata[packageindex], packageindex, filelen);
	pos2 = PosExTbytes(SEGINFOR_END, 1, (const char *)&filedata[pos1], pos1, filelen);
	templen = pos2 - pos1 - 2;
	//=====================
	if ((pos1 < 1) || (pos2 < 1) || (templen< 1))
	{
#if (_DEBUG_VK70xxMC_LIB_>0)//(0)// 
		printf("警告:序列号信息错误！\n");
		printf("free(filedata)=%d\n", filelen);
#endif	
		free(filedata);
		return -3;
	}
	tempstr = malloc(sizeof (char)* (templen + 1));  // 
	memset(tempstr, '\0', (templen + 1));
	memcpy(tempstr, (char *)&filedata[pos1 + 2], templen);
#if (_DEBUG_VK70xxMC_LIB_>0)//(0)// 
	printf("当前采集卡序列号：%s\n", tempstr);
	//sprintf(printoutstr, "当前采集卡序列号：%s", tempstr);
	//InsertTextBoxLine(panel2_sdfileHandle, PANEL_SF_TEXTBOX, -1, printoutstr);
#endif		
	free(tempstr);
	//==============================
	packageindex = pos2;  // 下一个位置开始搜索
	pos1 = PosExTbytes(SEGINFOR_STATUS_ST, 7, (const char *)&filedata[packageindex], packageindex, filelen);
	pos2 = PosExTbytes(SEGINFOR_END, 1, (const char *)&filedata[pos1], pos1, filelen);
	templen = pos2 - pos1 - 2;
	//=====================
	if ((pos1 < 1) || (pos2 < 1) || (templen< 1))
	{
#if (_DEBUG_VK70xxMC_LIB_>0)//(0)// 
		printf("警告:采集卡状态信息错误！\n");
		printf("free(filedata)=%d\n", filelen);
#endif			
		free(filedata);
		return -4;
	}
	tempstr = malloc(sizeof (char)* (templen + 1));  // 
	memset(tempstr, '\0', (templen + 1));
	memcpy(tempstr, (char *)&filedata[pos1 + 2], templen);
#if (_DEBUG_VK70xxMC_LIB_>0)//(0)// 
	printf("当前采集卡状态：%s\n", tempstr);
	//sprintf(printoutstr, "当前采集卡状态：%s", tempstr);
	//InsertTextBoxLine(panel2_sdfileHandle, PANEL_SF_TEXTBOX, -1, printoutstr);
	//InsertTextBoxLine(panel2_sdfileHandle, PANEL_SF_TEXTBOX, -1,"采集状态：");
	//InsertTextBoxLine(panel2_sdfileHandle, PANEL_SF_TEXTBOX, -1,tempstr); 
#endif	
	free(tempstr);
	//================================
	packageindex = pos2;  // 下一个位置开始搜索
	//dwloadindex = 1;
	//if Sdcard_DeletFileFalg>=0 then
	//begin
	//Disposal_Stringgrid1DeleteFile(tstatus);
	//Sdcard_DeletFileFalg:=-1;
	//end;
#if (_DEBUG_VK70xxMC_LIB_>0)//(0)// 
	printf("当前采集卡数据位置：【%d】【%d】【%d】【%d】\n", pos1, pos2, packageindex, filelen);
#endif	
	//================================
	//if i > 0 then
	//begin
	//const char  TASK_STREAM_START ={"STREAM_START="};//<CR><LF>STREAM_START=1,A000000001,123,<CR><LF>
	//const char  TASK_INFOR_START = {"INFOR_START="};   //(开始发一条数据流，机身编号长度为10，机身编号为:A000000001，文件号为123)
	//const char  TASK_FILE_START = {"FILE_START="};//<CR><LF>TXT_START=2,12,<CR><LF>           (开始发txt文件，大小为12 bytes)
	//const char  TASK_FILE_END = {"FILE_END="}; 
	while (packageindex<filelen)	   //5540243	//5475231
	{
		//  Mainform.Memo1.Lines.Add('pospackagestart ='+inttostr(pospackagestart));
		//TASK_INFOR_START = 'INFOR_START=' ;                                                //(开始发一条数据流，机身编号长度为10，机身编号为:A000000001，文件号为123)
		//TASK_FILE_START = 'FILE_START=' ;//<CR><LF>TXT_START=2,12,<CR><LF>           (开始发txt文件，大小为12 bytes)
		//TASK_FILE_END
		//=======================================================================
		pos1 = PosExTbytes(TASK_FILE_START, 12, (const char *)&filedata[packageindex], packageindex, filelen);//PosEx(TASK_STREAM_START,DisapolStrSegBuffer,1);
		if (pos1>0)
		{
			packageflag = 22;
			//SetCtrlVal (panel2_sdfileHandle, PANEL_SF_NUMERICSLIDE,100); 
		}
		else
		{
			pos1 = PosExTbytes(TASK_INFOR_START, 11, (const char *)&filedata[packageindex], packageindex, filelen);//PosEx(TASK_STREAM_START,DisapolStrSegBuffer,1);
			if (pos1>0)
			{
				packageflag = 11;
				//SetCtrlVal (panel2_sdfileHandle, PANEL_SF_NUMERICSLIDE,0);
			}
			else
			{
#if (_DEBUG_VK70xxMC_LIB_>0)//(0)// 
				printf("free(filedata)=%d\n", filelen);
#endif
				free(filedata);
				return 0; // 信息段搜索完毕，
			}
		}
		//=============================================================================================================
		// file
		//=============================================================================================================
		if (packageflag == 22) // file
		{
			//======================== length( Edit1.text )  file name
			char tempfilepath[256];
			char tempfilename[64];
			char tempfileszie[64];
			intptr_t tempfilelen = 0;
			//int     numRows;
			//---------------
			memset(tempfilepath, '\0', 256);
			memset(tempfilename, '\0', 64);
			memset(tempfileszie, '\0', 64);
			packageindex = pos1;  // 下一个位置开始搜索
			pos1 = PosExTbytes("name[", 5, (const char *)&filedata[packageindex], packageindex, filelen);
			pos2 = PosExTbytes(SEGINFOR_END, 1, (const char *)&filedata[pos1], pos1, filelen);
			templen = pos2 - pos1 - 2;
#if (_DEBUG_VK70xxMC_LIB_>0)//(0)// 
			printf("文件参数【%d】【%d】【%d】!\n", pos1, pos2, templen);
			//InsertTextBoxLine(panel2_sdfileHandle, PANEL_SF_TEXTBOX, -1, "警告:文件名错误!");
#endif	
			if ((pos1 < 1) || (pos2 < 1) || (templen< 1))
			{
#if (_DEBUG_VK70xxMC_LIB_>0)//(0)// 
				printf("警告:文件名错误!\n");
				printf("free(filedata)=%d\n", filelen);
#endif				
				free(filedata);
				return -20;
			}
			tempstr = malloc(sizeof (char)* (templen + 1));  // 
			memset(tempstr, '\0', (templen + 1));
			memcpy(tempstr, (char *)&filedata[pos1 + 2], templen);
			//-------------------------------------
			strcat(tempfilepath, sDFile[mci].TempADCFilePath);
			strcat(tempfilepath, "\\");
			strcat(tempfilepath, tempstr);
			strcat(tempfilename, tempstr);

#if (_DEBUG_VK70xxMC_LIB_>0)//(0)// 
			printf("文件名：%s\n", tempstr);
			//sprintf(printoutstr, "文件名：%s", tempstr);
			//InsertTextBoxLine(panel2_sdfileHandle, PANEL_SF_TEXTBOX, -1, printoutstr);
			//InsertTextBoxLine(panel2_sdfileHandle, PANEL_SF_TEXTBOX, -1,"文件名:");
			//InsertTextBoxLine(panel2_sdfileHandle, PANEL_SF_TEXTBOX, -1,tempstr); 
#endif				
			free(tempstr);
			//==============================	 file size
			packageindex = pos2;  // 下一个位置开始搜索
			pos1 = PosExTbytes("size[", 5, (const char *)&filedata[packageindex], packageindex, filelen);
			pos2 = PosExTbytes(SEGINFOR_END, 1, (const char *)&filedata[pos1], pos1, filelen);
			templen = pos2 - pos1 - 2;
			if ((pos1 < 1) || (pos2 < 1) || (templen< 1))
			{
#if (_DEBUG_VK70xxMC_LIB_>0)//(0)// 
				printf("警告:文件大小错误!\n");
				printf("free(filedata)=%d\n", filelen);
#endif					
				free(filedata);
				return -21;
			}
			tempstr = malloc(sizeof (char)* (templen + 1));  // 
			memset(tempstr, '\0', (templen + 1));
			memcpy(tempstr, (char *)&filedata[pos1 + 2], templen);
			//-----------------------
			tempfilelen = atoi(tempstr);
			//------------------------
			strcat(tempfileszie, tempstr);

#if (_DEBUG_VK70xxMC_LIB_>0)//(0)// 
			printf("文件大小：%s 字节\n", tempstr);
#endif	
			free(tempstr);
			//============================= file datum
			packageindex = pos1;  // 下一个位置开始搜索
			pos1 = PosExTbytes("datum[", 6, (const char *)&filedata[packageindex], packageindex, filelen);
			//pos2 = PosExTbytes(TASK_FILE_END,9,(const char *)&filedata[pos1],pos1,filelen);
			//templen = pos2-pos1-2;
			pos2 = pos1 + tempfilelen + 2;
			if ((pos1 < 1) || (tempfilelen< 1) || (pos2>filelen))
			{
#if (_DEBUG_VK70xxMC_LIB_>0)//(0)// 
				printf("警告:文件数据错误! pos1=%d,pos2=%d,tempfilelen=%d,filelen=%d\n", (int)pos1, (int)pos2, (int)tempfilelen, (int)filelen);
				printf("free(filedata)=%d\n", filelen);
#endif				
				free(filedata);
				return -22;
			}
#if (_DEBUG_VK70xxMC_LIB_>0)//(0)// 
			printf("文件数据正确! pos1=%d,pos2=%d,tempfilelen=%d,filelen=%d\n", (int)pos1, (int)pos2, (int)tempfilelen, (int)filelen);
			//sprintf(printoutstr, "文件数据正确! pos1=%d,pos2=%d,tempfilelen=%d,filelen=%d", (int)pos1, (int)pos2, (int)tempfilelen, (int)filelen);
			//InsertTextBoxLine(panel2_sdfileHandle, PANEL_SF_TEXTBOX, -1, printoutstr);
			////tempstr = malloc (sizeof (char) * (tempfilelen+1));  // 
			////memset(tempstr, '\0', (tempfilelen+1)); 
			////memcpy(tempstr,(char *)&filedata[pos1+2],tempfilelen);
			////InsertTextBoxLine(panel2_sdfileHandle, PANEL_SF_TEXTBOX, -1,"文件数据:");
			////InsertTextBoxLine(panel2_sdfileHandle, PANEL_SF_TEXTBOX, -1,tempstr); 
			////free(tempstr);	 //5540243	//5475231  160064
			printf("文件保存的路径:%s\n",tempfilepath);
			//InsertTextBoxLine(panel2_sdfileHandle, PANEL_SF_TEXTBOX, -1, tempfilepath);
#endif				
			FILE *fp0 = fopen(tempfilepath, "wb");// in
			//tempfilehandle = OpenFile(tempfilepath, VAL_WRITE_ONLY, VAL_TRUNCATE, VAL_BINARY);
			//WriteFile(tempfilehandle, (char *)&filedata[pos1 + 2], tempfilelen);
			fwrite((char *)&filedata[pos1 + 2], 1, tempfilelen, fp0);// 
			fclose(fp0);
			//------------------------------------------
#if (0)// (_DEBUG_VK70xxMC_LIB_>0)//
			GetNumTableRows(panel2_sdfileHandle, PANEL_SF_TABLE, &numRows);
			numRows = numRows + 1;  //Inserting the row  
			InsertTableRows(panel2_sdfileHandle, PANEL_SF_TABLE, numRows, 1, VAL_USE_MASTER_CELL_TYPE);
			SetTableCellVal(panel2_sdfileHandle, PANEL_SF_TABLE, MakePoint(1, numRows), tempfilename);
			SetTableCellVal(panel2_sdfileHandle, PANEL_SF_TABLE, MakePoint(2, numRows), tempfileszie);
			SetTableCellVal(panel2_sdfileHandle, PANEL_SF_TABLE, MakePoint(3, numRows), tempfilepath);
			//SetActiveTableCell (panel2_sdfileHandle, PANEL_SF_TABLE, MakePoint(0, numRows));
#endif
			//-----------------------------------------
#if (_DEBUG_VK70xxMC_LIB_>0)//
			//int atoi (const char *str)
			//filesize := strtoint(tstr);  
			//Mainform.Memo1.Lines.Add('文件已保存: '+ filename + ' ,  文件大小 ：'  + inttostr(filesize)+' 字节');  
			printf("文件保存后数据参数【%d】【%d】【%d】【%d】【%d】\n", packageindex, pos1, pos2, tempfilelen, filelen);
#endif
			packageindex = pos1 + tempfilelen;//pos1+filesize+1;  // 下一个位置开始搜索
			///////////////////////////////////////////////
			//lastpos := MainForm.GetComboBoxPosition1(MainForm.ComboBox20);
			//if (lastpos>0)
			//{
			//MainForm.StringGrid1.Cells[2,lastpos]:= inttostr(filesize);
			//MainForm.StringGrid1.Cells[3,lastpos]:= '已下载';
			//MainForm.StringGrid1.Cells[4,lastpos]:= filename;
			//}
			//else
			//{
			//MainForm.StringGrid1.Cells[2,dwloadindex]:= inttostr(filesize);
			//MainForm.StringGrid1.Cells[3,dwloadindex]:= '已下载';
			//MainForm.StringGrid1.Cells[4,dwloadindex]:= filename;
			//filename := mainform.Get_Local_CurrentDirSaveFile(filename);
			//INC(dwloadindex);
			//}
			////////////////////////////////////////////////
		}
		//=============================================================================================================
		// information
		//=============================================================================================================
		else if (packageflag == 11)///    文件目录信息
		{
			//lastpos := pos1;
			intptr_t sdtotalspace = 0;
			intptr_t sdavailablesize = 0;
			intptr_t sdusedsize = 0;
			intptr_t filenum = 0;
			char tempfiledirpathname[256];
			memset(tempfiledirpathname, '\0', 256);
			strcat(tempfiledirpathname, sDFile[mci].TempADCFilePath);
			strcat(tempfiledirpathname, "\\vk70xnh_sdfile_dir_information.txt");
			//ssize_t allfilenames:='';
			//ssize_t filedir:='';
			//Mainform.Memo1.Lines.Add('下一个位置开始搜索：开始开始开始开始开始'+inttostr(pos1)+'/'+inttostr(SdcardBytes_Buffer_Count));
			//sdtotalspace,sdavailablesize,sduesdsize,filenum:integer;
			//allfilenames,filedir:string;
			//sdtotalspace[…],sdavailablesize […],sdusedsize[…], filedir[…],filename[…],filenum[…],<CR><LF>
	     	//-------------------------------------		
				
			FILE *fp2 = fopen(tempfiledirpathname, "wb");// in
			fprintf(fp2, "[采集卡SD卡文件系统目录]\n");// 
			//fwrite((char *)&filedata[packageindex], 1, (filelen - packageindex), fp2);// 
			//fclose(fp2);
			//======================== length( Edit1.text )
			packageindex = pos1;  // 下一个位置开始搜索
			pos1 = PosExTbytes("sdtotalspace[", 13, (const char *)&filedata[packageindex], packageindex, filelen);
			pos2 = PosExTbytes(SEGINFOR_END, 1, (const char *)&filedata[pos1], pos1, filelen);
			templen = pos2 - pos1 - 2;
			if ((pos1 > 1) && (pos2 > 1) && (templen>0))
			{
				tempstr = malloc(sizeof (char)* (templen + 1));  //
				memset(tempstr, '\0', (templen + 1));
				memcpy(tempstr, (char *)&filedata[pos1 + 2], templen);
#if (_DEBUG_VK70xxMC_LIB_>0)//(0)// 
				printf("采集卡SD卡总存储空间：%s \n", tempstr);
#endif	
				fprintf(fp2, "采集卡SD卡总存储空间 = \"%s\"\n", tempstr);// 
				free(tempstr);
			}

			//======================== length( Edit1.text )
			packageindex = pos1;  // 下一个位置开始搜索
			pos1 = PosExTbytes("sdavailablesize[", 16, (const char *)&filedata[packageindex], packageindex, filelen);
			pos2 = PosExTbytes(SEGINFOR_END, 1, (const char *)&filedata[pos1], pos1, filelen);
			templen = pos2 - pos1 - 2;
			if ((pos1 > 1) && (pos2 > 1) && (templen>0))
			{
				tempstr = malloc(sizeof (char)* (templen + 1));  //
				memset(tempstr, '\0', (templen + 1));
				memcpy(tempstr, (char *)&filedata[pos1 + 2], templen);
				fprintf(fp2, "采集卡SD卡可用空间 = \"%s\"\n", tempstr);// 
#if (_DEBUG_VK70xxMC_LIB_>0)//(0)// 
				printf("采集卡SD卡可用空间：%s \n", tempstr);
#endif
				free(tempstr);
			}

			//======================== length( Edit1.text )
			packageindex = pos1;  // 下一个位置开始搜索
			pos1 = PosExTbytes("sdusedsize[", 11, (const char *)&filedata[packageindex], packageindex, filelen);
			pos2 = PosExTbytes(SEGINFOR_END, 1, (const char *)&filedata[pos1], pos1, filelen);
			templen = pos2 - pos1 - 2;
			if ((pos1 > 1) && (pos2 > 1) && (templen>0))
			{
				tempstr = malloc(sizeof (char)* (templen + 1));  //
				memset(tempstr, '\0', (templen + 1));
				memcpy(tempstr, (char *)&filedata[pos1 + 2], templen);
				fprintf(fp2, "采集卡SD卡已使用空间 = \"%s\"\n", tempstr);//
				sprintf(printoutstr, "采集卡SD卡已使用空间：%s \n", tempstr);
#if (_DEBUG_VK70xxMC_LIB_>0)//(0)// 
				printf(printoutstr);
				//InsertTextBoxLine(panel2_sdfileHandle, PANEL_SF_TEXTBOX, -1, printoutstr);
#endif
				memset(printoutstr, '\0', 16);
				CommStr_RemoveInvaildCharForInteger(tempstr, printoutstr);
				//tempfilelen = atoi(tempstr);
				sDFile[mci].TotalusedSDSize = atoi(printoutstr);
				sDFile[mci].TotalusedSDSize = sDFile[mci].TotalusedSDSize * 1024 * 1024;
				//InsertTextBoxLine(panel2_sdfileHandle, PANEL_SF_TEXTBOX, -1,"sdusedsize:");
				//InsertTextBoxLine(panel2_sdfileHandle, PANEL_SF_TEXTBOX, -1,tempstr); 
				//int atoi (const char *str)
				//filesize := strtoint(tstr); 
				free(tempstr);
			}

			//======================== length( Edit1.text )
			packageindex = pos1;  // 显示文件路径
			pos1 = PosExTbytes("filedir[", sizeof("filedir["), (const char *)&filedata[packageindex], packageindex, filelen);
			pos2 = PosExTbytes(SEGINFOR_END, 1, (const char *)&filedata[pos1], pos1, filelen);
			templen = pos2 - pos1 - 2;
			if ((pos1 > 1) && (pos2 > 1) && (templen>0))
			{
				tempstr = malloc(sizeof (char)* (templen + 1));  //
				memset(tempstr, '\0', (templen + 1));
				memcpy(tempstr, (char *)&filedata[pos1 + 2], templen);
				fprintf(fp2, "采集卡SD卡文件路径 = \"%s\"\n", tempstr);//
				sprintf(printoutstr, "采集卡SD卡文件路径：%s \n", tempstr);
#if (_DEBUG_VK70xxMC_LIB_>0)//(0)// 
				printf(printoutstr);
				//InsertTextBoxLine(panel2_sdfileHandle, PANEL_SF_TEXTBOX, -1, printoutstr);
				//ClearListCtrl(panel2_sdfileHandle, PANEL_SF_TREE);
				//InsertTreeItem(panel2_sdfileHandle, PANEL_SF_TREE, VAL_SIBLING, -1, VAL_NEXT, tempstr, "", Tag, -1);//创建根节点   
#endif
				free(tempstr);
			}


			//======================== length( Edit1.text )
			packageindex = pos1;  // 显示详细信息
			pos1 = PosExTbytes("filedetial[", sizeof("filedetial["), (const char *)&filedata[packageindex], packageindex, filelen);
			pos2 = PosExTbytes(SEGINFOR_END, 1, (const char *)&filedata[pos1], pos1, filelen);
			templen = pos2 - pos1 - 1;
			if ((pos1 > 1) && (pos2 > 1) && (templen>0))
			{
				tempstr = malloc(sizeof (char)* (templen + 1));  //
				memset(tempstr, '\0', (templen + 1));
				memcpy(tempstr, (char *)&filedata[pos1 + 1], templen);
				int fileno = 0;
				intptr_t indexi, j, len;
				indexi = 0;
				j = 0;
				len = 0;				
				while (j<templen)
				{
					indexi = PosExTbytes(SEGINFOR_MARK_SF, 1, (const char *)&tempstr[j], j, templen);
					if (indexi>0) //len>0 && 
					{
						len = indexi - j;
						memcpy(printoutstr, (char *)&tempstr[j], len);
						printoutstr[len] = '\0';
						fileno++;
						fprintf(fp2, "文件%d = \"%s\"\n", fileno,printoutstr);//
#if (_DEBUG_VK70xxMC_LIB_>0)//(0)// 
						printf("文件%d：%s \n", fileno,printoutstr);
						//InsertTreeItem(panel2_sdfileHandle, PANEL_SF_TREE, VAL_CHILD, 0, VAL_LAST, printoutstr, "", Tag, -1);
#endif
						j = indexi + 1;
					}
					else j = templen;
				}
				free(tempstr);
			}
			//======================== length( Edit1.text )
			packageindex = pos1;  // 显示文件数量
			pos1 = PosExTbytes("filenum[", sizeof("filenum["), (const char *)&filedata[packageindex], packageindex, filelen);
			pos2 = PosExTbytes(SEGINFOR_END, 1, (const char *)&filedata[pos1], pos1, filelen);
			templen = pos2 - pos1 - 2;
			if ((pos1 > 1) && (pos2 > 1) && (templen>0))
			{
				tempstr = malloc(sizeof (char)* (templen + 1));  //
				memset(tempstr, '\0', (templen + 1));
				memcpy(tempstr, (char *)&filedata[pos1 + 2], templen);
				fprintf(fp2, "采集卡SD卡文件数量 = \"%s\"\n", tempstr);//
				sprintf(printoutstr, "采集卡SD卡文件数量：%s 个文件\n", tempstr);
#if (_DEBUG_VK70xxMC_LIB_>0)//(0)// 
				printf(printoutstr);
				//InsertTextBoxLine(panel2_sdfileHandle, PANEL_SF_TEXTBOX, -1, printoutstr);
#endif				

				memset(printoutstr, '\0', 16);
				CommStr_RemoveInvaildCharForInteger(tempstr, printoutstr);
				//tempfilelen = atoi(tempstr);
				sDFile[mci].tsdfileNum = atoi(printoutstr);
				free(tempstr);
			}
			//==============================
			fclose(fp2);
		}
		//=============================================================================================================
		if (filelen > packageindex)
		{

			i = filelen - packageindex;
			if (i < 10)
			{
				packageindex = filelen;
			}
		}
		//=============================================================================================================
	}
	//i = ExtractCmpStrsEndPosFromL2R_FirstFound(SYSNCHANDER_END,5,rxdat,len);
#if (_DEBUG_VK70xxMC_LIB_>0)//(0)// 
	printf("free(filedata)endddddddddddddddddddd=%d\n", filelen);
#endif
	free(filedata);
	//--------------------------------------

	return 0;
}

////////////////////////////////////////////////////





////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// sd file  function
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////


int Def_Function_OUTfmt VK70xNMC_Set_SaveFileDeafultPath(int tflag, const char *defaultdir)
{
	//int j;
	FILE *tfilehandle;
	char tempstr[MAX_PATHNAME_LEN];

	tfilehandle = fopen("vk70xmcsdconfig.ini", "wb");// in
	memset(tempstr, '\0', sizeof(tempstr));//
	//------------------------------------
	sprintf(tempstr, "[SD Default Configuration]\n");
	fwrite(tempstr, 1, strlen(tempstr), tfilehandle);//
	///////////////////////////////////////
	memset(tempstr, '\0', sizeof(tempstr));//
	sprintf(tempstr, "Default DIR=\"");
	fwrite(tempstr, 1, strlen(tempstr), tfilehandle);//
	memset(tempstr, '\0', sizeof(tempstr));//
	//==========================================
	if (tflag == 0)
	{
		if (getcwd(tempstr, MAX_PATHNAME_LEN) == NULL)
		{
			sprintf(tempstr, "D:");
		}
	}
	else sprintf(tempstr, defaultdir);	
	//----------------------------------------------
	fwrite(tempstr, 1, strlen(tempstr), tfilehandle);//
	memset(tempstr, '\0', sizeof(tempstr));//
	sprintf(tempstr, "\"\n");
	fwrite(tempstr, 1, strlen(tempstr), tfilehandle);//
	fclose(tfilehandle);
	//============================================
	return 0;
}

int Def_Function_OUTfmt VK70xNMC_Get_SDFileRuningInformation(int mci, int *para)
{
	if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开 
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -13;
	//----------------------------------------------
	if ((VK[mci].WorkMode != VKxxx_MODE_DOWNLOADFILE) || (sDFile[mci].FileOpenFlag == 0))return -7;// 当前未工作SD 模式下
	//----------------------------------------------
	*para++ = (int)sDFile[mci].TotalusedSDSize;
	*para++ = sDFile[mci].tsdfileCount;
	*para++ = sDFile[mci].tsdfileNum;
	*para++ = sDFile[mci].tsdfileStatus;
	*para++ = sDFile[mci].tNextTask;	
	//-----------------------------------------------
	return 0;
}

//------------------------------------------------------
// enter and exit sd file system
//--------------------------------------------------------

int Def_Function_OUTfmt VK70xNMC_Enter_SDFileSystem(int mci)
{
	int i;
	unsigned char tempdatbuf[16];
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
	printf("ThreadRunningState=%d  \n", TCPMonitor_ThreadRunningState);
#endif
	if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开 
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -13;
	//----------------------------------------------
	//if (VK[mci].WorkMode != VKxxx_MODE_DOWNLOADFILE)
	//{
		//sDFile_Intializetempsdcardfile(mci);
	//}
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
	printf("sDFile[mci].FileOpenFlag= [%d] [VK[mci].WorkMode=%d] \n", sDFile[mci].FileOpenFlag, VK[mci].WorkMode);
#endif
	sDFile_CheckSDCardDownloadCondition(mci);
	//----------------------------------------------
	//for (i = 0; i < 16; i++)tempdatbuf[i] = 0;

	tempdatbuf[0] = 0x8B; // 
	tempdatbuf[1] = 0; // 采样方式
	tempdatbuf[2] = 0; //保存文件格式
	i = DisposalTXDatum(VKTCPServer.SockClient[mci], vCOM_CMD_RW_MODE, tempdatbuf, 16, 1);  //vCOM_CMD_RW_IO
	//-----------------------------------------------
	if (i >= 0)
	{//VK[mci].LastWorkMode = VKxxx_MODE_RTTX_SAMPLING;
		VK[mci].LastWorkMode = VK[mci].WorkMode;// 
		VK[mci].WorkMode = VKxxx_MODE_DOWNLOADFILE;
		sDFile[mci].tsdfileStatus = 0;
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
		printf("采集卡 [%d] 前面模式【%d】重新进入下载模式[VK[mci].WorkMode=%d] \n", sDFile[mci].FileOpenFlag, VK[mci].LastWorkMode, VK[mci].WorkMode);
#endif
	}	
	return i;
}


int Def_Function_OUTfmt VK70xNMC_Exit_SDFileSystem(int mci)
{
	int i;
	unsigned char tempdatbuf[16];
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
	printf("ThreadRunningState=%d  \n", TCPMonitor_ThreadRunningState);
#endif
	if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开 
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -13;
	//----------------------------------------------
	//VKxxx_MODE_RTTX_SAMPLING = 0x00,    //   real time 实时传输模式    直接命令、IO4中断触发以及IO4时钟同步触发采集数据或切换模式，开始连续采集、N点采集，停止采集等,
	//	VKxxx_MODE_RTSAVE_SAMPLING,      //   real time 保存到SD卡模式  直接命令、IO4中断触发以及IO4时钟同步触发采集数据或切换模式，开始连续采集、N点采集，停止采集等,
	//	VKxxx_MODE_DOWNLOADFILE,         //   离线文件下载模式                 ：下载文件或切换模式，需要命令下载存储的文件
	//	VKxxx_MODE_UDISK,                //    USB U盘文件模式                  :  下载文件或切换模式，所有总线交由USB文件系统
	//	VKxxx_MODE_FACOTRY,              //   工厂测试模式                     : 用于烧录工厂设置信息，工厂测试等等
	if (VK[mci].LastWorkMode > VKxxx_MODE_RTSAVE_SAMPLING)
		VK[mci].LastWorkMode = VKxxx_MODE_RTTX_SAMPLING;
	//----------------------------------------------
	for (i = 0; i < 16; i++)tempdatbuf[i] = 0;

	if (VK[mci].LastWorkMode == VKxxx_MODE_RTTX_SAMPLING)tempdatbuf[0] = 0; // 采样模式 0x8A
	else tempdatbuf[0] = 0x8A; // 采样模式 0x8A

	tempdatbuf[1] = 0; // 采样方式
	tempdatbuf[2] = 0; //保存文件格式
	i = DisposalTXDatum(VKTCPServer.SockClient[mci], vCOM_CMD_RW_MODE, tempdatbuf, 16, 1);  //vCOM_CMD_RW_IO
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
	printf("退出SD模式=[%d] [%d]  \n", i,sDFile[mci].FileOpenFlag);
#endif
	//-----------------------------------------------	
	if (i>0)//VK[mci].WorkMode = VKxxx_MODE_RTTX_SAMPLING;
	{  //下载模式退出返回的模式
		VK[mci].WorkMode = VK[mci].LastWorkMode;
		sDFile[mci].tsdfileStatus = 0;
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
		printf("退出SD模式，退出后采集卡模式=[%d] [%d]  \n", i, VK[mci].WorkMode);
#endif
	}
	//-------------------------------------------------
	return i;
}

///////////////////////////////////////////////////////////////////////////////////
//------------------------------------------------------
// download sd file
//--------------------------------------------------------

int Def_Function_OUTfmt VK70xNMC_Get_SDFileDIR(int mci)
{
	int i;
	unsigned char tempdatbuf[8];
	if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开 
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -13;
	//----------------------------------------------
	sDFile[mci].RxSDBytesCount = 0;
	sDFile[mci].tsdfileNum = 0;
	sDFile[mci].tsdfileCount = 0;
	sDFile[mci].tNextTask = 0;
	//=====================================
	for (i = 0; i < 8; i++)tempdatbuf[i] = 0;
	tempdatbuf[0] = vCOM_STATUS_REPONSE_START;
	tempdatbuf[1] = 0x11;
	i = DisposalTXDatum(VKTCPServer.SockClient[mci], vCOM_CMD_RW_SDCARD_INFOR, tempdatbuf, 2, 0);  //vCOM_CMD_RW_IO
	//-----------------------------------------------
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
	printf("获取文件目录状态=[%d] [VK[mci].WorkMode=%d] \n", i, VK[mci].WorkMode);
#endif
	sDFile[mci].tsdfileStatus = 1;
	return i;
}


int Def_Function_OUTfmt VK70xNMC_Get_OneSDFile(int mci, int fileindex)
{
	int i;
	unsigned char tempdatbuf[8];
	if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开 
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -13;
	//----------------------------------------------
	if (sDFile[mci].tsdfileNum <= 0)return -5;//未更新目录信息或无文件
	if ((fileindex <= 0) || (fileindex > sDFile[mci].tsdfileNum))return -6;// 选择文件出错
	//-----------------------
    sDFile[mci].RxSDBytesCount = 0;
	sDFile[mci].tsdfileCount = fileindex;
	sDFile[mci].tNextTask = 0;
	//----------------------------------------------
	
	for (i = 0; i < 8; i++)tempdatbuf[i] = 0;
	tempdatbuf[0] = vCOM_STATUS_REPONSE_START;
	tempdatbuf[1] = 0x11;
	tempdatbuf[2] = (unsigned char)(fileindex / 0x100);
	tempdatbuf[3] = (unsigned char)fileindex;
	i = DisposalTXDatum(VKTCPServer.SockClient[mci], vCOM_CMD_RW_SDCARD_FILES, tempdatbuf, 4, 0);  //vCOM_CMD_RW_IO
	//-----------------------------------------------
	sDFile[mci].tsdfileStatus = 1;
	return i;
}



int Def_Function_OUTfmt VK70xNMC_Get_MultiSDFiles(int mci)
{
	int i;
	unsigned char tempdatbuf[8];
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
	printf("ThreadRunningState=%d [] \n", TCPMonitor_ThreadRunningState);
#endif
	if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开 
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -13;
	//----------------------------------------------
	if (sDFile[mci].tsdfileNum <= 0)return -5;//未更新目录信息或无文件
	sDFile[mci].RxSDBytesCount = 0;
	sDFile[mci].tsdfileCount = 1;
	sDFile[mci].tNextTask = 2;
	//----------------------------------------------

	for (i = 0; i < 8; i++)tempdatbuf[i] = 0;
	tempdatbuf[0] = vCOM_STATUS_REPONSE_START;
	tempdatbuf[1] = 0x11;
	tempdatbuf[2] = (unsigned char)(sDFile[mci].tsdfileCount / 0x100);
	tempdatbuf[3] = (unsigned char)sDFile[mci].tsdfileCount;
	i = DisposalTXDatum(VKTCPServer.SockClient[mci], vCOM_CMD_RW_SDCARD_FILES, tempdatbuf, 4, 0);  //vCOM_CMD_RW_IO
	//-----------------------------------------------
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
	printf("获取文件目录状态=[%d] [VK[mci].WorkMode=%d] \n", i, VK[mci].WorkMode);
#endif
	sDFile[mci].tsdfileStatus = 1;
	return i;
}


//------------------------------------------------------
// Delete sd file
//--------------------------------------------------------

int Def_Function_OUTfmt VK70xNMC_Delete_OneSDFile(int mci, int fileindex)
{
	int i;
	unsigned char tempdatbuf[8];
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
	printf("ThreadRunningState=%d  \n", TCPMonitor_ThreadRunningState);
#endif
	if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开 
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -13;
	//----------------------------------------------
	if (sDFile[mci].tsdfileNum <= 0)return -5;//未更新目录信息或无文件
	if ((fileindex <= 0) || (fileindex > sDFile[mci].tsdfileNum))return -6;// 选择文件出错
	//-----------------------
	sDFile[mci].RxSDBytesCount = 0;
	sDFile[mci].tsdfileCount = 0;
	sDFile[mci].tNextTask = 0;
	//----------------------------------------------
	for (i = 0; i < 8; i++)tempdatbuf[i] = 0;
	tempdatbuf[0] = vCOM_STATUS_REPONSE_START;
	tempdatbuf[1] = 0x44;
	tempdatbuf[2] = (unsigned char)(fileindex / 0x100);
	tempdatbuf[3] = (unsigned char)fileindex;
	i = DisposalTXDatum(VKTCPServer.SockClient[mci], vCOM_CMD_RW_SDCARD_FILES, tempdatbuf, 4, 0);  //vCOM_CMD_RW_IO
	//-----------------------------------------------
	if (i >= 0)
	{
		if(sDFile[mci].tsdfileNum > 0)
			sDFile[mci].tsdfileNum --;
	}
	//-----------------------------------------------
	sDFile[mci].tsdfileStatus = 1;
	return i;
}


int Def_Function_OUTfmt VK70xNMC_Delete_MultiSDFiles(int mci)
{
	int i;
	unsigned char tempdatbuf[8];
	if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开 
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -13;
	//----------------------------------------------
	if (sDFile[mci].tsdfileNum <= 0)return -5;//未更新目录信息或无文件
	sDFile[mci].RxSDBytesCount = 0;
	sDFile[mci].tsdfileCount = 0;
	sDFile[mci].tNextTask = 0;
	//----------------------------------------------
	for (i = 0; i < 8; i++)tempdatbuf[i] = 0;
	tempdatbuf[0] = vCOM_STATUS_REPONSE_START;
	tempdatbuf[1] = 0x44;
	tempdatbuf[2] = 0;
	tempdatbuf[3] = 0;
	i = DisposalTXDatum(VKTCPServer.SockClient[mci], vCOM_CMD_RW_SDCARD_FILES, tempdatbuf, 4, 0);  //vCOM_CMD_RW_IO
	//-----------------------------------------------
	if (i>=0)sDFile[mci].tsdfileNum = 0;
	//-----------------------------------------------
	sDFile[mci].tsdfileStatus = 1;
	return i;
}

/////////////////////////////////////////////////////////////////////////////////////////////////
