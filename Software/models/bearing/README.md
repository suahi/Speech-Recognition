# 轴承诊断模型产物

模型由 `Software/tools/train_bearing_models.py` 从外部 `data_v3` 目录生成；原始音频不保存在仓库。

- `bearing_classifier.joblib`：健康、轴承损伤、间隙异常三分类随机森林。
- `feature_config.json`：16 kHz、5 秒分段与声学异常基线。
- `test_manifest.csv`：按文件隔离的固定 20% 测试集相对路径清单。
- `training_metrics.json`：本次训练的文件级指标和限制说明。

“算法估计剩余寿命”由三类概率和相对健康声学基线的异常度以固定公式计算，输出稳定的两位小数百分比；它不使用不存在的寿命标签训练。
