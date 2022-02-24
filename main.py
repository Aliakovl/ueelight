import sys
from PySide6.QtCore import *
from PySide6.QtWidgets import *
from PySide6.QtGui import *
from yeelight import Bulb
from yeelight import discover_bulbs


class PyToggle(QCheckBox):
    def __init__(
            self,
            bulb,
            width=60,
            bg_color="#3C3C3C",
            circle_color="#CCC",
            active_color="#7850BE",
            animation_curve=QEasingCurve.OutCirc,
            init_state=False,
            setValue=None,
    ):
        QCheckBox.__init__(self)
        self.setFixedSize(width, 28)
        self.bulb = bulb
        self.setCursor(Qt.PointingHandCursor)
        self._bg_color = bg_color
        self._circle_color = circle_color
        self._active_color = active_color
        self.setValue = setValue
        self._circle_position = self.width() - 26 if init_state else 3
        self.animation = QPropertyAnimation(self, b"circle_position", self)
        self.animation.setEasingCurve(animation_curve)
        self.animation.setDuration(500)
        self.clicked.connect(self.turn)

    @Property(float)
    def circle_position(self):
        return self._circle_position

    @circle_position.setter
    def circle_position(self, pos):
        self._circle_position = pos
        self.update()

    def turn(self):
        self.animation.stop()
        if self.isChecked():
            self.animation.setEndValue(self.width() - 26)
        else:
            self.animation.setEndValue(3)
        self.animation.start()
        self.bulb.toggle()
        self.setValue()

    def hitButton(self, pos: QPoint):
        return self.contentsRect().contains(pos)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(Qt.NoPen)
        if not self.isChecked():
            p.setBrush(QColor(self._bg_color))
            p.drawRoundedRect(0, 0, self.width(), self.height(), self.width() / 6, self.width() / 6)
            p.setBrush(QColor(self._circle_color))
            p.drawEllipse(self._circle_position, 3, 22, 22)
            p.end()
        else:
            p.setBrush(QColor(self._active_color))
            p.drawRoundedRect(0, 0, self.width(), self.height(), self.width() / 6, self.width() / 6)
            p.setBrush(QColor(self._circle_color))
            p.drawEllipse(self._circle_position, 3, 22, 22)
            p.end()


class Form(QDialog):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        self.setMinimumSize(400, 100)
        icon = QIcon()
        icon.addFile("yeelight-logo.svg")
        self.setWindowIcon(icon)
        self.setMaximumSize(400, 100)
        self.setWindowTitle("Yeelight")
        layout = QHBoxLayout(self)
        self.slider = QSlider(orientation=Qt.Orientation.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(100)
        self.slider.setMinimumSize(300, 28)
        self.slider.setStyleSheet('''
            QSlider::groove:horizontal {
                border-radius: 10px;
                height: 28px;
                margin: 0px;
                background-color: rgb(40,40,40);
            }
            QSlider::groove:horizontal:hover {
                background-color: rgb(50,50,50);
            }
            QSlider::handle:horizontal {
                background-color: rgb(120, 80, 190);
                border: none;
                height: 28px;
                width: 28px;
                margin: 0px;
                border-radius: 10px;
            }
            QSlider::handle:horizontal:hover {
                background-color: rgb(130, 90, 200);
            }
        ''')
        self.bulb = Bulb(self.get_ip(), effect="sudden", duration=10000)
        bright, power = self.initValue()
        if not bright and not power:
            self.button = PyToggle(init_state=False, setValue=1, bulb=self.bulb)
            self.button.setDisabled(True)
            self.slider.setDisabled(True)
            layout.addWidget(self.slider, Qt.AlignTop, Qt.AlignLeft)
            layout.addWidget(self.button, Qt.AlignTop, Qt.AlignRight)
            return

        self.button = PyToggle(init_state=power, setValue=self.setValue, bulb=self.bulb)

        self.button.setCheckState(Qt.CheckState.Checked if power else Qt.CheckState.Unchecked)
        self.slider.setValue(bright)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(5)
        layout.addWidget(self.slider, Qt.AlignTop, Qt.AlignLeft)
        layout.addWidget(self.button, Qt.AlignTop, Qt.AlignRight)
        self.slider.sliderReleased.connect(self.setValue)
        self.setLayout(layout)

    def setValue(self):
        value = self.slider.value()
        self.bulb.set_brightness(value)

    def initValue(self):
        try:
            power = self.bulb.get_properties()['power']
            bright = self.bulb.get_properties()['bright']
            return int(bright), power == 'on'
        except Exception:
            return 0, 0

    def get_ip(self):
        with open("ip", 'r+') as ip_file:
            ip = ip_file.read()
            bulb = Bulb(ip)
            if bulb.get_capabilities() is None:
                db = discover_bulbs()
                ip_file.seek(0)
                ip_file.write(db[0]['ip'])
                ip_file.truncate()
                return db[0]['ip']
            return ip


if __name__ == '__main__':
    app = QApplication(sys.argv)
    form = Form()
    form.setStyleSheet('''
        QDialog {
            background: rgb(30, 30, 30);        
        }
    ''')
    form.show()
    sys.exit(app.exec())
