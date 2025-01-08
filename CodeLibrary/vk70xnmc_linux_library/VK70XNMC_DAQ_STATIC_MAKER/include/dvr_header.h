#ifndef _MAINDLL_VK_HEADER_H
#define _MAINDLL_VK_HEADER_H

#include <WinSock2.h>  
//#pragma comment(lib, "WS2_32.lib")

#define vCOM_SYSNC_HEADER1   0x55
#define vCOM_SYSNC_HEADER2   0xEE
#define vCOM_SYSNC_SN1       0x10
#define vCOM_SYSNC_SN2       0x01
//----------------------
#define vCOM_CMD_8BIT_CH1    0x11
#define vCOM_CMD_8BIT_CH2    0x12
#define vCOM_CMD_8BIT_CH3    0x13
#define vCOM_CMD_8BIT_CH4    0x14
#define vCOM_CMD_16BIT_CH1     0x21
#define vCOM_CMD_16BIT_CH2     0x22
#define vCOM_CMD_16BIT_CH3     0x23
#define vCOM_CMD_16BIT_CH4     0x24

#define vCOM_CMD_24BIT_CH1     0x31
#define vCOM_CMD_24BIT_CH2     0x32
#define vCOM_CMD_24BIT_CH3     0x33
#define vCOM_CMD_24BIT_CH4     0x34

#define vCOM_CMD_32BIT_CH1     0x41
#define vCOM_CMD_32BIT_CH2     0x42
#define vCOM_CMD_32BIT_CH3     0x43
#define vCOM_CMD_32BIT_CH4     0x44

#define vCOM_CMD_RW_ADC        0x81  //
#define vCOM_CMD_RW_IO         0x90  // write and read the IO,pWM, DAC, counter, temperature   
#define vCOM_CMD_RW_MODE       0x91  // write and read mode  

#define  vCOM_CMD_RW_SYSTEM           0xA0  //
#define  vCOM_CMD_RW_WIFIPARA         0xA1  // write and read the wifi parameter //网络信息              
#define  vCOM_CMD_RW_ONLINE           0xAA  // check whether the deivce is online?
#define  vCOM_CMD_RW_UDI              0xAB

#define  vCOM_CMD_RW_SDCARD_INFOR     0xB0  // 读取SD card 文件信息，目录信息
#define  vCOM_CMD_RW_SDCARD_FILES     0xB1  //  读取 SD card 文件
#define  vCOM_CMD_RW_UPGRADEMODE      0xBB

#define vCOM_STATUS_REPONSE_START    0x10 //  start with reset
#define vCOM_STATUS_REPONSE_NEXT     0x11 //  start, next with confirm
#define vCOM_STATUS_REPONSE_OK       0x22  // ok, pending
#define vCOM_STATUS_REPONSE_FAIL     0x44  // failed

#define vCOM_STATUS_CHECKSUM_YES     0x01
#define vCOM_STATUS_CHECKSUM_NO      0x00


#define    DS_DLL_INTIALIZEOK        0x748167 // 初始化了OK
//------------------------------------
//int  SampleRate;           // 采样率
//int  SampleRateResolution; // 采样分辨率
//int  Sampling_Channel;     // 采样通道
//==============================================================================
#define  MAX_PATHNAME_LEN         260    /* includes nul byte */  

#define  _DISP_MAX_LEN           1200000    //2000000
#define  MAX_READ_TCP_UNIT       103200      //206400   1032
#define  MAX_RXLAN_LEN           (MAX_READ_TCP_UNIT*10)    //103200*10    
//----------------------------------
//#define  MAX_RX_CARD_NUM         3        // 最大连接采集卡数量
#define  MAX_TCP_CILENT_NUM      8    // 最大连接采集卡数量  
//==============================================================================

