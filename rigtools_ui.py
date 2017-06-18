from Qt import QtCore, QtWidgets, QtGui
from Qt.QtCore import Slot, Signal
import logging

##############################
#          Logging           #
##############################

# Create a logger for this module
logger = logging.getLogger(__name__)

# Create a formatter for all log statements
formatter = logging.Formatter('%(name)s:%(message)s')

# Create a handler for logging to the console
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.DEBUG)


##############################
#       UI Controllers       #
##############################

class MainController(QtCore.QObject):
    '''
    The Base class for the ui controller, not intended for direct use.
    '''

    onComponentsUpdated = Signal()
    onRigUpdated = Signal()
    onControlsUpdated = Signal()

    onUpdateBuildStatus = Signal(bool)
    onUpdateBakeStatus = Signal(bool)
    onUpdateBindStatus = Signal(bool)

    def __init__(self, window):
        QtCore.QObject.__init__(self)

        # Grab a reference to the main window
        self.mainWindow = window

        window.rig = self.rig
        window.components = self.components
        window.controls = self.controls

        # Connect the windows signals to the controller slots
        self.mainWindow.onBuildRig.connect(self.buildRig)
        self.mainWindow.onBindRig.connect(self.bindRig)
        self.mainWindow.onBakeRig.connect(self.bakeRig)
        self.mainWindow.onRefreshRig.connect(self.refreshRig)

        self.onUpdateBuildStatus.connect(self.mainWindow.updateBuildButton)
        self.onUpdateBakeStatus.connect(self.mainWindow.updateBakeButton)
        self.onUpdateBindStatus.connect(self.mainWindow.updateBindButton)

        self.mainWindow.onAddComponent.connect(self.addComponent)
        self.mainWindow.onAddSelected.connect(self.addSelected)
        self.mainWindow.onUpdateData.connect(self.updateData)

        # Connect the controller signals to the windows slots
        self.onRigUpdated.connect(self.updateRig)

        # Fill the ui with initial components
        self.onRigUpdated.emit()


    #### Public Properties ####

    @property
    def rig(self):
        return {}

    @rig.setter
    def rig(self, value):
        pass

    @property
    def components(self):
        return {}

    @property
    def controls(self):
        return {}


    #### Slots ####

    @Slot()
    def updateRig(self):
        logger.debug('Setting the mainWindow rig to the controller rig')
        self.mainWindow.rig = self.rig

    @Slot()
    def buildRig(self):
        pass

    @Slot()
    def bindRig(self):
        pass

    @Slot()
    def bakeRig(self):
        pass

    @Slot()
    def refreshRig(self):
        pass

    @Slot(str)
    def addComponent(self, name):
        pass

    @Slot(str)
    def addSelected(self, name):
        pass

    @Slot()
    def updateData(self):
        pass

