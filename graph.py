import pyqtgraph as pg
from pyqtgraph.Qt import QtWidgets
from PyQt5.QtCore import QTimer, QElapsedTimer

import numpy as np
from collections import deque
import time
from data_collection import data_collection2

# 配置参数
SAMPLING_RATE = 110  # Hz
DISPLAY_SECONDS = 5   # 显示时长（秒）
BUFFER_SIZE = SAMPLING_RATE * DISPLAY_SECONDS  # 10000点缓冲区

class RealTimePlot(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 主窗口设置
        self.setWindowTitle(f"ACC力反馈数据实时显示")
        self.resize(1900, 1000)
        
        # 创建图形窗口
        self.graph = pg.PlotWidget()
        self.setCentralWidget(self.graph)
        
        # 图形配置
        self.graph.setLabel('left', '数值')
        self.graph.setLabel('bottom', '时间 (s)')
        self.graph.showGrid(x=True, y=True, alpha=0.3)
        self.graph.setYRange(-1, 1)  # 初始Y轴范围
        
        # 曲线配置
        self.curves = {
            #'steerAngle': self.graph.plot(pen='b', name='转向角度 (deg)'),
            'finalFF': self.graph.plot(pen='r', name='力反馈 (N)')
        }
        
        # 数据缓冲区
        self.timestamps = deque(maxlen=BUFFER_SIZE)
        self.data_buffers = {
            #'steerAngle': deque(maxlen=BUFFER_SIZE),
            'finalFF': deque(maxlen=BUFFER_SIZE)
        }
        self.elapsed_timer = QElapsedTimer()
        self.elapsed_timer.start()
        # 定时器
        # self.timer = pg.QtCore.QTimer()
        # self.timer.timeout.connect(self.update)
        # self.timer.start(1)  # 1ms刷新
                # 定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(1)  # 1ms刷新
        
        # 记录起始时间
        self.start_time = time.time()
    
    def get_new_data(self):
        """获取新数据点"""
        data = data_collection2()
        data["timestamp"] = time.time() - self.start_time
        return data
    
    def update(self):
        if self.elapsed_timer.elapsed() < 1:
            return
        self.elapsed_timer.restart()
        # 获取新数据
        new_data = self.get_new_data()
        current_time = new_data["timestamp"]
        
        # 存储数据
        self.timestamps.append(current_time)
        for name in self.curves:
            self.data_buffers[name].append(new_data[name])
        
        # 更新曲线
        for name, curve in self.curves.items():
            curve.setData(self.timestamps, self.data_buffers[name])
        
        # 自动滚动X轴
        if current_time > DISPLAY_SECONDS:
            self.graph.setXRange(current_time - DISPLAY_SECONDS, current_time)
        
        # 自动调整Y轴（对称范围）
        if self.data_buffers['finalFF']:
            all_values = np.concatenate([np.array(buf) for buf in self.data_buffers.values()])
            max_abs = max(np.min(np.abs(all_values)), np.max(np.abs(all_values)))  # 防止归零
            print(f"Current Time: {current_time:.2f}s Max Abs Value: {max_abs}, len: {len(all_values)}")
            self.graph.setYRange(-max_abs*1.1, max_abs*1.1)

# 启动应用
if __name__ == "__main__":
    from PyQt5 import QtCore, QtWidgets
    # DPI设置（必须在QApplication之前）
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
    
    app = QtWidgets.QApplication([])
    window = RealTimePlot()
    window.show()
    app.exec_()