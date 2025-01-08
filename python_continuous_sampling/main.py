#----------------------------------------------------------------------------------------------------
# 版权所有 深圳维京电子有限公司 2013-2024。保留所有权利。
# 文件名：1. Coutinuous Sampling.py
# Python 解释器：Virtualenv
# 作者：Andy Jiang / Mr. Jin	版本：1.0	日期：2024-01-03
# 描述：调用 DLL 进行连续采样的 Python 示例程序（适用于 VK701N-SD/VK701W-SD）
# 其他：Python 版本 3.10。DLL 使用 64 位版本。
# 历史记录：v2: 增加了 VK70xNMC_InitializeAll 函数
#----------------------------------------------------------------------------------------------------

import queue            # 导入队列模块，用于线程间通信
import ctypes           # 导入 ctypes 模块，用于调用 DLL 函数
import wave             # 导入 wave 模块，用于处理 WAV 文件
import os               # 导入 os 模块，用于操作文件路径
import time             # 导入 time 模块，用于时间相关操作

from ctypes import *    # 从 ctypes 模块导入所有内容
from GetSampleDataAndSave import GetSampleDataAndSave  # 导入自定义模块，用于获取采样数据并保存
from inference import * # 导入推理模块，用于数据推理
from in_iotdb import in_iotdb  # 导入 IoT 数据库模块，用于将数据存入数据库

# 加载 64 位 DLL 库
vk701n = cdll.LoadLibrary('./VK70xNMC_DAQ2.dll')

# 打开 TCP 服务器
TCPOpen = vk701n.Server_TCPOpen
TCPOpen.argtypes = [c_int]      # 定义函数参数类型为整数
TCPOpen.restypes = c_int        # 定义返回类型为整数
# [原型]；int Server_TCPOpen(int portnumber);
# [参数]：int portnumber: TCP 服务器端口号 范围：[0] ~ [65535]，默认值：[8234]
# [返回值]：>= 0 : 服务器成功打开
#            1   : 服务器已打开且未连接到客户端
#            2   : 服务器已有连接的客户端
#           -13  : 服务器端口已被占用！
#            其他：异常退出

# 关闭 TCP 服务器
TCPClose = vk701n.Server_TCPClose
TCPClose.argtypes = [c_int]     # 定义函数参数类型为整数
TCPClose.restypes = c_int        # 定义返回类型为整数
# [原型]；int Server_TCPClose(int portnumber);
# [参数]：int portnumber: 已打开的 TCP 服务器端口号。范围：[0]~[65535]，[0] 自动关闭所有打开的服务器端口
# [返回值]：>= 0 : 服务器关闭成功
#           -11  : 服务器未打开
#           -12  : DAQ 未连接或不存在
#           其他：异常退出

# 读取已连接服务器上的采集卡数量
GetConnectedClientNumbers = vk701n.Server_Get_ConnectedClientNumbers
GetConnectedClientNumbers.argtypes = [POINTER(c_int)]  # 参数为指向整数的指针
GetConnectedClientNumbers.restypes = c_int             # 返回类型为整数
# [原型]；int Server_Get_ConnectedClientNumbers(int* cnum);
# [参数]：int* cnum: 用于存储和读取已连接服务器上的 DAQ 数量
# [返回值]：>= 0 : 读取成功
#           -11  : 服务器未打开
#           -12  : 服务器没有 DAQ 连接
#           其他：异常退出

# 读取当前采集卡的句柄和 IP 地址
GetConnectedClientHandle = vk701n.Server_Get_ConnectedClientHandle
GetConnectedClientHandle.argtypes = [c_int, POINTER(c_int), POINTER(c_char)]  # 参数类型
GetConnectedClientHandle.restypes = c_int                                  # 返回类型
# [原型]；int Server_Get_ConnectedClientHandle(int mci, int* ihandle, char* ipAdr);
# [参数]：int mci: DAQ 序列号 默认：[0]（信号 DAQ）
#          int* ihandle: 指向当前 DAQ 连接句柄的指针，用于存储读取句柄
#          char* ipAdr: 用于存储当前活动采集卡的 IP 地址，至少需要 128 字节空间
# [返回值]：>= 0 : 读取成功
#           -11  : 服务器未打开
#           -12  : 服务器没有 DAQ 连接
#           -13  : 请求的采集卡未连接或不存在
#           其他：异常退出