class TestController(MainController):
    '''
    A class inheriting from the standard controller setup for testing without a model.
    '''

    _rig = {
        'name': 'ethan',
        'components': [
            {
                'type': 'FKComponent',
                'name': 'hip_M',
                'deformTargets': ['ethan_hips_M'],
                'mainControlType': 'circle',
                'aimAxis': [1,0,0],
                'parentSpace': None,
                'uprightSpace': None
            },
            {
                'type': 'IKComponent',
                'name': 'leg_L',
                'deformTargets': ['ethan_thigh_L', 'ethan_knee_L', 'ethan_foot_L'],
                'mainControlType': 'cube',
                'aimAxis': [1,0,0],
                'parentSpace': 'hip',
                'uprightSpace': 'hip'
            }
        ]
    }

    def __init__(self, window):
        MainController.__init__(self, window)

        self._built = False
        self._bound = False
        self._baked = False

    #### Private Methods ####

    def _create_rig(self, name):
        '''
        Creates an new empty rig for testing
        '''

        logger.debug('Creating a new rig')

        newRig = {
            'name': name,
            'components': {}
        }

        return newRig

    def _add_FK_component(self, name='TestFKComponent'):
        '''
        Add a new FkComponent to the rig
        '''

        logger.debug('Adding a new FKComponent named: ' + name)

        fkComponent = {
            'type': 'FKComponent',
            'name': 'hip_M',
            'deformTargets': ['ethan_hips_M'],
            'mainControlType': 'circle',
            'aimAxis': [0,1,0],
            'parentSpace': None,
            'uprightSpace': None
        }

        newRig = self.rig
        newRig['components'].append(fkComponent)

        self.rig = newRig

    def _add_IK_component(self, name='TestIKComponent'):
        '''
        Add a new IKComponent to the rig
        '''

        logger.debug('Adding a new IK Component named: ' + name)

        ikComponent = {
            'type': 'IKComponent',
            'name': 'leg_L',
            'deformTargets': ['ethan_thigh_L', 'ethan_knee_L', 'ethan_foot_L'],
            'mainControlType': 'cube',
            'aimAxis': [1,0,0],
            'parentSpace': 'hip',
            'uprightSpace': 'hip'
        }

        newRig = self.rig
        newRig['components'].append(ikComponent)

        self.rig = newRig


    #### Public Properties ####

    @property
    def rig(self):
        return self._rig

    @rig.setter
    def rig(self, value):
        self._rig = value

        logger.debug('Sending rig updated signal')

        self.onRigUpdated.emit()

    @property
    def components(self):
        return COMPONENT_TYPES

    @property
    def controls(self):
        return CONTROL_TYPES

    #### Slots ####

    @Slot()
    def buildRig(self):
        self._built = not self._built
        self.onUpdateBuildStatus.emit(self._built)

    @Slot()
    def bindRig(self):
        self._bound = not self._bound
        self.onUpdateBindStatus.emit(self._bound)

    @Slot()
    def bakeRig(self):
        self._baked = not self._baked
        self.onUpdateBakeStatus.emit(self._baked)

    @Slot()
    def refreshRig(self):
        pass

    @Slot(str)
    def addComponent(self, name):

        # Update the rig
        self.updateData()

        # Check the name of the component, and add to the rig accordingly
        if str(name) == 'FKComponent':
            logger.debug('Adding an FK component')
            self._add_FK_component()

        elif str(name) == 'IKComponent':
            logger.debug('Adding an IK component')
            self._add_IK_component()

        else:
            logger.warning('Attempted to create a component, but did not recognize the name')

    @Slot(int)
    def addSelected(self, index):

        logger.debug('Rig is adding selected joints to the rig')

        # Grab the latest version of the data
        self.updateData()

        # Add selected object to the deform targets of the specified component
        self.rig['components'][index]['deformTargets'].append('ethan_head_M')

        # Update the UI
        self.onRigUpdated.emit()

    @Slot()
    def updateData(self):

        logger.debug('Updating the rig data from the view')

        self._rig['components'] = self.mainWindow.data

##############################
#         UI Windows         #
##############################

