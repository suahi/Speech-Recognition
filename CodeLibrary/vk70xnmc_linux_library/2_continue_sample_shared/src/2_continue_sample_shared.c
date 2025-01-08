#include "VK70xNMC_DAQ2.h"

#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <signal.h>

#include <unistd.h>
#define Sleep(n) usleep(n * 1000)

int clientnum = 0;

void ctrl_c_handler(int s)
{
	int i;
	printf("\n");
	for (i = 0; i<clientnum; i++)
	{
		VK70xNMC_StopSampling(i);
		printf("采集卡【%d】已停止采样!\n", i);
	}
	Server_TCPClose(8234);
	exit(1);
}

int main(int argc, char* argv[])
{
	time_t t;
	struct tm *lt;
	//-----------------------
	int stopenflag[8];
	static double resbuffer[100000];
	int ioobuffer[4];
	//int timeout = 0;
	int len, i = 0;
//	int clientnum = 0;
	int st = 0;
	int respeed;
	unsigned int testcounter = 0;
	int timeout_1s_uc = 0;

	struct sigaction sigIntHandler;

	sigIntHandler.sa_handler = ctrl_c_handler;
	sigemptyset(&sigIntHandler.sa_mask);
	sigIntHandler.sa_flags = 0;

	sigaction(SIGINT, &sigIntHandler, NULL);

	//====================================
	for (i = 0; i < 8; i++)stopenflag[i] = 0;
	//=====================================
	st = Server_TCPOpen(8234);
	printf("Open the Server port, start to search the DAQ device:%d\n", st);
	while (1)
	{
		///////////////////////////////////////////////////////////////////////////////////////////////
		Sleep(5);
		if (++timeout_1s_uc >= 200)
		{
			len = Server_Get_ConnectedClientNumbers(&clientnum);// to check the connected daq deivce
			timeout_1s_uc = 0;
			Server_Get_RxTotoalBytes(&respeed, 1);// To read  the received bytes with 1 seconds then clear the counter
			printf("Speed rate： %d bytes per second\n", respeed);
		}
		//////////////////////////////////////////////////////////////////////////////////////////////////
		for (i = 0; i<clientnum; i++)
		{
			if (stopenflag[i] == 1)
			{
				//len = VK70xNMC_GetOneChannel(i, 1, resbuffer, 10000);// To read one channel for VK701N and VK702N
				len = VK70xNMC_GetFourChannel(i, resbuffer, 10000);// To read all channels for VK701N,  or read channe 1~4 for VK702N
				//len = VK70xNMC_GetAllChannel(i, resbuffer, 10000);// To read all channels for VK702N
				//------------------------------
				//len = VK70xNMC_GetOneChannel_WithIOStatus(i,1, resbuffer, 10000, 3);//To read one channel 2 & IO2 & IO3 for VK701N and VK702N
				//len = VK70xNMC_GetFourChannel_WithIOStatus(i, resbuffer, 10000,2);// To read all channels & IO3 for VK701N,  or read channe 1~4 & IO3  for VK702N
				//len = VK70xNMC_GetAllChannel_WithIOStatus(i, resbuffer, 10000, 1);// To read all channels & IO2 for VK702N
				//------------------------------
				if (len>0)
				{
					printf("Read the DAQ【%d】 continous sampling number:  %d\n", i, len);
					/*-----------------------
					 please add the print result arrording to the called function in here
					-------------------------*/
				}
			}
		}
		/////////////////////////////////////////////////////////////////////
		for (i = 0; i<clientnum; i++)
		{
			if (stopenflag[i] == 0)
			{
				stopenflag[i] = 1;
				//st = VK70xNMC_Set_SystemMode(0, 0, 0, 0);// return the nomal mode
				//-------------------------------------------------
				printf("==============================================================\n");
				printf("Found the connected DAQ clients and start sending commands: %d\n", clientnum);
				int param[12];
				param[0] = 1000;//sampling freq
				param[1] = 4; //fixed 4
				param[2] = 24; //24bit mode
				param[3] = 0; //N_Samples
				param[4] = 0;	//Set channel- 1,5 inputting voltage range for +/-10V
				param[5] = 1;	//Set channel- 2,6 inputting voltage range for +/-5V
				param[6] = 1;	//Set channel- 2,7 inputting voltage range for +/-5V
				param[7] = 0;	//Set channel- 3,8 inputting voltage range for +/-10V
				param[8] = 0; //Set channel- 1,5 ADC mode
				param[9] = 0; //Set channel- 2,6 ADC mode
				param[10] = 0; //Set channel- 3,7 ADC mode
				param[11] = 0; //Set channel- 4,8 ADC mode
				st = VK70xNMC_InitializeAll(i, param, 12);// for VK
				printf("DAQ-%d Initialize function return status:【%d】\n", i, st);
				Sleep(1000);
				st = VK70xNMC_StartSampling(i);//  start to contintous sampling
				printf("DAQ-%d Start to continous sampling!\n", i);
			}
		}
	}
	return 0;
}