# 开始连续采样
StartSampling = vk701n.VK70xNMC_StartSampling
StartSampling.argtypes = [c_int]      # 参数类型为整数
StartSampling.restypes = c_int         # 返回类型为整数
# [原型]；int VK70xNMC_StartSampling(int mci);
# [参数]：int mci: DAQ 序列号。默认值：[0]（信号 DAQ）
# [返回值]：>= 0 : 设置成功
#           -11  : USB 未打开
#           -12  : USB 未连接 DAQ
#           -13  : DAQ 未连接或不存在
#           其他：异常退出

# 开始 N 点采样
StartSamplingNPoints = vk701n.VK70xNMC_StartSampling_NPoints
StartSamplingNPoints.argtypes = [c_int, c_int]  # 参数类型为两个整数
StartSamplingNPoints.restypes = c_int           # 返回类型为整数
# [原型]；int VK70xNMC_StartSampling_NPoints(int mci, int Npointsnums);
# [参数]：int mci: DAQ 序列号。默认值：[0]（信号 DAQ）
#          int Npointsnums: N 点采样的数量。范围：[0] 无效，>= [1] N 点采样
# [返回值]：>= 0 : 操作成功，开始第一次采样
#           -11  : USB 未打开
#           -12  : USB 未连接 DAQ
#           -13  : DAQ 未连接或不存在
#           其他：异常退出

# 停止采样
StopSampling = vk701n.VK70xNMC_StopSampling
StopSampling.argtypes = [c_int]       # 参数类型为整数
StopSampling.restypes = c_int          # 返回类型为整数
# [原型]；int VK70xNMC_StopSampling(int mci);
# [参数]：int mci: DAQ 序列号。默认值：[0]（信号 DAQ）
# [返回值]：>= 0 : 操作成功
#           -11  : USB 未打开
#           -12  : USB 未连接 DAQ
#           -13  : DAQ 未连接或不存在
#           其他：异常退出

# 设置 PWM/DAC/IO/计数器/温度通道等附加功能
SetAdditionalFeature = vk701n.VK70xNMC_Set_AdditionalFeature
SetAdditionalFeature.argtypes = [c_int, c_int, c_int, c_double]  # 参数类型为整数、整数、整数、双精度
SetAdditionalFeature.restypes = c_int                         # 返回类型为整数
# [原型]；int VK70xNMC_Set_AdditionalFeature(int mci, UInt32 funcNo, UInt32 para1, double initPara);
# [参数]：
#   int mci: DAQ 序列号。默认值：[0]（信号 DAQ）
#   UInt32 funcNo: 功能参数。范围详见注释。
#   UInt32 para1: 参数 1。
#   double initPara: 参数 2。
# [返回值]：
#   >= 0 : 设置成功
#   -1   : 设置错误
#   -2   : 设置超时
#   -11  : USB 未打开
#   -12  : DAQ 未连接或不存在
#   -13  : DAQ 未连接或不存在
#   其他：异常退出

# 初始化连接的采集卡参数
# Initialize = vk701n.VK70xNMC_Initialize
# Initialize.argtypes = [c_int, c_double, c_int, c_int, c_int, c_int, c_int, c_int]
# Initialize.restypes = c_int
# [原型]；int VK70xNMC_Initialize(int mci, double refvol, int bitmode, int sr, int volrg15, int volrg26, int volrg37, int volrg48);
# [参数]：
#   int mci: DAQ 序列号。默认值：[0]（信号 DAQ）
#   double refvol: 选择 DAQ 模式。范围：[4.000] 或 [1]（VK701N）
#   int bitmode: 采样分辨率。范围：[0]: 8-bit, [1]: 16-bit, [2]/[3]: 24-bit
#   int sr: 采样频率。范围：[1]~[100000](16-bit), [1]~[50000](24-bit)
#   int volrg15 ~ volrg48: 各通道电压输入范围。范围详见注释。
# [返回值]：
#   >= 0 : 设置成功
#   -11  : 服务器未打开
#   -12  : DAQ 未连接或不存在
#   -13  : DAQ 未连接或不存在
#   其他：异常退出

