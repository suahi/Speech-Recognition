# Windows 电脑直连采集与六类识别

`Software/` 是当前唯一的电脑端演示程序。信号与网络连接为：

```text
麦克风 → VK701N-SD CH2 → 网线直连 Windows 电脑
```

界面提供“开始实时采集”和“加载 WAV 并识别”两个入口。未连接采集卡时也能启动程序并完成 WAV 文件演示；厂商 SDK 只在开始实时采集后加载。

## 环境准备

推荐使用 Windows 64 位、Python 3.11 64 位。项目自带的 `vendor/vk701n/VK70xNMC_DAQ2.dll` 为 x64 SDK。

```powershell
cd Software
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[desktop,test]"
```

## 直连网络配置

1. 麦克风接入采集卡 `CH2`，采集卡通过网线直接连接电脑网口。
2. 在 Windows 以太网适配器的 IPv4 设置中配置静态地址：
   - 电脑 IP：`192.168.1.188`
   - 子网掩码：`255.255.255.0`（`/24`）
   - 网关和 DNS：直连演示无需填写
3. 采集卡默认地址为 `192.168.1.199`。
4. 在 Windows Defender 防火墙中允许本程序使用专用网络，并放行 TCP `8234`。
5. 启动本程序前关闭厂商测试软件及其他可能占用 SDK 或 TCP 端口的程序。

程序不会自动修改网卡或防火墙，以上设置需在演示电脑上人工完成。

## 启动

```powershell
cd Software
python run_app.py
```

默认配置文件只有 `configs/pc_direct.json`，主要参数为 CH2、50 kHz、24 bit、±5 V、10 秒采集、TCP 8234 和 `windows_c_example` 初始化方式。DLL 与模型均使用相对项目路径，程序加载配置时会解析成绝对路径并校验 SDK 为 Windows x64。

## 操作

- 实时采集：点击“开始实时采集”，程序连接采集卡并显示波形。到达 10 秒后自动归档和识别；“停止采集”只影响本次实时采集，已有有效数据仍会继续识别。
- 文件演示：点击“加载 WAV 并识别”，选择单声道或双声道 WAV。程序立即在后台归档和识别，任意有效采样率都会转为单声道 16 kHz 模型输入。
- 任一任务运行时，采集与导入按钮均被禁用，避免重复任务竞争模型或记录目录。

## 输出记录

每次任务创建唯一目录 `data/records/{record_id}/`：

- `raw.wav`：实时采集生成的 WAV，或导入 WAV 的原样归档副本；模型始终读取此副本。
- `raw_voltage.npy`：仅实时采集任务生成的 CH2 原始电压。
- `metadata.json`：来源、原始文件参数、采集参数和模型信息。
- `result.json`：C0–C5 六分类结果、置信度和全部概率。

类别固定为 C0 静音、C1 风扇、C2 敲击、C3 摩擦、C4 气流、C5 人声。

## 自动化验收

```powershell
cd Software
python -m pytest
```

无硬件演示可从界面导入仓库中的 `../CodeSource/python_continuous_sampling/_ch1.wav`。实物验收需在完成上述网卡和防火墙设置后，分别执行一次实时采集和一次文件导入。
