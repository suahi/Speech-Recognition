from getqueuelen import getqueuelen
import time
import os
import wave


def SaveWavFile(sample_rate, reason_num, queue, saveTimeLengthSec, filepath):
    isSampling = True
    StopFlag = True
    databuff = bytearray()
    timestamp = 0
    if getqueuelen(queue) % reason_num == 0:
        timestamp = time.time()
        for index, arrayall in enumerate(queue.queue):
            if index == queue.qsize() - 1:
                array = arrayall
                for ii in range(len(array)):
                    databuff.append(array[ii])

    if getqueuelen(queue) >= (saveTimeLengthSec * sample_rate * 24 / 8 * 1):
        tempfilepath = filepath
        tempfilepath += "_ch1.wav"
        isSampling = False
        StopFlag = False
        if not os.path.exists(tempfilepath):
            os.system(r"touch {}".format(tempfilepath))
        with wave.open(tempfilepath,'wb') as wav_file:
            num_channel = 1
            sampwidth = 3
            num_frame = queue.qsize()

            wav_file.setnchannels(num_channel)
            wav_file.setsampwidth(sampwidth)
            wav_file.setframerate(sample_rate)
            wav_file.setnframes(num_frame)

            databuff1 = bytearray()
            for array in queue.queue:
                for ii in range(len(array)):
                    databuff1.append(array[ii])

            while True:
                queue.get()
                if queue.empty():
                    break
            wav_file.writeframes(databuff1)
            print("sampling is finished")
    return isSampling, StopFlag, databuff, timestamp