# 使用 VK70xNMC_InitializeAll 函数初始化连接的采集卡参数
Initialize = vk701n.VK70xNMC_InitializeAll
Initialize.argtypes = [c_int, POINTER(c_int), c_int]  # 参数类型为整数，指向整数的指针，整数
Initialize.restypes = c_int                           # 返回类型为整数
# [原型]；int VK70xNMC_InitializeAll(int mci, int[] para, int len);
# [参数]：
#   int mci: DAQ 序列号。默认值：[0]（信号 DAQ）
#   int[] para: 设置参数。详细范围见注释。
#   int len: 数组长度。范围：固定值为 12。
# [返回值]：
#   >= 0 : 设置成功
#   -11  : 服务器未打开
#   -12  : DAQ 未连接或不存在
#   -13  : DAQ 未连接或不存在
#   其他：异常退出

# 切换系统模式
SetSystemMode = vk701n.VK70xNMC_Set_SystemMode
SetSystemMode.argtypes = [c_int, c_int, c_int, c_int]  # 参数类型为四个整数
SetSystemMode.restypes = c_int                         # 返回类型为整数
# [原型]；int VK70xNMC_Set_SystemMode(int mci, int sysmodeval, int samplemethod, int sdfilefmt);
# [参数]：
#   int mci: DAQ 序列号。默认值：[0]（信号 DAQ）
#   int sysmodeval: 选择系统模式。范围详见注释。
#   int samplemethod: 选择采样方法。范围详见注释。
#   int sdfilefmt: VK701N 不具备此功能。默认值：[0]
# [返回值]：
#   >= 0 : 设置成功
#   -11  : 服务器未打开
#   -12  : DAQ 未连接或不存在
#   -13  : DAQ 未连接或不存在
#   其他：异常退出

# 读取带有 IO 状态的单通道数据
GetOneChannelWithIOStatus = vk701n.VK70xNMC_GetOneChannel_WithIOStatus
GetOneChannelWithIOStatus.argtypes = [c_int, c_int, POINTER(c_double), c_int, c_int]  # 参数类型
GetOneChannelWithIOStatus.restypes = c_int                                       # 返回类型
# [原型]；int VK70xNMC_GetOneChannel_WithIOStatus(int mci, int CHNum, double* adcbuffer, int rsamplenum, int ioenable);
# [参数]：
#   int mci: DAQ 序列号。默认值：[0]（信号 DAQ）
#   int CHNum: 通道选择。范围：[0]~[15]：CH1~CH16
#   double* adcbuffer: 用于存储数据的缓冲区首地址
#   int rsamplenum: 读取的采样点数
#   int ioenable: 读取 IO 状态。范围详见注释。
# [返回值]：
#   > 0 : 实际读取的采样点数
#   = 0 : 无数据
#   -2  : 超时退出
#   其他：异常退出

# 读取带有 IO 状态的四通道采样数据
GetFourChannelWithIOStatus = vk701n.VK70xNMC_GetFourChannel_WithIOStatus
GetFourChannelWithIOStatus.argtypes = [c_int, POINTER(c_double), c_int, c_int]  # 参数类型
GetFourChannelWithIOStatus.restypes = c_int                                  # 返回类型
# [原型]；int VK70xNMC_GetFourChannel_WithIOStatus(int mci, int CHNum, double* adcbuffer, int rsamplenum, int ioenable);
# [参数]：
#   int mci: DAQ 序列号。默认值：[0]（信号 DAQ）
#   int CHNum: 通道选择。范围：[0]~[15]：CH1~CH16
#   double* adcbuffer: 用于存储数据的缓冲区首地址
#   int rsamplenum: 读取的采样点数
#   int ioenable: 读取 IO 状态。范围详见注释。
# [返回值]：
#   > 0 : 实际读取的采样点数
#   = 0 : 无数据
#   -2  : 超时退出
#   其他：异常退出

