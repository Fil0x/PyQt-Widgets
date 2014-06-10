import sys

from util import shorten_str

from PyQt4 import QtGui
from PyQt4 import QtCore

'''
ISSUE: if the list gets updated while the mouse is over an element,
it will be moved down but the click will still copy the share of that element.
'''
class ListViewModel(QtCore.QAbstractListModel):

    def __init__(self, data, max_count=5, parent=None, *args):
        QtCore.QAbstractListModel.__init__(self, parent, *args)
        self.data = data
        self.max_count = max_count

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.data)

    def data(self, index, role):
        if index.isValid() and role == QtCore.Qt.DisplayRole:
            return QtCore.QVariant(self.data[index.row()])
        else:
            return QtCore.QVariant()

    def removeAll(self):
        self.beginRemoveRows(QtCore.QModelIndex(), 0, self.max_count - 1)
        del self.data[:]
        self.endRemoveRows()

    def addNewElements(self, items):
        ''' [[img, filename, sharelink]...] '''
        if len(items) >= self.max_count:
            self.beginRemoveRows(QtCore.QModelIndex(), 0, self.max_count - 1)
            del self.data[:]
            self.endRemoveRows()
        elif (len(self.data) + len(items)) > self.max_count:
            begin_row = self.max_count - len(items)
            end_row = len(self.data) - 1
            self.beginRemoveRows(QtCore.QModelIndex(), begin_row, end_row)
            self.data = self.data[:begin_row]
            self.endRemoveRows()

        self.beginInsertRows(QtCore.QModelIndex(), 0, len(items) - 1)
        for i in items:
            self.data.insert(0, i)

        self.endInsertRows()

class ListItemDelegate(QtGui.QStyledItemDelegate):

    sharelink_path = r'../images/popup-sharelink.png'
    sharelink_pos = QtCore.QPoint(219, 3)

    def __init__(self, device, font, share_signal):
        QtGui.QStyledItemDelegate.__init__(self, device)

        self.font = font
        self.share_signal = share_signal
        self.cursor_changed = False
        self.mouse_pressed = False
        self.brush = QtGui.QBrush(QtGui.QColor('#E5FFFF'))
        self.sharelink_img = QtGui.QImage(self.sharelink_path)
        self.date_color = QtGui.QColor(QtCore.Qt.black)
        self.date_color.setAlpha(80)

    def paint(self, painter, option, index):
        painter.save()
        sharelink_rect = self.sharelink_img.rect().translated(self.sharelink_pos.x(),
                                            option.rect.top() + self.sharelink_pos.y())
        model = index.model()
        d = model.data[index.row()]

        if option.state & QtGui.QStyle.State_MouseOver:
            painter.fillRect(option.rect, self.brush)

        painter.translate(option.rect.topLeft())
        painter.setClipRect(option.rect.translated(-option.rect.topLeft()))
        painter.setFont(self.font)
        painter.drawImage(QtCore.QPoint(5, 4), d[0])
        painter.drawText(QtCore.QPoint(40, 15), shorten_str(d[1], 35))
        painter.setPen(self.date_color)
        painter.drawText(QtCore.QPoint(40, 30), d[3])
        if option.state & QtGui.QStyle.State_MouseOver:
            painter.drawImage(self.sharelink_pos, self.sharelink_img)

        painter.restore()

    def editorEvent(self, event, model, option, index):
        sharelink_rect = self.sharelink_img.rect().translated(self.sharelink_pos.x(),
                                                option.rect.top() + self.sharelink_pos.y())
        if event.type() == QtCore.QEvent.MouseButtonRelease:
            if sharelink_rect.contains(event.pos()):
                model = index.model()
                link = model.data[index.row()][2]
                c = QtGui.QApplication.clipboard()
                c.setText(link)
                self.share_signal.emit()
        elif event.type() == QtCore.QEvent.MouseMove:
            if sharelink_rect.contains(event.pos()):
                if not self.cursor_changed:
                    self.cursor_changed = True
                    QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
            else:
                if self.cursor_changed:
                    self.cursor_changed = False
                    QtGui.QApplication.restoreOverrideCursor()

        return False

    def sizeHint(self, option, index):
        model = index.model()
        d = model.data[index.row()]
        return QtCore.QSize(35, 35)

