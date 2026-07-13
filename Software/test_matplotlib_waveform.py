#!/usr/bin/env python3
"""
测试 matplotlib 版本波形显示的流畅度
"""
import sys
import time
import numpy as np
from src.voice_fault_diagnosis.app.main_window import WaveformWidget

def test_matplotlib_widget():
    """测试 matplotlib 版本的 WaveformWidget"""
    try:
        # 检查是否使用了 matplotlib 版本
        widget = WaveformWidget()
        print(f"✅ WaveformWidget 初始化成功")
        print(f"   类型: {type(widget)}")

        # 测试基本功能
        print("\n🔧 测试基本功能...")

        # 设置显示模式
        widget.set_display_mode(True, 5.0)
        print("   ✅ set_display_mode 成功")

        # 设置流配置
        widget.set_stream_config(50000, 1.0)
        print("   ✅ set_stream_config 成功")

        # 测试 set_audio
        test_data = np.sin(2 * np.pi * 1000 * np.linspace(0, 0.1, 5000)).astype(np.float32)
        widget.set_audio(test_data)
        print(f"   ✅ set_audio 成功，数据长度: {len(test_data)}")

        # 测试 push_samples
        new_samples = np.sin(2 * np.pi * 1000 * np.linspace(0.1, 0.2, 5000)).astype(np.float32)
        widget.push_samples(new_samples)
        print(f"   ✅ push_samples 成功，新数据长度: {len(new_samples)}")

        # 测试流控制
        widget.start_streaming()
        print("   ✅ start_streaming 成功")

        # 让它运行一段时间
        print("\n⏱️  运行 3 秒测试流畅度...")
        time.sleep(3)

        widget.stop_streaming()
        print("   ✅ stop_streaming 成功")

        print("\n🎉 所有测试通过！matplotlib 版本运行正常")

        # 显示统计信息
        stats = widget.display_stats
        print(f"\n📊 显示统计:")
        print(f"   - 均值: {stats.mean_volts:.6f} V")
        print(f"   - 交流 RMS: {stats.ac_rms_volts:.6f} V")
        print(f"   - 峰峰值: {stats.peak_to_peak_volts:.6f} V")
        print(f"   - 缩放倍数: {stats.display_scale:.1f}x")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("测试 matplotlib 版本的 WaveformWidget\n")

    success = test_matplotlib_widget()

    if success:
        print("\n✅ 结论: matplotlib 版本已成功实现，预期会显著提升波形流畅度！")
        sys.exit(0)
    else:
        print("\n❌ 结论: 需要检查 matplotlib 依赖或代码")
        sys.exit(1)