# 读取带有 IO 状态的所有通道采样数据（CH1~CH8）
GetAllChannelWithIOStatus = vk701n.VK70xNMC_GetAllChannel_WithIOStatus
GetAllChannelWithIOStatus.argtypes = [c_int, POINTER(c_double), c_int, c_int]  # 参数类型
GetAllChannelWithIOStatus.restypes = c_int                                  # 返回类型
# [原型]；int VK70xNMC_GetAllChannel_WithIOStatus(int mci, double* adcbuffer, int rsamplenum, int ioenable);
# [参数]：
#   int mci: DAQ 序列号。默认值：[0]（信号 DAQ）
#   double* adcbuffer: 用于存储数据的缓冲区首地址
#   int rsamplenum: 读取的采样点数
#   int ioenable: 读取 IO 状态。范围详见注释。
# [返回值]：
#   > 0 : 实际读取的采样点数
#   = 0 : 无数据
#   -2  : 超时退出
#   其他：异常退出

# 读取单通道数据
GetOneChannel = vk701n.VK70xNMC_GetOneChannel
GetOneChannel.argtypes = [c_int, c_int, POINTER(c_double), c_int]  # 参数类型
GetOneChannel.restypes = c_int                                  # 返回类型
# [原型]；int VK70xNMC_GetOneChannel(int mci, int CHNum, double* adcbuffer, int rsamplenum);
# [参数]：
#   int mci: DAQ 序列号。默认值：[0]（信号 DAQ）
#   int CHNum: 通道选择。范围：[0]~[15]：CH1~CH16
#   double* adcbuffer: 用于存储数据的缓冲区首地址
#   int rsamplenum: 读取的采样点数
# [返回值]：
#   > 0 : 实际读取的采样点数
#   = 0 : 无数据
#   -2  : 超时退出
#   其他：异常退出

# 读取四通道采样数据
GetFourChannel = vk701n.VK70xNMC_GetFourChannel
GetFourChannel.argtypes = [c_int, POINTER(c_double), c_int]  # 参数类型
GetFourChannel.restypes = c_int                             # 返回类型
# [原型]；int VK70xNMC_GetFourChannel(int mci, double* adcbuffer, int rsamplenum);
# [参数]：
#   int mci: DAQ 序列号。默认值：[0]（信号 DAQ）
#   double* adcbuffer: 用于存储数据的缓冲区首地址
#   int rsamplenum: 读取的采样点数
# [返回值]：
#   > 0 : 实际读取的采样点数
#   = 0 : 无数据
#   -2  : 超时退出
#   其他：异常退出

# 读取八通道采样数据
GetAllChannel = vk701n.VK70xNMC_GetAllChannel
GetAllChannel.argtypes = [c_int, POINTER(c_double), c_int]  # 参数类型
GetAllChannel.restypes = c_int                             # 返回类型
# [原型]；int VK70xNMC_GetAllChannel(int mci, double* adcbuffer, int rsamplenum);
# [参数]：
#   int mci: DAQ 序列号。默认值：[0]（信号 DAQ）
#   double* adcbuffer: 用于存储数据的缓冲区首地址
#   int rsamplenum: 读取的采样点数
# [返回值]：
#   > 0 : 实际读取的采样点数
#   = 0 : 无数据
#   -2  : 超时退出
#   其他：异常退出

# 设置 ADC 结果的阻塞读取方法
SetBlockingMethodtoReadADCResult = vk701n.VK70xNMC_Set_BlockingMethodtoReadADCResult
SetBlockingMethodtoReadADCResult.argtypes = [c_int, c_int]  # 参数类型为两个整数
SetBlockingMethodtoReadADCResult.restypes = c_int            # 返回类型为整数
# [原型]；int VK70xNMC_Set_BlockingMethodtoReadADCResult(int tmode, int timeout);
# [参数]：
#   int tmode: 读取方法。范围：[0]: 非阻塞读取方法, [1]: 阻塞读取方法
#   int timeout: 设置阻塞读取的超时时间。范围：
#       如果是非阻塞读取方法，默认值为 [0]
#       [1]~[10000]: 1ms~10秒
# [返回值]：
#   >= 0 : 设置成功
#   其他：异常退出