enum _VK_DAQ_DEFINE_PARA  //typedef 
{
	//---------------------
	VKxxx_DATAFORMAT_8BIT = 0,
	VKxxx_DATAFORMAT_16BIT = 1,
	VKxxx_DATAFORMAT_24BIT,
	VKxxx_DATAFORMAT_32BIT,
	//-----------------------
	VKxxx_DQA_NO1 = 0,
	VKxxx_DQA_NO2,
	VKxxx_DQA_NO3,
	VKxxx_DQA_NO4,
	VKxxx_DQA_NO5,
	VKxxx_DQA_NO6,
	VKxxx_DQA_NO7,
	VKxxx_DQA_NO8,
	//------------------------
	VKxxx_IOFUNCTION_PWM1 = 0x1,//功能1-PWM1
	VKxxx_IOFUNCTION_PWM2 = 0x2,//功能2-PWM2
	VKxxx_IOFUNCTION_DAC1 = 0x11,//功能11-DAC1
	VKxxx_IOFUNCTION_DAC2 = 0x12,//功能12-DAC2
	VKxxx_IOFUNCTION_IO = 0x20,//
	VKxxx_IOFUNCTION_IO1 = 0x21,//功能21~24-IO1-IO4
	VKxxx_IOFUNCTION_IO2 = 0x22,
	VKxxx_IOFUNCTION_IO3 = 0x23,
	VKxxx_IOFUNCTION_IO4 = 0x24,
	VKxxx_IOFUNCTION_COUNTER = 0x31,//功能31 - Counter+Freq
	VKxxx_IOFUNCTION_FREQ = 0x32,//功能31 - Counter+Freq
	VKxxx_IOFUNCTION_INTMEP = 0x41,//功能41 - temp+humiduty
	VKxxx_IOFUNCTION_EXTEMP = 0x42,//功能41 - temp+humiduty
	//-----------------------
	VKxxx_FUNCTION_SAMPLINGMODE = 0x80, //#define vCOM_CMD_RW_SAMPLING   0x80  //  开始连续采样和N点采样， 停止采样
	VKxxx_FUNCTION_ADCCONFIG,//#define vCOM_CMD_RW_ADC        0x81  //
	VKxxx_FUNCTION_IO,//#define vCOM_CMD_RW_IO         0x90  // write and read the IO,pWM, DAC, counter, temperature   
	VKxxx_FUNCTION_SYSTEMMODE,//#define vCOM_CMD_RW_MODE       0x91  // write and read mode  
	VKxxx_FUNCTION_SG,//#define vCOM_CMD_RW_SG         0x9A  // 控制信号发生器     
	VKxxx_FUNCTION_SYSTEMCONFIG,//#define vCOM_CMD_RW_SYSTEM     0xA0  //
	//------------------------
	VKxxx_MODE_RTTX_SAMPLING = 0x00,    //   real time 实时传输模式    直接命令、IO4中断触发以及IO4时钟同步触发采集数据或切换模式，开始连续采集、N点采集，停止采集等,
	VKxxx_MODE_RTSAVE_SAMPLING,      //   real time 保存到SD卡模式  直接命令、IO4中断触发以及IO4时钟同步触发采集数据或切换模式，开始连续采集、N点采集，停止采集等,
	VKxxx_MODE_DOWNLOADFILE,         //   离线文件下载模式                 ：下载文件或切换模式，需要命令下载存储的文件
	VKxxx_MODE_UDISK,                //    USB U盘文件模式                  :  下载文件或切换模式，所有总线交由USB文件系统
	VKxxx_MODE_FACOTRY,              //   工厂测试模式                     : 用于烧录工厂设置信息，工厂测试等等
	//------------------------------
	VKxxx_SAMLEMETHOD_IDLE = 0x00,    //  
	VKxxx_SAMLEMETHOD_CONTIMUE = 0x01,
	VKxxx_SAMLEMETHOD_NPOINTS = 0x02,
	VKxxx_SAMLEMETHOD_IO4_CONTIMUE = 0x11,
	VKxxx_SAMLEMETHOD_IO4_NPOINTS = 0x12,
	VKxxx_SAMLEMETHOD_IO4_ASADCCLOCK = 0x13,
	VKxxx_SAMLEMETHOD_TIMER_NPOINTS = 0x21,
	//-----------------------------
	VKxxx_SDFILEFMT_BIN  = 0,
	VKxxx_SDFILEFMT_TEXT = 0x11,
};


