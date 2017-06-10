from Qt import QtCore, QtWidgets, QtGui
from Qt.QtCore import Slot, Signal

class ARController(QtCore.QObject):


    def __init__(self, app):

        self.app = app

        self.currentWindow = RigCreationWindow(self)

        self.currentWindow.createRig.connect(self.onCreateRig)

        self.currentWindow.show()

        self.app.exec_()

    @Slot()
    def onCreateRig(self):
        self.currentWindow.close()

        self.currentWindow = MainWindow(self)

        self.currentWindow.show()

        self.app.exec_()

class MainContainer(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)

        self.layout = QtWidgets.QHBoxLayout(self)

        self.form_layout = QtWidgets.QFormLayout()

        self.componentTypes = ['IKComponent', 'FKComponent', 'GlobalComponent']

        self.componentType = QtWidgets.QComboBox(self)
        self.componentType.addItems(self.componentTypes)

        self.form_layout.addRow('Component Type', self.componentType)

        self.name = QtWidgets.QLineEdit(self)
        self.name.setPlaceholderText('defaultName')

        self.form_layout.addRow('Name', self.name)

        self.layout.addLayout(self.form_layout)

        self.layout.addStretch(1)

        self.buttonBox = QtWidgets.QHBoxLayout()

        self.buttonBox.addStretch(1)

        self.buildButton = QtWidgets.QPushButton('build', self)

        self.buildButton.clicked.connect(self.buildComponent)

        self.buttonBox.addWidget(self.buildButton)

        self.layout.addLayout(self.buttonBox)

        self.setLayout(self.layout)

    @Slot()
    def buildComponent(self):
        print 'test'

class MetaDataTab(QtWidgets.QWidget):

    def __init__(self):
        QtWidgets.QWidget.__init__(self)

        self.layout = QtWidgets.QVBoxLayout

        self.rigNameLabel = QtWidgets.QLabel("test Rig", self)








class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, controller=None, name="defaultRig", *args, **kwargs):
        # Initialize the window as a mainwindow
        # Set its title and minimum width
        QtWidgets.QMainWindow.__init__(self, *args, **kwargs)
        self.setWindowTitle(name)
        self.setMinimumWidth(400)

        # Add the mainContainer widget and set it as the central widget
        self.mainContainer = MainContainer()
        self.setCentralWidget(self.mainContainer)




class RigCreationWindow(QtWidgets.QWidget):
    createRig = Signal()

    def __init__(self, controller, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)
        self.setWindowTitle('Create Rig')
        self.controller = controller

        self.layout = QtWidgets.QVBoxLayout()
        self.formLayout = QtWidgets.QFormLayout()

        self.name = QtWidgets.QLineEdit(self)
        self.name.setPlaceholderText('defaultRig')

        self.formLayout.addRow('Rig Name:', self.name)

        self.layout.addLayout(self.formLayout)

        self.layout.addStretch(1)

        self.button = QtWidgets.QPushButton('Create Rig', self)
        self.button.clicked.connect(self.onCreateRig)

        self.layout.addWidget(self.button)

        self.setLayout(self.layout)

    def onCreateRig(self):
        self.createRig.emit()

class ComponentCreationWindow(QtWidgets.QWidget):
    def __init__(self, *args, **kwargs):
        QtWidgets.QWidget.__init__(self, *args, **kwargs)
        self.setWindowTitle('Create Component')


def _pytest():

    app = QtWidgets.QApplication([])

    controller = ARController(app)



if __name__ == '__main__':
    _pytest()
