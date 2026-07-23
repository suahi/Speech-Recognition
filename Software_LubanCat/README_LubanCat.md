# 鲁班猫声纹采集与六类识别

这是面向鲁班猫 ARM64 Linux 的 VK701N-SD 声纹采集程序。界面只保留一次采集和自动识别：采集结束后会保存 `raw.wav`，再用内置 WAV CNN 输出六类结果。

## 使用步骤

```bash
cd /home/cat/OilStream/Software_LubanCat
bash scripts/install_lubancat.sh
bash scripts/probe_vk701n.sh
bash scripts/run_app.sh
```

开始前请确认 VK701N-SD 和鲁班猫处于同一网段，并关闭其他机器上的厂家 DAQ 程序。`probe_vk701n.sh` 应持续输出非零的 `recvLen` 后再启动界面。

## 唯一配置文件

所有可调整参数都在 `configs/lubancat_light.json`：

- `hardware`：SDK、端口、设备号、采样率、通道、量程和采集卡初始化参数。
- `capture.duration_seconds`：一次采集的时长，默认 `10.0` 秒，与模型的固定特征窗口一致。
- `model`：WAV 模型、标准化文件、来源版本和固定类别中文名称。

修改配置后重启应用。应用会在启动时验证配置、模型文件和六类映射；错误会直接显示在桌面端。

## 识别模型

模型来自 `suahi/Voice_detection_test@b5c73ea` 的默认推理组合：

- `models/wav_cnn/best_model_cnn.pt`
- `models/wav_cnn/mean_std_new.pkl`

推理流程与参考 `inference.py` 一致：将单声道 WAV 重采样至 16 kHz，提取 MFCC、Mel、Chroma-STFT、Chroma-CQT、Chroma-CENS 五类时频特征，按训练集统计量标准化后执行 PyTorch CPU 推理。

| 代码 | 界面显示 |
| --- | --- |
| C0 | 静音 |
| C1 | 风扇 |
| C2 | 敲击 |
| C3 | 摩擦 |
| C4 | 气流 |
| C5 | 人声 |

## 保存结果

每次成功采集会创建 `data/records/<record_id>/`，其中包含：

- `raw_voltage.npy`：原始声纹电压。
- `raw.wav`：由原始电压生成、实际送入模型的单声道 WAV。
- `metadata.json`：采集卡参数、状态和模型元数据。
- `result.json`：类别代码、中文名称、置信度、全量概率和 Top-K。

不再生成旧字节流输入、降噪 WAV 或历史/重分析副本。