typedef struct TCPServerPara
{
	int  PortNumber;   // =8234  VKTCPServer.Portnumber
	//------------------------------
	SOCKET SockServer;//VKTCPServer.
	SOCKADDR_IN LocalAddr;
	//---------------------------
	int  Client_Num;  //  连接的客户机数量 
	SOCKET SockClient[MAX_TCP_CILENT_NUM + 1];
	SOCKADDR_IN ClientAddr[MAX_TCP_CILENT_NUM + 1];
	int  ClientStatus[MAX_TCP_CILENT_NUM + 1];// 1: connected; 0 and other is disconnnected  
	//----------------------------	
	int  RecievedBytes_Count;
	// Static global variables
	//-------------------
	//int  ClientHandle[MAX_TCP_CILENT_NUM + 1];  // 最大可以连接128个客户机
	//char ClientIP[MAX_TCP_CILENT_NUM + 1][128]; // connected IP
}TypeDefTCPServerPara;
//---------------------------------- 
typedef struct VK70xNMCPara
{
	unsigned char PacketState;
	unsigned char PacketCheckSum;
	unsigned int  PacketLen;
	unsigned int  PacketCount;
	unsigned char PacketDatum[2048]; // 解析数据包
	///////////////////////////////////////////////////////////////
	int           IOUpdateFlag;// result
	double        CHShowBuffer[10][_DISP_MAX_LEN + 2];// 防止溢出
	int           CHSrcHexBuffer[10][_DISP_MAX_LEN + 2];// 防止溢出;
	int           SaveShowPI, ReadShowPI, Read4CHPI, ReadCHPI[8];
	//----------------- // buffer
	unsigned char RXLANDatum[MAX_RXLAN_LEN + MAX_READ_TCP_UNIT];//
	int           RXLANSavePI, RXLANReadPI;
	int           MaxBuffer_SaveedLen;
	unsigned char MaxBuffer_OverFlag;
	//-----------------------------------------------------------
	//TypeDefVK70xNMCAdddtionalFeature;//TypeDefVK70xNMCAdddtionalFeature     VKFuntionPara[MAX_RX_CARD_NUM];
	//mbytes(6) = vCOM_CMD_RW_IO
	//len = mbytes(2) * 256 + mbytes(3) + 4
	//If (ReadTaskIndex = NEXTTASK_TEMP) And (len > 24) Then
	//mbytes(7) = &H22 设置成功
	//-----------------------------------------------------------
	int UpdateFlag;  //IO
	int IO[4];//bytes(21-24)
	double DAC[2];
	int PWMFreq[2];
	double PWMDuty[2];
	int Excounter; //i = mbytes(25) * &H1000000 + mbytes(26) * &H10000 + mbytes(27) * &H100 + mbytes(28)	"计数器
	double Temp; //i = mbytes(29) * &H100 + mbytes(30)摄氏度 ; i = i / 100
	int           ExFreq;
	double        ExTemp;
	double        ExHumidity;
	//--------------------------------------------
	//TypeDefVK70xNMCAdddtionalFeature     VKFuntionPara[MAX_RX_CARD_NUM];
	//--------------------------------
	///////////////////////////////////////////////////////////////
	int SampleComand;//用于发送命令，切换采集卡模式， 如连续采样， 停止，N点采样，IO、
	// 采样模式; 0x00: 停止/待采样模式 
	//           0x01： 连续采样模式；0x02：单次N点采样模式  
	//           0x11： IO4触发连续采样模式；0x12：IO4触发单次N点采样模式  0x13： IO4作为采样时钟采样模式; 
	//           0x21： 定时进行一次N点采样
	int WorkMode; // 0: 正常采集模式。 1：SD模式	
	int LastWorkMode;//  下载模式退出返回的模式

	double  PGAGainRange[8];        // 通道1-8 放大倍数
	double  ReferenceVoltage;      // 参考电压
	int     VolRange[8]; // 
	//int     IEPEflag[8];

	int     CommucanitionProtocol;// 缺省通讯协议， 0： USB， 1： LANWIFI,  
	int     SampleRate;      // 采样率   ;  1-100000Hz
	int     SampleDataFormat;// 采样精度;  0=8bit; 1-16bit; 2-24bit; 3-32bit
	int     Npoints;  // 设置N 点采样 ;  1-100000000
	int     Tintervals;
	int     Channel;// 传输通道， 1，2，4，8
	int     SDFileFormat; //
	int     SDFileIndex; //
	int     CVMode[8];
	//int     IO4TrigeEdage;
	//============================================
	// wifi/LAN/eNet infromation
	//============================================
	short int     VKPort;
	unsigned char VKIP[4];
	unsigned char VKNetMask[4];
	unsigned char VKGateWay[4];
	unsigned char VKMac[6];

	short int     ServerPort;
	unsigned char ServerIP[4];

	unsigned char enetProtocol;
	unsigned char enetdisconectTime;  // 断网重连时间
	unsigned char maxecacheTime;  // 最大缓存时间
	//============================================
	// device infromation
	//============================================
	char           ModelName[7]; // 采集卡的项目名称，保留 
	char           SWVer[7];     // 采集卡的软件版本，保留 
	char           HWVer[7];     // 采集卡的硬件版本，保留  
	char           SN[17];       // 采集卡的序列号， 用于绑定采集卡
	double         OffsetRatio[8];        // 调整偏置系数 ，+- 0~10mV， 默认0mV coefficient
	double         CalibrationRatio[8];   // 调整系数   0.98~1.05
	char           Cal_RTC_Direction;
	int            Cal_RTC_Value;
	char           UDI[32];
	//-------------------------------------------------------------
	//客户定制负误差模式
	//客户定制负误差模式
	//	Customized negative error mode
	int           CNP_Trig_Status;   //  0: 空闲， 不触发；  1-准备触发， 2-正在触发数据
	int           CNP_Trig_Channel;  //  0: 无效通道，  1-8：对应电压值触发通道；  12/0x12：IO2，13/0x13：IO3 IO电平触发
	int           CNP_Trig_Edge;    //   0: 上升沿触发/高于电压值触发；  1： 下降沿触发/低于电压值触发； 2： 高电平触发/高于电压值触发；3： 低电平触发/低于电压值触发
	double        CNP_Trig_Value;   //   触发的电压值
	//-------------------------
	int           CNP_Target_Len;    // 触发N点长度
	int           CNP_Target_Neg_Len;// 触发N点时前M点负采样
	//---------------
	int           CNP_Counter;	     // 触发N点计数器
	int           CNP_Read_PI;       // 读取数据指针，主要用于负采样点数
	///////////////////////////////////////////////////////////////
}TypeDefVK70xNMCPara;
//--------------------------------
extern TypeDefVK70xNMCPara                  VK[MAX_TCP_CILENT_NUM];
extern TypeDefTCPServerPara                 VKTCPServer;

