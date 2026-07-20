# 鲁班猫 ARM64 Linux 版声纹故障诊断系统

本目录是从 Windows 可用版 `Software` 独立复制出的鲁班猫版本。Windows 版仍保留在 `OilStream/Software`，本目录内的修改不会影响原始本地项目。

## 目录内容

- `src/`：采集、实时显示、降噪、推理和本地记录核心代码
- `configs/`：鲁班猫默认配置，SDK 路径指向 `vendor/vk701n/libVK70XNMC_DAQ_SHARED.so`
- `vendor/vk701n/`：AArch64 Linux SDK `.so` 和 ini 配置
- `models/legacy_cnn/`：legacy CNN 模型、标准化参数和模型说明
- `tools/probe_vk701n.py`：VK701N-SD 采集探针
- `tools/check_sound_capture.py`：四通道声音采集链路自检
- `scripts/`：安装、探针、测试和 GUI 启动脚本
- `data/records/`：采集和诊断结果保存目录
- `data/capture_checks/`：安静/机械噪声对照、试听 WAV 和自检报告

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

## 验证是否真正采到声音

采集探针只能证明 SDK 持续返回 ADC 数据，非零电压也可能只是直流偏置或电气底噪。进入降噪和模型前，先执行两阶段声音自检：

```bash
bash scripts/check_sound_capture.sh
```

脚本会依次提示：

1. 保持现场安静，采集 5 秒四通道基线。
2. 持续制造可重复的机械噪声，再采集 5 秒四通道数据。
3. 比较每个通道的 AC RMS、20 Hz 至 20 kHz 频带能量、峰值和削波率。
4. 输出推荐通道、推荐输入量程和 `data/capture_checks/{timestamp}/` 报告目录。

需要延长每阶段采样时可以执行：

```bash
bash scripts/check_sound_capture.sh --duration 10
```

判定规则：

- AC RMS 和可听频带能量都提升至少 `10 dB`：明确检测到机械声音响应。
- 两项都提升至少 `6 dB`：较大概率检测到声音，建议重复一次确认。
- 未达到 `6 dB`：证据不足，不能仅凭 WAV 非零认定麦克风正常。
- 削波超过 `0.1%`：当前量程过小，增大量程后重新自检。

GUI 的“硬件设置”页也提供“采集链路自检”。应用推荐通道和量程后不会自动保存，并会要求从安静基线开始重新测试，确认新量程没有削波。

每个通道会生成两类音频：

- `*_raw.wav`：按当前采集量程线性映射的原始 PCM16 文件，不改变实际相对幅度。
- `*_monitor.wav`：去直流、20 Hz 高通后施加一次固定线性增益，目标 RMS 为 `-20 dBFS`、峰值不超过 `-1 dBFS`、最大增益 `40 dB`。

`monitor.wav` 不使用降噪、压缩或动态 AGC，只用于复制到电脑试听；处理增益记录在 `report.json`，该文件永远不会进入模型。`quiet_voltage.npy` 和 `noise_voltage.npy` 才是四通道原始电压原件。

可以从电脑复制完整目录，例如：

```bash
scp -r cat@<鲁班猫IP>:/home/cat/OilStream/Software_LubanCat/data/capture_checks/<时间戳> .
```

如果四个通道都没有达到 `6 dB`，按顺序排查：

- 确认麦克风实际接入 CH1 至 CH4 中的哪一路，并检查信号地、单端/差分接法。
- 确认驻极体麦克风是否有偏置供电，IEPE/ICP 传感器是否有恒流激励。
- 确认传感器输出是否经过前置放大；VK701N 电压输入不能替代麦克风前置放大器。
- 在不削波的前提下使用更小量程；程序只推荐量程，不会自动切换硬件。

由于当前未知麦克风灵敏度、供电和前置增益，自检只能证明电压随机械声音变化并还原可辨认的时序和音色，不能输出校准后的真实响度或 dB SPL。

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

## 推荐操作流程