#----------------------------------------------------------------------------------------------------

# 初始化采样相关的全局变量
totalPointNum = 0                               # 采样计数
samplingFrequency = 50000                       # 采样频率（Hz）
portNum = 8234                                  # TCP 服务器端口号，默认值为 8234
curDeviceNum = c_int(0)                         # 当前设备数量，初始化为 0
deviceNo = 0                                    # 默认设备编号为 0，单个 DAQ 默认值
curHandle = c_int(0)                            # 当前设备的句柄，初始化为 0
ipAdr = ctypes.create_string_buffer(0)          # 用于存储 IP 地址的缓冲区，初始化为空
revResult = (c_double * 200000)()        # 接收数据的缓冲区，最大支持采样频率 * 8 通道
NumofADCChannel = 4                             # ADC 通道数量
initPara = (c_int * 12)()                       # 初始化参数数组，长度为 12
recvLen = 0                                     # 接收的数据长度
isSampling = True                               # 采样状态标志，初始为 True
StopFlag = True                                 # 停止标志，初始为 True
saveTimeLengthSec = 10                          # 保存时间长度（秒）
gain = 0.668                                    # 增益系数
reason_num = 12800                              # 原因编号（用途待定）
databuff = []                                   # 数据缓冲列表
timestamp = []                                  # 时间戳列表
filepath = 'F:/python_continuous_sampling'      # 数据保存路径
queueCh1 = queue.Queue()                        # 通道 1 的数据队列
queueCh2 = queue.Queue()                        # 通道 2 的数据队列
queueCh3 = queue.Queue()                        # 通道 3 的数据队列
queueCh4 = queue.Queue()                        # 通道 4 的数据队列

# 打开 TCP 服务器端口
print("打开 TCP 服务器端口...")
result = TCPOpen(portNum)
if result < 0:
    print("打开 TCP 服务器端口失败")
else:
    print("打开 TCP 服务器端口成功")
    
    # 查找已连接的 DAQ 设备
    print("查找已连接的 DAQ 设备...")
    result = -1
    while result < 0:
        result = GetConnectedClientNumbers(byref(curDeviceNum))  # 获取已连接的 DAQ 数量
        time.sleep(0.02)                                        # 等待 20 毫秒
    if(result < 0):
        print("查找已连接的 DAQ 设备失败")
    else:
        print("查找已连接的 DAQ 设备成功")
        print(f"已连接的采集卡数量: {curDeviceNum.value}")
    
        # 获取当前 DAQ 的句柄和 IP 地址
        print("获取当前 DAQ 的句柄和 IP 地址...")
        result = GetConnectedClientHandle(deviceNo, byref(curHandle), ipAdr)
        if(result < 0):
            print("获取当前 DAQ 的句柄和序列号失败")
        else:
            print("获取当前 DAQ 的句柄和序列号成功")
            print(f"DAQ 句柄: {curHandle.value}")
            print(f"IP 地址: {ipAdr.value.decode()}")  # 解码字节串为字符串
    
            # 切换系统模式
            print("切换系统模式...")
            result = SetSystemMode(deviceNo, 0, 0, 0)
            if(result < 0):
                print("切换系统模式失败")
            else:
                print("切换系统模式成功")
    
                # 初始化参数
                print(f"采样分辨率: 16-bit")
                print(f"采样频率: {samplingFrequency} Hz")
                print("初始化参数...")
                initPara[0] = samplingFrequency    # 设置采样频率
                initPara[1] = 4                    # 固定值为 4
                initPara[2] = 24                   # 设置采样分辨率为 24-bit
                initPara[3] = samplingFrequency    # 再次设置采样频率
                for i in range(4, 12):
                    initPara[i] = 1                # 设置剩余参数为 1
                result = Initialize(deviceNo, initPara, 12)  # 调用初始化函数
                if(result < 0):
                    print("初始化参数失败")
                else:
                    print("初始化参数成功")
    
                    # 设置阻塞读取数据方法
                    print("设置阻塞读取数据方法...")
                    result = SetBlockingMethodtoReadADCResult(1, 1000)  # 设置为阻塞模式，超时 1000 ms
                    if (result < 0):
                        print("设置阻塞读取数据方法失败")
                    else:
                        print("设置阻塞读取数据方法成功")
                        print("请按任意键开始连续采样...")
                        input()  # 等待用户输入
                        # 开始连续采样
                        print("开始连续采样...")
                        result = StartSampling(deviceNo)  # 开始采样
                        if (result < 0):
                            print("开始连续采样失败")
                        else:
                            print("开始连续采样成功")

