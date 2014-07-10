import sys
import math
from operator import add, sub
from PyQt4 import QtGui, QtCore

ex = None
minimum = -20.0
maximum =  20.0
i = 0

class Gauge(QtGui.QWidget):
    ''' Gauge pointer movement:
        minimum->maximum values: clockwise rotation
    '''
    marker_set = QtCore.pyqtSignal(float)

    def __init__(self, length=300.0, end_angle=300.0, min=-30.0, max=30.0, main_points=10,
                 warning=[], danger=[], multiplier='', units='', description=''):
        super(Gauge, self).__init__()

        self.setFixedSize(300, 300)
        self.setWindowTitle('Nil')
        self.setAutoFillBackground(True)

        self.min = self.curr_value = min
        self.max = max

        self.main_points = main_points
        self.length = length
        self.start_angle = (end_angle + length) % 360
        self.end_angle = end_angle % 360
        self.is_circle = self.start_angle == self.end_angle

        self.gauge_ticks = []
        self.margin = 12
        self.center_radius = 5.0
        self.center = QtCore.QPointF(150.0, 150.0)
        self.bounding_rect = QtCore.QRectF(25.0, 25.0, 250.0, 250.0)
        self.marker_rect = QtCore.QRectF(15.0, 15.0, 270.0, 270.0)
        self.danger = danger
        self.warning = warning

        self.units = units
        self.multiplier = multiplier
        self.description = description

        #Various ui colors
        self.marker_tick_color = QtGui.QPen(QtGui.QColor('#FF9900'), 1.8)

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
        divisor = self.main_points
        if self.start_angle != self.end_angle:
            divisor -= 1

        angle_step = self.length/divisor
        value_step = abs(self.max-self.min)/divisor

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
            angle = self.start_angle - i*angle_step
            value = self.min + i*value_step
            p = QtGui.QPainterPath()
            p.arcMoveTo(self.bounding_rect, angle)
            x, y = p.currentPosition().x(), p.currentPosition().y()
            x_new = x*0.9 + self.center.x()*0.1
            y_new = y*0.9 + self.center.y()*0.1

            x_text = x*0.8 + self.center.x()*0.2 - (text_width(str(round(value, 1)))-10)/2
            y_text = y*0.8 + self.center.y()*0.2 + 4

            #And create the path
            tick_path = QtGui.QPainterPath()
            tick_path.moveTo(x_new, y_new)
            tick_path.lineTo(x, y)

            self.gauge_ticks.append([QtCore.QPointF(x_text, y_text), value, tick_path])

        #Store the tick_length for the marker area
        self.tick_length = math.sqrt((x-x_new)**2+(y-y_new)**2)

    def val2deg(self, value):
        return self.length*((value-self.min)/abs(self.max-self.min))
        
    def val2deg_tuple(self, t):
        return map(self.val2deg, t)

    def deg2val(self, degrees):
        #Convert the given degress relative to the start_angle to
        #the respective value
        return abs(self.max-self.min)*(degrees/self.length)+self.min

    def mouseMoveEvent(self, e):
        #marker_line and marker_value don't exist before the first call of this function
        click_pos = e.posF()

        x_coeff = (click_pos.x() - self.center.x())**2
        y_coeff = (click_pos.y() - self.center.y())**2
        dist = math.sqrt(x_coeff + y_coeff)

        w = self.bounding_rect.width()/2

        if w -  self.tick_length <= dist <= w:
            #Find the angle between the start angle and the click point
            angle = self.angle_from_zero(self.center, click_pos, self.start_angle)
            #Return if the user clicked outside of the allowed range
            if self.deg2val(angle) > self.max or self.deg2val(angle) < self.min:
                return

            self.set_marker(self.deg2val(angle))

    def angle_from_zero(self, p1, p2, offset):
        angle = math.degrees(math.atan2(p1.y()-p2.y(), p2.x()-p1.x()))

        if angle < 0:
            angle += 360
        angle = offset - angle
        if angle < 0:
            angle += 360

        return angle

    def set_marker(self, value):
        #New values: marker_point
        #Emit the new value
        self.marker_value = max(min(value, self.max), self.min)
        self.marker_set.emit(self.marker_value)
        #Rount it for presentation purposes
        self.marker_value = round(self.marker_value, 2)

        #Create the marker line
        p = QtGui.QPainterPath()
        p.arcMoveTo(self.bounding_rect, self.start_angle - self.val2deg(value))
        self.marker_point = p.currentPosition()
        self.draw_marker(y=3)

    def compute_marker_rotation(self):
        #Marker_point is already set and ready for use
        return self.angle_from_zero(self.center, self.marker_point, 90)

    def draw_marker(self, x=0, y=0, size=10):
        poly = QtGui.QPolygonF()
        poly.append(QtCore.QPointF(x-size, y))
        poly.append(QtCore.QPointF(x+size, y))
        poly.append(QtCore.QPointF(x+size, y-size))
        poly.append(QtCore.QPointF(x, y))
        poly.append(QtCore.QPointF(x-size, y-size))
        poly.append(QtCore.QPointF(x-size, y))

        self.marker_line = QtGui.QPainterPath()
        self.marker_line.addPolygon(poly)

        self.update()

    def set_gauge(self, value):
        #Clamp between [min, max]
        self.curr_value = max(min(value, self.max), self.min)

        p = QtGui.QPainterPath()
        p.arcMoveTo(self.bounding_rect, self.start_angle-self.val2deg(self.curr_value))
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

    def _set_bg_color(self):
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
        self._set_bg_color()
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

        #Draw the marker line
        if getattr(self, 'marker_line', None):
            painter.setPen(self.marker_tick_color)
            painter.translate(self.marker_point)
            painter.rotate(self.compute_marker_rotation())
            painter.drawPath(self.marker_line)
            painter.resetTransform()

        #Draw the center circle
        painter.setPen(self.ui_color)
        painter.drawEllipse(self.center.x()-self.center_radius/2, self.center.y()-self.center_radius/2,
                            self.center_radius, self.center_radius)

        #Draw the paths
        painter.setPen(self.ui_color_tick)
        for i, path in enumerate(self.gauge_ticks):
            if not (self.is_circle and i == (len(self.gauge_ticks))):
                painter.drawText(path[0], str(int(path[1])))
 		painter.drawPath(path[2])

        #Draw the text labels
        painter.drawText(QtCore.QPointF(self.center.x()-center_text(str(self.curr_value)), self.center.y()-40), str(self.curr_value))
        painter.drawText(QtCore.QPointF(self.center.x()-center_text(self.multiplier), self.center.y()+20+self.margin), self.multiplier)
        painter.drawText(QtCore.QPointF(self.center.x()-center_text(self.units), self.center.y()+20+self.margin*2), self.units)
        painter.drawText(QtCore.QPointF(self.center.x()-center_text(self.description), self.center.y()+20+self.margin*3), self.description)

        painter.setPen(self.marker_tick_color)
        if getattr(self, 'marker_value', None):
            painter.drawText(QtCore.QPointF(self.center.x()-center_text(str(self.marker_value)), self.center.y()-20), str(self.marker_value))

        QtGui.QWidget.paintEvent(self, event)

def onTimeout():
    global i, minimum
    ex.set_gauge(minimum + i*0.2)
    i += 1
    # if i == 50:
        # ex.set_marker(5.5)

def onClick(val):
    # print val
    pass

if __name__ == '__main__':
    timer = QtCore.QTimer()
    timer.timeout.connect(onTimeout)
    timer.setInterval(50)

    app = QtGui.QApplication(sys.argv)
    ex = Gauge(warning=[(-15, -10), (10, 15)],
               danger=[(-20, -15), (15, 20)],
               description='Pitch',
               multiplier='', units='degrees')
    ex.marker_set.connect(onClick)
    ex.show()
    timer.start()
    sys.exit(app.exec_())