extern char                                 SD_DefaultFilePath[MAX_PATHNAME_LEN];
extern HANDLE                               RXLANMonitor_Handle, TCPMonitor_Handle;//线程
extern unsigned char                        TCPMonitor_ThreadRunningState, RXLANMonitor_ThreadRunningState;
extern int                                  ReadADCResultTimeout;
extern int                                  error_count;
//==============================================================================
DWORD WINAPI MonitorRXLANEvent(PVOID pvParam);
//void  DisposalDownloadRXTask_LEN(TypeDefVK70xNMCPara *vkmc, int len);
void  DisposalDownloadRXTask_LEN(int mci, TypeDefVK70xNMCPara *vkmc, int len);
//-------------------------------- sockserver.c
int   DisposalTXDatum(SOCKET connectHandle, unsigned char cmd, unsigned char *txbuff, unsigned int txlen, unsigned char wrflag);
//-------------------------------- core.c
void    InitDLL(void);
void    IntializeVKinging_RXTaskBuffer(void);
double  GetGainValue_NOPGA(int volrange);
double  GetGainValue_PGA(int volrange);
//-------------------------------- lowlayerinterface.c
void   seNet_Load_DefaultTCPIPConfigurationFile(void);
int    seNet_DefaultAfterChangeModelType(int mci);
//int    seNet_Send_WriteSystemParameterToDevice(int mci, unsigned char flagswitchsetpara);
int seNet_Send_WriteSystemParameterToDevice(int mci, unsigned char flagswitchsetpara, unsigned char wrsnflag);
int    seNet_Send_ReadCommand(int mci, unsigned char cmd);
//-------------------------------- common str
//int  CommStr_GetNewStringsFromCongfigfile(const char tkeychar, const char *tsrcstring, char *deststr);
int  CommStr_GetNewStringsWithBlankFromCongfigfile_RemoveSpecialCharacters(const char tkeychar, const char *tsrcstring, char *deststr);
int  CommStr_GetNewStringsFromCongfigfile_RemoveSpecialCharacters(const char tkeychar, const char *tsrcstring, char *deststr);
int  CommStr_RemoveInvaildCharForHex(char *tsrcstring, char *tresstr);
int  CommStr_RemoveInvaildCharForInteger(char *tsrcstring, char *tresstr);
int  CommStr_RemoveInvaildCharForDouble(char *tsrcstring, char *tresstr);
int  CommStr_GetParameterDoubleValueFromCongfigfile(char tkeychar, char *tsrcstring, double *value);
int  CommStr_GetParameterUnintegerValueFromCongfigfile(char tkeychar, char *tsrcstring, int *value);
int  CommStr_GetNewStringsFromCongfigfile(const char tkeychar, const char *tsrcstring, char *deststr);
//==============================================================================
// sd file
void sDFile_Intializetempsdcardfile(int mci);
int  sDFile_CheckSDCardDownloadCondition(int mci);
int  sDFile_WriteReadSDCardTask(int mci, const char *rxdat, int len);
int  sDFile_SendtheNextFileComamnd(int mci);
void sDFile_CheckSdTempFileWhetherisClosed(void);
void sDFile_IntializeVKinging_SdFileRxBuffer(void);
void sDFile_LoadDefaultSDConfigurationFile(void);


#endif
