# VK701N-SD 声纹故障诊断演示

本项目的当前演示程序位于 `Software/`，采用 Windows 电脑直连方案：

```text
麦克风 → VK701N-SD CH2 → 网线直连 Windows 电脑
```

程序支持两种互斥任务：从采集卡实时采集 10 秒后识别，以及加载本地 WAV 后立即识别。两种入口共用六分类 WAV CNN，并把输入、元数据和结果保存到本地记录目录。

部署、网络设置、运行方式和验收步骤见 [`Software/README.md`](Software/README.md)。