class MainComponentWindow(QtWidgets.QMainWindow):

    # Event Signals
    onBuildRig = Signal()
    onBindRig = Signal()
    onBakeRig = Signal()
    onRefreshRig = Signal()

    onAddComponent = Signal(str)
    onAddSelected = Signal(int)
    onUpdateData = Signal()

    onRigChanged = Signal()
    onControlsChanged = Signal()
    onComponentsChanged = Signal()

    _rig = {}
    _components = {}
    _controls = {}

    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)

        # Setup the widgets
        self._setup()

    def _setup(self):

        logger.debug('Setting up the Main Window')

        # Set the default state of the window
        self.setWindowTitle = ('RigTools Component Manager')

        self.componentWidgets = []

        # Connect signals to slots
        self.onComponentsChanged.connect(self.updateAddComponentButton)
        self.onRigChanged.connect(self.updateRig)

        # Create a vertical layout for the widget and add it
        self.main_widget = QtWidgets.QWidget(self)
        self.main_layout = QtWidgets.QVBoxLayout(self.main_widget)
        self.main_layout.setAlignment(QtCore.Qt.AlignTop)

        # Set up each subWidget in order
        self.scrollWidget = self._add_scroll_widget()
        self._add_button_widget()

        # Set the main widget as the center widget
        self.setCentralWidget(self.main_widget)

    def _add_button_widget(self):

        logger.debug('Creating the add button widget')

        # Create the container widget for the buttons
        layout = QtWidgets.QGridLayout()
        self.main_layout.addLayout(layout)

        # Create an 'AddComponent' button
        self.addButton = QtWidgets.QPushButton('Add Component')
        layout.addWidget(self.addButton, 0, 0, 1, 0)

        # Create a 'Build' button
        self.buildButton = QtWidgets.QPushButton('Build')
        layout.addWidget(self.buildButton, 1, 0)
        self.buildButton.clicked.connect(self.onBuildRig)

        # Create a 'Bind' button
        self.bindButton = QtWidgets.QPushButton('Bind')
        layout.addWidget(self.bindButton, 1, 1)
        self.bindButton.clicked.connect(self.onBindRig)

        # Create a 'Bake' button
        self.bakeButton = QtWidgets.QPushButton('Bake to Control Rig')
        layout.addWidget(self.bakeButton, 2, 0)
        self.bakeButton.clicked.connect(self.onBakeRig)

        # Create a 'Bind' button
        self.refreshButton = QtWidgets.QPushButton('Refresh')
        layout.addWidget(self.refreshButton, 2, 1)
        self.refreshButton.clicked.connect(self.onRefreshRig)

        return

    def _add_scroll_widget(self):

        logger.debug('Adding the scroll widget')

        # Create a scroll area to house container
        scroll = QtWidgets.QScrollArea(self.main_widget)
        scroll.setWidgetResizable(False)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.main_layout.addWidget(scroll)

        return scroll

    @Slot()
    def updateRig(self):

        logger.debug('Regenerating the component ui with new rig components')

        # Save the position of the scrollbar
        scrollValue = self.scrollWidget.verticalScrollBar().value()

        # Clear the component widget list
        del self.componentWidgets[:]

        # If the widget already exists, destroy it
        try:
            self.componentWidget.deleteLater()
            del self.componentWidget
        except AttributeError:
            pass

        # Create a widget to contain the components
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        container.setLayout(layout)

        # For each component in the components dictionary
        for component in self.rig['components']:

            # Create a widget for the component
            widget = ComponentWidget(component['name'], component, self, self.rig['components'].index(component))

            # Connect the widgets signals
            widget.onAddSelected.connect(self.onAddSelected)
            widget.onUpdateData.connect(self.onUpdateData)

            # Add the widget to the component widget dict
            self.componentWidgets.append(widget)

            # Add the widget to the layout
            layout.addWidget(widget)

        self.scrollWidget.setWidget(container)

        self.scrollWidget.verticalScrollBar().setValue(scrollValue)

    @Slot()
    def updateAddComponentButton(self):

        logger.debug('Updating the menus on the AddComponent button')

        # Create a menu for the add button
        menu = QtWidgets.QMenu(self.main_widget)

        # Add a menu action for each component type
        for component in self.components:
            action = QtWidgets.QAction(self.main_widget)
            action.setText(component)
            action.triggered.connect(self._onAddComponentGenerator(action.text()))
            menu.addAction(action)

        # Apply the menu
        self.addButton.setMenu(menu)

    @Slot(bool)
    def updateBuildButton(self, built):
        if built:
            self.buildButton.setText('Remove')
        else:
            self.buildButton.setText('Build')

    @Slot(bool)
    def updateBindButton(self, bound):
        if bound:
            self.bindButton.setText('Unbind')
        else:
            self.bindButton.setText('Bind')

    @Slot(bool)
    def updateBakeButton(self, baked):
        if baked:
            self.bakeButton.setText('Bake to Skeleton')
        else:
            self.bakeButton.setText('Bake to Control Rig')

    @property
    def data(self):

        logger.debug('Generating data from the view')

        # Create a dict to store return data
        data = []

        # For each component, store its value in the dict
        for widget in self.componentWidgets:
            data.append(widget.value)

        return data

    @property
    def rig(self):
        return self._rig

    @rig.setter
    def rig(self, value):
        self._rig = value

        logger.debug('The Main Window rig has been changed, sending signal')

        self.onRigChanged.emit()

    @property
    def components(self):
        return self._components

    @components.setter
    def components(self, value):
        self._components = value

        logger.debug('The Main Windows component type dict has been updated, emitting signal')

        self.onComponentsChanged.emit()

    @property
    def controls(self):
        return self._controls

    @controls.setter
    def controls(self, value):
        self._controls = value

        logger.debug('The Main Windows control dict has been changed, emitting signal')

        self.onControlsChanged.emit()

    def _onAddComponentGenerator(self, index):

        logging.debug('Adding a menu action')

        def onAddComponent():
            self.onAddComponent.emit(index)

        return onAddComponent


