#if _MSC_VER > 1000
#pragma once
#endif 

#include "VK70xNMC_DAQ2.h"
#include "dvr_header.h"
#include <Windows.h>
#include <stdio.h>

/*
TXRec[0]: = ord('R'); TXRec[1]: = ord('e'); TXRec[2]: = ord('s'); TXRec[3]: = ord('e'); TXRec[4]: = ord('t');
TXRec[5]: = ord('V'); TXRec[6]: = ord('K'); TXRec[7]: = ord('7'); TXRec[8]: = ord('0'); TXRec[9]: = ord('x');
TXRec[10]: = ord('N'); TXRec[11]: = ord('t'); TXRec[12]: = ord('o'); TXRec[13]: = ord('U'); TXRec[14]: = ord('p');
TXRec[15]: = ord('g'); TXRec[16]: = ord('r'); TXRec[17]: = ord('a'); TXRec[18]: = ord('d'); TXRec[19]: = ord('e');
DisposalTXDatum($BB, TXRec, 20, true);
*/
int Def_Function_OUTfmt  VK70xNMC_Set_DeviceEnterUpgradeMode(int mci)
{   
	unsigned char wbuf[64];  //128
	//unsigned short int tvol;
	int i = 0;
	//int len1;
	//=====================================
	if (TCPMonitor_ThreadRunningState == 0)return -11;  //服务未打开  
	if ((VKTCPServer.Client_Num<1) || (VKTCPServer.Client_Num>MAX_TCP_CILENT_NUM))return -12; //未连接客户端 或连接客户端错误      
	if (VKTCPServer.ClientStatus[mci] == 0)return -13;  // 请求非法客户端
	if ((mci < 0) || (mci >(MAX_TCP_CILENT_NUM - 1)))return -13;
	//----------------------------------
	for (i = 0; i< 64; i++)wbuf[i] = 0;
	wbuf[0] = 'R';
	wbuf[1] = 'e';
	wbuf[2] = 's';
	wbuf[3] = 'e';
	wbuf[4] = 't';
	wbuf[5] = 'V';
	wbuf[6] = 'K';
	wbuf[7] = '7';
	wbuf[8]= '0';
	wbuf[9]= 'x';
	wbuf[10] = 'N';
	wbuf[11] = 't';
	wbuf[12] = 'o';
	wbuf[13] = 'U';
	wbuf[14] = 'p';
	wbuf[15] = 'g';
	wbuf[16] = 'r';
	wbuf[17] = 'a';
	wbuf[18] = 'd';
	wbuf[19] = 'e';	
	//----------------------------------
	//DisposalTXDatum($BB, TXRec, 20, true);
	//int DisposalTXDatum(SOCKET connectHandle, unsigned char cmd, unsigned char *txbuff, unsigned int txlen, unsigned char wrflag)
	i = DisposalTXDatum(VKTCPServer.SockClient[mci], 0xBB, wbuf, 20, 1);
	return i;//
}


/*
TXBuffer[0]:= $1B;
TXBuffer[1]:= $00;
TXBuffer[2]:= $FE;
TXBuffer[3]:= $01;
TXBuffer[4]:= $88;  //$;   准备进入工厂模式
TXBuffer[5]:= $89;


TXBuffer[0]:= $1B;
TXBuffer[1]:= $11;
TXBuffer[2]:= $EE;
TXBuffer[3]:= $00;
TXBuffer[4]:= $01;
TXBuffer[5]:= $88;  //$;   准备进入工厂模式
TXBuffer[6]:= $89;
*/
//===================================================================



