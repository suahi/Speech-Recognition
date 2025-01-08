#include "stdafx.h"
#include "VK70xNMC_DAQ2.h"
#include <Windows.h>

int _tmain(int argc, _TCHAR* argv[])
{
	int totalPointNum = 0;                      // sample counter
	int samplingFrequency = 100000;             // sample frequency
	int portNum = 8234;                         // 8234 is the default port number
	int curDeviceNum = 0;                       // Current number of devices
	int deviceNo = 0;                           // The default value for a single DAQ is 0
	int curHandle = 0;                          // The handle of the current device
	static char ipAdrStr[15];                   // IP address string
	static char ipAdr[128];						// Used to store IP addresses
	static double revResult[800000];			// max samplingFrequency points x (4 adc channels + 4 IO channels)
	int getPoints = 0;
	int loopTimes = 0;
	int recvLen = 0;
	int result = -1;
	int i;

	// Open TCP server port
	printf("Open TCP server port...\n");
	result = Server_TCPOpen(portNum);
	if (result < 0)
	{
		printf("Open TCP server port fail\n");
		goto err0;
	}
	else
		printf("Open TCP server port success\n");

	// Find the connected DAQ devices
	result = -1;
	while (result < 0)
	{
		loopTimes++;
		if (loopTimes > 500)// Approximately 10 seconds
		{
			printf("Timed out exit\n");
			break;
		}
		result = Server_Get_ConnectedClientNumbers(&curDeviceNum);
		Sleep(20);
	}
	if (result < 0)
	{
		printf("Find the connected DAQ devices fail\n");
		goto err1;
	}
	else
	{
		printf("Find the connected DAQ devices success \n");
		printf("Number of connected collection cards: %d\n", curDeviceNum);
	}

	// Get the Handle and IP address of the current DAQ
	for (i = 0; i < 128; i++)
	{
		ipAdr[i] = 0;
	}
	printf("Get the Handle and IP address of the DAQ...\n");
	result = Server_Get_ConnectedClientHandle(deviceNo, &curHandle, ipAdr);
	if (result < 0)
	{
		printf("Get the Handle and IP address of the DAQ fail\n");
		goto err1;
	}
	else
	{
		printf("Get the Handle and IP address of the DAQ success\n");
		for (i = 14; i < 128; i++)// Zero invalid characters
		{
			ipAdr[i] = 0;
		}
		printf("DAQ IP address: %s\n", ipAdr);
		printf("DAQ Handle: %d\n", curHandle);
	}

	// Switching System Mode
	printf("Switching System Mode...\n");
	result = VK70xNMC_Set_SystemMode(deviceNo, 0, 0, 0);
	if (result < 0)
	{
		printf("Switching System Mode fail\n");
		goto err1;
	}
	else
		printf("Switching System Mode success\n");

	// Initialize parameters
	printf("Sampling Resolution: 16-bit\n");
	printf("Sampling Frequency: %d\n", samplingFrequency);
	printf("Initialize DAQ parameters...\n");
	result = VK70xNMC_Initialize(deviceNo, 4, 1, samplingFrequency, 0, 0, 0, 0);
	if (result < 0)
	{
		printf("Initialize DAQ parameters fail\n");
		goto err1;
	}
	else
		printf("Initialize DAQ parameters success\n");

	// Set blocking read data
	printf("Switching System Mode...\n");
	result = VK70xNMC_Set_BlockingMethodtoReadADCResult(1, 1000);
	if (result < 0)
	{
		printf("Switching System Mode fail\n");
		goto err1;
	}
	else
		printf("Switching System Mode success\n");

	printf("Please press any key to start continuous sampling...\n");
	getchar();

	// Start continuous sampling
	printf("Start continuous sampling...\n");
	result = VK70xNMC_StartSampling(deviceNo);
	if (result < 0)
	{
		printf("Start continuous sampling fail\n");
		goto err1;
	}
	else
		printf("Start continuous sampling success\n");

	getPoints = (samplingFrequency > 10) ? samplingFrequency / 10 : 1;
	while (result >= 0)
	{
		// Read sampling data from 4 channels.
		recvLen = VK70xNMC_GetFourChannel(deviceNo, revResult, getPoints);
		if (recvLen > 0)
		{
			// Count the number of points obtained each time
			totalPointNum = totalPointNum + recvLen;
			printf("Total sampling 4 channels[%d] data , The number of data points currently read is: %d\n", totalPointNum, recvLen);

			// Print the numerical values of some points
			for (i = 0; i < recvLen * 4; i += 4)
			{
				if (i % (100 * 4) == 0)// Print only 1% because the printing speed cannot keep up with the speed of DAQ transmission.
				{
					printf("CH1=%.8fV  ", revResult[i + 0]);
					printf("CH2=%.8fV  ", revResult[i + 1]);
					printf("CH3=%.8fV  ", revResult[i + 2]);
					printf("CH4=%.8fV\n", revResult[i + 3]);
				}
			}
		}
		else
		{
			printf("Data acquisition failed or timed out!");
		}
	}
err2:
	// Stop sampling
	VK70xNMC_StopSampling(deviceNo);
err1:
	// Close TCP server
	Server_TCPClose(portNum);
err0:
	printf("Please press any key to end...");
	getchar();

	return 0;
}