class HistoryWindow(QtGui.QWidget):

    db_path = r'../images/dropbox-small.png'
    pithos_path = r'../images/pithos-small.png'
    gd_path = r'../images/googledrive-small.png'
    close_button_img = r'../images/popup-cancel.png'
    main_frame_background = r'QWidget {background-color:white}'
    static_title_style = r'QLabel {font-weight:bold}'
    font = QtGui.QFont('Tahoma', 10)
    static_title_str = r'Recently uploaded'
    share_link_str = r'Link copied'
    link_copied = QtCore.pyqtSignal()

    def __init__(self, width=320, height=240):
        QtGui.QWidget.__init__(self)

        self.link_copied.connect(self.onShareClick)

        self.close_on_share = False

        self.data = []
        self.dropbox_icon = QtGui.QImage(self.db_path)
        self.pithos_icon = QtGui.QImage(self.pithos_path)
        self.googledrive_icon = QtGui.QImage(self.gd_path)

        self.setVisible(False)
        self.setFixedSize(width, height)
        self.center()

        self.setWindowFlags(QtCore.Qt.CustomizeWindowHint)

        self.main_frame = QtGui.QFrame(self)
        self.main_frame.setGeometry(0, 0, width, height)
        self.main_frame.setStyleSheet(self.main_frame_background)

        #Upper layout
        static_title = QtGui.QLabel(self.static_title_str)
        static_title.setStyleSheet(self.static_title_style)
        static_title.setFont(self.font)

        self.link_copy_label = QtGui.QLabel()
        self.link_copy_label.setFont(self.font)

        close_button = QtGui.QPushButton(self.main_frame)
        close_button.setFlat(True)
        close_button.setIcon(QtGui.QIcon(self.close_button_img))
        close_button.clicked.connect(self.onClose)

        upper_layout = QtGui.QHBoxLayout()
        upper_layout.addWidget(static_title, 1)
        upper_layout.addWidget(self.link_copy_label, 0)
        upper_layout.addWidget(close_button, 0)

        #Main layout
        line = QtGui.QFrame(self)
        line.setGeometry(QtCore.QRect(0, 30, width, 2))
        line.setFrameShape(QtGui.QFrame.HLine)

        self.model = ListViewModel(self.data, parent=self)

        self.list = QtGui.QListView()
        self.list.setModel(self.model)
        self.list.setItemDelegate(ListItemDelegate(self, self.font, self.link_copied))
        self.list.setMouseTracking(True)

        main_layout = QtGui.QVBoxLayout()
        main_layout.addLayout(upper_layout)
        main_layout.addWidget(line)
        main_layout.addWidget(self.list)

        self.main_frame.setLayout(main_layout)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.onTimeout)
        self.timer.setInterval(1500)
        self.timer.setSingleShot(True)
        
        #REMOVE THIS
        self.showcase()

    def onShareClick(self):
        if not self.close_on_share:
            self.link_copy_label.setText(self.share_link_str)
            self.timer.start() #Restart timer if it's running already.
        else:
            QtGui.QApplication.restoreOverrideCursor()
            self.setVisible(False)

    def onTimeout(self):
        self.link_copy_label.clear()

    def showEvent(self, e):
        self.fix_position()

    def fix_position(self):
        p = self.position()
        if p:
            self.move(p)

    def position(self, m=20):
        ''' Routine to detect the taskbar position '''
        d = QtGui.QApplication.desktop()
        av = d.availableGeometry()
        sc = d.screenGeometry()
        width = self.width()
        height = self.height()

        x = sc.x() - av.x()
        y = sc.y() - av.y()
        w = sc.width() - av.width()
        h = sc.height() - av.height()

        if h > 0: #bottom or top
            if y < 0: #top
                return QtCore.QPoint(sc.width()-width-m, h+m)
            else: #bottom
                return QtCore.QPoint(sc.width()-width-m, av.height()-height-m)
        elif w > 0: #left or right
            if x < 0: #left
                return QtCore.QPoint(w+m, sc.height()-height-m)
            else: #right
                return QtCore.QPoint(av.width()-width-m, sc.height()-height-m)

        #Taskbar is hidden
        return None

    def onClose(self):
        self.close()
        #self.setVisible(False)

    def add_item(self, service, file_name, link, date):
        e = getattr(self, '{}_icon'.format(service.lower()))
        l = [[e, file_name, link, date]]
        self.model.addNewElements(l)

    def update_all(self, items):
        self.model.removeAll()
        for i in items:
            self.add_item(*i[:])

    #find tray icon and place it on top
    def center(self):
        appRect = self.frameGeometry()
        clientArea = QtGui.QDesktopWidget().availableGeometry().center()
        appRect.moveCenter(clientArea)
        self.move(appRect.topLeft())
        
    #Just for showing the widget, remove this function and the call inside __init__.
    def showcase(self):
        l = [[self.dropbox_icon, 'moo.pdf', 'aLink.html','aDate1'], 
             [self.googledrive_icon, 'boo.pdf', 'aLink.html','aDate2']]
        self.model.addNewElements(l)

if __name__ == '__main__':
    qtApp = QtGui.QApplication(sys.argv)
    frame = HistoryWindow()
    frame.show()
    sys.exit(qtApp.exec_())