##############################
#       Custom Widgets       #
##############################

class ComponentWidget(QtWidgets.QWidget):
    '''
    A widget to display a single component.
    :param argumentDict: A dictionary from the rig dict containing argument information.
    '''

    onAddSelected = Signal(int)
    onUpdateData = Signal()

    def __init__(self, name, argumentDict, parent, index):
        QtWidgets.QWidget.__init__(self)

        # Grab a reference to the parent widget
        self.parent = parent

        # Grab a reference to the component dictionary
        self.arguments = argumentDict

        # Set the widgets title
        self.name = name

        # Set the widgets index
        self.index = index

        self._setup()

    def _setup(self):

        logger.debug('Setting up the component widget for ' + self.name)

        # Create a vertical layout to contain everything
        vertical_layout = QtWidgets.QVBoxLayout()
        vertical_layout.setAlignment(QtCore.Qt.AlignTop)
        vertical_layout.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.setLayout(vertical_layout)

        # Create a button for the title and connect it to the toggle visibility method
        self.title = QtWidgets.QPushButton(self._getTitle(self.name), self)
        self.title.setFlat(False)
        self.title.setMinimumSize(300, 0)
        self.title.clicked.connect(self._toggle_visibility)
        vertical_layout.addWidget(self.title)

        # Create a container for the arguments
        self.argumentContainer = QtWidgets.QWidget(self)
        vertical_layout.addWidget(self.argumentContainer)

        # Create a form layout to house the arguments
        form_layout = QtWidgets.QFormLayout()
        form_layout.setRowWrapPolicy(QtWidgets.QFormLayout.RowWrapPolicy.WrapLongRows)
        self.argumentContainer.setLayout(form_layout)
        form_layout.setAlignment(QtCore.Qt.AlignTop)

        # Create a list to store argumentWidgets
        self.argumentWidgets = {}

        for key, value in self.arguments.iteritems():

            # Create the widget for the argument
            try:
                widget = COMPONENT_SETTINGS[key](self)
                widget.value = value
                self.argumentWidgets[key] = widget

                # Add the widget to the form layout
                form_layout.addRow(key, widget)
            except KeyError:
                pass

        self.argumentWidgets['name'].textChanged.connect(self._updateTitle)

        # Set the default state of visibility
        try:
            self.hidden = self.arguments['hidden']
        except KeyError:
            pass

    @property
    def value(self):

        logger.debug('Generating data from ' + self.name)

        # Create a dictioary to reconstruct data
        data = {}

        # Iterate through widgets and grab their values
        for key, widget in self.arguments.iteritems():
            try:
                data[key] = self.argumentWidgets[key].value
            except KeyError:
                data[key] = self.arguments[key]

        data['hidden'] = self.hidden

        return data

    @property
    def rig(self):
        return self.parent.rig

    @property
    def components(self):
        return self.parent.components

    @property
    def controls(self):
        return self.parent.controls

    @property
    def hidden(self):
        return self.argumentContainer.isVisible()

    @hidden.setter
    def hidden(self, value):
        self.argumentContainer.setVisible(value)

    def _toggle_visibility(self):

        self.hidden = not self.hidden

    def _getTitle(self, name):
        return self.arguments['type'] + ' : ' + name

    @Slot()
    def _updateTitle(self):
        logger.debug('updating component title for ' + self.name)

        self.title.setText(self._getTitle(self.argumentWidgets['name'].value))


