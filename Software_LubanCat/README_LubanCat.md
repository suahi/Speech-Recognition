# 鲁班猫 ARM64 Linux 版声纹故障诊断系统

本目录是从 Windows 可用版 `Software` 独立复制出的鲁班猫版本。Windows 版仍保留在 `OilStream/Software`，本目录内的修改不会影响原始本地项目。

## 目录内容

- `src/`：采集、实时显示、降噪、推理和本地记录核心代码
- `configs/`：鲁班猫默认配置，SDK 路径指向 `vendor/vk701n/libVK70XNMC_DAQ_SHARED.so`
- `vendor/vk701n/`：AArch64 Linux SDK `.so` 和 ini 配置
- `models/legacy_cnn/`：legacy CNN 模型、标准化参数和模型说明
- `tools/probe_vk701n.py`：VK701N-SD 采集探针
- `scripts/`：安装、探针、测试和 GUI 启动脚本
- `data/records/`：采集和诊断结果保存目录

## 环境要求

- 鲁班猫 ARM64 Linux，建议使用 Debian/Ubuntu 系镜像
- Python 3.10 到 3.12
- 桌面环境或 X11/Wayland 转发，用于运行 PySide6 GUI
- VK701N-SD 与鲁班猫处于同一网段，默认端口 `8234`

依赖策略：

- NumPy 固定为 `>=1.26,<2.0`，避免 legacy 音频特征和模型栈被 NumPy 2.x 破坏
- PySide6 在 ARM64 Linux 上使用 `PySide6_Essentials==6.7.3`，避免过新的 Qt wheel 要求更高 glibc
- PyTorch 固定为 `>=2.8,<2.13`，使用 PyPI 上已有的 Linux aarch64 CPU wheel

## 安装

建议放到：

```bash
/home/cat/OilStream/Software_LubanCat
```

进入目录后执行：

```bash
cd /home/cat/OilStream/Software_LubanCat
bash scripts/install_lubancat.sh
```

脚本会优先创建并使用本目录下的 `.venv`，安装 Qt/XCB 等系统运行库，然后以 editable 方式安装 `.[desktop,test]`。常用覆盖项：

```bash
PYTHON=/usr/bin/python3.10 bash scripts/install_lubancat.sh
VENV_DIR=/home/cat/oilstream-venv bash scripts/install_lubancat.sh
SKIP_APT=1 bash scripts/install_lubancat.sh
```

如果已经在现有 conda/miniforge 环境中启动过，并看到 `NumPy 2.0.2`、`shiboken6` 或 `xcb` 相关报错，先在该环境内修复：

```bash
cd /home/cat/gyroscope_detect/oilStream-test/Software_LubanCat
python -m pip install --upgrade --force-reinstall --prefer-binary -r requirements-lubancat-aarch64.txt
python -m pip install --no-deps -e .
sudo apt-get update
sudo apt-get install -y libxcb-cursor0 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 libxcb-shape0 libxcb-xfixes0 libxcb-xinerama0 libxcb-xinput0
```

## 运行采集探针

先关闭其他电脑上的厂家 DAQ 软件，确保只有鲁班猫连接采集卡：

```bash
bash scripts/probe_vk701n.sh
```

正常情况下应看到连续非 0 的 `recvLen`，例如接近：

```text
recvLen=5000
```

如果持续为 `0`，或只出现 `1/2` 后全是 `0`，优先检查：

- 采集卡和鲁班猫是否在同一网段
- 端口是否为 `8234`
- 厂家 DAQ 软件是否已经关闭
- 采集卡是否需要断电重启
- `configs/hardware_vk701n.json` 中的初始化 profile 是否需要在 `code_source` 和 `fixed` 间切换

## 启动 GUI

探针正常后启动桌面程序：

```bash
bash scripts/run_app.sh
```

脚本会自动：

- 激活 `.venv`
- 设置 `LD_LIBRARY_PATH` 到 `vendor/vk701n`
- 设置 `PYTHONPATH` 到 `src`
- 在未设置 Qt 平台时选择 `xcb` 或 `wayland`

默认参数：

- 端口：`8234`
- 设备号：`0`
- ADC 通道：`2`
- 采样率：`50000 Hz`
- 位深：`24`
- 每次读取点数：`5000`
- 初始化 profile：`code_source`
- SDK：`vendor/vk701n/libVK70XNMC_DAQ_SHARED.so`

## 运行测试

安装完成后可在鲁班猫上执行：

```bash
bash scripts/test_lubancat.sh
```

也可以直接在本目录运行：

```bash
python -m pytest
```

## 保存结果

每次诊断会在 `data/records/{record_id}/` 下保存：

- `raw_voltage.npy`
- `raw.wav`
- `legacy_input.bin`
- `denoised.wav`
- `metadata.json`
- `result.json`

历史记录页直接扫描本地文件目录，不使用 SQLite。

## 与 Windows 版的关系

- Windows 版目录：`OilStream/Software`
- 鲁班猫版目录：`OilStream/Software_LubanCat`

两个目录彼此独立。鲁班猫版默认使用 `.so`，Windows 版默认使用 `.dll`。
