import sys
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import numpy as np
from data_collection import data_collection2  # 你的数据采集函数
from collections import deque
import time

# 配置参数
SAMPLING_RATE = 110  # 1000Hz
DISPLAY_SECONDS = 5   # 显示5秒
BUFFER_SIZE = SAMPLING_RATE * DISPLAY_SECONDS  # 缓冲区大小

class PolarPlotApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("ACC G值表")
        self.resize(800, 800)

        # Set up the main graphics layout
        self.graphWidget = pg.PlotWidget()
        
        # Configure the plot
        self.graphWidget.setAspectLocked()
        self.graphWidget.setRange(xRange=[-2, 2], yRange=[-2, 2])
        self.graphWidget.hideAxis('left')
        self.graphWidget.hideAxis('bottom')

        # Draw the circular grid with labels
        self.draw_circle_grid()

        # Initialize point plot
        self.point_plot = self.graphWidget.plot([], [], pen=None, symbol='o', symbolBrush='r', symbolSize=10)

        # Set up a timer to update the point
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_point)
        self.timer.start(1)  # Update every millisecond

    def draw_circle_grid(self):
        # Draw circles with radius 0.5, 1.0, 1.5, 2.0
        for r in np.arange(0.5, 2.5, 0.5):
            circle = QtWidgets.QGraphicsEllipseItem(-r, -r, r*2, r*2)
            if r == 2.0:
                circle.setPen(pg.mkPen('blue', width=2))
            elif r == 1.0:
                circle.setPen(pg.mkPen('yellow', width=2))
            else:
                circle.setPen(pg.mkPen('gray'))
            self.graphWidget.addItem(circle)

            # Add radius label on the circle
            label = pg.TextItem(text=f"{r}", color='red', anchor=(0.5, 0.5))
            label.setPos(r / np.sqrt(2), r / np.sqrt(2))
            self.graphWidget.addItem(label)

        # Add crosshair lines
        self.graphWidget.addLine(x=0, pen=pg.mkPen('gray'))
        self.graphWidget.addLine(y=0, pen=pg.mkPen('gray'))

    def update_point(self):
        # Simulate reading new data
        data = self.get_new_data()
        x = data.get("accG")[0]
        z = data.get("accG")[2]

        # Update point position
        self.point_plot.setData([x], [z])

    def get_new_data(self):
        """获取新数据点"""
        data = data_collection2()
        return data

class RealTimePlot(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        
        # 创建图形窗口
        self.graph = pg.PlotWidget()
        
        # 图形配置
        self.graph.setLabel('left', '数值')
        self.graph.setLabel('bottom', '时间 (s)')
        self.graph.showGrid(x=True, y=True, alpha=0.3)
        self.graph.setYRange(-1, 1)  # 初始Y轴范围
        
        # 曲线配置
        self.curves = {
            'finalFF': self.graph.plot(pen='r', name='力反馈 (N)')
        }
        
        # 数据缓冲区
        self.timestamps = deque(maxlen=BUFFER_SIZE)
        self.data_buffers = {
            'finalFF': deque(maxlen=BUFFER_SIZE)
        }
        self.elapsed_timer = QtCore.QElapsedTimer()
        self.elapsed_timer.start()

        # 定时器
        self.timer = QtCore.QTimer()
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
            self.graph.setYRange(-max_abs*1.1, max_abs*1.1)

class MainApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("综合显示")
        self.resize(1800, 800)

        # 使用 QSplitter 创建左右布局
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)

        # 左边的 G 值图
        self.polarPlot = PolarPlotApp()
        splitter.addWidget(self.polarPlot.graphWidget)

        # 右边的力反馈曲线图
        self.realTimePlot = RealTimePlot()
        splitter.addWidget(self.realTimePlot.graph)

        # 新增垂直进度条
        self.create_progress_bars(splitter)

        # 设置布局
        layout = QtWidgets.QHBoxLayout()
        layout.addWidget(splitter)
        self.setLayout(layout)

    def create_progress_bars(self, splitter):
        # 创建容器小部件
        progressContainer = QtWidgets.QWidget()
        progressLayout = QtWidgets.QVBoxLayout()

        # 创建进度条
        self.brakeBar = self.create_progress_bar('刹车', 'red')
        self.throttleBar = self.create_progress_bar('油门', 'green')
        self.clutchBar = self.create_progress_bar('离合', 'blue')
        self.handbrakeBar = self.create_progress_bar('手刹', 'purple')

        # 添加到布局
        progressLayout.addWidget(self.brakeBar)
        progressLayout.addWidget(self.throttleBar)
        progressLayout.addWidget(self.clutchBar)
        progressLayout.addWidget(self.handbrakeBar)

        progressContainer.setLayout(progressLayout)
        splitter.addWidget(progressContainer)

    def create_progress_bar(self, label, color):
        progressBar = QtWidgets.QProgressBar()
        progressBar.setOrientation(QtCore.Qt.Vertical)
        progressBar.setMaximum(100)
        progressBar.setValue(0)
        progressBar.setFormat(label + " %p%")
        progressBar.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; }}")
        return progressBar

if __name__ == '__main__':
    from PyQt5 import QtCore, QtWidgets
    # 关键DPI设置（必须在QApplication之前）
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
    
    app = QtWidgets.QApplication(sys.argv)
    main = MainApp()
    main.show()
    sys.exit(app.exec_())