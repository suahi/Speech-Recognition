# Voice Fault Diagnosis

本目录是基于 `CodeSource/python_continuous_sampling` 重建的本地文件版声纹故障诊断系统。

## Run

```powershell
cd Software
python run_app.py
```

## Data

每次诊断记录保存到 `data/records/{record_id}/`，不使用 SQLite。

关键文件：

- `raw_voltage.npy`: CH1 原始声纹电压
- `raw.wav`: 原始电压归一化后的 WAV
- `legacy_input.bin`: 兼容旧 CNN 的输入字节流
- `denoised.wav`: 降噪后的 WAV
- `metadata.json`: 硬件和采集元数据
- `result.json`: 推理结果
