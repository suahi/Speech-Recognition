import os
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


def in_iotdb(predicted,confidence,Time,raw_bytes,Real_part,Imaginary_part):
    ms=(re.findall(r"[-+]?\d+\.?\d*[eE]?[-+]?\d*", str(predicted)))
    mc=(re.findall(r"[-+]?\d+\.?\d*[eE]?[-+]?\d*", str(confidence)))
    session = Session(
        host="127.0.0.1",
        port="6667",
        user="root",
        password="root",
        fetch_size=1024,
        zone_id="UTC+8",
    )

# 打开连接
    session.open(False)
    Real=str(ms)
    con=str(mc)
    raw=str(raw_bytes)
    stft_R=str(Real_part)
    stft_Im=str(Imaginary_part)
    measurements_ = ["Real_classification_results", "Confidence", "raw_data", "stft_Real_part", "imaginary_part"]
    values_ = [Real, con, raw, stft_R, stft_Im]
    data_types_ = [
    TSDataType.STRING,
    TSDataType.STRING,
    TSDataType.STRING,
    TSDataType.STRING,
    TSDataType.STRING,
    ]
    timestamp=int(time.time() * 1000)
    session.insert_record("root.test.test", timestamp, measurements_, data_types_, values_)
    # result = session.execute_query_statement("select Real_classification_results,Confidence,raw_data,stft_Real_part,imaginary_part from root.test.test order by time desc")
    result = session.execute_query_statement(
        "select imaginary_part from root.test.test order by time desc")
    while result.has_next():
        print(result.next())
    session.close()