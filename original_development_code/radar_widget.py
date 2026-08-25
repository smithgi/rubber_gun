import logging

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
    QHBoxLayout,
    QGraphicsView,
    QGraphicsScene,
    QGraphicsLineItem,
    QGraphicsEllipseItem,
    QGraphicsTextItem,
    QGraphicsItem,
    
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QPen, QColor

logger = logging.getLogger(__name__)



class RadarWidget(QWidget):
    item_added = pyqtSignal(str)  # Signal to communicate with main.py
    #self.item_added.emit(item_text) # Emit signal

    def __init__(self, parent=None):
        super().__init__(parent)

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.radar_view = QGraphicsView()
        self.scene = QGraphicsScene(self)
        self.radar_view.setScene(self.scene)

        # Draw the radar lines
        center_x = 512
        center_y = 512
        length = 200
        pen = QPen(QColor("white"))

        # Line from bottom center to top left
        line1 = self.scene.addLine(center_x, center_y, center_x - length, center_y - length, pen)

        # Line from bottom center to top right
        line2 = self.scene.addLine(center_x, center_y, center_x + length, center_y - length, pen)

        layout.addWidget(self.radar_view)
        self.setLayout(layout)
        logger.debug("RadarWidget initialized")