# 定义任务函数，用于持续获取采样数据并处理
def task():
    global isSampling, StopFlag
    while isSampling:
        # 获取采样数据并保存，返回采样状态、停止标志、数据元素和时间戳
        isSampling, StopFlag, databuff_element, timestamp_element = GetSampleDataAndSave(
            samplingFrequency, 
            reason_num, 
            deviceNo, 
            revResult, 
            NumofADCChannel, 
            gain, 
            queueCh1, 
            queueCh2, 
            queueCh3, 
            queueCh4, 
            filepath
        )
        if timestamp_element:
            # 对采样数据进行推理处理
            predicted, confidences, raw_datas, real, imaginary = inference(databuff_element)
            # 将推理结果存入 IoT 数据库
            in_iotdb(predicted, confidences, timestamp_element, raw_datas, real, imaginary)
    if not StopFlag:
        # 如果停止标志被触发，停止采样
        StopSampling(deviceNo)

# 定义 GetSampleDataAndSave 函数，用于获取采样数据并保存（注释已取消，保留为参考）
# def GetSampleDataAndSave():
#     if samplingFrequency > 10:
#         getPoints = 6400
#     else:
#         getPoints = 1
#     global recvLen
#     # 从四个通道读取采样数据
#     recvLen = GetFourChannel(deviceNo, revResult, int(getPoints))
#     if recvLen > 0:
#         # 统计每次获取的点数
#         global totalPointNum
#         totalPointNum = totalPointNum + recvLen
#         for i in range(0, recvLen * NumofADCChannel, NumofADCChannel):
#             if (i % (100 * NumofADCChannel) == 0):
#                 for j in range(0, NumofADCChannel):
#                     print(f"CH{j + 1} = {revResult[i + j]:.8f}V, \t", end="")
#                 print("")
#         print(
#             f"总点数为 [{totalPointNum}], 本次获取点数为 [{recvLen}]")
#         # 创建保存数据的数组及队列
#         revResultCh1 = (c_double * 50000)()
#         revResultCh2 = (c_double * 50000)()
#         revResultCh3 = (c_double * 50000)()
#         revResultCh4 = (c_double * 50000)()
#         bufferCh1 = bytearray(150000)
#         bufferCh2 = bytearray(150000)
#         bufferCh3 = bytearray(150000)
#         bufferCh4 = bytearray(150000)
#
#         for i in range(recvLen * NumofADCChannel):
#             a = i % 4
#             b = i // 4
#             if a == 0:
#                 revResultCh1[b] = revResult[i]
#             elif a == 1:
#                 revResultCh2[b] = revResult[i]
#             elif a == 2:
#                 revResultCh3[b] = revResult[i]
#             elif a == 3:
#                 revResultCh4[b] = revResult[i]
#
#         for i in range(recvLen):
#             revResultCh1[i] *= gain
#             revResultCh1[i] += 5
#             revResultCh1[i] *= 0.1
#             if revResultCh1[i] > 1:
#                 revResultCh1[i] = 1
#             if revResultCh1[i] < 0:
#                 revResultCh1[i] = 0
#             intSample = int(revResultCh1[i] * 8388607)
#             bufferCh1[3 * i] = intSample & 0x0000ff
#             bufferCh1[3 * i + 1] = (intSample & 0x00ff00) >> 8
#             bufferCh1[3 * i + 2] = intSample >> 16
#         print(len(bufferCh1))
#         while len(bufferCh1) - 1 > 3 * recvLen - 1:
#             del bufferCh1[-1]
#         queueCh1.put(bufferCh1)
#
#         for i in range(recvLen):
#             revResultCh2[i] *= gain
#             revResultCh2[i] += 5
#             revResultCh2[i] *= 0.1
#             if revResultCh2[i] > 1:
#                 revResultCh2[i] = 1
#             if revResultCh2[i] < 0:
#                 revResultCh2[i] = 0
#             intSample = int(revResultCh2[i] * 8388607)
#             bufferCh2[3 * i] = intSample & 0x0000ff
#             bufferCh2[3 * i + 1] = (intSample & 0x00ff00) >> 8
#             bufferCh2[3 * i + 2] = intSample >> 16
#         while len(bufferCh1) - 1 > 3 * recvLen - 1:
#             del bufferCh1[-1]
#         queueCh2.put(bufferCh2)
#
#         for i in range(recvLen):
#             revResultCh3[i] *= gain
#             revResultCh3[i] += 5
#             revResultCh3[i] *= 0.1
#             if revResultCh3[i] > 1:
#                 revResultCh3[i] = 1
#             if revResultCh3[i] < 0:
#                 revResultCh3[i] = 0
#             intSample = int(revResultCh3[i] * 8388607)
#             bufferCh3[3 * i] = intSample & 0x0000ff
#             bufferCh3[3 * i + 1] = (intSample & 0x00ff00) >> 8
#             bufferCh3[3 * i + 2] = intSample >> 16
#         while len(bufferCh1) - 1 > 3 * recvLen - 1:
#             del bufferCh1[-1]
#         queueCh3.put(bufferCh3)
#
#         for i in range(recvLen):
#             revResultCh4[i] *= gain
#             revResultCh4[i] += 5
#             revResultCh4[i] *= 0.1
#             if revResultCh4[i] > 1:
#                 revResultCh4[i] = 1
#             if revResultCh4[i] < 0:
#                 revResultCh4[i] = 0
#             intSample = int(revResultCh4[i] * 8388607)
#             bufferCh4[3 * i] = intSample & 0x0000ff
#             bufferCh4[3 * i + 1] = (intSample & 0x00ff00) >> 8
#             bufferCh4[3 * i + 2] = intSample >> 16
#         while len(bufferCh1) - 1 > 3 * recvLen - 1:
#             del bufferCh1[-1]
#         queueCh4.put(bufferCh4)
#
#         SaveWavFile(samplingFrequency)
#
#
# def SaveWavFile(sample_rate):
#     if getqueuelen(queueCh1) % 12800 == 0:
#         timestamp.append(time.time())
#         print(timestamp)
#
#     if getqueuelen(queueCh1) >= (saveTimeLengthSec * samplingFrequency * 24 / 8 * 1):
#         tempfilepath = filepath
#         tempfilepath += "//"
#         tempfilepath += "_ch1.wav"
#         global isSampling
#         global StopFlag
#         isSampling = False
#         StopFlag = False
#         if not os.path.exists(tempfilepath):
#             os.system(r"touch {}".format(tempfilepath))
#         with wave.open(tempfilepath,'wb') as wav_file:
#             num_channel = 1
#             sampwidth = 3
#             num_frame = queueCh1.qsize()
#
#             wav_file.setnchannels(num_channel)
#             wav_file.setsampwidth(sampwidth)
#             wav_file.setframerate(sample_rate)
#             wav_file.setnframes(num_frame)
#
#             databuff = bytearray()
#             for array in queueCh1.queue:
#                 for ii in range(len(array)):
#                     databuff.append(array[ii])
#
#             while True:
#                 queueCh1.get()
#                 if queueCh1.empty():
#                     break
#             wav_file.writeframes(databuff)
#             print("采样完成")
#
#
# def getqueuelen(queue1):
#     arraylen = 0
#     for array in queue1.queue:
#         arraylen += len(array)
#     return arraylen

# 检查是否为主程序运行
if __name__ == '__main__':
    task()  # 执行采样任务
