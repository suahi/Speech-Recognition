# 轴承状态识别与剩余寿命预测系统

`Software/` 是一个纯离线的轴承音频演示小软件。它只读取本地 M4A/WAV 文件，不需要外接音频设备、网络连接或厂商驱动。

界面采用经典工业/MATLAB 桌面布局：上方读取音频和三类概率柱状图，底部左侧显示完整音频波形，右侧显示算法估计剩余寿命。

## 环境安装

推荐 Windows 64 位与 Python 3.11（Python 3.10–3.12 也可）。

```powershell
cd Software
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[desktop,test]"
```

M4A 解码使用 `imageio-ffmpeg` 自带的 FFmpeg 后端，无需另行安装系统 FFmpeg。WAV 与 M4A 都会转为单声道 16 kHz 后分析。

## 用外部数据训练模型

原始音频不应复制或提交到 Git。训练时通过 `--data-root` 指向外部 `data_v3` 目录：

```powershell
cd Software
python tools\train_bearing_models.py --data-root "D:\yzy\02 项目\202601JY陀螺仪故障检测\demo\data_v3"
```

训练脚本仅将下列产物写入 `models/bearing/`：

- `bearing_classifier.joblib`：健康、轴承损伤、间隙异常三分类随机森林。
- `feature_config.json`：MFCC、能量、峭度、频谱统计与健康样本声学异常基线。
- `test_manifest.csv`、`train_manifest.csv`：不含绝对路径的文件级划分清单。
- `training_metrics.json`：文件级测试指标与限制说明。

标签依据文件名建立：`好*` 为健康、包含 `轴承损伤` 为轴承损伤、包含 `间隙` 为间隙异常。脚本固定随机种子，以原始文件为单位做 80:20 划分；5 秒片段只在各自分区内扩充特征，绝不会跨训练和测试集。

当前给定的 53 段数据会形成 42 个训练文件和 11 个测试文件（健康 7/2、轴承损伤 34/8、间隙异常 1/1）。间隙异常只有 2 个原始文件，因此它的泛化结论仅供演示。

## 启动与操作

```powershell
cd Software
python run_app.py
```

1. 点击“读取音频”。
2. 选择 M4A 或 WAV 文件。若设置了外部数据根目录，文件选择器会优先定位到测试集清单所在目录：

   ```powershell
   $env:BEARING_DATA_ROOT = "D:\yzy\02 项目\202601JY陀螺仪故障检测\demo\data_v3"
   python run_app.py
   ```

3. 音频会在后台解码、归档并分析。执行时“读取音频”按钮禁用，任务结束或失败后自动恢复；取消文件选择不会改变界面。
4. 解码成功后，底部左侧立即显示完整音频波形；顶部显示三类概率柱状图，右侧显示带两位小数的算法估计剩余寿命和状态等级。

## 结果记录

每次识别在 `data/records/{record_id}/` 建立唯一记录目录（该目录已被 Git 忽略）：

- `source.m4a` 或 `source.wav`：归档的原始输入文件。
- `metadata.json`：原始路径、解码参数、音频时长/声道/采样率、模型版本和片段数。
- `result.json`：三类概率、类别、置信度、算法版本、分类风险、声学异常风险和两位小数的寿命估计。

## 算法估计剩余寿命

系统不训练虚构的寿命回归标签。它以健康、轴承损伤、间隙异常的分类风险权重（0.02、0.68、0.92）以及相对于健康声学基线的异常度计算总退化度，并输出范围为 3.00%–99.80% 的稳定两位小数百分比。状态等级为：≥70% 健康、40%–69.99% 预警、<40% 检修。

## 测试

```powershell
cd Software
python -m pytest
```

测试覆盖 M4A/WAV 解码、文件级划分、模型产物、结果归档、后台互斥与离屏工业风界面。
