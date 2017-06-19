from Qt import QtCore, QtWidgets, QtGui
from Qt.QtCore import Slot, Signal
import logging
import uuid

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

class BaseController(QtCore.QObject):

    # A signal to tell the ui to regenerate its components
    onRefreshComponents = Signal(dict)

    # Signals to let the view and its widgets know type data was updated
    # The dict is the updated type data
    onControlTypeDataUpdated = Signal(dict)
    onComponentTypeDataUpdated = Signal(dict)

    # Signals to update on the current state of the rig
    onBuiltStateChange = Signal(bool)
    onBoundStateChange = Signal(bool)
    onBakedStateChange = Signal(bool)

    # Signal to update the view when a new rig is created
    onNewRig = Signal()

    def __init__(self, window, model):
        QtCore.QObject.__init__(self)

        # Set a variable to store the active rig
        self._activeRig = None

        # Grab a reference to the View
        self._window = window

        # Grab a reference to the model
        self._model = model


    ##### View Slots #####


    @Slot(str, dict)
    def setComponentValue(self, id, data):
        # This takes the data from the ui
        # And sends it to the model for storage
        raise NotImplementedError

    @Slot(str)
    def addComponent(self, componentType):
        # Tells the model to add a new component
        # Then refreshes the view's components
        raise NotImplementedError

    @Slot(str)
    def addSelected(self, id):
        # Adds selected joints to the specified component
        # Then refresh the view
        raise NotImplementedError

    @Slot(str)
    def createRig(self, rigName):
        # Tells the model to create a rig with the specified name
        # Tells the view to show the componentData widget and refresh the components
        raise NotImplementedError

    @Slot(str, str)
    def loadRig(self, rigName, rigDir):
        # Tells the model to load the specified rig
        # tells the view to show the componentData and refresh the components
        raise NotImplementedError

    @Slot()
    def buildRig(self):
        # If the model is not built, build it, otherwise remove it
        # Send update button signal on view
        raise NotImplementedError

    @Slot()
    def bakeRig(self):
        # If the model is baked, bake it, otherwise unbake it
        # Send the update button signal for view
        raise NotImplementedError

    @Slot()
    def refreshRig(self):
        # Tell the model to refresh the rig
        raise NotImplementedError

    @Slot()
    def bindRig(self):
        # If the model is not bound, bind it, otherwise unbind it
        # Send the update button signal for view
        raise NotImplementedError


    #### Private Methods ####

    def _refreshView(self):
        # Update the view's componentData
        # Tell the view to regenerate components
        raise NotImplementedError



    ##### private properties #####

    @property
    def componentData(self):
        # Return the latest version of the model's componet Data
        raise NotImplementedError

    @property
    def bound(self):
        # Return whether the rig is bound or not
        raise NotImplementedError

    @property
    def built(self):
        # Return whether the rig is built or not
        raise NotImplementedError

    @property
    def baked(self):
        # Return whether the rig is baked or not
        raise NotImplementedError

    @property
    def activeRig(self):
        return self._activeRig

    @activeRig.setter
    def activeRig(self, value):
        self._activeRig = value


