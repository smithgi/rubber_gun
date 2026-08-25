from PyQt6.QtWidgets import QGraphicsItem
from PyQt6.QtGui import QPainter, QPen, QColor
from PyQt6.QtCore import QRectF


class StickFigure(QGraphicsItem):
    def __init__(self, x=0, y=0):
        super().__init__()
        self.x = x
        self.y = y

    def boundingRect(self) -> QRectF:
        # Define the bounding rectangle for the stick figure
        return QRectF(self.x, self.y, 32, 32)

    def paint(self, painter: QPainter, option, widget=None):
        # Set up a QPainter to draw the stick figure in white
        pen = QPen(QColor("red"))
        pen.setWidth(1)
        painter.setPen(pen)

        # Draw head: a circle with bounding rectangle at (x+13,y+2) with width and height 6
        painter.drawEllipse(self.x + 13, self.y + 2, 6, 6)

        # Draw body: a vertical line starting from the bottom of the head (y+8) to y+20
        painter.drawLine(self.x + 16, self.y + 8, self.x + 16, self.y + 20)

        # Draw arms: a horizontal line crossing the body (from x+10 to x+22 at y+12)
        painter.drawLine(self.x + 10, self.y + 12, self.x + 22, self.y + 12)

        # Draw hands: small circles at the end of each arm
        painter.drawEllipse(self.x + 9, self.y + 11, 2, 2)  # Left hand
        painter.drawEllipse(self.x + 21, self.y + 11, 2, 2)  # Right hand

        # Draw legs: two diagonal lines from the body bottom (y+20) to near the bottom of the pixmap
        painter.drawLine(self.x + 16, self.y + 20, self.x + 12, self.y + 30)
        painter.drawLine(self.x + 16, self.y + 20, self.x + 20, self.y + 30)