class QTargetList(QtWidgets.QWidget):
    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)

        self.parent = parent

        # Create a layout to contain sub widgets
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        # Create a list widget to hold deform targets
        self.list = QtWidgets.QListWidget(self)
        self.list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.layout.addWidget(self.list)

        # Create a layout for the buttons
        buttonLayout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(buttonLayout)

        # Create an add button
        self.addButton = QtWidgets.QPushButton('+', self)
        buttonLayout.addWidget(self.addButton)
        self.addButton.clicked.connect(self.addButtonClicked)

        # Create a remove button
        self.removeButton = QtWidgets.QPushButton('-', self)
        buttonLayout.addWidget(self.removeButton)
        self.removeButton.clicked.connect(self.removeButtonClicked)

    @property
    def value(self):
        # Return values of list widget in an array
        return [self.list.item(index).text() for index in range(self.list.count())]

    @value.setter
    def value(self, value):
        # Clear the list widget
        self.list.clear()

        # Add each value into the list
        self.list.addItems(value)

    def addButtonClicked(self):
        logger.debug('Add button clicked')
        self.parent.onAddSelected.emit(self.parent.index)

    def removeButtonClicked(self):

        logger.debug('Remove button clicked for ' + self.parent.name)

        # Remove the selected items from the list
        items = self.list.selectedItems()
        for item in items:
            self.list.takeItem(self.list.row(item))

        # Update the rig
        self.parent.onUpdateData.emit()


class QControlComboBox(QtWidgets.QComboBox):
    def __init__(self, parent):

        QtWidgets.QComboBox.__init__(self, parent)

        # Fill the combo box with the control types
        for control in parent.controls:
            self.addItem(control)

    @property
    def value(self):
        return self.currentText()

    @value.setter
    def value(self, value):
        self.setCurrentText(value)


class QComponentComboBox(QtWidgets.QComboBox):
    def __init__(self, parent):
        QtWidgets.QComboBox.__init__(self, parent)

        # Add each component type to the list
        for component in parent.components:
            self.addItem(component)

    @property
    def value(self):
        return self.currentText()

    @value.setter
    def value(self, value):
        self.setCurrentText(value)


class QRigComponentComboBox(QtWidgets.QComboBox):
    def __init__(self, parent):
        QtWidgets.QComboBox.__init__(self, parent)

        # Add each component type to the list
        for component in parent.rig['components']:
            self.addItem(component['name'])

        self.addItem('world')

    @property
    def value(self):
        if self.currentText() is 'world':
            return None
        else:
            return self.currentText()

    @value.setter
    def value(self, value):
        if value is None:
            self.setCurrentText('world')
        else:
            self.setCurrentText(value)


class QVectorWidget(QtWidgets.QWidget):
    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)

        # Create a horizontal layout to hold text fields
        self.layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.layout)

        # Create three line edits and grab references to them
        self.spinBoxes = [QtWidgets.QDoubleSpinBox(self),
                           QtWidgets.QDoubleSpinBox(self),
                           QtWidgets.QDoubleSpinBox(self)]

        for spinBox in self.spinBoxes:
            self.layout.addWidget(spinBox)

    @property
    def value(self):
        return [spinBox.value() for spinBox in self.spinBoxes]

    @value.setter
    def value(self, value):
        for num in range(3):
            self.spinBoxes[num].setValue(value[num])


class QNameWidget(QtWidgets.QLineEdit):
    def __init__(self, parent):

        QtWidgets.QLineEdit.__init__(self, parent)

    @property
    def value(self):
        return self.text()

    @value.setter
    def value(self, value):
        self.setText(value)


##############################
#       UI Settings         #
##############################

COMPONENT_SETTINGS = {
    'name': QNameWidget,
    'deformTargets': QTargetList,
    'mainControlType': QControlComboBox,
    'aimAxis': QVectorWidget,
    'parentSpace': QRigComponentComboBox,
    'uprightSpace': QRigComponentComboBox
}

COMPONENT_TYPES = {
    'FKComponent': 'Basic FK Compoment',
    'IKComponent': 'Basic IK Component',
    'GlobalComponent': 'Global Component'
}

CONTROL_TYPES = [
    'default',
    'square',
    'circle',
    'cube',
    'star'
]

##############################
#     Testing Functions      #
##############################

def _test():
    '''
    Tests the ui
    '''

    # Create a handler for file logging
    file_handler = logging.FileHandler('rigtools_ui.log')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # By default, just add the file logging handler
    logger.addHandler(file_handler)

    # Enable logging to the console
    #logger.addHandler(stream_handler)
    logger.setLevel(logging.DEBUG)

    # Create a reference to the application
    app = QtWidgets.QApplication([])

    # Create the main window
    mainWindow = MainComponentWindow()

    # Create the ui controller
    controller = TestController(mainWindow)

    # Show the main window
    mainWindow.show()

    # Begin the event loop
    app.exec_()



if __name__ == '__main__':
    _test()

