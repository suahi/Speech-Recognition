# 鲁班猫 Linux 版声纹故障诊断系统

该目录是从 Windows 可用版 `Software` 独立复制出的鲁班猫版本。Windows 版仍保留在 `OilStream/Software`，本目录内的改动不会影响 Windows 程序。

## 1. 目录内容

- `src/`：声纹采集、实时显示、降噪、推理、保存记录的核心代码
- `configs/`：鲁班猫默认配置，SDK 路径指向 `vendor/vk701n/libVK70XNMC_DAQ_SHARED.so`
- `vendor/vk701n/`：AArch64 Linux SDK `.so` 和 ini 配置
- `models/legacy_cnn/`：legacy CNN 模型、标准化参数和模型说明
- `tools/probe_vk701n.py`：VK701N-SD 采集探针
- `scripts/`：安装、探针和 GUI 启动脚本
- `data/records/`：采集和诊断结果保存目录

## 2. 拷贝到鲁班猫

建议放到：

```bash
/home/cat/OilStream/Software_LubanCat
```

进入目录：

```bash
cd /home/cat/OilStream/Software_LubanCat
```

## 3. 安装依赖

建议在 conda/miniforge 环境或 Python 3.10 虚拟环境中执行：

```bash
bash scripts/install_lubancat.sh
```

如果 PyTorch 在当前鲁班猫镜像上无法直接安装，需要先安装匹配 ARM64/aarch64 的 CPU 版 torch wheel，再重新执行安装脚本。

如果 PySide6 GUI 无法打开，先确认鲁班猫已经进入桌面环境，或远程桌面/X11 转发已经配置好。

## 4. 运行采集探针

先关闭其他电脑上的厂家 DAQ 软件，确保只有鲁班猫连接采集卡。

```bash
bash scripts/probe_vk701n.sh
```

正常情况下应看到连续非 0 的 `recvLen`，例如接近：

```text
recvLen=5000
```

如果持续为 `0` 或只出现 `1/2` 后全是 `0`，优先检查：

- 采集卡和鲁班猫是否在同一网段
- 端口是否为 `8234`
- 厂家 DAQ 软件是否已经关闭
- 采集卡是否需要断电重启
- `configs/hardware_vk701n.json` 中的初始化布局是否需要切换

## 5. 启动 GUI

探针正常后启动桌面程序：

```bash
bash scripts/run_app.sh
```

默认参数：

- 端口：`8234`
- 设备号：`0`
- ADC 通道：`2`
- 采样率：`50000 Hz`
- 位深：`24`
- 每次读取点数：`5000`
- 初始化布局：`code_source`
- SDK：`vendor/vk701n/libVK70XNMC_DAQ_SHARED.so`

## 6. 保存结果

每次诊断会在 `data/records/{record_id}/` 下保存：

- `raw_voltage.npy`
- `raw.wav`
- `legacy_input.bin`
- `denoised.wav`
- `metadata.json`
- `result.json`

历史记录页直接扫描本地文件目录，不使用 SQLite。

## 7. 和 Windows 版的关系

- Windows 版目录：`OilStream/Software`
- 鲁班猫版目录：`OilStream/Software_LubanCat`

两个目录彼此独立。鲁班猫版默认使用 `.so`，Windows 版默认使用 `.dll`。