class TestViewController(BaseController):

    def __init__(self, window, componentData, controlTypeData, componentTypeData):
        BaseController.__init__(self, window, None)

        # For testing, this will be the rig data
        self._componentData = componentData

        # Also setup some type data
        self._controlTypeData = controlTypeData
        self._componentTypeData = componentTypeData

        # Setup the state variables
        self._bound = False
        self._baked = False
        self._built = False

        # Connect controller signals to view slots
        self.onRefreshComponents.connect(window.refreshComponentWidgets)
        self.onBoundStateChange.connect(window.updateBindButton)
        self.onBakedStateChange.connect(window.updateBakeButton)
        self.onBuiltStateChange.connect(window.updateBuildButton)
        self.onControlTypeDataUpdated.connect(window.updateControlTypeData)
        self.onComponentTypeDataUpdated.connect(window.updateComponentTypeData)
        self.onNewRig.connect(window.createRigWidget)

        # Connect view signals to controller slots
        window.onComponentDataUpdated.connect(self.setComponentValue)
        window.onAddComponentClicked.connect(self.addComponent)
        window.onAddSelectedClicked.connect(self.addSelected)
        window.onCreateNewRigClicked.connect(self.createRig)
        window.onLoadRigClicked.connect(self.loadRig)
        window.onBuildRigClicked.connect(self.buildRig)
        window.onBakeRigClicked.connect(self.bakeRig)
        window.onRefreshRigClicked.connect(self.refreshRig)
        window.onBindRigClicked.connect(self.bindRig)


    ##### View Slots #####

    @Slot(str, dict)
    def setComponentValue(self, id, data):
        # This takes the data from the ui
        # And sends it to the model for storage
        self._componentData[id] = data

    @Slot(str)
    def addComponent(self, componentType):
        # Tells the model to add a new component
        # Then refreshes the view's components
        id = uuid.uuid1().hex

        if componentType == 'FKComponent':
            component = {
                'type' : componentType,
                'name' : 'fkComponent',
                'mainControlType' : 'default',
                'deformJoints' : ['thigh'],
                'id' : id
            }
        elif componentType == 'IKComponent':
            component = {
                'type' : componentType,
                'name' : 'ikComponent',
                'mainControlType' : 'cube',
                'deformJoints': ['thigh', 'knee', 'foot'],
                'id' : id
            }
        else:
            component = {
                'type': componentType,
                'name': 'UnknownComponent',
                'mainControlType': 'default',
                'deformJoints': [],
                'id': id
            }

        self._componentData[id] = component

        self._refreshView()

    @Slot(str)
    def addSelected(self, id):
        # Adds selected joints to the specified component
        # Then refresh the view
        self._componentData[id]['deformJoints'].append(['newSelectedJoint'])

    @Slot()
    def createRig(self):
        # Tells the model to create a rig with the specified name
        # Set that rig as the current rig
        # Tells the view to show the componentData widget and refresh the components
        rigName = 'defaultRig'
        self._componentData.clear()
        self.activeRig = rigName
        self.onNewRig.emit()
        self._refreshView()

    @Slot(str, str)
    def loadRig(self, rigName, rigDir):
        # Tells the model to load the specified rig
        # tells the view to show the componentData and refresh the components
        self.activeRig = 'defaultRig'
        self.onNewRig.emit()
        self._refreshView()

    @Slot()
    def buildRig(self):
        # If the model is not built, build it, otherwise remove it
        # Send update button signal on view
        self._built = not self.built
        self.onBuiltStateChange(self.built)

    @Slot()
    def bakeRig(self):
        # If the model is baked, bake it, otherwise unbake it
        # Send the update button signal for view
        self._baked = not self.baked
        self.onBakedStateChange(self.baked)

    @Slot()
    def refreshRig(self):
        # Tell the model to refresh the rig
        pass

    @Slot()
    def bindRig(self):
        # If the model is not bound, bind it, otherwise unbind it
        # Send the update button signal for view
        self._bound = not self.bound
        self.onBoundStateChange(self.bound)


    #### Private Methods ####

    def _refreshView(self):
        # Update the view's componentData
        # Tell the view to regenerate components
        self.onRefreshComponents.emit(self._componentData)

    ##### private properties #####

    @property
    def componentData(self):
        # Return the latest version of the model's componet Data
        raise self._componentData

    @property
    def bound(self):
        # Return whether the rig is bound or not
        return self._bound

    @property
    def built(self):
        # Return whether the rig is built or not
        return self._built

    @property
    def baked(self):
        # Return whether the rig is baked or not
        return self._baked


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

    def __init__(self, window, model):
        QtCore.QObject.__init__(self)

        # Grab a reference to the main window
        self.mainWindow = window

        # Grab a reference to the model
        self.model = model

        window.componentData = self.componentData
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
    def componentData(self):
        return {}

    @componentData.setter
    def componentData(self, value):
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

    def __init__(self, window, model):
        MainController.__init__(self, window, model)

        self._built = False
        self._bound = False
        self._baked = False

        self._componentdata = [
            {
                'type': 'FKComponent',
                'name': 'hip_M',
                'deformTargets': ['ethan_hips_M'],
                'mainControlType': 'circle',
                'aimAxis': [1, 0, 0],
                'parentSpace': None,
                'uprightSpace': None
            },
            {
                'type': 'IKComponent',
                'name': 'leg_L',
                'deformTargets': ['ethan_thigh_L', 'ethan_knee_L', 'ethan_foot_L'],
                'mainControlType': 'cube',
                'aimAxis': [1, 0, 0],
                'parentSpace': 'hip',
                'uprightSpace': 'hip'
            }
        ]

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
    def componentData(self):
        return self._componentdata

    @componentData.setter
    def componentData(self, value):
        self._componentdata = value

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

    # Event Signals for main button presses
    onBuildRigClicked = Signal()
    onBindRigClicked = Signal()
    onBakeRigClicked = Signal()
    onRefreshRigClicked = Signal()

    # A signal for creating a rig
    # The string is the name for the rig
    onCreateNewRigClicked = Signal()

    # A signal for loading rig
    # The first string is the rig name, the second is the directory
    onLoadRigClicked = Signal(str, str)

    # A signal for adding a component
    # The string is the name of the component type
    onAddComponentClicked = Signal(str)

    # A signal to let the control know it should add selected joints to a component
    # The str is the id of the component to update
    onAddSelectedClicked = Signal(str)

    # A signal to let the control know a component was updated
    # The string is the id of the component, the dict is the componentData
    onComponentDataUpdated = Signal(str, dict)

    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)

        # Create a list for storing component widgets
        self._componentWidgets = []

        # Create a default value for the main widget
        self.main_widget = None

        # Setup the widgets
        self._setup()

    def _setup(self):

        logger.debug('Setting up the Main Window')

        # Set the default state of the window
        self.setWindowTitle = ('RigTools Component Manager')

        # Set up the create rig widget (This will create a main_widget and main_layout
        self._showCreateRigWidget()

        # Set the main widget as the center widget
        self.setCentralWidget(self.main_widget)

    def _createMainWidget(self):

        # If the main widget exists, delete it
        if self.main_widget is not None:
            del self.main_widget
            self.main_widget = None

        # Create a vertical layout for the widget and add it
        self.main_widget = QtWidgets.QWidget(self)
        self.main_layout = QtWidgets.QVBoxLayout(self.main_widget)
        self.main_layout.setAlignment(QtCore.Qt.AlignTop)

    def _showCreateRigWidget(self):

        # Create a new main widget
        self._createMainWidget()

        # Create a button for creating new rigs
        newRigButton = QtWidgets.QPushButton('Create Rig', self.main_widget)
        self.main_layout.addWidget(newRigButton)
        newRigButton.clicked.connect(self.onCreateNewRigClicked)

        # Create a button for loading rigs
        loadRigButton = QtWidgets.QPushButton('Load Rig', self.main_widget)
        self.main_layout.addWidget(loadRigButton)
        # TODO connect load button to something

    def _showComponentDataWidget(self):

        # Create a new main widget
        self._createMainWidget()

        # TODO Create the top menu bar

        # Add the scroll area
        self._addScrollWidget()

        # Add the buttons to the bottom
        self._addButtonWidget()

    def _addButtonWidget(self):

        logger.debug('Creating the add button widget')

        # Create the container widget for the buttons
        layout = QtWidgets.QGridLayout()
        self.main_layout.addLayout(layout)

        # Create an 'AddComponent' button
        self.addButton = QtWidgets.QPushButton('Add Component')
        layout.addWidget(self.addButton, 0, 0, 1, 0)
        self.addButton.clicked.connect(self.onAddComponentClicked)

        # Create a 'Build' button
        self.buildButton = QtWidgets.QPushButton('Build')
        layout.addWidget(self.buildButton, 1, 0)
        self.buildButton.clicked.connect(self.onBuildRigClicked)

        # Create a 'Bind' button
        self.bindButton = QtWidgets.QPushButton('Bind')
        layout.addWidget(self.bindButton, 1, 1)
        self.bindButton.clicked.connect(self.onBindRigClicked)

        # Create a 'Bake' button
        self.bakeButton = QtWidgets.QPushButton('Bake to Control Rig')
        layout.addWidget(self.bakeButton, 2, 0)
        self.bakeButton.clicked.connect(self.onBakeRigClicked)

        # Create a 'Bind' button
        self.refreshButton = QtWidgets.QPushButton('Refresh')
        layout.addWidget(self.refreshButton, 2, 1)
        self.refreshButton.clicked.connect(self.onRefreshRigClicked)

        return

    def _addScrollWidget(self):

        logger.debug('Adding the scroll widget')

        # Create a scroll area to house container
        scroll = QtWidgets.QScrollArea(self.main_widget)
        scroll.setWidgetResizable(False)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.main_layout.addWidget(scroll)

        return scroll


    ##### Controller Slots #####

    @Slot(dict)
    # The controller calls this to regenerate the component ui
    # The dict is an updated version of the component Data
    def refreshComponentWidgets(self, componentData):

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

    @Slot(dict)
    def updateControlTypeData(self, controlTypeData):
        pass

    @Slot(dict)
    def updateComponentTypeData(self, componentTypeData):
        pass

    # These are called by the controller when the state of the rig changes
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

    @Slot()
    def createRigWidget(self):
        self._showComponentDataWidget()

    ##### Widget Slots #####

    @Slot(str)
    # A componentWidget calls this to alert that a component has been changed
    def componentUpdated(self, id):

        # Grab the data from that component
        # Emit a signal with the data
        raise NotImplementedError


    ##### Private Methods #####

    # This returns a dict of component data for a specified component
    def _getComponentData(self, id):

        raise NotImplementedError

    # This adds a menu action for the addComponent menu
    # Not sure what index means though
    def _onAddComponentGenerator(self, index):

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

TEST_COMPONENT_DATA = {
    'legID' : {
        'type': 'IKComponent',
        'name': 'leg_L',
        'deformTargets': ['ethan_thigh_L', 'ethan_knee_L', 'ethan_foot_L'],
        'mainControlType': 'cube',
        'aimAxis': [1, 0, 0],
        'parentSpace': 'hipID',
        'uprightSpace': 'hipID'
    },
    'hipID' : {
        'type': 'FKComponent',
        'name': 'hips_M',
        'deformTargets': ['ethan_hips'],
        'mainControlType': 'square',
        'aimAxis': [1, 0, 0],
        'parentSpace': 'rootID',
        'uprightSpace': 'rootID'

    },
    'rootID' : {
        'type': 'Component',
        'name': 'root_M',
        'deformTargets': ['ethan_root'],
        'mainControlType': 'circle',
        'aimAxis': [1, 0, 0],
        'parentSpace': 'world',
        'uprightSpace': 'world'
    }
}


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
    controller = TestViewController(mainWindow, TEST_COMPONENT_DATA, CONTROL_TYPES, COMPONENT_TYPES)

    # Show the main window
    mainWindow.show()

    # Begin the event loop
    app.exec_()



if __name__ == '__main__':
    _test()

