/***************************************************************************************************
 Copyright © Shenzhen Vkinging Electronic Co., Ltd. 2013-2023. All rights reserved.
 File name: 1. Coutinuous Sampling.cpp
 Author: Andy Jiang / Mr. Jin	Version: 1.0	Date:2023-12-25
 Description: VC version calling DLL for continuous sampling example program (VK701N-SD/VK701W-SD)
 Others: Debug passed VC 64bit vesion. DLL must use a 64 bit version.
 History:
***************************************************************************************************/
#ifndef __DS_WIN32DLL_VKINGING_H
#define __DS_WIN32DLL_VKINGING_H

//==============================================================================
// 如果生产 stdcall，屏蔽 _OUT+CDCEL+DLL定义，同时定义 项目属性中 -连接器中-输入-模块定义文件 {VK70xNHMC_DAQ.def}
// 如果生产 cdcel，打开 _OUT+CDCEL+DLL定义 
//==============================================================================
#define DLL_OUT_CDCEL_STDCALL  1 // [0]: CDCEL, [1]: STDCALL 
#define _DEBUG_VK70xxMC_LIB_   0
//==============================================================================
#if(DLL_OUT_CDCEL_STDCALL == 0)
//取消VK70xNHMC_DAQ.def
#define VK70xnMCDLL_fmt  __declspec(dllexport)  
//#define VK70xnMCDLL_fmt  __declspec(dllimport)
#define Def_Function_OUTfmt   

#elif (DLL_OUT_CDCEL_STDCALL==1)

//项目属性>连接器>输入>模块定义文件（VK70xNHMC_DAQ.def）
#define VK70xnMCDLL_fmt
#define Def_Function_OUTfmt  __stdcall

#else
#error “error define cdcel and stdcall!!!”
#endif

