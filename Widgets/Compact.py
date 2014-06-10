import os
import copy

from PyQt4 import QtGui
from PyQt4 import QtCore

class MyLabel(QtGui.QLabel):
    droppedSignal = QtCore.pyqtSignal(tuple)

    def __init__(self, normal, scaled, service, state='Idle'):
        QtGui.QLabel.__init__(self)

        self.normal = normal
        self.scaled = scaled
        self.state =  state
        self.setMouseTracking(True)
        self.setAcceptDrops(True)
        self.setPixmap(self.normal)

        self.roundness = 20.
        self.gradient_radius = 40
        self.active_color = QtGui.QColor(74, 209, 59, 255)
        self.error_color = QtGui.QColor(255, 0, 0, 255)

        self.service = service

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)

        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtCore.Qt.NoPen)
        center = QtCore.QPointF(event.rect().center())

        gradient = QtGui.QRadialGradient(center, self.gradient_radius)
        if self.state == 'Active':
            gradient.setColorAt(0.0, self.active_color)
        elif self.state == 'Error':
            gradient.setColorAt(0.0, self.error_color)
        else:
            gradient.setColorAt(0.0, QtCore.Qt.transparent)
        gradient.setColorAt(1.0, QtCore.Qt.transparent)
        painter.setBrush(gradient)

        painter.drawRoundedRect(0, 0, self.width(), self.height(), self.roundness, self.roundness)

        QtGui.QLabel.paintEvent(self, event)

    def set_state(self, state):
        #One of Idle, Active, Error
        self.state = state
        self.repaint()

    def dragEnterEvent(self, event):
        event.accept()

        self.setPixmap(self.scaled)

    def dragLeaveEvent(self, event):
        event.accept()

        self.setPixmap(self.normal)

    def dropEvent(self, e):
        e.accept()
        self.setPixmap(self.normal)

        m = e.mimeData()
        self.droppedSignal.emit((self.service, m))

class MyFrame(QtGui.QFrame):
    def __init__(self, parent=None):
        QtGui.QFrame.__init__(self, parent)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)

        painter.setRenderHint(QtGui.QPainter.Antialiasing);
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor(40,43,49, 205))

        painter.drawRoundedRect(0, 0, self.width(), self.height(), 15., 15.)

