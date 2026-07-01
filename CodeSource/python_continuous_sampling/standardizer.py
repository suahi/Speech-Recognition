import numpy as np
import pickle

# 全局缓存：用于保存「当前用于推理的」均值、方差
model_mean = None
model_std = None

# 用于记录新数据的“环境”缓冲区，可按需限制最大长度
local_data_buffer = None
MAX_BUFFER_SIZE = 2000  # 自定义上限，防止无限增大

def load_initial_mean_std(pkl_path='mean_std.pkl'):
    """
    从训练阶段保存的 mean_std.pkl 中加载模型原始的均值和方差。
    并将其存储到全局变量 model_mean, model_std。
    """
    global model_mean, model_std
    with open(pkl_path, 'rb') as f:
        mean_std = pickle.load(f)
    model_mean = mean_std['mean']
    model_std = mean_std['std']
    print("[standardizer] Loaded initial mean/std from model:", model_mean, model_std)

def initialize_buffer():
    """
    初始化本地数据缓冲区，用于后续累计收集新数据。
    """
    global local_data_buffer
    local_data_buffer = None  # 或者设为 np.empty((0, X_dim))，根据数据维度做初始化

def standardize_data(X):
    """
    用当前 model_mean, model_std 对数据 X 做标准化 (X - mean) / std
    """
    if model_mean is None or model_std is None:
        raise ValueError("model_mean or model_std is not loaded. Please call load_initial_mean_std first.")
    return (X - model_mean) / model_std

def update_local_buffer(X_original):
    """
    将当前 batch 的原始数据 X_original 添加到 local_data_buffer 中，用于后续计算新的均值和方差。
    假设 X_original shape 为 (N, feature_dim)。
    """
    global local_data_buffer
    if local_data_buffer is None:
        local_data_buffer = X_original.copy()
    else:
        local_data_buffer = np.vstack([local_data_buffer, X_original])

    # 如果超过最大缓存长度，就只保留后 MAX_BUFFER_SIZE 条
    if local_data_buffer.shape[0] > MAX_BUFFER_SIZE:
        local_data_buffer = local_data_buffer[-MAX_BUFFER_SIZE:]

def compute_environment_mean_std():
    """
    根据 local_data_buffer 中收集的数据计算“环境随时间变化”的均值、方差。
    返回 new_mean, new_std。
    """
    global local_data_buffer
    if local_data_buffer is None or local_data_buffer.size == 0:
        return None, None  # 还没数据呢
    new_mean = np.mean(local_data_buffer, axis=0)
    new_std = np.std(local_data_buffer, axis=0) + 1e-9  # 防止除 0
    return new_mean, new_std

def update_model_mean_std(new_mean, new_std):
    """
    将新的环境均值/方差替换或融合到 global model_mean, model_std 里。
    如果想做平滑更新，可以引入一个 EMA 或加权。
    """
    global model_mean, model_std
    model_mean = new_mean
    model_std = new_std
    print("[standardizer] Updated model mean/std to:", model_mean, model_std)
