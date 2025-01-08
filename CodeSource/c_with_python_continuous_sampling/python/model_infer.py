# server.py
import socket
import json
import struct
from dataset import dataprocess, AudioDataset
import numpy as np
import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader
import time
import pickle

def inference(raw_bytes):
    start = time.time()
    X, y, real, imaginary = dataprocess(raw_bytes, n_fft=1024)
    end = time.time()
    print("特征提取的执行时间为:", (end - start) * 1e6, "us")

    start = time.time()
    X = np.array(X)
    with open('mean_std.pkl', 'rb') as f:
        mean_std = pickle.load(f)
    mean = mean_std['mean']
    std = mean_std['std']
    X = (X - mean) / std
    end = time.time()
    print("标准化的执行时间为:", (end - start) * 1e6, "us")

    X = torch.tensor(X, dtype=torch.float32).unsqueeze(1)
    X_dataset = AudioDataset(X)
    X_loader = DataLoader(X_dataset, batch_size=32, shuffle=False)

    model = torch.load('best_model_cnn.pt', map_location=torch.device('cpu'))
    model.eval()

    device = torch.device("cpu")
    model.to(device)

    predicted_all = []
    confidences_all = []

    with torch.no_grad():
        for inputs in X_loader:
            start = time.time()
            inputs = inputs.to(device)
            outputs = model(inputs)
            softmax_outputs = F.softmax(outputs, dim=1)
            confidences, predicted = torch.max(softmax_outputs.data, 1)
            end = time.time()
            print("推理的执行时间为:", (end - start) * 1e6, "us")
            predicted_all.extend(predicted.cpu().numpy().tolist())
            confidences_all.extend(confidences.cpu().numpy().tolist())

    return predicted_all, confidences_all, y, real, imaginary

def start_server(host='127.0.0.1', port=65224):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, port))
        s.listen()
        print(f"服务器启动，监听 {host}:{port}")
        while True:
            conn, addr = s.accept()
            with conn:
                print(f"连接来自 {addr}")
                try:
                    # 接收数据长度
                    data_len_bytes = conn.recv(4)
                    if not data_len_bytes:
                        print("未接收到数据长度")
                        continue
                    data_len = struct.unpack('!I', data_len_bytes)[0]
                    print(f"接收数据长度: {data_len} bytes")

                    # 接收实际数据
                    data = b''
                    while len(data) < data_len:
                        packet = conn.recv(data_len - len(data))
                        if not packet:
                            break
                        data += packet
                    if len(data) != data_len:
                        print("接收的数据长度不匹配")
                        continue
                    print(f"接收完毕，实际接收: {len(data)} bytes")

                    # 执行推理
                    predicted, confidences, y, real, imaginary = inference(data)

                    # 构建结果字典
                    result = {
                        'predicted': predicted,
                        'confidences': confidences,
                        # 根据需要添加 y, real, imaginary
                    }

                    # 将结果转换为JSON字符串
                    json_result = json.dumps(result)
                    serialized_result = json_result.encode('utf-8')
                    print(f"发送JSON数据长度: {len(serialized_result)} bytes")
                    print(f"发送的JSON数据示例: {json_result[:100]}...")  # 打印前100字符

                    # 发送结果长度和数据
                    conn.sendall(struct.pack('!I', len(serialized_result)))
                    conn.sendall(serialized_result)
                    print("推理结果已发送")

                except Exception as e:
                    print(f"处理请求时发生错误: {e}")
                    # 发送错误信息
                    error_msg = json.dumps({"error": str(e)}).encode('utf-8')
                    conn.sendall(struct.pack('!I', len(error_msg)))
                    conn.sendall(error_msg)

if __name__ == "__main__":
    start_server()
