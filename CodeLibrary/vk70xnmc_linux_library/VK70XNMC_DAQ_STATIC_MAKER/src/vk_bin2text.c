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

const char  SIGNMARK_DOT[] = { "." };// separted file 文件分隔符号
const char  SIGNMARK_LINE[] = { "\\" }; // mark file size header


typedef struct _SDFILESYSTEM_BIN2TEXT_WORK_GLOBAL
{// global
	int Cvt_Status;
	int Cvt_Precent;
	char Cvt_Filename[MAX_PATHNAME_LEN];
}SDFILESYSTEM_BIN2TEXT_WORK_GLOBAL;


typedef struct _SDFILESYSTEM_BIN2TEXT_ {
	//------------------
	int year;
	unsigned char month;
	unsigned char day;
	unsigned char hour;
	unsigned char mintue;
	unsigned char second;
	int           ms;
	//--------------
	double referencevoltage;// 4.00/2.442V
	int    channelvolrange[8];
	//----------------
	int sr;
	int npoints;
	//-----------------
	int           vCOM_PackageLen;
	unsigned char vCOM_CMD;
	//------------------
} SDFILESYSTEM_BIN2TEXT;


HANDLE                              handle_Bin2Text;//线程
SDFILESYSTEM_BIN2TEXT_WORK_GLOBAL   sys_Bin2Text; //


//Month:byte;// (Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec);
//Day:byte;// 1..31;
int getmaxdays(int yyear, unsigned char mmonth)
{
	unsigned char mdays;
	if (mmonth == 2)
	{
		if ((((yyear % 4) == 0) && ((yyear % 100)!= 0)) || ((yyear % 400) == 0)) mdays = 29;
		else mdays = 28;
	}
	else if ((mmonth == 1) || (mmonth == 3) || (mmonth == 5) || (mmonth == 7) || (mmonth == 8) || (mmonth == 10) || (mmonth == 12))
	{
		mdays = 31;
	}
	else mdays = 30;
	return mdays;
}


