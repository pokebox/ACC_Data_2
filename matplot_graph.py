from time import time, sleep
from collections import deque
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from data_collection import data_collection2  # 你的数据采集函数

# 配置参数
SAMPLING_RATE = 1000  # 1000Hz采样率
DISPLAY_SECONDS = 10   # 显示10秒数据
BUFFER_SIZE = SAMPLING_RATE * DISPLAY_SECONDS  # 10000点缓冲区

# 性能优化配置
plt.style.use('fast')  # 使用轻量级样式
plt.rcParams['path.simplify'] = False      # 禁用路径简化
plt.rcParams['path.simplify_threshold'] = 0  # 完全禁用简化
plt.rcParams['agg.path.chunksize'] = 10000  # 提高渲染性能

# 创建图形
fig, ax = plt.subplots(figsize=(15, 6))
ax.set_title(f'datashow (raw {SAMPLING_RATE}Hz Data)', fontsize=12)
ax.set_xlabel('Time (s)', fontsize=10)
ax.set_ylabel('Value', fontsize=10)
ax.grid(True, linestyle=':', alpha=0.5)

# 曲线配置
curves_config = {
    'steerAngle': {'color': 'b', 'line': None, 'label': 'Axis (deg)'},
    'finalFF': {'color': 'r', 'line': None, 'label': 'FFB (N)'}
}

# 初始化曲线（禁用抗锯齿）
for name, config in curves_config.items():
    config['line'], = ax.plot([], [], 
                            color=config['color'], 
                            linewidth=0.5,  # 细线更精确
                            antialiased=False,  # 关闭抗锯齿
                            label=config['label'])
ax.legend(fontsize=8)

# 数据存储优化（预分配内存）
timestamps = deque(maxlen=BUFFER_SIZE)
curve_data = {name: deque(maxlen=BUFFER_SIZE) for name in curves_config}

# 高精度时间戳生成
def get_timestamp():
    """获取毫秒级时间戳（相对程序启动时间）"""
    return time()  # 直接使用浮点秒数，避免字符串转换开销

# 数据获取函数
def get_new_data():
    """获取新数据点（包含优化后的时间戳处理）"""
    data = data_collection2()  # 你的原始数据采集
    data["timestamp"] = get_timestamp()  # 添加高精度时间戳
    return data

# 对称Y轴设置（保持0点居中）
def set_symmetric_y_axis(ax, margin=0.1):
    if not any(curve_data.values()): return
    
    # 计算所有通道的最大绝对值
    max_abs = max(
        max(abs(val) for val in data) 
        for data in curve_data.values() 
        if data
    )
    
    if max_abs > 0:
        limit = max_abs * (1 + margin)
        ax.set_ylim(-limit, limit)
        # 设置合理刻度
        ax.yaxis.set_major_locator(plt.MultipleLocator(max_abs/2))
        ax.yaxis.set_minor_locator(plt.MultipleLocator(max_abs/4))

# 初始化函数
def init():
    ax.set_xlim(0, DISPLAY_SECONDS)
    set_symmetric_y_axis(ax)
    return [config['line'] for config in curves_config.values()]

# 关键优化：原始数据更新
def raw_data_update(frame):
    # 获取新数据
    new_data = get_new_data()
    current_time = new_data['timestamp']
    
    # 初始化参考时间
    if not timestamps:
        global start_time
        start_time = current_time
    
    # 存储数据（相对时间）
    timestamps.append(current_time - start_time)
    for name in curves_config:
        curve_data[name].append(new_data[name])
    
    # 滚动时间窗口
    if timestamps:
        latest_time = timestamps[-1]
        if latest_time > DISPLAY_SECONDS:
            ax.set_xlim(latest_time - DISPLAY_SECONDS, latest_time)
    
    # 更新曲线（直接传递原始数据）
    for name, config in curves_config.items():
        config['line'].set_data(timestamps, curve_data[name])
    
    # 动态调整Y轴
    set_symmetric_y_axis(ax)
    
    return [config['line'] for config in curves_config.values()]

# 运行动画
try:
    ani = animation.FuncAnimation(
        fig, raw_data_update,
        init_func=init,
        interval=1,  # 1ms刷新间隔
        blit=True,
        cache_frame_data=False  # 防止内存泄漏
    )
    plt.tight_layout() 
    plt.show()
except KeyboardInterrupt:
    print("程序被用户终止")