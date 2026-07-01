import os
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
from dataset import dataprocess, AudioDataset
import time
import torch.nn.functional as F
import pickle
from standardizer import (
    load_initial_mean_std, initialize_buffer, 
    standardize_data, update_local_buffer, 
    compute_environment_mean_std, update_model_mean_std
)

# 全局只做一次：加载模型时，加载初始 mean & std，并初始化本地缓冲
load_initial_mean_std('mean_std.pkl')  # 第一次加载时执行
initialize_buffer()

def inference(raw_bytes):

    start = time.time()

    X, y, real, imaginary = dataprocess(raw_bytes, n_fft=1024)  # n_fft参数指定了FFT（快速傅里叶变换）的窗口大小

    # X：音频特征（维度36*5），y：标签
    end = time.time()
    elapsed_time1 = end - start
    print("特征提取的执行时间为:", elapsed_time1 * 1000000, "us")

    start = time.time()
    # 3. 将 X 转为 numpy
    X = np.array(X)  # shape: (num_samples, feature_dim)

    # 4. 先用模型初始化 mean/std 做标准化
    start = time.time()
    X_norm = standardize_data(X)
    end = time.time()
    print("标准化的执行时间为:", (end - start) * 1000000, "us")

    # 5. 将原始数据（未标准化的 X）存入本地缓冲，用于统计新的环境均值和方差
    update_local_buffer(X)

    # 6. 每次推理后都试着计算新的环境均值、方差，并更新到 model_mean, model_std
    new_mean, new_std = compute_environment_mean_std()
    if new_mean is not None and new_std is not None:

        update_model_mean_std(new_mean, new_std)
        
    end = time.time()
    elapsed_time2 = end - start
    print("标准化的执行时间为:", elapsed_time2 * 1000000, "us")




    # 转换为PyTorch张量
    X_tensor = torch.tensor(X_norm, dtype=torch.float32).unsqueeze(1)  # 添加通道维度

    # 加载和处理数据，以便于使用 PyTorch 的 DataLoader 类来迭代地加载数据批次
    X_dataset = AudioDataset(X_tensor)
    # 创建一个 DataLoader 实例，用于以指定的批次大小（32个样本）从 X_dataset 数据集中加载数据，而不打乱数据的顺序。
    X_loader = DataLoader(X_dataset, batch_size=32, shuffle=False)

    # 加载模型
    model = torch.load('best_model_cnn.pt')
    # 将模型设置为推理模式
    model.eval()

    # device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    device = torch.device("cpu")
    model.to(device)  # 将模型移到GPU

    with torch.no_grad():  # 不计算梯度
        for inputs in X_loader:  # 遍历 X_loader 中的每个数据批次。每个批次包含一对 inputs（输入数据）
            start = time.time()

            inputs = inputs.to(device)
            outputs = model(inputs)  # 将输入数据传递给模型，并获取模型的输出（也称为 logits）。

            softmax_outputs = F.softmax(outputs, dim=1)
            # Softmax函数用于多分类问题，它将神经网络的原始输出（logits）转换为概率分布。
            # softmax函数的输出是一个向量，向量中的每个元素都是介于0和1之间的概率值，并且这些概率值的总和为1。
            confidences, predicted = torch.max(softmax_outputs.data, 1)  # 获取最大概率值（置信度）和对应的最大概率索引

            confidence_val = confidences.item()  # 只取单个值
            class_idx = predicted.item()         # 只取单个值
        
            end = time.time()
            elapsed_time3 = end - start
            print("推理的执行时间为:", elapsed_time3 * 1000000, "us")
            print("分类结果：", class_idx)
            print("置信度：", confidence_val)

    """
    with torch.no_grad():  # 不计算梯度
        for batch_idx, (inputs, labels) in enumerate(X_loader):  # 遍历 X_loader 中的每个数据批次
            # 假设inputs是一个形状为(batch_size, ...)的张量
            batch_size = inputs.size(0)
            for file_idx in range(batch_size):
                # 提取当前文件的输入数据和标签
                input_file = inputs[file_idx].unsqueeze(0)  # 将单个样本的形状从(...)变为(1, ...)
                label_file = labels[file_idx].unsqueeze(0)  # 同样处理标签（如果需要的话）
                # 将数据移动到正确的设备（CPU或GPU）
                input_file = input_file.to(device)
                # 开始计时
                start = time.time()
                # 进行推理
                output_file = model(input_file)  # 注意这里只传递了一个文件的输入
                softmax_outputs_file = F.softmax(output_file, dim=1)
                _, predicted_file = torch.max(softmax_outputs_file.data, 1)
                # 结束计时
                end = time.time()
                elapsed_time = end - start
                print(f"文件 {batch_idx * batch_size + file_idx + 1} 的推理时间为: {elapsed_time * 1000000} us")
                print("推理结果", predicted_file)
    """
    return predicted, confidences, y, real, imaginary


