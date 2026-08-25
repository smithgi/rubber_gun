import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsView, QGraphicsEllipseItem
from PyQt6.QtCore import Qt, QPointF, QTimer
from PyQt6.QtGui import QBrush, QColor, QPainter
import time


class RadarInterface(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Radar Interface")
        self.setGeometry(100, 100, 1024, 768)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene, self)
        self.setCentralWidget(self.view)

        self.view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.targets = []

        self.target_x = 0
        self.target_y = 0

        self.timer = QTimer(self)  # Create a QTimer
        self.timer.timeout.connect(self.animate_targets)  # Connect the timer to the animation method
        self.timer.start(500)  # Set the timer to trigger every 1000 ms (1 second)

    def set_position(self, x, y):
        self.target_x = x
        self.target_y = y

    def animate_targets(self):
        # Example animation logic: move each target slightly
        for target in self.targets:
            current_pos = target.pos()
            new_pos = QPointF(self.target_x, self.target_y)  # Move target to the right
            target.setPos(new_pos)
        
        self.update_view()  # Refresh the view to show the updated positions


    def test_update_view(self):
        time.sleep(10)
        for i in range(10):
            self.add_target(i*10, 410, 50, 45)
            time.sleep(1)

        self.update_view()

    def update_view(self):
        self.view.viewport().update()  # Refresh the view

    def add_target(self, x, y, distance, angle):
        # Convert the coordinates to the scene's coordinate system
        scene_x = x / 10.0
        scene_y = -y / 10.0  # Invert y-axis for correct orientation

        # Create an ellipse item to represent the target
        target = QGraphicsEllipseItem(-5, -5, 10, 10)
        target.setBrush(QBrush(QColor(255, 0, 0)))
        target.setPos(QPointF(scene_x, scene_y))

        self.scene.addItem(target)
        self.targets.append(target)
        self.view.viewport().update()  # Refresh the view

    def remove_target(self, x, y):
        # Convert the coordinates to the scene's coordinate system
        scene_x = x / 10.0
        scene_y = -y / 10.0  # Invert y-axis for correct orientation    

        for target in self.targets:
            if target.pos() == QPointF(scene_x, scene_y):
                self.scene.removeItem(target)
                self.targets.remove(target)
                self.view.viewport().update()  # Refresh the view
                break


if __name__ == "__main__":
    app = QApplication(sys.argv)
    radar_interface = RadarInterface()
    radar_interface.show()

    # Example usage
    radar_interface.add_target(123, 410, 50, 45)

    sys.exit(app.exec())

