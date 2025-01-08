import os
import librosa
import numpy as np
from torch.utils.data import DataLoader, Dataset
import torch
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder


class AudioDataset(Dataset):
    def __init__(self, features, transform=None):
        self.features = features  # 存储音频特征的数据
        self.transform = transform  # 一个可选的转换函数，用于在加载数据时对特征进行预处理或增强

    # 这个方法返回数据集中样本的总数
    def __len__(self):
        return len(self.features)

    # 这个方法支持通过索引访问数据集中的元素。接受一个索引idx作为输入，并返回该索引对应的特征
    def __getitem__(self, idx):
        feature = self.features[idx]

        if self.transform:
            feature = self.transform(feature)

        return feature


# n_fft参数指定了FFT（快速傅里叶变换）的窗口大小
def dataprocess(raw_bytes, n_fft=1024):

    # 创建数据集
    X = []

    num_samples = len(raw_bytes) // 3  # 每个样本3个字节

    sr = 50000  # 采样率50000hz

    # 创建一个空的int32数组来存储解析后的整数样本（虽然每个样本只有24位有效）
    # 我们使用int32是因为numpy没有直接的24位整数类型，但我们会忽略最高的8位
    int_audio_data = np.empty(num_samples, dtype=np.int32)

    # 解析字节数据为整数样本
    for i in range(num_samples):
        int_audio_data[i] = (raw_bytes[3 * i] | (raw_bytes[3 * i + 1] << 8) | (raw_bytes[3 * i + 2] << 16)) & 0xFFFFFF  # 掩码确保只有24位有效

    # 将整数数组转换为浮点数数组并标准化
    # 对于无符号24位整数数据，最大值是2**23 - 1
    max_24bit_value = 2 ** 23 - 1
    y = int_audio_data.astype(np.float32) / max_24bit_value

    # 计算特征

    mfccs = np.mean(librosa.feature.mfcc(y=y, sr=sr, n_mfcc=36, n_fft=n_fft).T, axis=0)

    Real_ = np.real(
        librosa.stft(y, n_fft=1024, hop_length=None, window='hann', center=True,
                     pad_mode='reflect'))

    Real = Real_.flatten()
    Imaginary_ = np.imag(
        librosa.stft(y, n_fft=1024, hop_length=None, window='hann', center=True,
                     pad_mode='reflect'))

    Imaginary = Imaginary_.flatten()


    melspectrogram = np.mean(librosa.feature.melspectrogram(y=y, sr=sr, n_mels=36, fmax=sr // 2, n_fft=n_fft).T, axis=0)
    chroma_stft = np.mean(librosa.feature.chroma_stft(y=y, sr=sr, n_chroma=36, n_fft=n_fft).T, axis=0)
    chroma_cq = np.mean(librosa.feature.chroma_cqt(y=y, sr=sr, n_chroma=36).T, axis=0)
    chroma_cens = np.mean(librosa.feature.chroma_cens(y=y, sr=sr, n_chroma=36).T, axis=0)

    # 将特征组合成一个数组
    features = np.reshape(np.vstack((mfccs, melspectrogram, chroma_stft, chroma_cq, chroma_cens,)), (36, 5))
    X.append(features)  # 每个音频文件的MFCC特征

    return X, y, Real, Imaginary