#ifdef __cplusplus
extern "C" {
#endif

	// Initialize connected collection card parameters
	VK70xnMCDLL_fmt int Def_Function_OUTfmt VK70xNMC_Initialize(int mci, double refvol, int bitmode, int sr, int volrg15, int volrg26, int volrg37, int volrg48);
	// [prototype]; int VK70xNMC_Initialize(int mci, double refvol, int bitmode, int sr, int volrg15, int volrg26, int volrg37, int volrg48);
	// [parameter]: int mci: DAQ serial number.                                     Default: [0] (Signal DAQ)
	//              double refvol: Select DAQ Mode.                                 Range: [4.000] or [1] (VK701N-SD)
	//              int bitmode: Sampling resolution.                               Range: [0]: 8-bit
	//                                                                                     [1]: 16-bit
	//                                                                                     [2]/[3]: 24-bit
	//              int sr: Sampling frequency.                                     Range: [1]~[100000](16-bit), [1]~[50000](24-bit)
	//              int volrg15: Voltage input range for CH1                        Range: [0]: +-10V, [1]: +-5V, [2]: +-2.5V, [3]: +-1V, [4]: +-500mV, [5]: +-100mV, [6]: +-20mV, [7]: +-1mV  
	//              int volrg26: Voltage input range for CH2                        Range: [0]: +-10V, [1]: +-5V, [2]: +-2.5V, [3]: +-1V, [4]: +-500mV, [5]: +-100mV, [6]: +-20mV, [7]: +-1mV  
	//              int volrg37: Voltage input range for CH3                        Range: [0]: +-10V, [1]: +-5V, [2]: +-2.5V, [3]: +-1V, [4]: +-500mV, [5]: +-100mV, [6]: +-20mV, [7]: +-1mV  
	//              int volrg48: Voltage input range for CH4                        Range: [0]: +-10V, [1]: +-5V, [2]: +-2.5V, [3]: +-1V, [4]: +-500mV, [5]: +-100mV, [6]: +-20mV, [7]: +-1mV  
	// [return value]: >= 0 : Set successfully 
	//                 -11  : Server not opened
	//                 -12  : DAQ not connected or not present
	//                 -13  : DAQ not connected or not present
	//                 other: Abnormal exit
		

	// Initialize connected acquisition card parameters, type 2
	VK70xnMCDLL_fmt int Def_Function_OUTfmt VK70xNMC_Initialize_2(int mci, double refvol, int bitmode, int sr, int npoints, int timeinval, int *volrg);
	// [prototype]; int VK70xNMC_Initialize_2(int mci, double refvol, int bitmode, int sr, int npoints, int timeinval, int* volrg);
	// [parameter]: int mci: DAQ serial number.                                     Default: [0] (Signal DAQ)
	//              double refvol: Select DAQ Mode.                                 Range: [4.000] or [1] (VK701N-SD)
	//              int bitmode: Sampling resolution.                               Range: [0]: 8-bit
	//                                                                                     [1]: 16-bit
	//                                                                                     [2]/[3]: 24-bit
	//              int sr: Sampling frequency.                                     Range: [1]~[100000](16-bit), [1]~[50000](24-bit)
	//              int npoints: Number of points to be sampled for N sampling.
	//              int timeinval: Fixed time interval N sampling time interval.    Range: >= 1 (in seconds)
	//              int* volrg: Voltage input range.								Range: [0]: +-10V, [1]: +-5V, [2]: +-2.5V, [3]: +-1V, [4]: +-500mV, [5]: +-100mV, [6]: +-20mV, [7]: +-1mV
	//                                                                              Details: Volrg[0] is the voltage input range for CH1.
	//                                                                                       Volrg[1] is the voltage input range for CH2.
	//                                                                                       Volrg[2] is the voltage input range for CH3.
	//                                                                                       Volrg[3] is the voltage input range for CH4.
	// [return value]: >= 0 : Set successfully 
	//                 -11  : Server not opened
	//                 -12  : DAQ not connected or not present
	//                 -13  : DAQ not connected or not present
	//                 other: Abnormal exit


	// Start continuous sampling
	VK70xnMCDLL_fmt int Def_Function_OUTfmt VK70xNMC_StartSampling(int mci);
	// [prototype]; int VK70xNMC_StartSampling(int mci);
	// [parameter]: int mci: DAQ serial number.                                     Default: [0] (Signal DAQ)
	// [return value]: >= 0 : Operation successful
	//                 -11  : Server not opened
	//                 -12  : No DAQ detected
	//                 -13  : DAQ not connected or not present
	//                 other: Abnormal exit


	// Start N-point sampling
	VK70xnMCDLL_fmt int Def_Function_OUTfmt VK70xNMC_StartSampling_NPoints(int mci, int Npointsnums);
	// [prototype]; int VK70xNMC_StartSampling_NPoints(int mci, int Npointsnums);
	// [parameter]: int mci: DAQ serial number.                                     Default: [0] (Signal DAQ)
	//              int Npointsnums: Number of N-point samples.                     Range: [0]: Continuous sampling mode
	//                                                                                     [1]: Stop sampling
	//                                                                                     >= [2]: Number of sampling points for N points
	// [return value]: >= 0 : Operation successful
	//                 -11  : Server not opened
	//                 -12  : No DAQ detected
	//                 -13  : DAQ not connected or not present
	//                 other: Abnormal exit


	// Stop sampling
	VK70xnMCDLL_fmt int Def_Function_OUTfmt VK70xNMC_StopSampling(int mci);
	// [prototype]; int VK70xNMC_StopSampling(int mci);
	// [parameter]: int mci: DAQ serial number.                                     Default: [0] (Signal DAQ)
	// [return value]: >= 0 : Operation successful
	//                 -11  : Server not opened
	//                 -12  : No DAQ detected
	//                 -13  : DAQ not connected or not present
	//                 other: Abnormal exit


	// Switching System Mode
	VK70xnMCDLL_fmt int Def_Function_OUTfmt VK70xNMC_Set_SystemMode(int mci, int sysmodeval, int  samplemethod, int  sdfilefmt);
	// [prototype]; int VK70xNMC_Set_SystemMode(int mci, int sysmodeval, int samplemethod, int sdfilefmt);
	// [parameter]: int mci: DAQ serial number                                      Default: [0] (Signal DAQ)
	//              int sysmodeval: Select System Mode.                             Range: [0x00]/[0x80]/[0x81]: LAN/WIFI real-time transmission mode
	//                                                                                     [0x01]/[0x8A]: SD file storage mode.
	//                                                                                     [0x02]/[0x8B]: SD file download mode.
	//                                                                                     Others: Reserve
	//              int samplemethod: Select sampling method.                       Range: [0x00]/[0x01]: LAN/WIFI real-time command sampling
	//                                                                                     [0x12]/[0x80]/[12]: IO4 triggers N-sampling
	//                                                                                     [0x13]/[0x77]/[13]: IO4 as ADC clock sampling
	//                                                                                     [0x21]/[0x9A]/[21]: Timed N-sampling mode
	//                                                                                     Others: Reserve
	//              int sdfilefmt: Choose SD storage method for files.              Default: [0]
	// [return value]: >= 0 : Set successfully 
	//                 -11  : Server not opened
	//                 -12  : DAQ not connected or not present
	//                 -13  : DAQ not connected or not present
	//                 other: Abnormal exit


	// Set up PWM/DAC/IO/counter/temperature channels
	VK70xnMCDLL_fmt int Def_Function_OUTfmt VK70xNMC_Set_AdditionalFeature(int mci, int funcNo, int para1, double para2);
	// [prototype]; int VK70xNMC_Set_AdditionalFeature(int mci, int funcNo, int para1, double para2);
	// [parameter]: int mci: DAQ serial number                                      Default: [0] (Signal DAQ)
	//              int funcNo: Function Parameter                                  Range: Name    Function Parameter    Parameter 1                Parameter 2
	//                                                                                     PWM     1                     The frequency of PWM1      The duty cycle of PWM1([0.1]%~[100.0]%)
	//                                                                                             2                     The frequency of PWM2      The duty cycle of PWM2([0.1]%~[100.0]%)
	//                                                                                     DAC     11                    Meaningless                Voltage value([0.0]V~[3.3]V)
	//                                                                                             12                    Meaningless                Voltage value([0.0]V~[3.3]V)
	//                                                                                     IO      21                    IO1,[0]:Low,[1]:High,      Meaningless
	//                                                                                                                   [2]:Input,[0xFF]:Invalid     
	//                                                                                     IO      22                    IO2,[0]:Low,[1]:High,      Meaningless
	//                                                                                                                   [2]:Input,[0xFF]:Invalid     
	//                                                                                     IO      23                    IO3,[0]:Low,[1]:High,      Meaningless
	//                                                                                                                   [2]:Input,[0xFF]:Invalid     
	//                                                                                     IO      24                    IO4,[0]:Low,[1]:High,      Meaningless
	//                                                                                                                       [2]:Input,[0xFF]:Invalid     
	//                                                                                     COUNT   31                    [0]:Reset counter          Meaningless
	//                                                                                     TEMP    41                    [0]~[4], Set temperature   Meaningless
	//                                                                                                                   channel,[0] is the internal channel   
	//                                                                                     RESERVE other                 Meaningless                Meaningless
	//              int para1: Parameter 1
	//              double para2: Parameter 2
	// [return value]: >= 0 : Set successfully 
	//                 -11  : Server not opened
	//                 -12  : DAQ not connected or not present
	//                 -13  : DAQ not connected or not present
	//                 other: Abnormal exit


	// Set network parameters
	VK70xnMCDLL_fmt int Def_Function_OUTfmt VK70xNMC_Set_eNetParameter(int mci, char *para, int len);
	// [prototype]; int VK70xNMC_Set_eNetParameter(int mci, byte[] para, int len);
	// [parameter]: int mci: DAQ serial number                                      Default: [0] (Signal DAQ)
	//              char* para: Set default parameters								Range: para[0]~para[3]: IP address of the server
	//                                                                                     para[4]~para[7]: IP address of DAQ
	//                                                                                     para[8]~para[11]: Gateway address of DAQ
	//                                                                                     para[12]~para[15]: The subnet mask of DAQ
	//                                                                                     para[16]~para[17]: Server port number, high byte first
	//                                                                                     para[18]~para[19]: DAQ port number, high byte first
	//                                                                                     para[20]: network protocol, [0]: UDP, [1]: TCP
	//                                                                                     para[21]: Network disconnection and reconnection request interval, default to 10 seconds
	//                                                                                     para[22]: Reserved, ADC buffer time, default to 10 seconds
	//                                                                                     para[23]~para[28]: MAC address of DAQ
	//                                                                                     para[29]~para[31]: Reserved. VK701N-SD does not have this function.
	//              int len: Set parameter length                                   Range: len < 23 : Exit setting network parameters
	//                                                                                     23 <= len <= 50 : The MAC address of DAQ is automatically ignored and not updated
	//                                                                                     len > 50: DAQ card updates MAC address
	// [return value]: >= 0 : Set successfully 
	//                 -11  : Server not opened
	//                 -12  : DAQ not connected or not present
	//                 -13  : DAQ not connected or not present
	//                 other: Abnormal exit


	// Set default parameters
	VK70xnMCDLL_fmt int Def_Function_OUTfmt VK70xNMC_Set_DefaultParameter(int mci, int *rdpara);
	// [prototype]; int VK70xNMC_Set_DefaultParameter(int mci, int* rdpara);
	// [parameter]: int mci: DAQ serial number                                      Default: [0] (Signal DAQ)
	//              int* rdpara: Set default parameters								Range: rdpara[0]: Voltage input range for CH1 and CH2
	//                                                                                     rdpara[1]: Voltage input range for CH3 and CH4
	//                                                                                     rdpara[2]: Voltage input range for CH5 and CH6
	//                                                                                     rdpara[3]: Voltage input range for CH7 and CH8
	//                                                                                     rdpara[4]: Default sampling rate
	//                                                                                     rdpara[5]: Default number of N samples
	//                                                                                     rdpara[6]: Default scheduled collection time interval
	//                                                                                     rdpara[7]: Default sampling resolution
	//                                                                                     rdpara[8]: Preserve, upgrade and expand
	//                                                                                     rdpara[9]: Default System Mode
	//                                                                                     rdpara[10]: Default sampling mode
	//                                                                                     rdpara[11]: Default System Mode
	//                                                                                     rdpara[12]: Default System Mode
	//                                                                                     rdpara[13]: Default System Mode
	// [return value]: >= 0 : Set successfully 
	//                 -11  : Server not opened
	//                 -12  : DAQ not connected or not present
	//                 -13  : DAQ not connected or not present
	//                 other: Abnormal exit

		
	// Read the current system mode
	VK70xnMCDLL_fmt int Def_Function_OUTfmt VK70xNMC_Get_SystemMode(int mci, int *sysmode, int *samplecmd, int *sdfilefmt, int timeout);
	// [prototype]; int VK70xNMC_Set_SystemMode(int mci, int sysmodeval, int samplemethod, int sdfilefmt);
	// [parameter]: int mci: DAQ serial number                                      Default: [0] (Signal DAQ)
	//              int* sysmode: Select System Mode.								Range: [0x00]: LAN/WIFI real-time transmission mode
	//                                                                                     [0x01]: SD file storage mode.
	//                                                                                     [0x02]: SD file download mode.
	//                                                                                     Others: Reserve
	//              int* samplecmd: Select sampling method.							Range: [0x00]: LAN/WIFI real-time command sampling
	//                                                                                     [0x12]: IO4 triggers N-sampling
	//                                                                                     [0x13]: IO4 as ADC clock sampling
	//                                                                                     [0x21]: Timed N-sampling mode
	//                                                                                     Others: Reserve
	//              int* sdfilefmt: Choose SD storage method for files.				Default: [0]
	//              int timeout: Read timeout                                       Range: [0]: No wait, other: Waiting time (in milliseconds)
	// [return value]: >= 0 : Set successfully 
	//                 -11  : Server not opened
	//                 -12  : DAQ not connected or not present
	//                 -13  : DAQ not connected or not present
	//                 other: Abnormal exit


	// Read default parameters
	VK70xnMCDLL_fmt int Def_Function_OUTfmt VK70xNMC_Get_DeviceDefaultParameter(int mci, char *rdmodol, char *rdswver, char *rdhdver, char *rdsn, int *para, int timeout);
	// [prototype]; int VK70xNMC_Get_DeviceDefaultParameter(int mci, char* rdmodol, char* rdswver, char* rdhdver, char* rdsn, int* rdpara, int timeout);
	// [parameter]: int mci: DAQ serial number                                      Default: [0] (Signal DAQ)
	//              char* rdmodol: Read project name								Range: rdmodol[0]~rdmodol[6]: 7-byte project name
	//              char* rdswver: Read software version							Range: rdswver[0]~rdswver[6]: 7-byte software version
	//              char* rdhdver: Read hardware version							Range: rdhdver[0]~rdhdver[6]: 7-byte hardware version
	//              char* rdsn: Read project serial number							Range: rdsn[0]~rdsn[16]: 17-byte project serial number
	//              int* rdpara: Get default parameters								Range: rdpara[0]: Voltage input range for CH1 and CH2
	//                                                                                     rdpara[1]: Voltage input range for CH3 and CH4
	//                                                                                     rdpara[2]: Voltage input range for CH5 and CH6
	//                                                                                     rdpara[3]: Voltage input range for CH7 and CH8
	//                                                                                     rdpara[4]: Default sampling rate
	//                                                                                     rdpara[5]: Default number of N samples
	//                                                                                     rdpara[6]: Default scheduled collection time interval
	//                                                                                     rdpara[7]: Default sampling resolution
	//                                                                                     rdpara[8]: Preserve, upgrade and expand
	//                                                                                     rdpara[9]: Default System Mode
	//                                                                                     rdpara[10]: Default sampling mode
	//                                                                                     rdpara[11]: Default System Mode
	//                                                                                     rdpara[12]: Default System Mode
	//                                                                                     rdpara[13]: Default System Mode
	//              int timeout: Read timeout                                       Range: [0]: No wait, other: Waiting time (in milliseconds)
	// [return value]: >= 0 : Set successfully 
	//                 -11  : Server not opened
	//                 -12  : DAQ not connected or not present
	//                 -13  : DAQ not connected or not present
	//                 other: Abnormal exit


	// Read network parameters
	VK70xnMCDLL_fmt int Def_Function_OUTfmt VK70xNMC_Get_eNetParameter(int mci, char *tvalue, int timeout);
	// [prototype]; int VK70xNMC_Get_eNetParameter(int mci, byte* para, int timeout);
	// [parameter]: int mci: DAQ serial number                                      Default: [0] (Signal DAQ)
	//              char* tvalue: Get default parameters							Range: para[0]~para[3]: IP address of the server
	//                                                                                     para[4]~para[7]: IP address of DAQ
	//                                                                                     para[8]~para[11]: Gateway address of DAQ
	//                                                                                     para[12]~para[15]: The subnet mask of DAQ
	//                                                                                     para[16]~para[17]: Server port number, high byte first
	//                                                                                     para[18]~para[19]: DAQ port number, high byte first
	//                                                                                     para[20]: network protocol, [0]: UDP, [1]: TCP
	//                                                                                     para[21]: Network disconnection and reconnection request interval, default to 10 seconds
	//                                                                                     para[22]: Reserved, ADC buffer time, default to 10 seconds
	//                                                                                     para[23]~para[28]: MAC address of DAQ
	//                                                                                     para[29]~para[31]: Reserved. VK701N-SD does not have this function.
	//              int timeout: Read timeout                                       Range: [0]: No wait, other: Waiting time (in milliseconds)
	// [return value]: >= 0 : Set successfully 
	//                 -11  : Server not opened
	//                 -12  : DAQ not connected or not present
	//                 -13  : DAQ not connected or not present
	//                 other: Abnormal exit


	// Set data reading method
	VK70xnMCDLL_fmt int Def_Function_OUTfmt VK70xNMC_Set_BlockingMethodtoReadADCResult(int tmode, int timeout);
	// [prototype]; int VK70xNMC_Set_BlockingMethodtoReadADCResult(int tmode, int timeout);
	// [parameter]: int tmode: Reading method										Range: [0]: Non blocking read method
	//																					   [1]: Blocking read method
	//              int timeout: Read timeout                                       Range: [0]: If the blocking read method is set, this value defaults to [0]
	//																					   [1]~[10000]: If non blocking read mode is set, the value range is from [1] to [10000]
	// [return value]: >= 0 : Set successfully 
	//                 other: Abnormal exit

	
	// Read single channel data
	VK70xnMCDLL_fmt int Def_Function_OUTfmt VK70xNMC_GetOneChannel(int mci, int CHNum, double *adcbuffer, int rsamplenum);
	// [prototype]; int VK70xNMC_GetOneChannel(int mci, int CHNum, double[] adcbuffer, int rsamplenum);
	// [parameter]: int mci: DAQ serial number                                      Default: [0] (Signal DAQ)
	//              int CHNum: Channel select                                       Range: [0]~[3]: CH1~CH4
	//              double* adcbuffer: Read the first address of the data          
	//              int rsamplenum: Number of sampling points to be read   
	// [return value]: > 0 : Actual reading of sampling points
	//                 = 0 : No data
	//                 other: Abnormal exit


	// Read 4-channel sampling data
	VK70xnMCDLL_fmt int Def_Function_OUTfmt VK70xNMC_GetFourChannel(int mci, double *adcbuffer, int rsamplenum);
	// [prototype]; int VK70xNMC_GetFourChannel(int mci, double[] adcbuffer, int rsamplenum);
	// [parameter]: int mci: DAQ serial number                                      Default: [0] (Signal DAQ)
	//              double* adcbuffer: Read the first address of the data          
	//              int rsamplenum: Number of sampling points to be read   
	// [return value]: > 0 : Actual reading of sampling points
	//                 = 0 : No data
	//                 other: Abnormal exit


	// Read 8-channel sampling data
	VK70xnMCDLL_fmt int Def_Function_OUTfmt VK70xNMC_GetAllChannel(int mci, double *adcbuffer, int rsamplenum);
	// [prototype]; int VK70xNMC_GetAllChannel(int mci, double* adcbuffer, int rsamplenum);
	// [parameter]: int mci: DAQ serial number                                      Default: [0] (Signal DAQ)
	//              double* adcbuffer: Read the first address of the data          
	//              int rsamplenum: Number of sampling points to be read   
	// [return value]: > 0 : Actual reading of sampling points
	//                 = 0 : No data
	//                 other: Abnormal exit


	// Read single channel data with IO status
	VK70xnMCDLL_fmt int Def_Function_OUTfmt VK70xNMC_GetOneChannel_WithIOStatus(int mci, int CHNum, double *adcbuffer, int rsamplenum, int ioenable);
	// [prototype]; int VK70xNMC_GetOneChannel_WithIOStatus(int mci, int CHNum, double* adcbuffer, int rsamplenum, int ioenable);
	// [parameter]: int mci: DAQ serial number                                      Default: [0] (Signal DAQ)
	//              int CHNum: Channel select                                       Range: [0]~[3]: CH1~CH4
	//              double* adcbuffer: Read the first address of the data          
	//              int rsamplenum: Number of sampling points to be read   
	//              int ioenable: Read IO status                                    Range: [0]: Do not read IO status
	//                                                                                     [1]: Read IO2 status
	//                                                                                     [2]: Read IO3 status
	//                                                                                     [3]: Read IO2 and IO3 status
	//                                                                                     other: Do not read IO status
	// [return value]: > 0 : Actual reading of sampling points
	//                 = 0 : No data
	//                 other: Abnormal exit
	// [note]: VK70xNMC_ Initialize(); It is necessary to ensure that the value of the refmode parameter in the Initialize function is 4.000 (VK701N-SD must be done this way). 
	//         In addition, before reading the status, IO needs to be set to input mode


	// Read 4-channel sampling data with IO status
	VK70xnMCDLL_fmt int Def_Function_OUTfmt VK70xNMC_GetFourChannel_WithIOStatus(int mci, double *adcbuffer, int rsamplenum, int ioenable);
	// [prototype]; int VK70xNMC_GetFourChannel_WithIOStatus(int mci, double* adcbuffer, int rsamplenum, int ioenable);
	// [parameter]: int mci: DAQ serial number                                      Default: [0] (Signal DAQ)
	//              double* adcbuffer: Read the first address of the data          
	//              int rsamplenum: Number of sampling points to be read   
	//              int ioenable: Read IO status                                    Range: [0]: Do not read IO status
	//                                                                                     [1]: Read IO2 status
	//                                                                                     [2]: Read IO3 status
	//                                                                                     [3]: Read IO2 and IO3 status
	//                                                                                     other: Do not read IO status
	// [return value]: > 0 : Actual reading of sampling points
	//                 = 0 : No data
	//                 other: Abnormal exit
	// [note]: VK70xNMC_ Initialize(); It is necessary to ensure that the value of the refmode parameter in the Initialize function is 4.000 (VK701N-SD must be done this way). 
	//         In addition, before reading the status, IO needs to be set to input mode


	// Read 8-channel sampling data with IO status
	VK70xnMCDLL_fmt int Def_Function_OUTfmt VK70xNMC_GetAllChannel_WithIOStatus(int mci, double *adcbuffer, int rsamplenum, int ioenable);
	// [prototype]; int VK70xNMC_GetAllChannel_WithIOStatus(int mci, double* adcbuffer, int rsamplenum, int ioenable);
	// [parameter]: int mci: DAQ serial number                                      Default: [0] (Signal DAQ)
	//              double* adcbuffer: Read the first address of the data          
	//              int rsamplenum: Number of sampling points to be read   
	//              int ioenable: Read IO status                                    Range: [0]: Do not read IO status
	//                                                                                     [1]: Read IO2 status
	//                                                                                     [2]: Read IO3 status
	//                                                                                     [3]: Read IO2 and IO3 status
	//                                                                                     other: Do not read IO status
	// [return value]: > 0 : Actual reading of sampling points
	//                 = 0 : No data
	//                 other: Abnormal exit
	// [note]: VK70xNMC_Initialize(); It is necessary to ensure that the value of the refmode parameter in the Initialize function is 4.000 (VK701N-SD must be done this way). 
	//         In addition, before reading the status, IO needs to be set to input mode


	// Read IO2 and IO3 status
	VK70xnMCDLL_fmt int Def_Function_OUTfmt VK70xNMC_GetIOStatus(int mci, int *iostatus);
	// [prototype]; int VK70xNMC_GetIOStatus(int mci, int* iostatus);
	// [parameter]: int mci: DAQ serial number                                      Default: [0] (Signal DAQ)
	//              int* iostatus: Read the first address of the IO status			Range: iostatus[0]: The status of IO1, [0]: low level, [1]: high level
	//                                                                                     iostatus[1]: The status of IO2, [0]: low level, [1]: high level
	//                                                                                     iostatus[2]: The status of IO3, [0]: low level, [1]: high level
	//                                                                                     iostatus[3]: The status of IO4, [0]: low level, [1]: high level
	// [return value]: = 0 : Read successful
	//                 = -1 : The working mode of the acquisition card does not support IO status return
	//                 = -2 : The acquisition card does not support IO status return
	//                 other: Abnormal exit
	// [note]: VK70xNMC_ Initialize(); It is necessary to ensure that the value of the refmode parameter in the Initialize function is 4.000 (VK701N-SD must be done this way). 
	//         In addition, before reading the status, IO needs to be set to input mode

	
	// Get version information of DLL functions
	VK70xnMCDLL_fmt char* Def_Function_OUTfmt VK70xNMC_GetVersionLot(void);
	// [prototype]; char* VK70xNMC_GetVersionLot();
	// [return value]: Get DLL version number (string)

	
	// Read all IO state functions
	VK70xnMCDLL_fmt int Def_Function_OUTfmt VK70xNMC_Get_AllIOS_Blocking(int mci, int *iobuffer, int timeout);
	// [prototype]; int VK70xNMC_Get_AllIOS_Blocking(int mci, int* iobuffer, int timeout);
	// [parameter]: int mci: DAQ serial number                                      Default: [0] (Signal DAQ)
	//              int* iobuffer: Read the first address of the IO status			Range: iobuffer[0]: The status of IO1, [0]: low level, [1]: high level
	//                                                                                     iobuffer[1]: The status of IO2, [0]: low level, [1]: high level
	//                                                                                     iobuffer[2]: The status of IO3, [0]: low level, [1]: high level
	//                                                                                     iobuffer[3]: The status of IO4, [0]: low level, [1]: high level
	//              int timeout: Read wait time (ms)
	// [return value]: >= 0 : Successfully read IO status
	//                 -1   : Read failed, IO status still not updated, please delay 100ms before attempting again.
	//                 -11  : Server not opened
	//                 -12  : DAQ not connected or not present
	//                 -13  : DAQ not connected or not present
	//                 other: Abnormal exit


	// Read IO1 status
	VK70xnMCDLL_fmt int Def_Function_OUTfmt VK70xNMC_Get_IO1_Blocking(int mci, int *iovalue, int timeout);
	// [prototype]; int VK70xNMC_Get_IO1_Blocking(int mci, int* iovalue, int timeout);
	// [parameter]: int mci: DAQ serial number                                      Default: [0] (Signal DAQ)
	//              int* iovalue: Read IO status									Range: [0]: low level, [1]: high level
	//              int timeout: Read wait time (ms)
	// [return value]: >= 0 : Successfully read IO status
	//                 -1   : Read failed, IO status still not updated, please delay 100ms before attempting again.
	//                 -11  : Server not opened
	//                 -12  : DAQ not connected or not present
	//                 -13  : DAQ not connected or not present
	//                 other: Abnormal exit


	// Read IO2 status
	VK70xnMCDLL_fmt int Def_Function_OUTfmt VK70xNMC_Get_IO2_Blocking(int mci, int *iovalue, int timeout);
	// [prototype]; int VK70xNMC_Get_IO2_Blocking(int mci, int* iovalue, int timeout);
	// [parameter]: int mci: DAQ serial number                                      Default: [0] (Signal DAQ)
	//              int* iovalue: Read IO status									Range: [0]: low level, [1]: high level
	//              int timeout: Read wait time (ms)
	// [return value]: >= 0 : Successfully read IO status
	//                 -1   : Read failed, IO status still not updated, please delay 100ms before attempting again.
	//                 -11  : Server not opened
	//                 -12  : DAQ not connected or not present
	//                 -13  : DAQ not connected or not present
	//                 other: Abnormal exit


	// Read IO3 status
	VK70xnMCDLL_fmt int Def_Function_OUTfmt VK70xNMC_Get_IO3_Blocking(int mci, int *iovalue, int timeout);
	// [prototype]; int VK70xNMC_Get_IO3_Blocking(int mci, int* iovalue, int timeout);
	// [parameter]: int mci: DAQ serial number                                      Default: [0] (Signal DAQ)
	//              int* iovalue: Read IO status									Range: [0]: low level, [1]: high level
	//              int timeout: Read wait time (ms)
	// [return value]: >= 0 : Successfully read IO status
	//                 -1   : Read failed, IO status still not updated, please delay 100ms before attempting again.
	//                 -11  : Server not opened
	//                 -12  : DAQ not connected or not present
	//                 -13  : DAQ not connected or not present
	//                 other: Abnormal exit.


	// Read IO4 status
	VK70xnMCDLL_fmt int Def_Function_OUTfmt VK70xNMC_Get_IO4_Blocking(int mci, int *iovalue, int timeout);
	// [prototype]; int VK70xNMC_Get_IO4_Blocking(int mci, int* iovalue, int timeout);
	// [parameter]: int mci: DAQ serial number                                      Default: [0] (Signal DAQ)
	//              int* iovalue: Read IO status									Range: [0]: low level, [1]: high level
	//              int timeout: Read wait time (ms)
	// [return value]: >= 0 : Successfully read IO status
	//                 -1   : Read failed, IO status still not updated, please delay 100ms before attempting again.
	//                 -11  : Server not opened
	//                 -12  : DAQ not connected or not present
	//                 -13  : DAQ not connected or not present
	//                 other: Abnormal exit


	// Read PWM parameters
	VK70xnMCDLL_fmt int Def_Function_OUTfmt VK70xNMC_Get_PWM_Blocking(int mci, double *dutyval, int *freqval, int timeout);
	// [prototype]; int VK70xNMC_Get_PWM_Blocking(int mci, double[] dutyval, int[] freqval, int timeout);
	// [parameter]: int mci: DAQ serial number                                      Default: [0] (Signal DAQ)
	//              double[] dutyval: Read PWM duty cycle                           Range: dutyval[0] is PWM1, dutyval[1] is PWM2
	//              int[] freqval: Read PWM frequency                               Range: freqval[0] is PWM1, freqval[1] is PWM2
	//              int timeout: Read wait time (ms)
	// [return value]: >= 0 : Successfully read IO status
	//                 -1   : Read failed, PWM parameter still not updated, please delay 100ms before attempting again.
	//                 -11  : Server not opened
	//                 -12  : DAQ not connected or not present
	//                 -13  : DAQ not connected or not present
	//                 other: Abnormal exit


	// Read DAC parameters
	VK70xnMCDLL_fmt int Def_Function_OUTfmt VK70xNMC_Get_DAC_Blocking(int mci, double *dacvalue, int timeout);
	// [prototype]; int VK70xNMC_Get_DAC_Blocking(int mci, double* dacvalue, int timeout);
	// [parameter]: int mci: DAQ serial number                                      Default: [0] (Signal DAQ)
	//              double* dacvalue: Read DAC voltage value						Range: [0]~[3.3]V
	//              int timeout: Read wait time (ms)
	// [return value]: >= 0 : Successfully read IO status
	//                 -1   : Read failed, DAC parameter still not updated, please delay 100ms before attempting again.
	//                 -11  : Server not opened
	//                 -12  : DAQ not connected or not present
	//                 -13  : DAQ not connected or not present
	//                 other: Abnormal exit


	// Read Counter parameters
	VK70xnMCDLL_fmt int Def_Function_OUTfmt VK70xNMC_Get_Counter_Blocking(int mci, int *countervalue, int timeout);
	// [prototype]; int VK70xNMC_Get_Counter_Blocking(int mci, int* countervalue, int timeout);
	// [parameter]: int mci: DAQ serial number                                      Default: [0] (Signal DAQ)
	//              int* countervalue: Read Counter value
	//              int timeout: Read wait time (ms)
	// [return value]: >= 0 : Successfully read IO status
	//                 -1   : Read failed, Counter parameter still not updated, please delay 100ms before attempting again.
	//                 -11  : Server not opened
	//                 -12  : DAQ not connected or not present
	//                 -13  : DAQ not connected or not present
	//                 other: Abnormal exit
	// [note]: Before using the current function, you need to first use the VK70xNMC_Set_AdditionalFeature() function to set IO4 to external interrupt mode.
	//         eg: VK70xNMC_Set_AdditionalFeature(0, 31, 0, 0);


	// Read Temperature parameters
	VK70xnMCDLL_fmt int Def_Function_OUTfmt VK70xNMC_Get_Temperature_Blocking(int mci, double *tempvalue, int timeout);
	// [prototype]; int VK70xNMC_Get_Temperature_Blocking(int mci, double* tempvalue, int timeout);
	// [parameter]: int mci: DAQ serial number                                      Default: [0] (Signal DAQ)
	//              double* tempvalue: Read temperature value
	//              int timeout: Read wait time (ms)
	// [return value]: >= 0 : Successfully read IO status
	//                 -1   : Read failed, temperature value still not updated, please delay 100ms before attempting again.
	//                 -11  : Server not opened
	//                 -12  : DAQ not connected or not present
	//                 -13  : DAQ not connected or not present
	//                 other: Abnormal exit
	// [note]: Before using the current function, you need to first use the VK70xNMC_Set_AdditionalFeature() function to set parameter.
	//         eg: VK70xNMC_Set_AdditionalFeature(0, 4, 0, 0); // Select the internal channel temperature sensor of the acquisition card
	//         eg: VK70xNMC_Set_AdditionalFeature(0, 4, 1, 0); // Select IO1 as the temperature sensor channel
	//         eg: VK70xNMC_Set_AdditionalFeature(0, 4, 2, 0); // Select IO2 as the temperature sensor channel
	//         eg: VK70xNMC_Set_AdditionalFeature(0, 4, 3, 0); // Select IO3 as the temperature sensor channel
	//         eg: VK70xNMC_Set_AdditionalFeature(0, 4, 4, 0); // Select IO4 as the temperature sensor channel


	// Open server
	VK70xnMCDLL_fmt int Def_Function_OUTfmt Server_TCPOpen(int portnumber);
	// [prototype]; int Server_TCPOpen(int portnumber);
	// [parameter]: int portnumber: TCP server port									Range: [0]~[65535], Default: [8234]
	// [return value]: >= 0 : Server successfully opened
	//                 1    : The server is already open and not connected to the client.
	//                 2    : The server already has connected clients.
	//                 -13  : The server port is already occupied!
	//                 other: Abnormal exit


	// Close server
	VK70xnMCDLL_fmt int Def_Function_OUTfmt Server_TCPClose(int portnumber);
	// [prototype]; int Server_TCPClose(int portnumber);
	// [parameter]: int portnumber: Opened TCP server ports.						Range: [0]~[65535], [0] automatically close opened server ports
	// [return value]: >= 0 : Server shutdown successful
	//                 -11  : Server not opened
	//                 -12  : DAQ not connected or not present
	//                 other: Abnormal exit


	// Read the port number of the opened server
	VK70xnMCDLL_fmt int Def_Function_OUTfmt Server_Get_ServerPort(int *iport);
	// [prototype]; int Server_Get_ServerPort(int* ipor);
	// [parameter]: int* ipor: Used to store the port number of the currently opened server
	// [return value]: >= 0 : Read successful
	//                 -11  : Server not opened
	//                 other: Abnormal exit


	// Read the number of collection cards on the connected server
	VK70xnMCDLL_fmt int Def_Function_OUTfmt Server_Get_ConnectedClientNumbers(int *cnum);
	// [prototype]; int Server_Get_ConnectedClientNumbers(int* cnum);
	// [parameter]: int* cnum: Used to store and read the number of DAQs on connected servers
	// [return value]: >= 0 : Read successful
	//                 -11  : Server not opened
	//                 -12  : No DAQ connection to server
	//                 other: Abnormal exit


	// Read the handle and IP address of the current collection card
	VK70xnMCDLL_fmt int Def_Function_OUTfmt Server_Get_ConnectedClientHandle(int mci, int *ihadble, char *ipadr);
	// [prototype]; int Server_Get_ConnectedClientHandle(int mci, int* ihadble, Byte[] ipAdr);
	// [parameter]: int mci: DAQ serial number                                      Default: [0] (Signal DAQ)
	//              int* ihadble: Connection handle pointing to the current DAQ used for storing reads.
	//              char* ipAdr: The IP address used to store the currently active collection card for reading.
	//                            Require at least 128 bytes of space to be guaranteed.
	// [return value]: >= 0 : Read successful
	//                 -11  : Server not opened
	//                 -12  : The requested collection card index number is incorrect
	//                 -13  : The requested collection card is not connected or does not exist
	//                 other: Abnormal exit


	// Read the total number of bytes received by the current server-side
	VK70xnMCDLL_fmt int Def_Function_OUTfmt Server_Get_RxTotoalBytes(int *totalbytesnum, int clrflag);
	// [prototype]; int Server_Get_RxTotoalBytes(int* totalbytesnum, int clrflag);
	// [parameter]: int* totalbytesnum: Used to store the total number of bytes received by the current server for reading.
	//              int clrflag: Clear the receive byte count flag after reading is completed.          Range: [0]: accumulate, [1]: Zero after reading
	// [return value]: >= 0 : Read successful
	//                 other: Abnormal exit

	
#ifdef __cplusplus
}
#endif

#endif