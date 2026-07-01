import os
import pdb
import re
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.manifold import LocallyLinearEmbedding
from torchvision import transforms
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from torch.utils.data import DataLoader, TensorDataset
import matplotlib.pyplot as plt

from audiomodel import AudioCNN
from dataset import dataprocess, AudioDataset
import time
from iotdb.Session import Session
from iotdb.utils.IoTDBConstants import TSDataType, TSEncoding, Compressor


def in_iotdb(predicted, confidence, Time, raw_bytes, Real_part, Imaginary_part):
    """
    将推理结果和数据写入 IoTDB，并查询最新的 imaginary_part 做演示。
    """

    # 使用正则表达式提取预测值和置信度中的数值
    ms = re.findall(r"[-+]?\d+\.?\d*(?:e[-+]?\d+)?", str(predicted))
    mc = re.findall(r"[-+]?\d+\.?\d*(?:e[-+]?\d+)?", str(confidence))

    # 初始化 IoTDB 会话
    session = Session(
        host="192.168.5.2",
        port=6667,  # IoTDB 默认端口
        user="root",
        password="root",
        fetch_size=1024,
        zone_id="UTC+8",
    )

    try:
        # 打开会话，不启用自动提交
        session.open(False)

        # 将数值列表转换为逗号分隔的字符串
        Real = ",".join(ms)
        con = ",".join(mc)
        print(raw_bytes, type(raw_bytes),len(raw_bytes))
        raw = ",".join(map(str, raw_bytes))
        #raw = raw_bytes.decode('utf-8') if isinstance(raw_bytes, bytes) else str(raw_bytes)
        stft_R = ",".join(map(str, Real_part))
        stft_Im = ",".join(map(str, Imaginary_part))
        print("aaa111")
        print(type(raw),len(raw))
        #print(stft_R,type(stft_R),len(stft_R))
        #print(stft_Im,type(stft_Im),len(stft_Im))
        # 定义测量项和对应的值（此处只用到 imaginary_part，不再使用 stft_Imaginary_part）
        measurements_ = [
            "Real_classification_results",
            "Confidence",
            "raw_data",
            "stft_Real_part",
            "imaginary_part",
        ]
        values_ = [
            Real,
            con,
            raw,
            stft_R,
            stft_Im,
        ]

        # 定义每个测量项的数据类型
        data_types_ = [
            TSDataType.TEXT,
            TSDataType.TEXT,
            TSDataType.TEXT,
            TSDataType.TEXT,
            TSDataType.TEXT,
        ]

        # 获取当前时间戳（毫秒）
        timestamp = int(time.time() * 1000)

        # 插入记录到 IoTDB
        session.insert_record("root.voice.test", timestamp, measurements_, data_types_, values_)

        # 查询 'imaginary_part'，按时间降序排列，并限制为最新的一条记录
        query = "SELECT imaginary_part FROM root.test.test ORDER BY time DESC LIMIT 1"
        result = session.execute_query_statement(query)

        # 遍历查询结果（按列顺序获取，而不是按测点名字）
        while result.has_next():
            row = result.next()
            fields = row.get_fields()

            if len(fields) > 0:
                # 由于查询只有一个字段 imaginary_part，所以取 fields[0] 即可
                imag_str = fields[0].get_string_value()
                # 使用正则表达式提取数值
                imag_list_str = re.findall(r"[-+]?\d+\.?\d*(?:e[-+]?\d+)?", imag_str)
                # 将字符串数字转换为浮点数
                imag_list = [float(num) for num in imag_list_str]


                # 判断列表长度，决定是否进行切片
                if len(imag_list) > 60:
                    # 获取前30个和后30个元素
                    sliced_imag = imag_list[:30] + imag_list[-30:]
                    print("Imaginary Part (First 30 + Last 30):")
                    print(sliced_imag)
                    
                else:
                    print("Imaginary Part:")
                    print(imag_list)
            else:
                print("查询结果中不包含 'imaginary_part' 字段。")

    except Exception as e:
        print(f"发生错误: {e}")

    finally:
        # 确保会话在发生错误时也能关闭
        session.close()