顶部标签按实际工作顺序排列：`硬件设置` → `数据采集` → `降噪对比` → `诊断结果` → `历史记录` → `模型信息`。标签页可以随时切换；缺少采样数据时，相关按钮会保持禁用并说明原因。

1. 在“硬件设置”中检查 SDK、通道、输入量程、采样率和采集时长，先运行“采集链路自检”。
2. 自检至少达到“较大概率响应”且无削波后，保存硬件设置并进入采集。
3. 在“数据采集”中点击“开始采集”。手动停止或达到设定时长后，程序只结束采样，不会立即运行模型。
4. 采集结束后可以选择“重新采样”“保存采样”或“进入降噪对比”。保存后当前数据仍保留，可以继续降噪。
5. 在“降噪对比”中选择带通滤波、小波降噪或两者串联，点击“应用并对比”。全量处理在后台运行，页面会显示阶段进度。
6. 对比完成后选择“不降噪，直接分析”或“使用当前降噪结果分析”。模型推理和保存过程会显示在“诊断结果”页。

“读取已保存采样”只读取本程序在 `data/records/` 中创建的记录，确保电压量程、gain、采样率和 legacy 输入能够完整恢复；不把任意外部 WAV 当作采集卡原始数据。

## 降噪与模型输入

`configs/denoise.json` 中的 `enabled` 只是总开关。只有 `bandpass_enabled` 或 `wavelet_enabled` 至少一项为 `true` 时，波形才会真正发生处理。默认配置中两种方法均关闭，因此程序会明确提示“尚未启用任何降噪方法”。

降噪页上下两条波形使用同一时间窗口和同一电压纵轴。播放按钮只驱动波形同步滚动，不播放声音，也不需要 QtMultimedia。参数修改后，旧降噪结果会标记为过期；必须重新点击“应用并对比”，才能使用降噪结果分析。

两种分析方式的数据语义不同：

- “不降噪，直接分析”逐字节使用采集时生成的 `legacy_input`，与原有模型输入保持一致。
- “使用当前降噪结果分析”把处理后的归一化波形还原为电压，再使用当前硬件配置中的量程和 gain 生成新的 legacy 输入。

Legacy CNN 是使用原有数据分布训练的，降噪输入可能改变分类结果。诊断结果和记录元数据都会保存 `analysis_source`，用于区分原始信号与降噪信号。

默认参数：

- 端口：`8234`
- 设备号：`0`
- ADC 通道：`2`
- 输入量程：`5 V`
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

点击“保存采样”后，记录首先以 `captured` 状态写入 `data/records/{record_id}/`：

- `raw_voltage.npy`：原始电压数组
- `raw.wav`：便于检查的归一化单声道 WAV
- `legacy_input.bin`：采集时生成的原始模型输入
- `metadata.json`：硬件配置、采集信息和记录状态

完成诊断后，同一条未诊断记录会补充为 `diagnosed` 状态：

- `analysis_input.bin`：本次实际送入模型的字节流
- `denoised.wav`：本次流程生成过降噪结果时保存
- `result.json`：模型输出、Top-K、输入来源和耗时

已经诊断过的历史记录再次分析时会创建一条关联的新记录，不覆盖旧结果。历史记录页直接扫描本地文件目录，不使用 SQLite，并可把选中的记录重新载入降噪对比页。

声音链路自检记录保存在 `data/capture_checks/{timestamp}/`，不与模型诊断记录混用：

- `quiet_voltage.npy`、`noise_voltage.npy`：四通道原始电压矩阵。
- `quiet_chN_raw.wav`、`noise_chN_raw.wav`：按量程映射的原始 WAV。
- `quiet_chN_monitor.wav`、`noise_chN_monitor.wav`：线性增强试听版。
- `report.json`：完整指标、硬件参数、试听增益和文件索引。
- `summary.txt`：便于现场阅读的中文结论。

## 与 Windows 版的关系

- Windows 版目录：`OilStream/Software`
- 鲁班猫版目录：`OilStream/Software_LubanCat`

两个目录彼此独立。鲁班猫版默认使用 `.so`，Windows 版默认使用 `.dll`。
