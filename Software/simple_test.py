#!/usr/bin/env python3
"""
简单测试 matplotlib 可用性
"""
import sys
import os

# 添加 src 到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    import matplotlib
    print("matplotlib 版本:", matplotlib.__version__)

    try:
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
        print("matplotlib Qt 后端可用")
    except ImportError as e:
        print("matplotlib Qt 后端不可用:", e)

    # 检查我们的模块
    from voice_fault_diagnosis.app.waveform_display import calculate_waveform_display
    import numpy as np

    # 测试计算函数
    test_data = np.sin(2 * np.pi * 100 * np.linspace(0, 1, 10000)).astype(np.float32)
    result = calculate_waveform_display(test_data, adaptive=True, full_scale_volts=5.0)

    print("calculate_waveform_display 工作正常")
    print("   - 数据长度:", len(result.y_values))
    print("   - 模式:", result.mode_name)

except ImportError as e:
    print("导入错误:", e)
    print("需要安装 matplotlib: pip install matplotlib")
    sys.exit(1)

print("\n所有依赖检查通过！")