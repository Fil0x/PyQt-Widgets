import sys
import math
from operator import add, sub
from PyQt4 import QtGui, QtCore

ex = None

class Gauge(QtGui.QWidget):
    ''' Gauge pointer movement:
        minimum->maximum values: clockwise rotation
        maximum value > minimum-value
    '''
    def __init__(self, length=300.0, end_angle=300.0, min=0.0, max=1000.0, main_points=10,
                 warning=[], danger=[], multiplier='', units='', description=''):
        super(Gauge, self).__init__()

        self.setFixedSize(300, 300)
        self.move(300, 200)
        self.setWindowTitle('A Magnificent Gauge')
        self.setAutoFillBackground(True)

        self.min = min
        self.curr_value = min
        self.max = max
        self.start_angle = (end_angle + length) % 360
        self.end_angle = end_angle % 360
        self.length = length
        self.main_points = main_points
        self.gauge_ticks = []
        self.bounding_rect = QtCore.QRectF(25.0, 25.0, 250.0, 250.0)
        self.center = QtCore.QPointF(150.0, 150.0)
        self.warning = warning #zones
        self.danger = danger #zones
        self.center_radius = 5.0
        self.margin = 12
        self.units = units
        self.multiplier = multiplier
        self.description = description

        #Various ui colors
        self.ui_color = QtGui.QPen(QtCore.Qt.green, 2.5)
        self.ui_color_tick = QtGui.QPen(QtCore.Qt.green, 1.5)
        self.gauge_color = QtGui.QPen(QtCore.Qt.lightGray, 2)

        self.warning_color = QtGui.QPen(QtCore.Qt.yellow, 2)
        self.warning_bg = QtGui.QRadialGradient(self.center, self.width()/3)
        self.warning_bg.setColorAt(0.0, QtCore.Qt.yellow)
        self.warning_bg.setColorAt(1.0, QtCore.Qt.black)

        self.danger_color = QtGui.QPen(QtCore.Qt.red, 2)
        self.danger_bg = QtGui.QRadialGradient(self.center, self.width()/3)
        self.danger_bg.setColorAt(0.0, QtCore.Qt.red)
        self.danger_bg.setColorAt(1.0, QtCore.Qt.black)

        self.current_bg = QtCore.Qt.black

        self.create_gauge()

    def detect_safe_zones(self):
        r = [(self.min, self.max)]
        unsafe = sorted(self.warning+self.danger, key=lambda i:i[0])

        for i in unsafe:
            temp = []
            for y in r:
                if i[0] > y[1] or i[1] < y[0]:
                    temp.append(y)
                elif i[0]==y[0] and i[1]==y[1]:
                    continue
                elif i[0]>y[0] and i[1]<y[1]:
                    temp.append((y[0], i[0]))
                    temp.append((i[1], y[1]))
                elif i[0]>y[0] and i[1]==y[1]:
                    temp.append((i[0], i[1]))
                elif i[0]==y[0] and i[1]<y[1]:
                    temp.append((i[1], y[1]))
            r = temp

        return r

    def create_gauge(self):
        def text_width(text):
            font = QtGui.QFont()
            metrics = QtGui.QFontMetrics(font)
            return metrics.width(text)
            
        #Main points
        if self.start_angle != self.end_angle:
            angle_step = self.length/(self.main_points-1)
            value_step = abs(self.max-self.min)/(self.main_points-1)
            op = add if self.start_angle > self.end_angle else sub
        else:
            angle_step = self.length/self.main_points
            value_step = abs(self.max-self.min)/self.main_points
            op = add

        #Gauge main line(the circular path)
        #Safe zones
        zones = map(self.val2deg_tuple, self.detect_safe_zones())
        self.gauge_safe = []
        for zone in zones:
            path = QtGui.QPainterPath()
            path.arcMoveTo(self.bounding_rect, self.start_angle-zone[0])
            path.arcTo(self.bounding_rect, self.start_angle-zone[0], -(zone[1]-zone[0]))
            self.gauge_safe.append(path)
        #Warning zones
        warning_zones =  map(self.val2deg_tuple, self.warning)
        self.gauge_warning = []
        for w in warning_zones:
            path = QtGui.QPainterPath()
            path.arcMoveTo(self.bounding_rect, self.start_angle-w[0])
            path.arcTo(self.bounding_rect, self.start_angle-w[0], -(w[1]-w[0]))
            self.gauge_warning.append(path)
        #Danger zones
        danger_zones =  map(self.val2deg_tuple, self.danger)
        self.gauge_danger = []
        for d in danger_zones:
            path = QtGui.QPainterPath()
            path.arcMoveTo(self.bounding_rect, self.start_angle-d[0])
            path.arcTo(self.bounding_rect, self.start_angle-d[0], -(d[1]-d[0]))
            self.gauge_danger.append(path)

        #Initial gauge position
        self.set_gauge(self.curr_value)

        for i in xrange(self.main_points):
            #Find the point on the curve
            angle = op(self.start_angle, i*angle_step)
            value = self.min + i*value_step
            p = QtGui.QPainterPath()
            p.arcMoveTo(self.bounding_rect, angle)
            x, y = p.currentPosition().x(), p.currentPosition().y()
            x_new = x*0.9 + self.center.x()*0.1
            y_new = y*0.9 + self.center.y()*0.1

            x_text = x*0.8 + self.center.x()*0.2 #- (text_width(str(value))/2)*self.polynomial_interpolation(abs(math.radians(angle)))
            y_text = y*0.8 + self.center.y()*0.2
            
            #And create the path
            new = QtGui.QPainterPath()
            new.moveTo(x_new, y_new)
            new.lineTo(x, y)

            self.gauge_ticks.append([QtCore.QPointF(x_text, y_text), value, new])

    def val2deg(self, value):
        return self.length*((value-self.min)/abs(self.max-self.min))

    def val2deg_tuple(self, t):
        return map(self.val2deg, t)

    def set_gauge(self, value):
        #Clamp between [min, max]
        value = max(min(value, self.max), self.min)

        p = QtGui.QPainterPath()
        p.arcMoveTo(self.bounding_rect, self.start_angle-self.val2deg(value))
        x, y = p.currentPosition().x(), p.currentPosition().y()

        self.gauge_line = QtGui.QPainterPath()
        self.gauge_line.moveTo(self.center)
        self.gauge_line.lineTo(x, y)
        self.update()

    def increment_gauge(self, step):
        #Clamp between (min, max)
        self.curr_value = max(min(self.curr_value + step, self.max), self.min)

        p = QtGui.QPainterPath()
        p.arcMoveTo(self.bounding_rect, self.start_angle-self.val2deg(self.curr_value))
        x, y = p.currentPosition().x(), p.currentPosition().y()

        self.gauge_line = QtGui.QPainterPath()
        self.gauge_line.moveTo(self.center)
        self.gauge_line.lineTo(x, y)
        self.update()

    def set_bg_color(self):
        #Determine the zone that the gauge arrow is inside
        #Is it in a warning zone?
        for w in self.warning:
            if w[0] <= self.curr_value <= w[1]:
                self.current_bg = self.warning_bg
                return
        #Or a danger zone?
        for d in self.danger:
            if d[0] <= self.curr_value <= d[1]:
                self.current_bg = self.danger_bg
                return
        #Don't be scared, you're safe!
        self.current_bg = QtCore.Qt.black

    def paintEvent(self, event):
        def center_text(text):
            rect = painter.boundingRect(self.bounding_rect, QtCore.Qt.AlignHCenter, text)
            return rect.width()/2

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        #Draw the background
        self.set_bg_color()
        painter.fillRect(event.rect(), self.current_bg)

        painter.setBrush(QtCore.Qt.transparent)
        painter.setPen(self.gauge_color)
        painter.drawPath(self.gauge_line)

        #Draw the safe zones
        painter.setPen(self.ui_color)
        for s in self.gauge_safe:
            painter.drawPath(s)
        #Draw the warning zones
        painter.setPen(self.warning_color)
        for w in self.gauge_warning:
            painter.drawPath(w)
        #Draw the danger zones
        painter.setPen(self.danger_color)
        for d in self.gauge_danger:
            painter.drawPath(d)

        #Draw the center circle
        painter.setPen(self.ui_color)
        painter.drawEllipse(self.center.x()-self.center_radius/2, self.center.y()-self.center_radius/2,
                            self.center_radius, self.center_radius)

        #Draw the paths
        painter.setPen(self.ui_color_tick)
        for path in self.gauge_ticks:
            painter.drawText(path[0], str(int(path[1])))
            painter.drawPath(path[2])

        #Draw the text labels
        painter.drawText(QtCore.QPointF(self.center.x()-center_text(str(self.curr_value)), 250.0), str(self.curr_value))
        painter.drawText(QtCore.QPointF(self.center.x()-center_text(self.multiplier), 250.0+self.margin), self.multiplier)
        painter.drawText(QtCore.QPointF(self.center.x()-center_text(self.units), 250.0+self.margin*2), self.units)
        painter.drawText(QtCore.QPointF(self.center.x()-center_text(self.description), 250.0+self.margin*3), self.description)

        QtGui.QWidget.paintEvent(self, event)

def onTimeout():
    step = 2
    ex.increment_gauge(step)

if __name__ == '__main__':
    timer = QtCore.QTimer()
    timer.timeout.connect(onTimeout)
    timer.setInterval(50)

    app = QtGui.QApplication(sys.argv)
    ex = Gauge(warning=[(100, 200)],
               danger=[(0, 100)],
               description='Very important description',
               multiplier='x5', units='m/s')
    ex.show()
    timer.start()
    sys.exit(app.exec_())
