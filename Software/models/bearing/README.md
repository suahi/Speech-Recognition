# 轴承诊断模型产物

模型由 `Software/tools/train_bearing_models.py` 从外部 `data_v3` 目录生成；原始音频不保存在仓库。

- `bearing_classifier.joblib`：健康、轴承损伤、间隙异常三分类随机森林。
- `bearing_health_index.joblib`：演示性健康指数回归随机森林。
- `feature_config.json`：16 kHz、5 秒分段与声学异常基线。
- `test_manifest.csv`：按文件隔离的固定 20% 测试集相对路径清单。
- `training_metrics.json`：本次训练的文件级指标和限制说明。

健康指数是稳定的整数百分比，用于演示状态趋势；它不是以小时计的真实剩余寿命。
