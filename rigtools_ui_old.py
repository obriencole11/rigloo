from Qt import QtCore, QtWidgets, QtGui
from Qt.QtCore import Slot, Signal

#############################
#      Main Rig Window      #
#############################

class MainRigWindow_Controller(QtCore.QObject):
    '''
    The state controller for the main rig window
    '''

class MainRigWindow(QtWidgets.QMainWindow):
    '''
    The Main container for the main rig window
    '''

    createComponentSignal = Signal()

    def __init__(self, controller, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.controller = controller

        # Create a main container widget with a horizontal layout
        # and set it as the central widget
        self.mainContainer = QtWidgets.QWidget(self)
        self.mainLayout = QtWidgets.QHBoxLayout(self.mainContainer)
        self.mainContainer.setLayout(self.mainLayout)
        self.setCentralWidget(self.mainContainer)

        # Create the metadata tab and add it to the main layout
        self.metaDataTab = self._metaDataTab(self.mainContainer)
        self.mainLayout.addWidget(self.metaDataTab)

        # Create the hierarchy display tab
        self.componentHierarchyTab = self._hierarchyTab(self.mainContainer)
        self.mainLayout.addWidget(self.componentHierarchyTab)

    def _metaDataTab(self, container):
        '''
        A tab for the main rig window containing meta data for selected components
        '''

        # Create the widget for the tab and add it to the main layout
        widget = QtWidgets.QWidget(container)

        # Create a Vertical layout for the tab
        layout = QtWidgets.QFormLayout(widget)
        widget.setLayout(layout)

        # Add a name row to the tab
        name = QtWidgets.QLineEdit(container)
        layout.addRow('name', name)

        return widget

    def _hierarchyTab(self, container):
        '''
        A tab to visualize the component hierarchy for the rig
        '''

        # Create the widget for the tab and add it to the main layout
        widget = QtWidgets.QWidget(container)

        # Create a Vertical layout for the tab
        layout = QtWidgets.QVBoxLayout(container)
        widget.setLayout(layout)

        # Create a tree widget and add it to the layout
        tree = QtWidgets.QTreeWidget(container)
        layout.addWidget(tree)

        # Create a horizontal layout and container for the bottom buttons
        buttonContainer = QtWidgets.QWidget(widget)
        layout.addWidget(buttonContainer)
        buttonLayout = QtWidgets.QHBoxLayout(buttonContainer)
        buttonContainer.setLayout(buttonLayout)

        # Create a button for creating new components
        createButton = QtWidgets.QPushButton('Create Component', buttonContainer)
        buttonLayout.addWidget(createButton)
        createButton.clicked.connect(self.createComponentSignal.emit)

        # Create a button for removing components
        removeButton = QtWidgets.QPushButton('Remove Component', buttonContainer)
        buttonLayout.addWidget(removeButton)

        return widget

    def updateComponents(self):
        for key, value in self.controller.components.iteritems():
            pass


#############################
#    Rig Creation Window    #
#############################

class RigCreationWindow_Controller(QtCore.QObject):
    '''
    The state controller for the Rig creation window
    '''

class RigCreationWindow(QtWidgets.QWidget):
    '''
    The Popup for rig creation
    '''

    createRigSignal = Signal()

    def __init__(self, controller, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.controller = controller

        # Set the window title
        self.setWindowTitle('Create Rig')

        # Create the main Vertical layout
        self.layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.layout)

        # Create the form layout
        self.formLayout = QtWidgets.QFormLayout(self)
        self.layout.addLayout(self.formLayout)

        # Create a LineEdit for the name setting
        self.name = QtWidgets.QLineEdit(self)
        self.name.setPlaceholderText('defaultRig')
        self.formLayout.addRow('Rig Name:', self.name)

        # Add a Create rig button
        self.button = QtWidgets.QPushButton('Create Rig', self)
        self.layout.addWidget(self.button)

        # Connect the create rig button to the onCreateRig event
        self.button.clicked.connect(self.createRigSignal.emit)

        # Add a stretch to the bottom to keep the widgets together
        self.layout.addStretch(1)


##############################
#  Component Creation Window #
##############################

class ComponentCreationWindow_Controller(QtCore.QObject):
    '''
    The state controller for the component creation popup
    '''

class ComponentCreationWindow(QtWidgets.QWidget):
    '''
    The popup for creating a new rig component
    '''

    createComponentSignal = Signal(str, dict)

    def __init__(self, controller, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.controller = controller

        # Set the window title
        self.setWindowTitle('Create Component')

        # Create a layout for the window
        self.mainLayout = QtWidgets.QVBoxLayout(self)
        self.setLayout(self.mainLayout)

        # Component type drop down
        label = QtWidgets.QLabel('Component Type:')
        self.mainLayout.addWidget(label)
        self.componentComboBox = QtWidgets.QComboBox(self)
        self.mainLayout.addWidget(self.componentComboBox)

        for com in self.controller.componentTypes:
            self.componentComboBox.addItem(com)

        # Component Type Widget
        # Create a container widget and assign it a form layout
        self.componentWidget = QtWidgets.QWidget(self)
        self.mainLayout.addWidget(self.componentWidget)
        self.componentWidgetLayout = QtWidgets.QFormLayout(self.componentWidget)
        self.componentWidget.setLayout(self.componentWidgetLayout)
        self.componentComboBox.currentIndexChanged.connect(self._updateComponentWidget)
        self._updateComponentWidget()

        # Add a stretch buffer
        self.mainLayout.addStretch(1)

        # Create a layout for the buttons
        buttonLayout = QtWidgets.QHBoxLayout(self)
        self.mainLayout.addLayout(buttonLayout)

        # Add a create button
        createButton = QtWidgets.QPushButton('Create', self)
        buttonLayout.addWidget(createButton)
        createButton.clicked.connect(self._onCreateComponent)

        # Add a cancel button
        cancelButton = QtWidgets.QPushButton('Cancel', self)
        buttonLayout.addWidget(cancelButton)
        cancelButton.clicked.connect(self._closeWindow)

    def _updateComponentWidget(self):

        # Remove all widgets from the component form layout
        for i in reversed(range(self.componentWidgetLayout.count())):
            self.componentWidgetLayout.itemAt(i).widget().setParent(None)

        # Iterate through component data, add ui elements for each one
        for key, value in self.controller.componentTypes[self.currentComponent].iteritems():

            # Grab the type of the data
            itemType = type(value)

            if itemType is str:
                # If type is string, create a line edit
                strWidget = QtWidgets.QLineEdit(self.componentWidget)
                strWidget.setText(value)
                self.componentWidgetLayout.addRow(key, strWidget)

            elif itemType is int:
                # If type is int, create a spinbox
                intWidget = QtWidgets.QSpinBox(self.componentWidget)
                intWidget.value = value
                self.componentWidgetLayout.addRow(key, intWidget)

            elif itemType is float:
                # If type is float, create a double spin box
                floatWidget = QtWidgets.QDoubleSpinBox(self.componentWidget)
                floatWidget.value = value
                self.componentWidgetLayout.addRow(key, floatWidget)

            elif itemType is list:
                # If type is list, create a bunch of line edits
                listWidget = QtWidgets.QWidget(self.componentWidget)
                listLayout = QtWidgets.QHBoxLayout(listWidget)
                listWidget.setLayout(listLayout)
                for obj in value:
                    objWidget = QtWidgets.QLineEdit(listWidget)
                    objWidget.setText(obj)
                    listLayout.addWidget(objWidget)
                self.componentWidgetLayout.addRow(key, listWidget)

            elif itemType is Control:
                # If the type is a Control, create a combobox selector for control types
                controlCombo = QtWidgets.QComboBox(self.componentWidget)
                self.componentWidgetLayout.addRow(key, controlCombo)

            else:
                # Otherwise ignore it
                pass

    def _onCreateComponent(self):

        # Grab the current component
        componentName = self.currentComponent

        # Create a dictionary to store the new component data
        componentData = {}

        # Create a list of each widget in the component layout
        widgets = (self.componentWidgetLayout.itemAt(i).widget() for i in range(self.componentWidgetLayout.count()))

        for widget in widgets:
            if isinstance(widget, QtWidgets.QLineEdit):
                componentData[self.componentWidgetLayout.labelForField(widget).text()] = widget.text
                print "creating data value: " + widget.text() + " at " + self.componentWidgetLayout.labelForField(widget).text()
            elif isinstance(widget, QtWidgets.QSpinBox):
                componentData[self.componentWidgetLayout.labelForField(widget).text()] = widget.value
                print "creating data value: " + str(widget.value) + " at " + self.componentWidgetLayout.labelForField(
                    widget).text()
            elif isinstance(widget, QtWidgets.QDoubleSpinBox):
                componentData[self.componentWidgetLayout.labelForField(widget).text()] = widget.value
                print "creating data value: " + str(widget.value) + " at " + self.componentWidgetLayout.labelForField(
                    widget).text()
            elif isinstance(widget, QtWidgets.QLabel):
                pass
            elif isinstance(widget, QtWidgets.QComboBox):
                componentData[self.componentWidgetLayout.labelForField(widget).text()] = widget.currentText
                print "creating data value: " + widget.currentText + " at " + self.componentWidgetLayout.labelForField(
                    widget).text()
            elif isinstance(widget, QtWidgets.QWidget):
                subLayout = widget.layout()
                subWidgets = (subLayout.itemAt(i).widget() for i in range(subLayout.count()))
                list = []
                for subWidget in subWidgets:
                    list.append(subWidget.text())
                componentData[self.componentWidgetLayout.labelForField(widget).text()] = list
                print "creating data value: " + str(list) + " at " + self.componentWidgetLayout.labelForField(
                    widget).text()
            else:
                pass


        # Emit the component name and data
        self.createComponentSignal.emit(componentName, componentData)

        # Close the window
        self._closeWindow()

    def _closeWindow(self):
        self.close()

    @property
    def creationData(self):
        return None

    @property
    def currentComponent(self):
        return self.componentComboBox.currentText()


##############################
#   Master Rig Tool Classes  #
##############################

class QTargetList(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)

class QControlComboBox(QtWidgets.QComboBox):
    def __init__(self):
        QtWidgets.QComboBox.__init__(self)

class QComponentComboBox(QtWidgets.QComboBox):
    def __init__(self):
        QtWidgets.QComboBox.__init__(self)

class QVectorWidget(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)

class RigTool_MasterController(QtCore.QObject):
    '''
    A master controller for the tool
    '''

    componentsUpdatedSignal = Signal()

    def __init__(self):
        QtCore.QObject.__init__(self)

        # Create instances of each of the windows
        self.mainRigWindow = MainRigWindow(self)
        self.mainRigWindow.createComponentSignal.connect(self.onOpenCreateWindow)
        self.componentsUpdatedSignal.connect(self.mainRigWindow.updateComponents)

        self.componentCreationWindow = ComponentCreationWindow(self)
        self.componentCreationWindow.createComponentSignal.connect(self.onCreateComponent)

        self.rigCreationWindow = RigCreationWindow(self)
        self.rigCreationWindow.createRigSignal.connect(self.onBuildRig)

        # Show the first window
        self.rigCreationWindow.show()

    def onBuildRig(self):
        '''
        Opens the rig creation window and opens the main window
        '''

        # Close the current window
        self.rigCreationWindow.close()

        # Show the main window
        self.mainRigWindow.show()

    def onOpenCreateWindow(self):
        '''
        Creates the popup window for component creation
        '''

        # Open the component creation window with the main window as the parent
        self.componentCreationWindow.show()

    def onCreateComponent(self, name, data):
        pass



def _test():
    '''
    Tests the ui
    '''

    # A dictionary of each argument that the tool supports, along with a
    # QtWidget to display it with
    componentArguments = {
        'name': QtWidgets.QLineEdit,
        'deformTargets': QTargetList,
        'mainControlType': QControlComboBox,
        'aimAxis': QVectorWidget,
        'parentSpace': QComponentComboBox,
        'uprightSpace': QComponentComboBox,
    }

    # A dict of the default component types and values
    componentTypes = {
        'FKComponent': {
            'stringValue': 'string',
            'intValue': 0,
            'floatValue': 0.1,
            'listValue': ['joint1', 'joint2', 'joint3']
        },
        'IK Component': {
            'stringValue': 'string',
            'intValue': 0
        }
    }

    # A dictionary to hold all the rig's components
    components = {

    }

    # Create a reference to the application
    app = QtWidgets.QApplication([])

    # Create the master controller
    controller = RigTool_MasterController()

    # Begin the event loop
    app.exec_()


if __name__ == '__main__':
    _test()

