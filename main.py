import logging
import serial
import signal
import sys
import time

from config import LOG_LEVEL, GUN_H_CALIBRATION, GUN_V_CALIBRATION, BURST_NUM
logging.basicConfig(level=LOG_LEVEL, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logger = logging.getLogger(__name__)
import tty
import termios
import threading
import math
import struct
from alarm import AlarmAgent
#from radar import RadarInterface
import sys
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
)
from PyQt6.QtCore import QThread, QEvent, QTimer
from PyQt6.QtGui import QPen, QColor, QFont
from rd_03d import RD03D
from rd_03d_json import RD03DJson
from arduino_gun.arduino_gun import ArduinoGun
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene
from stick_figure import StickFigure
from alarm_generator import AssetMonitor


USE_MULTI_TARGET_DETECTION = False

# Configure the serial port
class RadarModule(QMainWindow):
    def __init__(self):
        super().__init__()
        #self.rd03d = RD03D()
        self.rd03d = RD03DJson()
        self.size = 1980
        #self.radar_interface = RadarInterface() 
        """
        if USE_MULTI_TARGET_DETECTION:
            self.rd03d.send_command(Multi_Target_Detection_CMD)
        else:
            self.rd03d.send_command(Single_Target_Detection_CMD)
        """

        self.alarm_stream_data = ""

        #self.asset_monitor = AssetMonitor(self.size/2, self.size/2)
        #self.start_radar_interface()

        #self.add_target_to_radar_interface(100, 100, 0, 0)

        #self.alarm_agent = AlarmAgent()
        self.keep_running = True
        #self.start_quit_listener()
        self.rd03d_thread = threading.Thread(target=self.rd03d.read_data, daemon=True)
        self.rd03d_thread.start()

        self.rd03d.item_added.connect(self.handle_item_added)
        self.last_angle = None
        try:
            self.arduino_gun = ArduinoGun()
        except Exception as e:
            logger.warning("Arduino gun not available: %s", e)
            self.arduino_gun = None
        self.gun_enabled = False
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Radar Gun Control")

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 8)

        self.radar_view = QGraphicsView()
        self.scene = QGraphicsScene(self)
        self.radar_view.setScene(self.scene)

        # Set the scene rect to ensure the circle is within view
        self.scene.setSceneRect(0, 0, self.size, self.size)

        self.status_label = QLabel()
        self.action_label = QLabel("")
        self.action_label.setMinimumWidth(160)
        self.action_label.setStyleSheet(
            "QLabel { color: #ff1744; font-weight: bold; font-size: 22px; }"
        )
        self.start_button = QPushButton("Start")
        self.start_button.setMinimumWidth(120)
        self.start_button.setStyleSheet(
            "QPushButton { background-color: #2e7d32; color: white; font-weight: bold; padding: 8px; }"
            "QPushButton:disabled { background-color: #555; color: #aaa; }"
        )
        self.start_button.clicked.connect(self.start_gun)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setMinimumWidth(120)
        self.stop_button.setStyleSheet(
            "QPushButton { background-color: #c62828; color: white; font-weight: bold; padding: 8px; }"
            "QPushButton:disabled { background-color: #555; color: #aaa; }"
        )
        self.stop_button.clicked.connect(self.stop_gun)

        controls = QHBoxLayout()
        controls.addWidget(self.status_label)
        controls.addStretch()
        controls.addWidget(self.action_label)
        controls.addStretch()
        controls.addWidget(self.start_button)
        controls.addWidget(self.stop_button)

        layout.addWidget(self.radar_view, stretch=1)
        layout.addLayout(controls)
        self.setCentralWidget(central)

        self.draw_lines()
        self.draw_meters()
        self.draw_circle(self.size/2, self.size/2)
        self._update_gun_controls()
        self.show()

    def start_gun(self):
        if not self.arduino_gun:
            logger.warning("Cannot start: Arduino gun not available")
            return
        self.gun_enabled = True
        logger.info("Gun operation started")
        self._update_gun_controls()

    def stop_gun(self):
        self.gun_enabled = False
        logger.info("Gun operation stopped (moving and shooting disabled)")
        self._update_gun_controls()

    def _update_gun_controls(self):
        available = self.arduino_gun is not None
        self.start_button.setEnabled(available and not self.gun_enabled)
        self.stop_button.setEnabled(available and self.gun_enabled)
        if not available:
            self.status_label.setText("Gun: UNAVAILABLE")
            self._set_action("")
        elif self.gun_enabled:
            self.status_label.setText("Gun: RUNNING")
        else:
            self.status_label.setText("Gun: STOPPED")
            self._set_action("")

    def _set_action(self, text):
        self.action_label.setText(text)
        QApplication.processEvents()

    def handle_item_added(self, x, y, distance, angle):
        #print(f"Item added: {x, y, distance, angle}")
        self.delete_previous_circle()
        #self.draw_circle(x+self.size/2, y)
        self.scene.addItem(StickFigure(int(x+self.size/2), int(y)))
        #self.asset_monitor.add_coordinates(x, y)

        if not self.arduino_gun or not self.gun_enabled:
            return
        if self.last_angle != angle:
            self.last_angle = angle
            try:
                logger.debug("Moving gun to angle: %s, distance: %s", angle, distance)
                v = int(distance/100) + GUN_V_CALIBRATION
                callicrated_angle = 180 - angle + GUN_H_CALIBRATION
                self.arduino_gun.move(h=int(callicrated_angle), v=v)
            except Exception as e:
                logger.error("Failed to send angle to arduino gun: %s", e)
        elif self.last_angle is not None:
            try:
                logger.info("Target still at angle %s — shooting", angle)
                self._set_action("Burst")
                #self.arduino_gun.shoot()
                self.arduino_gun.burst_shoot(BURST_NUM)
                #time.sleep(0.5)
                #self.arduino_gun.shoot()
            except Exception as e:
                logger.error("Failed to shoot: %s", e)
            finally:
                self._set_action("")

    def delete_previous_circle(self):
        # Assuming the last added item is the circle to be deleted
        if self.scene.items():
            last_item = self.scene.items()[0]  # Get the last added item
            self.scene.removeItem(last_item)

    def draw_circle(self, x, y, circle_radius=5):
        pen = QPen(QColor("red"))
        circle = self.scene.addEllipse(x, y, circle_radius * 2, circle_radius * 2, pen)


    def draw_lines(self):
       # Draw the radar lines
        center_x = self.size/2
        center_y = self.size/2
        length = 10
        pen = QPen(QColor("white"))

        # Line from bottom center to top left
        line1 = self.scene.addLine(0, self.size, center_x, length, pen)

        # Line from bottom center to top right
        line2 = self.scene.addLine(self.size, self.size, center_x, length, pen)

    def draw_meters(self):
        # Draw meters from top to bottom, every 1 px is 1 cm
        pen = QPen(QColor("gray"))
        for i in range(0, self.size, 10):  # Every 10 pixels (1 cm)
            self.scene.addLine(0, i, self.size, i, pen)
            # Write x cm on the left side of the screen next to each line
            text = f"{i/10} cm"
            self.scene.addText(text).setPos(10, i - 10)

    def start_quit_listener(self):
        return
        quit_thread = threading.Thread(target=self.check_for_quit, daemon=False)
        quit_thread.daemon = True
        quit_thread.start()

    def getch(self):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    def check_for_quit(self):
            ch = self.getch()
            if ch.lower() == 'q':
                self.stop()

    def closeEvent(self, event):
        self.stop()
        event.accept()

    def stop(self):
        if not self.keep_running:
            return
        self.keep_running = False
        logger.info("Shutting down")
        try:
            self.rd03d.stop()
        except Exception as e:
            logger.error("Failed to stop radar: %s", e)
        if self.rd03d_thread.is_alive():
            self.rd03d_thread.join(timeout=2)
        if self.arduino_gun:
            try:
                self.arduino_gun.close()
            except Exception as e:
                logger.error("Failed to close arduino gun: %s", e)
            self.arduino_gun = None
        app = QApplication.instance()
        if app is not None:
            app.quit()


    """
    def add_target_to_radar_interface(self, x, y, distance, angle):
        logger.debug("Adding target to radar interface: %s, %s, %s, %s", x, y, distance, angle)
        self.radar_interface.set_position(x, y)
    """


if __name__ == "__main__":
    app = QApplication(sys.argv)
    radar = RadarModule()

    def handle_signal(signum, _frame):
        logger.info("Received signal %s, shutting down", signal.Signals(signum).name)
        radar.stop()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    # Qt's C++ event loop blocks Python signal handlers unless we wake it.
    signal_timer = QTimer()
    signal_timer.start(200)
    signal_timer.timeout.connect(lambda: None)

    sys.exit(app.exec())