int bin2txt_PosEx(const char *cmpbuf, int len, const char *adata, int startpos, int endpos)
{
	int i, j;
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
			if (j >= len)return i;//返回对比字符最后的一个字符的位置。 
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

///////////////////////////////////////////////////////////////////////////////////////////
int Disposal_bin2text_FileInformation(void)
{
	SDFILESYSTEM_BIN2TEXT vkres;
	int File_offset, FileTotalSize;
	//-------------------------
	int	index, i, j, r, rSamplePointNum;
	//-----------------
	char result_str[1024];
	char tstr[128];
	//--------------------
	///int vkcountinsecond;
	char vktxtfilename[MAX_PATHNAME_LEN];
	char tempstr[MAX_PATHNAME_LEN];	
	char vktimestamp[MAX_PATHNAME_LEN];
	FILE *tbinfilehandle,*tresultfilehandle;
   
	//unsigned char tempb;
	int tdat32;// : integer;
	short int tdat16;// : smallint;
	unsigned char tdat8;
	double tvolvalue;// : double;
	unsigned char theadbuffer[64];
	double   tgainrg[8];    
	double   volcoeffient;
	//-----------------
	unsigned char rByteCount;// : byte;//每个采样点的
	unsigned char rChannel;// : byte; //每个采样点占多少个通道
	unsigned char rSRwidth;// : byte; //每个通道上字节宽度
	
	///////////////////////////
	//binadroffset, testprinti:integer;
    //volcoeffient:double;
	memset(vktxtfilename, '\0', sizeof(vktxtfilename));//
	memset(tempstr, '\0', sizeof(tempstr));//
	//sprintf(vktxtfilename, "Res_"); // vktxtfilename= 'Res_'; //c:\\yyyy\\filetext.txt
	
	i = bin2txt_PosEx(SIGNMARK_DOT, 1, (const char *)&sys_Bin2Text.Cvt_Filename[0], 1, MAX_PATHNAME_LEN); //i= MainForm.RightPosEx('.', filename);    
	j = bin2txt_PosEx(SIGNMARK_LINE, 1, (const char *)&sys_Bin2Text.Cvt_Filename[0], 1, MAX_PATHNAME_LEN); // j= MainForm.RightPosEx('\',filename); 

	if ((j > 0) && (i > 0) && (i > j))
	{   //vktxtfilename = vktxtfilename + copy(filename, (j + 1), (i - j - 1));  		
		memcpy(vktxtfilename, (const char *)&sys_Bin2Text.Cvt_Filename[0], j);
		memcpy(tempstr, (const char *)&sys_Bin2Text.Cvt_Filename[j], (i - j - 1));
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
		printf("输出Text文件名称1：%s\n", vktxtfilename);
		printf("输入Text文件名称2：%s\n", tempstr);
#endif
		strcat(tempstr, "_out.txt");
		strcat(vktxtfilename, tempstr);
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
		printf("输出Text文件名称3：%s\n", vktxtfilename);
		printf("输入Text文件名称4：%s\n", tempstr);
#endif
	}
	else 
	{  //vktxtfilename= inttostr(Fbin.Size) + '.txt'; 
		getcwd(vktxtfilename, MAX_PATHNAME_LEN);
		sprintf(vktxtfilename, "\\temp_out.txt");
	}
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
	printf("输出Text文件名称：%s\n", vktxtfilename);
	printf("输入bin文件名称：%s\n", sys_Bin2Text.Cvt_Filename);
#endif
	//strcat(vktxtfilename, ".txt");   //vktxtfilename= vktxtfilename + '.txt';  
    //vktxtfilename= mainform.Get_Local_CurrentDirSaveFile(vktxtfilename);
	tbinfilehandle = fopen(sys_Bin2Text.Cvt_Filename, "r");// Fbin= TFileStream.Create(filename, fmOpenRead);  //打开文  
	if (tbinfilehandle == NULL)return -1;

	File_offset=0;
	fseek(tbinfilehandle, 0L, SEEK_END);
	FileTotalSize = ftell(tbinfilehandle);
	fseek(tbinfilehandle, 0L, 0);
	
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
	printf("开始处理文件【%d】。。。。。。。。文件路径【%s】！！\n", tbinfilehandle, sys_Bin2Text.Cvt_Filename);
	printf("文件大小：【%d】【%d】\n", File_offset, FileTotalSize);
	//fseek(tbinfilehandle, 0, SEEK_END);
	//filelen = ftell(tbinfilehandle);
	//filedata = (char*)malloc(filelen + 1);
	//fseek(tbinfilehandle, 0, SEEK_SET);
	//fread(filedata, 1, filelen, tbinfilehandle);
	//filedata[filelen] = '\0';
	//fclose(tbinfilehandle);
#endif

	tresultfilehandle = fopen(vktxtfilename, "wb+");// Fbin= TFileStream.Create(filename, fmOpenRead);  //打开文  
	if (tresultfilehandle == NULL)
	{
		fclose(tbinfilehandle);
		return -1;
	}
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
	printf("输出文件【%d】。。。。。。。。文件路径【%s】！！\n", (int)tresultfilehandle, vktxtfilename);
#endif
	//assignfile(SaveVKTxtFile, vktxtfilename);
	//rewrite(SaveVKTxtFile);
	/////////////////////////////////////////////////
	//文件当前的指针位置
	/////////////////////////////////////////////////
	//tfilestrings := TStringList.Create;
	//tfilestrings.Clear;
	//===================================
	//size_t fread(void *buf, size_t size, size_t count, FILE *fp);
    //size_t fwrite(const void * buf, size_t size, size_t count, FILE *fp);
#if (_DEBUG_VK70xxMC_LIB_>0)//0//
	for (i = 0; i < 64; i++)theadbuffer[i]=0;
	printf("--------------------------------------\n");
	printf("读取信息：%d\n", (int)tbinfilehandle);
	for (i = 0; i < 64; i++)
	{
		if ((i % 15) == 0)printf("\n");
		printf("%02X ", theadbuffer[i]);
	}
	printf("--------------------------------------\n");
#endif
	fread(theadbuffer,1,64,tbinfilehandle);   // 读取64个字符
	//for i= 1 to 64 do
	//begin
	//	Fbin.Read(theadbuffer[i], 1);   // SizeOf(tempb)
	//end;
	//------------------------------------
	//if Fbin.Size > 64  then MainForm.ProgressBar1.Position = (64 * 100) div Fbin.Size
	//else MainForm.ProgressBar1.Position = 100;
	// 更新文件读取进度条
	//----------------------
#if (_DEBUG_VK70xxMC_LIB_>0)//0//
	printf("--------------------------------------\n");
	printf("读取信息：%d\n", (int)tbinfilehandle);
	for (i = 0; i < 64; i++)
	{
		if ((i % 15) == 0)printf("\n");
		printf("%02X ", theadbuffer[i]);		
	}	
	printf("--------------------------------------\n");
#endif
	//---------------------------------------------------
	fprintf(tresultfilehandle, "-------------------------------------\n");
	for (i = 0; i < 6; i++)tempstr[i] = theadbuffer[i];
	tempstr[6] = 0;
	fprintf(tresultfilehandle, "Model Name:%s\n", tempstr);
	for (i = 0; i < 16; i++)tempstr[i] = theadbuffer[i+6];
	tempstr[16] = 0;
	fprintf(tresultfilehandle, "SN:%s\n", tempstr);
	//---------------------------------
	fprintf(tresultfilehandle, "System Mode:%d\n", theadbuffer[22]);
	fprintf(tresultfilehandle, "Sample Mode:%d\n", theadbuffer[23]);
	fprintf(tresultfilehandle, "Samlpe Format:%d\n", theadbuffer[24]);
	//----------------------------
	// Get_vCOMModule_FileHeader(&tsdfilebuf[25]); // 7bytes
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
	printf("输出采集卡信息!!!!!!!!!!!!!!!!!!!!!!!!\n");
#endif
	vkres.vCOM_PackageLen = (int)theadbuffer[27] * 0x100 + theadbuffer[28];
	vkres.vCOM_CMD = theadbuffer[31];
	//===================================
	vkres.year = (int)theadbuffer[32] * 256 + theadbuffer[33];
	vkres.month  = theadbuffer[34];
	vkres.day = theadbuffer[35];
	fprintf(tresultfilehandle, "Samlpe Date:%d-%d-%d\n", vkres.year, vkres.month, vkres.day);
	vkres.hour = theadbuffer[36];
	vkres.mintue = theadbuffer[37];
	vkres.second = theadbuffer[38];
	fprintf(tresultfilehandle, "Samlpe Time:%d:%d:%d\n", vkres.hour, vkres.mintue, vkres.second);
	sprintf(vktimestamp, "%d-%d-%d %d:%d:%d", vkres.year, vkres.month, vkres.day, vkres.hour, vkres.mintue, vkres.second);
	//---------------------------
	
	vkres.channelvolrange[0] = theadbuffer[39];
	vkres.channelvolrange[1] = theadbuffer[39];
	vkres.channelvolrange[2] = theadbuffer[40];
	vkres.channelvolrange[3] = theadbuffer[40];
	vkres.channelvolrange[4] = theadbuffer[41];
	vkres.channelvolrange[5] = theadbuffer[41];
	vkres.channelvolrange[6] = theadbuffer[42];
	vkres.channelvolrange[7] = theadbuffer[42];

	for (i = 0; i < 8; i++)
	{
		fprintf(tresultfilehandle, "Samlpe Channels [%d] Voltage Value:%d\n", i, vkres.channelvolrange[i]);
		tgainrg[i] = GetGainValue_PGA(vkres.channelvolrange[i]);
	}
	vkres.referencevoltage = theadbuffer[43];
	fprintf(tresultfilehandle, "Reference Voltage%lf\n", vkres.referencevoltage);//Reference Voltage
	
	fprintf(tresultfilehandle, "Sample Accuracy(8/16/24bit):%d\n", theadbuffer[44]);
	//vkres.ADCSampleMode= theadbuffer[45];
	//mainform.memo1.Lines.Add('采集精度（8/16/24bit）：' + inttostr(vkres.ADCSampleMode));

	vkres.sr = (int)theadbuffer[45] * 0x10000 + (int)theadbuffer[46] * 0x100 + theadbuffer[47];
	fprintf(tresultfilehandle, "Sample Rate:%d\n", vkres.sr);

	vkres.npoints = (int)theadbuffer[49] * 0x1000000 +  (int)theadbuffer[50] * 0x10000 + (int)theadbuffer[51] * 0x100 + theadbuffer[52];
	fprintf(tresultfilehandle, "N Points:%d\n", vkres.npoints);
	fprintf(tresultfilehandle, "-------------------------------------\n");
	////////////////////////////////////////////////////////////////////
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
	printf("命令字节：%d\n", vkres.vCOM_CMD);
#endif
    rChannel  = vkres.vCOM_CMD & 0x0F;   // 通道数目
	//-------------------------------------
	if ((vkres.vCOM_CMD & 0xF0) == 0x10)
	{
		rSRwidth = 1;     //  每个通道占 1 个字节
	    rByteCount = rChannel; // //每个采样点占字节总数
	}
	else if ((vkres.vCOM_CMD & 0xF0) == 0x20)
	{
	   rSRwidth = 2;  // 每个通道占2 个字节
	   rByteCount = rChannel * 2; // //每个采样点占字节总数
	}
	else if ((vkres.vCOM_CMD & 0xF0) == 0x30)
	{
	   rSRwidth = 3;// 每个通道占4 个字节
	   rByteCount = rChannel * 4; // //每个采样点占字节总数
	}
	else //if ((vkres.vCOM_CMD & 0xF0) == 0x10)rSRwidth = 1;     //  每个通道占 1 个字节
	{
		rSRwidth = 4;// 每个通道占4 个字节
		rByteCount = rChannel * 4; // //每个采样点占字节总数
	}	
	//-------------------------------------
	//fprintf(tresultfilehandle, "Date/Time(1/sr)\t'CH-1 Voltage Value\tCH-2 Voltage Value\tCH-3 Voltage Value\tCH-4 Voltage Value\tCH-5 Voltage Value\tCH-6 Voltage Value\tCH-7 Voltage Value\tCH-8 Voltage Value\tIO2 Value\tIO3 Value\n");
	memset(tstr, '\0', sizeof(tstr));//
	memset(result_str, '\0', sizeof(result_str));//	
	sprintf(tstr, "Date/Time(1/sr)\t");
	strcat(result_str, tstr);
	for (j = 0; j < rChannel; j++)
	{
		memset(tstr, '\0', sizeof(tstr));//
		sprintf(tstr, "CH-%d Voltage Value\t",(j+1));
		strcat(result_str, tstr);
	}
	//----------------------
	if (rSRwidth == 3)
	{
		memset(tstr, '\0', sizeof(tstr));//
		sprintf(tstr, "IO2 Value\t");
		strcat(result_str, tstr);
		memset(tstr, '\0', sizeof(tstr));//
		sprintf(tstr, "IO3 Value\t");
		strcat(result_str, tstr);
	}
	//-----------------------
	fprintf(tresultfilehandle, "%s\n", result_str);	
	//tstr= '日期/时间(1/采样率)' + #9;  
	//tstr= tstr + '通道1电压值' + #9;
	//tstr= tstr + '通道2电压值' + #9;
	//tstr= tstr + '通道3电压值' + #9;
	//tstr= tstr + '通道4电压值' + #9;
	//tstr= tstr + '通道5电压值' + #9;
	//tstr= tstr + '通道6电压值' + #9;
	//tstr= tstr + '通道7电压值' + #9;
	//tstr= tstr + '通道8电压值' + #9;
	//tstr= tstr + 'IO1值' + #9;
	//tstr= tstr + 'IO2值' + #9;
	//tstr= tstr + 'IO3值' + #9;
	//tstr= tstr + 'IO4值';
	//writeln(SaveVKTxtFile, tstr); // 写文件头

	//-------------------------------------
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
	printf("每个通道占字节数：%d\n", rSRwidth);
	printf("通道数目：%d\n", rChannel);
	printf("每个采样点占字节总数：%d\n", rByteCount);
#endif
	//======================
    rSamplePointNum= 0;
    index = 1;
    if (vkres.referencevoltage == 0) volcoeffient = 14.652;//
	else  volcoeffient = 4;
	vkres.ms = 0;
    File_offset = 64;//FileTotalSize
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
	printf("文件总字节数：%d\n", FileTotalSize);
#endif
	///////////////////////////////////////////
	//for i:=65 to Fbin.Size do
	while (File_offset < FileTotalSize)
	{
		//fread(theadbuffer, 1, 64, tbinfilehandle);   // 读取64个字符
		fseek(tbinfilehandle, File_offset, 0);

		fread(theadbuffer, 1, rByteCount, tbinfilehandle); // SizeOf(tempb)   // 读取1字节
		File_offset = File_offset + rByteCount;
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
		//printf("文件处理进度：【%d】【%d】\n", File_offset,rByteCount);
		//printf("文件处理进度：%d\n", sys_Bin2Text.Cvt_Precent);
#endif
		sys_Bin2Text.Cvt_Precent = (File_offset * 100) / FileTotalSize;

		index = 1;    // 复位， 下一个采样点
		memset(tstr, '\0', sizeof(tstr));//
		memset(result_str, '\0', sizeof(result_str));//		
		////////////////////////////////
		if (vkres.ms >= vkres.sr)
		{
			vkres.ms = 0;
			vkres.second++;
			if (vkres.second > 59)
			{
				vkres.second = 0;
				vkres.mintue++;
				if (vkres.mintue > 59)
				{
					vkres.mintue = 0;
					vkres.hour++;
					if (vkres.hour > 23)
					{
						vkres.hour = 0;
						vkres.day++;
						if (vkres.day > getmaxdays(vkres.year, vkres.month))
						{
							vkres.day = 0;
							vkres.month++;
							if (vkres.month > 12)
							{
								vkres.month = 1;
								vkres.year++;
							}
						}
					}
				}
			}
			//--------------------------------------
			sprintf(vktimestamp, "%d-%d-%d %d:%d:%d", vkres.year, vkres.month, vkres.day, vkres.hour, vkres.mintue, vkres.second);
			//--------------------------------------
		}
		else vkres.ms++;
		//-----------------------------------
		sprintf(result_str, "%s:%d\t", vktimestamp, vkres.ms);
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
		//printf("文件1：%s\n", result_str);
#endif
		//=====================================================================
		//=====================================================================
		//=====================================================================
		//=====================================================================
		//=====================================================================
		//=====================================================================
		//=====================================================================
		//  VK702N ,  电压值需要取反
		//----------------------------------------------------------------------
		if (vkres.referencevoltage == 0)
		{
			if (rSRwidth == 1)  // 8bit, singnal bytes
			{
				r = 0;
				for (j = 0; j < rChannel; j++)
				{
					//tdat16 = theadbuffer[r++] * 0x100;
					tdat16 = (short int)(~((theadbuffer[r++] * 0x100))) + 1;
					tdat32 = (int)tdat16;
					tvolvalue = (((tdat32)*volcoeffient) / 0x8000) / tgainrg[j];
					sprintf(tstr, "%lf\t", tvolvalue);
					strcat(result_str, tstr);
				}
			}
			else if (rSRwidth == 2)  // 16bit, double bytes
			{
				r = 0;
				for (j = 0; j < rChannel; j++)
				{
					//tdat16:= theadbuffer[r]+ (theadbuffer[r+1]*256);   VK 701 LAN传输
					//注意原始数据与 VK 701 LAN传输  和 文件存储方式不一样。
					//tdat16 = (int)theadbuffer[r + 1] * 0x100 + (int)theadbuffer[r];//文件存储方式
					tdat16 = (short int)(~(theadbuffer[r] + (theadbuffer[r + 1] * 0x100))) + 1;					
					tdat32 = (int)tdat16 * 0x100;
					tvolvalue = (((tdat32)*volcoeffient) / 0x800000) / tgainrg[j];
					sprintf(tstr, "%lf\t", tvolvalue);
					strcat(result_str, tstr);
					r += 2;
				}
			}
			else if (rSRwidth == 3)// 24bit, three bytes
			{
				r = 0;
				tdat8 = theadbuffer[r + 3];
				//-------------------------
				for (j = 0; j < rChannel; j++)
				{
					//tdat16:= theadbuffer[r]+ (theadbuffer[r+1]*256);   VK 701 LAN传输
					//注意原始数据与 VK 701 LAN传输  和 文件存储方式不一样。
					//tdat32 = (int)theadbuffer[r] * 0x100 + (int)theadbuffer[r + 1] * 0x10000 + (int)theadbuffer[r + 2] * 0x10000;//文件存储方式
					tdat32 = (~((int)theadbuffer[r] * 0x100 + ((int)theadbuffer[r+1] * 0x10000) + ((int)theadbuffer[r + 2] * 0x1000000))) + 1;
					tdat32 = (int)tdat16 / 0x100;
					tvolvalue = (((tdat32)*volcoeffient) / 0x800000) / tgainrg[j];
					sprintf(tstr, "%lf\t", tvolvalue);
					strcat(result_str, tstr);
					r += 4;
				}
				//IO2 固定在 8通道上， IO3固定9通道
				//if ((theadbuffer[r + 3] & 0x10) == 0x10)vknextmc->CHShowBuffer[8][vknextmc->SaveShowPI] = 1;
				//else vknextmc->CHShowBuffer[8][vknextmc->SaveShowPI] = 0;
				//if ((theadbuffer[r + 3] & 0x20) == 0x20)vknextmc->CHShowBuffer[9][vknextmc->SaveShowPI] = 1;
				//else vknextmc->CHShowBuffer[9][vknextmc->SaveShowPI] = 0;

				if ((tdat8 & 0x10) == 0x10)strcat(result_str, " 1\t");
				else strcat(result_str, " 0\t");  // IO2

				if ((tdat8 & 0x20) == 0x20)strcat(result_str, " 1\t");
				else strcat(result_str, " 0\t");  // IO3
			}
			else// 32bit, four bytes
			{
				r = 0;
				for (j = 0; j < rChannel; j++)
				{
					//tdat16:= theadbuffer[r]+ (theadbuffer[r+1]*256);   VK 701 LAN传输
					//注意原始数据与 VK 701 LAN传输  和 文件存储方式不一样。
					//tdat32 = (int)theadbuffer[r + 1] * 0x100 + (int)theadbuffer[r + 2] * 0x10000 + (int)theadbuffer[r + 3] * 0x10000;//文件存储方式
					tdat32 = (~((int)theadbuffer[r + 1] * 0x100 + ((int)theadbuffer[r+2] * 0x10000) + ((int)theadbuffer[r + 3] * 0x1000000))) + 1;
					tdat32 = (int)tdat16 / 0x100;
					tvolvalue = (((tdat32)*volcoeffient) / 0x800000) / tgainrg[j];
					sprintf(tstr, "%lf\t", tvolvalue);
					strcat(result_str, tstr);
					r += 4;
				}

			}
		}
		//=====================================================================
		//=====================================================================
		//=====================================================================
		//=====================================================================
		//=====================================================================
		//=====================================================================
		//=====================================================================
		// VK701N ,电压值不需要取反， 所有需要分开处理
		//----------------------------------------------------------------------
		else  
		{
			if (rSRwidth == 1)  // 8bit, singnal bytes
			{
				r = 0;
				for (j = 0; j < rChannel; j++)
				{
					tdat16 = theadbuffer[r++] * 0x100;
					tdat32 = (int)tdat16;
					tvolvalue = (((tdat32)*volcoeffient) / 0x8000) / tgainrg[j];
					sprintf(tstr, "%lf\t", tvolvalue);
					strcat(result_str, tstr);
				}
			}
			else if (rSRwidth == 2)  // 16bit, double bytes
			{
				r = 0;
				for (j = 0; j < rChannel; j++)
				{
					//tdat16:= theadbuffer[r]+ (theadbuffer[r+1]*256);   VK 701 LAN传输
					//注意原始数据与 VK 701 LAN传输  和 文件存储方式不一样。
					tdat16 = (int)theadbuffer[r + 1] * 0x100 + (int)theadbuffer[r];//文件存储方式
					tdat32 = (int)tdat16 * 0x100;
					tvolvalue = (((tdat32)*volcoeffient) / 0x800000) / tgainrg[j];
					sprintf(tstr, "%lf\t", tvolvalue);
					strcat(result_str, tstr);
					r += 2;
				}
			}
			else if (rSRwidth == 3)// 24bit, three bytes
			{
				r = 0;
				if (rChannel == 4) // 24bit , VK701N, 4Channels, 4.000V, 特殊出来
				{
					tdat8 = theadbuffer[r];
					//----------------------------------------------------
					//00 22 FF 00 D0 F8 F2 FF FF F4 9F F3 FA FF FF 2F
					//      FFF8D0      FFF2F4     FFF39F FFFA2F
					r = r + 2;
					tdat32 = theadbuffer[r] * 0x1000000 + (theadbuffer[r + 3] * 0x10000) + (theadbuffer[r + 2] * 0x100);//(~(PacketDatum[r]*0x1000000+ (PacketDatum[r+3]*0x10000)+ (PacketDatum[r+2]*0x100)))+1;
					//tdat32= (~(PacketDatum[r]*0x1000000+ (PacketDatum[r+3]*0x10000)+ (PacketDatum[r+2]*0x100)))+1;
					tdat32 = tdat32 / 0x100;
					tvolvalue = (((tdat32)*volcoeffient) / 0x800000) / tgainrg[0];
					sprintf(tstr, "%lf\t", tvolvalue);
					strcat(result_str, tstr);
					r = r + 4;
					//---------------------
					tdat32 = theadbuffer[r + 3] * 0x100 + (theadbuffer[r] * 0x10000) + (theadbuffer[r + 1] * 0x1000000);//(~ (PacketDatum[r+3]*0x100+ (PacketDatum[r]*0x10000)+ (PacketDatum[r+1]*0x1000000)))+1;
					//tdat32= (~ (PacketDatum[r+3]*0x100+ (PacketDatum[r]*0x10000)+ (PacketDatum[r+1]*0x1000000)))+1;
					tdat32 = tdat32 / 0x100;
					tvolvalue = (((tdat32)*volcoeffient) / 0x800000) / tgainrg[1];
					sprintf(tstr, "%lf\t", tvolvalue);
					strcat(result_str, tstr);
					r = r + 2;
					//------------------
					tdat32 = theadbuffer[r + 2] * 0x100 + (theadbuffer[r + 3] * 0x10000) + (theadbuffer[r] * 0x1000000);//(~ (PacketDatum[r+2]*0x100+ (PacketDatum[r+3]*0x10000)+ (PacketDatum[r]*0x1000000)))+1;
					//tdat32= (~ (PacketDatum[r+2]*0x100+ (PacketDatum[r+3]*0x10000)+ (PacketDatum[r]*0x1000000)))+1;
					tdat32 = tdat32 / 0x100;
					tvolvalue = (((tdat32)*volcoeffient) / 0x800000) / tgainrg[2];
					sprintf(tstr, "%lf\t", tvolvalue);
					strcat(result_str, tstr);
					r = r + 4;
					//------------------
					tdat32 = theadbuffer[r + 3] * 0x100 + (theadbuffer[r] * 0x10000) + (theadbuffer[r + 1] * 0x1000000);//(~ (PacketDatum[r+2]*0x100+ (PacketDatum[r+3]*0x10000)+ (PacketDatum[r]*0x1000000)))+1;
					//tdat32= (~ (PacketDatum[r+3]*0x100+ (PacketDatum[r]*0x10000)+ (PacketDatum[r+1]*0x1000000)))+1;
					tdat32 = tdat32 / 0x100;
					tvolvalue = (((tdat32)*volcoeffient) / 0x800000) / tgainrg[3];
					sprintf(tstr, "%lf\t", tvolvalue);
					strcat(result_str, tstr);
					r = r + 4;

					//tdat32 = theadbuffer[r] * 0x1000000 + (theadbuffer[r + 7] * 0x10000) + (theadbuffer[r + 6] * 0x100);//(not (PacketDatum[r]*0x1000000+ (PacketDatum[r+3]*0x10000)+ (PacketDatum[r+2]*0x100)))+1;
					//tdat32 = tdat32 / 0x100;
					//tvolvalue = (((tdat32)*volcoeffient) / 0x800000) / tgainrg[0];
					//sprintf(tstr, "%lf\t", tvolvalue);
					//strcat(result_str, tstr);
					//---------------------
					//tdat32 = theadbuffer[r + 11] * 0x100 + (theadbuffer[r + 4] * 0x10000) + (theadbuffer[r + 5] * 0x1000000);//(not (PacketDatum[r+3]*0x100+ (PacketDatum[r]*0x10000)+ (PacketDatum[r+1]*0x1000000)))+1;
					//tdat32 = tdat32 / 0x100;
					//tvolvalue = (((tdat32)*volcoeffient) / 0x800000) / tgainrg[1];
					//sprintf(tstr, "%lf\t", tvolvalue);
					//strcat(result_str, tstr);
					//------------------
					//tdat32 = theadbuffer[r + 8] * 0x100 + (theadbuffer[r + 9] * 0x10000) + (theadbuffer[r + 10] * 0x1000000);//(not (PacketDatum[r+2]*0x100+ (PacketDatum[r+3]*0x10000)+ (PacketDatum[r]*0x1000000)))+1;
					//tdat32 = tdat32 / 0x100;
					//tvolvalue = (((tdat32)*volcoeffient) / 0x800000) / tgainrg[2];
					//sprintf(tstr, "%lf\t", tvolvalue);
					//strcat(result_str, tstr);
					//------------------
					//tdat32 = theadbuffer[r + 13] * 0x100 + (theadbuffer[r + 14] * 0x10000) + (theadbuffer[r + 15] * 0x1000000);//(not (PacketDatum[r+3]*0x100+ (PacketDatum[r]*0x10000)+ (PacketDatum[r+1]*0x1000000)))+1;
					//tdat32 = tdat32 / 0x100;
					//tvolvalue = (((tdat32)*volcoeffient) / 0x800000) / tgainrg[3];
					//sprintf(tstr, "%lf\t", tvolvalue);
					//strcat(result_str, tstr);
					//================================================
					//IO2 固定在 8通道上， IO3固定9通道
					//if ((theadbuffer[r] & 0x10) == 0x10)vknextmc->CHShowBuffer[8][vknextmc->SaveShowPI] = 1;
					//else vknextmc->CHShowBuffer[8][vknextmc->SaveShowPI] = 0;
					//if ((theadbuffer[r] & 0x20) == 0x20)vknextmc->CHShowBuffer[9][vknextmc->SaveShowPI] = 1;
					//else vknextmc->CHShowBuffer[9][vknextmc->SaveShowPI] = 0;

					if ((tdat8 & 0x10) == 0x10)strcat(result_str, " 1\t");
					else strcat(result_str, " 0\t");  // IO2

					if ((tdat8 & 0x20) == 0x20)strcat(result_str, " 1\t");
					else strcat(result_str, " 0\t");  // IO3
				}
				else // 2.442 mode
				{
					r = 0;
					tdat8 = theadbuffer[r + 3];
					//-------------------------
					for (j = 0; j < rChannel; j++)
					{
						//tdat16:= theadbuffer[r]+ (theadbuffer[r+1]*256);   VK 701 LAN传输
						//注意原始数据与 VK 701 LAN传输  和 文件存储方式不一样。
						tdat32 = (int)theadbuffer[r] * 0x100 + (int)theadbuffer[r + 1] * 0x10000 + (int)theadbuffer[r + 2] * 0x10000;//文件存储方式
						tdat32 = (int)tdat16 / 0x100;
						tvolvalue = (((tdat32)*volcoeffient) / 0x800000) / tgainrg[j];
						sprintf(tstr, "%lf\t", tvolvalue);
						strcat(result_str, tstr);
						r += 4;
					}
					//IO2 固定在 8通道上， IO3固定9通道
					//if ((theadbuffer[r + 3] & 0x10) == 0x10)vknextmc->CHShowBuffer[8][vknextmc->SaveShowPI] = 1;
					//else vknextmc->CHShowBuffer[8][vknextmc->SaveShowPI] = 0;
					//if ((theadbuffer[r + 3] & 0x20) == 0x20)vknextmc->CHShowBuffer[9][vknextmc->SaveShowPI] = 1;
					//else vknextmc->CHShowBuffer[9][vknextmc->SaveShowPI] = 0;

					if ((tdat8 & 0x10) == 0x10)strcat(result_str, " 1\t");
					else strcat(result_str, " 0\t");  // IO2

					if ((tdat8 & 0x20) == 0x20)strcat(result_str, " 1\t");
					else strcat(result_str, " 0\t");  // IO3
				}
			}
			else// 32bit, four bytes
			{
				r = 0;
				for (j = 0; j < rChannel; j++)
				{
					//tdat16:= theadbuffer[r]+ (theadbuffer[r+1]*256);   VK 701 LAN传输
					//注意原始数据与 VK 701 LAN传输  和 文件存储方式不一样。
					tdat32 = (int)theadbuffer[r + 1] * 0x100 + (int)theadbuffer[r + 2] * 0x10000 + (int)theadbuffer[r + 3] * 0x10000;//文件存储方式
					tdat32 = (int)tdat16 / 0x100;
					tvolvalue = (((tdat32)*volcoeffient) / 0x800000) / tgainrg[j];
					sprintf(tstr, "%lf\t", tvolvalue);
					strcat(result_str, tstr);
					r += 4;
				}

			}
		}
		//=====================================================================
		//=====================================================================
		//=====================================================================
		//=====================================================================
		//=====================================================================
		//=====================================================================
		//=====================================================================
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
		//printf("文件1：%s\n", result_str);
#endif
		//=====================================================================================
		fprintf(tresultfilehandle, "%s\n", result_str);
	}
	//========================================================================================================================================================
	//fprintf(tresultfilehandle, "%s\n", tstr);
	fclose(tresultfilehandle);
	fclose(tbinfilehandle);
	//RunConvertFilethreadFlag = 0;
	//------------------------------------'
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
	printf("文件已保存:fffffffffffffffffffffffffffffffffffffffff " );
#endif
	return 0;
}
//========================================================================================================================================================

///////////////////////////////////////////////////////
//RXLANMonitor_Handle = CreateThread(NULL, 0, DisposalBin2TextFileEvent, NULL, 0, NULL);	
//void MonitorUSBEvent(void)
DWORD WINAPI DisposalBin2TextFileEvent(PVOID pvParam)
{
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
	printf("开始BINtoText线程............\n");
#endif
	sys_Bin2Text.Cvt_Status = 1;
	Disposal_bin2text_FileInformation();
	sys_Bin2Text.Cvt_Precent = 0;
	sys_Bin2Text.Cvt_Status = 0;
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
	printf("--------------------------------------\n");
#endif
	return 0;
}

//////////////////////////////////////////////////////////////////
///
//////////////////////////////////////////////////////////////////

int Def_Function_OUTfmt VK70xNMC_Get_ConvertBin2Text_Progress(int *precent, int *tstatus)//progress
{
	*precent = sys_Bin2Text.Cvt_Precent;
	*tstatus = sys_Bin2Text.Cvt_Status;
	return 0;
}
//-----------------------------------------------------

int Def_Function_OUTfmt VK70xNMC_Start_ConvertBin2Text(const char *filename)
{
	int tsize = 0;
	sys_Bin2Text.Cvt_Precent=0;
	sys_Bin2Text.Cvt_Status=0;
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
	printf("Bin2Txt--------------------------------------\n");
	printf("打开文件路径：%s\n", filename);
#endif
	FILE *fp = fopen(filename, "r");//无法打开文件
	if (!fp)
	{
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
		printf("Error 1----Bin2Txt\n");
#endif
		return -1;
	}
	//------------------------
	fseek(fp, 0L, SEEK_END);
	tsize = ftell(fp);
	fclose(fp);
	if (tsize < 64)
	{
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
		printf("Error 2----Bin2Txt\n");
#endif
		return -2;
	}
	//memset(sys_Bin2Text.Cvt_Filename, '\0', sizeof(sys_Bin2Text.Cvt_Filename));//
	memset(sys_Bin2Text.Cvt_Filename, '\0', MAX_PATHNAME_LEN);
	strcat(sys_Bin2Text.Cvt_Filename, filename);
	//-------------------------	
	handle_Bin2Text = CreateThread(NULL, 0, DisposalBin2TextFileEvent, NULL, 0, NULL);
#if  (_DEBUG_VK70xxMC_LIB_>0)//(0)//
	printf("文件大小：%d\n", tsize);
	printf("转换文件名称：%s\n", sys_Bin2Text.Cvt_Filename);
	printf("开始文件转换！线程：%d\n", handle_Bin2Text);
#endif
	//--------------------------
	return 0;
}
