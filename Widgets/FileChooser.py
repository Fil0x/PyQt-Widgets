import os
from util import raw
from PyQt4 import QtCore, QtGui


class FileChooser(QtGui.QDialog):
    def __init__(self, used_services, parent=None):
        super(FileChooser, self).__init__(parent)

        browseButton = QtGui.QPushButton('&Browse...')
        browseButton.clicked.connect(self.browse)

        #@Mediator
        self.okButton = QtGui.QPushButton('&OK')
        self.okButton.setEnabled(False)

        #@Mediator
        self.cancelButton = QtGui.QPushButton('&Cancel')

        self.total_size = 0
        self.used_services = used_services
        self.filters =  'All Files (*.*);;Images (*.png *.jpg);;PDF (*.pdf);;' +\
                        'Audio (*.mp3 *.wmv *.avi);;ZIP (*.zip *.7z *.tgz)'

        self.serviceComboBox = self.createComboBox(self.used_services)

        fileLabel = QtGui.QLabel("Service:")
        directoryLabel = QtGui.QLabel("In directory:")
        self.filesFoundLabel = QtGui.QLabel('0 file(s) with size 0 KB')
        self.currDirLabel = QtGui.QLabel(os.path.expanduser('~'))

        self.createFilesTable()

        buttonsLayout = QtGui.QHBoxLayout()
        buttonsLayout.addStretch()
        buttonsLayout.addWidget(self.okButton)
        buttonsLayout.addWidget(self.cancelButton)

        mainLayout = QtGui.QGridLayout()
        mainLayout.addWidget(fileLabel, 0, 0)
        mainLayout.addWidget(self.serviceComboBox, 0, 1)
        mainLayout.addWidget(directoryLabel, 2, 0)
        mainLayout.addWidget(self.currDirLabel, 2, 1)
        mainLayout.addWidget(browseButton, 2, 2)
        mainLayout.addWidget(self.filesTable, 3, 0, 1, 3)
        mainLayout.addWidget(self.filesFoundLabel, 4, 0)
        mainLayout.addLayout(buttonsLayout, 5, 0, 1, 3)
        mainLayout.setColumnStretch(1, 1)
        self.setLayout(mainLayout)

        self.setWindowTitle("Choose files to upload")
        self.resize(600, 300)

    def browse(self):
        filenames = QtGui.QFileDialog.getOpenFileNames(self,
                                    'Open file(s)...', self.currDirLabel.text(),
                                    self.filters)

        if filenames:
            self.currDirLabel.setText(os.path.dirname(str(filenames[0])))
            self.showFiles(filenames)
            self.okButton.setEnabled(True)

    def get_filenames(self):
        paths = []
        dir = str(self.currDirLabel.text())
        for i in range(self.filesTable.rowCount()):
            filename = self.filesTable.item(i, 0)
            paths.append(os.path.join(dir, str(filename.text())))

        return map(raw, paths)

    def get_selected_service(self):
        return self.serviceComboBox.currentText()

    def showFiles(self, files):
        self.filesTable.setRowCount(0)

        self.total_size = 0
        for fn in files:
            file = os.path.abspath(str(fn))
            filename = os.path.basename(file)
            size = os.path.getsize(file)
            size = int((size + 1023) / 1024)
            self.total_size += size

            fileNameItem = QtGui.QTableWidgetItem(filename)
            fileNameItem.setFlags(fileNameItem.flags() ^ QtCore.Qt.ItemIsEditable)
            sizeItem = QtGui.QTableWidgetItem("{} KB".format(size))
            sizeItem.setTextAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
            sizeItem.setFlags(sizeItem.flags() ^ QtCore.Qt.ItemIsEditable)

            row = self.filesTable.rowCount()
            self.filesTable.insertRow(row)
            self.filesTable.setItem(row, 0, fileNameItem)
            self.filesTable.setItem(row, 1, sizeItem)

        self.formatStatusLabel()

    def createComboBox(self, choices=[]):
        comboBox = QtGui.QComboBox()
        comboBox.setEditable(False)
        for c in choices:
            comboBox.addItem(c)
        comboBox.setSizePolicy(QtGui.QSizePolicy.Expanding,
                QtGui.QSizePolicy.Preferred)
        return comboBox

    def createFilesTable(self):
        self.filesTable = QtGui.QTableWidget(0, 2)
        self.filesTable.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)

        self.filesTable.setHorizontalHeaderLabels(("File Name", "Size"))
        self.filesTable.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.Stretch)
        self.filesTable.verticalHeader().hide()
        self.filesTable.setShowGrid(False)

        self.filesTable.cellDoubleClicked.connect(self.onTableDoubleClick)

    def formatStatusLabel(self):
        rows = self.filesTable.rowCount()
        size = self.total_size
        if self.total_size > 1023:
            size /= 1024
            self.filesFoundLabel.setText("{} file(s) with size {} MB - Double click on a file to remove it".format(rows, size))
        else:
            self.filesFoundLabel.setText("{} file(s) with size {} KB - Double click on a file to remove it".format(rows, size))

    def onTableDoubleClick(self, row, col):
        self.total_size -= int(self.filesTable.item(row, 1).text().split(' ')[0])
        self.filesTable.removeRow(row)
        if not self.filesTable.rowCount():
            self.okButton.setEnabled(False)
        self.formatStatusLabel()

if __name__ == '__main__':

    import sys

    app = QtGui.QApplication(sys.argv)
    window = FileChooser(['Dropbox', 'GoogleDrive', 'Pithos'])
    window.show()
    sys.exit(app.exec_())