class CompactWindow(QtGui.QWidget):

    dropbox = r'../images/dropbox-{}.png'
    googledrive = r'../images/googledrive-{}.png'
    pithos = r'../images/pithos-{}.png'

    def __init__(self, services, orientation, pos, screen_id, parent=None):
        super(CompactWindow, self).__init__(parent, QtCore.Qt.Window)

        #Data
        self.items = {} #Key is a service.
        self.move_pos = None
        self.used_services = services
        self.orientation = orientation
        self.mask = ord('H')^ord('V')

        self.dropbox_images = []
        self.pithos_images = []
        self.googledrive_images = []
        for t in ['normal', 'scaled']:
            self.dropbox_images.append(QtGui.QPixmap(self.dropbox.format(t)))
            self.pithos_images.append(QtGui.QPixmap(self.pithos.format(t)))
            self.googledrive_images.append(QtGui.QPixmap(self.googledrive.format(t)))
        #End data

        self.setAutoFillBackground(False)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)# |
                            #QtCore.Qt.WindowStaysOnTopHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        d = QtGui.QApplication.desktop()
        pos_rect = d.availableGeometry(screen_id).adjusted(pos[0], pos[1], 0, 0)
        self.move(pos_rect.topLeft())

        self.main_frame = MyFrame(self)

        size = self.size()
        self.main_frame.resize(size.width(), size.height())

        #main layout
        layout = getattr(QtGui, 'Q{}BoxLayout'.format(orientation))()
        for s in self.used_services:
            layout.addWidget(self.create_item(s))

        layout.setAlignment(QtCore.Qt.AlignCenter)
        self.main_frame.setLayout(layout)

        self.resize_frame()

    def resize_frame(self):
        if self.orientation == 'H':
            self.main_frame.resize(len(self.used_services)*80, 87)
            self.resize(len(self.used_services)*80, 87)
        else:
            self.main_frame.resize(87, len(self.used_services)*80)
            self.resize(87, len(self.used_services)*80)

    def mouseDoubleClickEvent(self, event):
        #Remove the old layout by reparenting it.
        curr_layout = self.main_frame.layout()
        for s in self.used_services:
            curr_layout.removeWidget(self.items[s])
        QtGui.QWidget().setLayout(self.main_frame.layout())

        #Add the new layout.
        new_layout = QtGui.QHBoxLayout() if self.orientation == 'V' else \
                     QtGui.QVBoxLayout()

        for s in self.used_services:
            new_layout.addWidget(self.items[s])
        new_layout.setAlignment(QtCore.Qt.AlignCenter)
        self.main_frame.setLayout(new_layout)

        self.orientation = chr(self.mask^ord(self.orientation))
        self.resize_frame()

    def get_window_info(self):
        d = QtGui.QApplication.desktop()
        pos = [self.pos().x(), self.pos().y()]
        screen_id = d.screenNumber(self)

        return [pos, screen_id, self.orientation]

    def set_service_states(self, new_states):
        if not new_states:
            for s in self.used_services:
                self.items[s].set_state('Idle')
            return
        used_services = set(self.used_services)
        update_services = set(zip(*new_states)[0])
        #Remove the states that dont exist anymore,
        #Possible race condition which occurs when the user removes a service.
        tmp = copy.copy(update_services)
        for s in tmp:
            if s not in used_services:
                update_services.remove(s)
                c = copy.copy(new_states)
                to_delete = filter(lambda x: x[0] == s, new_states)
                [new_states.remove(state) for state in c if state in to_delete]

        for service in used_services.difference(update_services):
            self.items[service].set_state('Idle')

        for service, state in new_states:
            self.items[service].set_state(state)

    def add_item(self, service):
        start = self.main_frame.geometry()
        self.used_services.append(service)
        self.main_frame.layout().addWidget(self.create_item(service))

        if self.orientation == 'H':
            end = start.adjusted(0, 0, 80, 0)
            self.resize(self.width() + 80, self.height())
        else:
            end = start.adjusted(0, 0, 0, 80)
            self.resize(self.width(), self.height() + 80)

        self.animate(start, end)

    def remove_item(self, service):
        start = self.main_frame.geometry()
        self.main_frame.layout().removeWidget(self.items[service])
        self.items[service].close()

        self.used_services.remove(service)
        del self.items[service]

        if self.orientation == 'H':
            end = start.adjusted(0, 0, -80, 0)
            self.resize(self.width() - 80, self.height())
        else:
            end = start.adjusted(0, 0, 0, -80)
            self.resize(self.width(), self.height() - 80)

        self.animate(start, end, dur=200)

    def create_item(self, service):
        e = getattr(self, '{}_images'.format(service.lower()))
        label = MyLabel(e[0], e[1], service)

        self.items[service] = label
        return label

    def animate(self, start, end, dur=400):
        self.anim = QtCore.QPropertyAnimation(self.main_frame, 'geometry')
        self.anim.setDuration(dur)
        self.anim.setStartValue(start)
        self.anim.setEndValue(end)
        self.anim.start()

    def mousePressEvent(self, event):
        self.move_pos = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() & QtCore.Qt.LeftButton:
            diff = event.pos() - self.move_pos
            new_pos = self.pos() + diff

            self.move(new_pos)

if __name__ == '__main__':
    import sys

    app = QtGui.QApplication(sys.argv)
    window = CompactWindow(['Dropbox', 'GoogleDrive', 'Pithos'], 'V', (100, 100), 0)
    window.show()

    sys.exit(app.exec_())