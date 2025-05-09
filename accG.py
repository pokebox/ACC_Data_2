import sys
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg
import numpy as np
from data_collection import data_collection2

class PolarPlotApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("ACC G值表")
        self.resize(800, 800)
        # Set up the main graphics layout
        self.graphWidget = pg.PlotWidget()
        self.setCentralWidget(self.graphWidget)

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
        y = data.get("accG")[1]
        z = data.get("accG")[2]

        # Update point position
        self.point_plot.setData([x], [z])

    def get_new_data(self):
        """获取新数据点"""
        data = data_collection2()
        return data

if __name__ == '__main__':
    from PyQt5 import QtCore, QtWidgets
    # 关键DPI设置（必须在QApplication之前）
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps)
    app = QtWidgets.QApplication(sys.argv)

    main = PolarPlotApp()
    main.show()

    sys.exit(app.exec_())
