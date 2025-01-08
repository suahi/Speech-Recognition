from ctypes import *
from SaveWavFile import SaveWavFile

vk701n = cdll.LoadLibrary('./VK70xNMC_DAQ2.dll')
GetFourChannelWithIOStatus = vk701n.VK70xNMC_GetFourChannel_WithIOStatus
GetFourChannelWithIOStatus.argtypes = [c_int, POINTER(c_double), c_int, c_int]
GetFourChannelWithIOStatus.restypes =c_int

GetFourChannel = vk701n.VK70xNMC_GetFourChannel
GetFourChannel.argtypes = [c_int, POINTER(c_double), c_int]
GetFourChannel.restypes =c_int


def GetSampleDataAndSave(samplingFrequency, reason_num, deviceNo, revResult, NumofADCChannel, gain, queueCh1, queueCh2, queueCh3, queueCh4, filepath):
    if samplingFrequency > 10:
        getPoints = reason_num
    else:
        getPoints = 1
    # Read sampling data from 4 channels.
    recvLen = GetFourChannel(deviceNo, revResult, int(getPoints))
    if recvLen > 0:
        #创建保存数据的数组及队列
        revResultCh1 = (c_double * 50000)()
        revResultCh2 = (c_double * 50000)()
        revResultCh3 = (c_double * 50000)()
        revResultCh4 = (c_double * 50000)()
        bufferCh1 = bytearray(150000)
        bufferCh2 = bytearray(150000)
        bufferCh3 = bytearray(150000)
        bufferCh4 = bytearray(150000)

        for i in range(recvLen * NumofADCChannel):
            a = i % 4
            b = i // 4
            if a == 0:
                revResultCh1[b] = revResult[i]
            elif a == 1:
                revResultCh2[b] = revResult[i]
            elif a == 2:
                revResultCh3[b] = revResult[i]
            elif a == 3:
                revResultCh4[b] = revResult[i]

        for i in range(recvLen):
            revResultCh1[i] *= gain
            revResultCh1[i] += 5
            revResultCh1[i] *= 0.1
            if revResultCh1[i] > 1:
                revResultCh1[i] = 1
            if revResultCh1[i] < 0:
                revResultCh1[i] = 0
            intSample = int(revResultCh1[i] * 8388607)
            bufferCh1[3 * i] = intSample & 0x0000ff
            bufferCh1[3 * i + 1] = (intSample & 0x00ff00) >> 8
            bufferCh1[3 * i + 2] = intSample >> 16
        while len(bufferCh1) - 1 > recvLen - 1:
            del bufferCh1[-1]
        queueCh1.put(bufferCh1)

        for i in range(recvLen):
            revResultCh2[i] *= gain
            revResultCh2[i] += 5
            revResultCh2[i] *= 0.1
            if revResultCh2[i] > 1:
                revResultCh2[i] = 1
            if revResultCh2[i] < 0:
                revResultCh2[i] = 0
            intSample = int(revResultCh2[i] * 8388608)
            bufferCh2[3 * i] = intSample & 0x0000ff
            bufferCh2[3 * i + 1] = (intSample & 0x00ff00) >> 8
            bufferCh2[3 * i + 2] = intSample >> 16
        while len(bufferCh1) - 1 > recvLen - 1:
            del bufferCh1[-1]
        queueCh2.put(bufferCh2)

        for i in range(recvLen):
            revResultCh3[i] *= gain
            revResultCh3[i] += 5
            revResultCh3[i] *= 0.1
            if revResultCh3[i] > 1:
                revResultCh3[i] = 1
            if revResultCh3[i] < 0:
                revResultCh3[i] = 0
            intSample = int(revResultCh3[i] * 8388608)
            bufferCh3[3 * i] = intSample & 0x0000ff
            bufferCh3[3 * i + 1] = (intSample & 0x00ff00) >> 8
            bufferCh3[3 * i + 2] = intSample >> 16
        while len(bufferCh1) - 1 > recvLen - 1:
            del bufferCh1[-1]
        queueCh3.put(bufferCh3)

        for i in range(recvLen):
            revResultCh4[i] *= gain
            revResultCh4[i] += 5
            revResultCh4[i] *= 0.1
            if revResultCh4[i] > 1:
                revResultCh4[i] = 1
            if revResultCh4[i] < 0:
                revResultCh4[i] = 0
            intSample = int(revResultCh4[i] * 8388608)
            bufferCh4[3 * i] = intSample & 0x0000ff
            bufferCh4[3 * i + 1] = (intSample & 0x00ff00) >> 8
            bufferCh4[3 * i + 2] = intSample >> 16
        while len(bufferCh1) - 1 > recvLen - 1:
            del bufferCh1[-1]
        queueCh4.put(bufferCh4)

        isSampling, StopFlag, databuff, timestamp = SaveWavFile(samplingFrequency, reason_num, queueCh1, 10, filepath)
        return isSampling, StopFlag, databuff, timestamp
