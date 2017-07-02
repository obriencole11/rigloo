from Qt import QtCore, QtWidgets, QtGui
from Qt.QtCore import Slot, Signal
import os
import logging
import uuid
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

##############################
#          Logging           #
##############################

logging.basicConfig(filename=os.path.join(os.environ['MAYA_APP_DIR'],'fossil.log'),
                    format='%(levelname)s:%(name)s:%(message)s',
                    level=logging.WARNING)

##############################
#       UI Controllers       #
##############################

class BaseController(QtCore.QObject):

    # A signal to tell the ui to regenerate its components
    onRefreshComponents = Signal(dict, list, list, dict, list, str)

    # Signals to let the view and its widgets know type data was updated
    # The dict is the updated type data
    onControlTypeDataUpdated = Signal(dict)
    onComponentTypeDataUpdated = Signal(dict)

    # Signal to update the view when a new rig is created
    onNewRig = Signal()

    # A Signal to update the view when a new active rig is added
    onActiveRigsUpdated = Signal(list)

    def __init__(self, window=None, model=None):
        QtCore.QObject.__init__(self)

        # Set up a logger for the controller classes
        self.logger = logging.getLogger(type(self).__name__)

        # Set a variable to store the active rig
        self._activeRig = None

        # Grab a reference to the View
        self._window = window
        self._model = model

        # Set the default value for the bakeMode
        self._bakeMode = False


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
    def removeComponent(self, id):
        # Tells the model to remove the specified component
        # Then refreshed the view
        raise NotImplementedError

    @Slot(str)
    def addSelected(self, id):
        # Adds selected joints to the specified component
        # Then refresh the view
        raise NotImplementedError

    @Slot()
    def createRig(self):
        # Tells the model to create a rig with the specified name at the specified directory
        # Tells the view to show the componentData widget and refresh the components
        raise NotImplementedError

    @Slot(str)
    def loadRig(self, dir):
        # Tells the model to load the specified rig
        # tells the view to show the componentData and refresh the components
        raise NotImplementedError

    @Slot()
    def saveRig(self):
        # Saves the active rig to the model's data
        raise NotImplementedError

    @Slot(str)
    def saveRigAs(self, dir):
        # Saves the rig to a new location
        raise NotImplementedError

    @Slot()
    def removeRig(self):
        # Attempt to remove the rig
        raise NotImplementedError

    @Slot()
    def previewRig(self):
        # Remove the rig and build it
        raise NotImplementedError

    @Slot()
    def bindRig(self):
        # Remove and bind the rig
        # If bake mode is on, bake the rig as well
        raise NotImplementedError

    @Slot(bool)
    def toggleBake(self, value):
        # Set the bake setting state
        raise NotImplementedError

    @Slot(bool)
    def toggleDebug(self, value):
        raise NotImplementedError

    @Slot()
    def removePreview(self):
        # This removes the rig, but only when previewed
        # This is useful for when the window closes
        raise NotImplementedError

    @Slot(str)
    def switchActiveRig(self, rigName):
         # This will tell the model to switch the active rig
        raise NotImplementedError

    #### Private Methods ####

    def _refreshView(self):
        # Update the view's componentData
        # Tell the view to regenerate components
        raise NotImplementedError

    def _loadViewData(self):
        # Update the model with new data from the view
        raise NotImplementedError

    def _loadSceneData(self):
        # Update the model with new data from the scene
        raise NotImplementedError

    def _showError(self, message):
        # Shows an error message
        raise NotImplementedError

    ##### private properties #####

    @property
    def componentData(self):
        # Return the latest version of the model's componet Data
        raise NotImplementedError

    @property
    def activeRig(self):
        return self._activeRig

    @activeRig.setter
    def activeRig(self, value):
        self._activeRig = value

    @property
    def bakeMode(self):
        return self._bakeMode

class ViewController(BaseController):
    '''
    A Controller that interacts with the view.
    Overrides commands that pertain to the view.
    '''

    def __init__(self, *args, **kwargs):
        BaseController.__init__(self, *args, **kwargs)

        # Connect controller signals to view slots
        self.onRefreshComponents.connect(self._window.refreshComponentWidgets)
        self.onNewRig.connect(self._window.createRigWidget)

        # Connect view signals to controller slots
        self._window.onAddComponentClicked.connect(self.addComponent)
        self._window.onAddSelectedClicked.connect(self.addSelected)
        self._window.onCreateNewRigClicked.connect(self.createRig)
        self._window.onLoadRigClicked.connect(self.loadRig)
        self._window.onSaveRigClicked.connect(self.saveRig)
        self._window.onSaveRigAsClicked.connect(self.saveRigAs)
        self._window.onPreviewClicked.connect(self.previewRig)
        self._window.onBindClicked.connect(self.bindRig)
        self._window.onRemoveClicked.connect(self.removeRig)
        self._window.onRemoveComponentClicked.connect(self.removeComponent)
        self._window.onRigSwitched.connect(self.switchActiveRig)
        self._window.onBakeToggled.connect(self.toggleBake)
        self._window.onWindowClosed.connect(self.removePreview)
        self._window.onDebugToggled.connect(self.toggleDebug)

        # Create a private variable to store the current component settings
        self._componentSettings = dict(COMPONENT_SETTINGS)

    def _showError(self, message):
        '''
        Shows a popup to alert the user that the rig cannot be built with the
        current inputs
        '''

        self.logger.warning(message)

        popup = QtWidgets.QMessageBox(self._window)
        popup.setWindowTitle('Build Failed')
        popup.setText(message)
        popup.show()

    @Slot(bool)
    def toggleBake(self, value):
        # Set the bake setting state
        self._bakeMode = value

        self.logger.debug('Setting the bake to component setting to %s', value)

    @Slot(bool)
    def toggleDebug(self, value):
        if value:
            newSettings = COMPONENT_SETTINGS.copy()
            newSettings.update(COMPONENT_SETTINGS_DEBUG)
            self._componentSettings = newSettings
        else:
            self._componentSettings = COMPONENT_SETTINGS

        self._refreshView()

    @property
    def componentSettings(self):
        return self._componentSettings

class TestViewController(ViewController):

    def __init__(self, window, componentData, controlTypeData, componentTypeData):
        ViewController.__init__(self, window, None)

        # For testing, this will be the rig data
        self._componentData = componentData

        # Also setup some type data
        self._controlTypeData = controlTypeData
        self._componentTypeData = componentTypeData

        # Setup the state variables
        self._bound = False
        self._baked = False
        self._built = False

        # This stores active rigs
        self.activeRig = 'defaultRig'
        self.rigs = {}
        self.rigs[self.activeRig] = componentData


    #### Private Methods ####

    def _refreshView(self):
        # Update the view's componentData
        # Tell the view to regenerate components
        pass
        '''
        self.onRefreshComponents.emit(self._componentData,
                                      self._componentTypeData,
                                      self._controlTypeData,
                                      self.componentSettings,
                                      self.rigs)
        '''

    ##### View Slots #####

    @Slot(str, dict)
    def setComponentValue(self, id, data):
        # This takes the data from the ui
        # And sends it to the model for storage
        self._componentData[id] = data

        self._refreshView()

    @Slot(str)
    def addComponent(self, componentType):
        # Tells the model to add a new component
        # Then refreshes the view's components
        logger.info('TestViewController: Received an addComponent Signal. Value: ' + componentType)

        id = uuid.uuid1().hex

        if componentType == 'FKComponent':
            component = {
                'index': len(self.componentData)+1,
                'type': componentType,
                'name': 'fkComponent',
                'mainControlType': 'default',
                'deformTargets': ['thigh'],
                'id': id,
                'hidden': True,
                'parentSpace': None,
                'uprightSpace': None,
                'aimAxis': [1, 0, 0],
                'mainControlScale': 10.0,
                'stretchEnabled': False,
                'squeashEnabled': False
            }
        elif componentType == 'IKComponent':
            component = {
                'index': len(self.componentData)+1,
                'type' : componentType,
                'name' : 'ikComponent',
                'mainControlType' : 'cube',
                'deformTargets': ['thigh', 'knee', 'foot'],
                'id' : id,
                'hidden': True,
                'parentSpace': None,
                'uprightSpace': None,
                'aimAxis': [1, 0, 0],
                'mainControlScale': 10.0,
                'stretchEnabled': False,
                'squeashEnabled': False
            }
        else:
            component = {
                'index': len(self.componentData)+1,
                'type': componentType,
                'name': 'UnknownComponent',
                'mainControlType': 'default',
                'deformTargets': [],
                'id': id,
                'hidden': True
            }

        print component['index']

        self._componentData[id] = component

        self._refreshView()

    @Slot(str)
    def removeComponent(self, id):
        # Tells the model to remove the specified component
        # Then refreshed the view
        del self._componentData[id]
        self._refreshView()

    @Slot(str)
    def addSelected(self, id):
        # Adds selected joints to the specified component
        # Then refresh the view
        logger.info('Test View Controller: addSelected Signal received. Value: ' + id)

        self._componentData[id]['deformTargets'].append('newSelectedJoint')
        self._refreshView()

    @Slot()
    def createRig(self):
        # Tells the model to create a rig with no name
        # Set that rig as the current rig
        # Tells the view to show the componentData widget and refresh the components
        rigName = uuid.uuid1().hex
        self._componentData = {}
        self.rigs[rigName] = self._componentData
        self.activeRig = rigName
        self.onNewRig.emit()
        self._refreshView()

        print self.rigs

    @Slot(str)
    def loadRig(self, directory):
        # Tells the model to load the specified rig
        # tells the view to show the componentData and refresh the components
        logger.info('TextViewController: loadRig Signal received.')

        rigName = directory
        self.activeRig = rigName
        self._componentData = TEST_COMPONENT_DATA
        self.onNewRig.emit()
        self._refreshView()

        print self.rigs

    @Slot()
    def saveRig(self):
        # Saves the active rig to the model's data
        logger.info('TextViewController: saveRig Signal received.')

        self.rigs['defaultRig'] = self._componentData
        print self.rigs

    @Slot()
    def buildRig(self):
        # If the model is not built, build it, otherwise remove it
        # Send update button signal on view

        error = False

        for id, com in self._componentData.iteritems():
            if len(com['deformTargets']) < 1:
                error = True

        if not error:
            self._built = not self.built
            self.onBuiltStateChange.emit(self.built)
        else:
            self._showError('Not enough deform targets!')

    @Slot()
    def bakeRig(self):
        # If the model is baked, bake it, otherwise unbake it
        # Send the update button signal for view
        self._baked = not self.baked
        self.onBakedStateChange.emit(self.baked)

    @Slot()
    def refreshRig(self):
        # Tell the model to refresh the rig
        pass

    @Slot()
    def bindRig(self):
        # If the model is not bound, bind it, otherwise unbind it
        # Send the update button signal for view
        self._bound = not self.bound
        self.onBoundStateChange.emit(self.bound)

    @Slot(str)
    def switchActiveRig(self, rigName):
        # This will tell the model to switch the active rig
        raise NotImplementedError

    ##### private properties #####

    @property
    def componentData(self):
        # Return the latest version of the model's componet Data
        return self._componentData

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

##############################
#         UI Windows         #
##############################

class MainComponentWindow(QtWidgets.QMainWindow):

    # Event Signals for main button presses
    onPreviewClicked = Signal()
    onBindClicked = Signal()
    onRemoveClicked = Signal()

    # A signal to alert the controller when the window has been close
    onWindowClosed = Signal()

    # A signal for creating a rig
    # The string is the directory
    onCreateNewRigClicked = Signal()

    # A signal for loading rig
    # The string is the directory
    onLoadRigClicked = Signal(str)

    # A signal for saving the current rig
    onSaveRigClicked = Signal()

    # A signal for saving the rig as
    onSaveRigAsClicked = Signal(str)

    # A signal for adding a component
    # The string is the name of the component type
    onAddComponentClicked = Signal(str)

    # A signal for removing a component
    # The string is the id of the component
    onRemoveComponentClicked = Signal(str)

    # A signal to let the control know it should add selected joints to a component
    # The str is the id of the component to update
    onAddSelectedClicked = Signal(str)

    # A signal to let the controller know debug mode should be on
    onDebugToggled = Signal(bool)

    # A signal to let the control know it should switch to bake mode
    onBakeToggled = Signal(bool)

    # A signal to let the control know a new rig was selected
    onRigSwitched = Signal(str)

    # Widget Signals
    # These are sent to slots in widget this window creates
    onUpdateComponentWidgets = Signal(dict)

    def __init__(self, parent=None):
        super(MainComponentWindow, self).__init__(parent=parent)

        # Set up a logger
        self.logger = logging.getLogger(type(self).__name__)

        # Create a list for storing component widgets
        self._componentWidgets = []

        # Create a default value for the main widget
        self.main_widget = None

        # Create a default value for the save directory
        self._directory = None

        # Setup the widgets
        self._setup()

    def _setup(self):

        # Set the default state of the window
        self.setWindowTitle('Fossil')

        # Set the icon for the window
        basePath = os.path.dirname(os.path.realpath(__file__))
        logoIcon = QtGui.QIcon(basePath + '/icons/icon-logo.svg')
        self.setWindowIcon(logoIcon)

        # Set the starting size
        self.resize(300, 700)

        # Create the menu bar
        self._createMenuBar()

        # Set up the create rig widget (This will create a main_widget and main_layout
        self._createMainWidget()

    def _createMenuBar(self):

        newAction = QtWidgets.QAction('New Rig', self)
        newAction.setStatusTip('New Rig')
        newAction.triggered.connect(self.onCreateNewRigClicked)

        saveAction = QtWidgets.QAction('Save Rig', self)
        saveAction.setStatusTip('Save the current rig')
        saveAction.triggered.connect(self.onSave)

        saveAsAction = QtWidgets.QAction('Save Rig as...', self)
        saveAsAction.setStatusTip('Save the current rig as...')
        saveAsAction.triggered.connect(self.onSaveAs)

        loadAction = QtWidgets.QAction('Load Rig', self)
        loadAction.setStatusTip('Load a rig')
        loadAction.triggered.connect(self.onLoadRig)

        debugAction = QtWidgets.QAction('Debug Mode', self)
        debugAction.setCheckable(True)
        debugAction.setChecked(False)
        debugAction.setStatusTip('Toggle Debug Mode')
        debugAction.toggled.connect(self.onDebugToggled)

        logAction = QtWidgets.QAction('Log to console', self)
        logAction.setCheckable(True)
        logAction.setChecked(False)
        logAction.setStatusTip('Toggle Debug Mode')
        logAction.toggled.connect(self.onLogToggled)

        bakeAction = QtWidgets.QAction('Bake To Animation', self)
        bakeAction.setCheckable(True)
        bakeAction.setChecked(False)
        bakeAction.setStatusTip('Toggle animation baking on bind')
        bakeAction.toggled.connect(self.onBakeToggled)

        self.statusBar()

        menubar = self.menuBar()

        fileMenu = menubar.addMenu('File')
        settingsMenu = menubar.addMenu('Settings')
        fileMenu.addAction(newAction)
        fileMenu.addAction(saveAction)
        fileMenu.addAction(saveAsAction)
        fileMenu.addAction(loadAction)
        settingsMenu.addAction(debugAction)
        settingsMenu.addAction(bakeAction)
        settingsMenu.addAction(logAction)

    def _createMainWidget(self):

        # If the main widget exists, delete it
        if self.main_widget is not None:
            del self.main_widget
            self.main_widget = None

        # Create a vertical layout for the widget and add it
        self.main_widget = QtWidgets.QWidget(self)
        self.main_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.main_widget.setMinimumWidth(350)
        self.main_layout = QtWidgets.QVBoxLayout(self.main_widget)
        self.main_layout.setSpacing(5)

        # Set the main widget as the center widget
        self.setCentralWidget(self.main_widget)

        # Add the rig selector widget
        self._addRigSelector()

    def _showComponentDataWidget(self):

        # Create a new main widget
        self._createMainWidget()

        # Add the scroll area
        self._addScrollWidget()

        # Add the buttons to the bottom
        self._addButtonWidget()

    def _addButtonWidget(self):

        # Create the container widget for the buttons
        layout = QtWidgets.QGridLayout()
        layout.setSpacing(5)
        self.main_layout.addLayout(layout)

        # Create an 'AddComponent' button
        self.addButton = QtWidgets.QPushButton('Add Component')
        layout.addWidget(self.addButton, 0, 0, 1, 0)

        # Create a 'Remove' button
        self.removeButton = QtWidgets.QPushButton('Remove')
        removeIcon = QtGui.QIcon(':/deleteActive.png')
        self.removeButton.setIcon(removeIcon)
        layout.addWidget(self.removeButton, 1, 0)
        self.removeButton.clicked.connect(self.onRemoveClicked)

        # Create a 'Preview' button
        self.previewButton = QtWidgets.QPushButton('Preview')
        previewIcon = QtGui.QIcon(':/rebuild.png')
        self.previewButton.setIcon(previewIcon)
        self.previewButton.setStyleSheet('QPushButton {background-color: #5285a6}')
        layout.addWidget(self.previewButton, 1, 1, 1, 2)
        self.previewButton.clicked.connect(self.onPreviewClicked)

        # Create a 'Bind' button
        self.bindButton = QtWidgets.QPushButton('Bind')
        self.bindButton.setStyleSheet('QPushButton {background-color: #cc3333}')
        layout.addWidget(self.bindButton, 1, 3)
        self.bindButton.clicked.connect(self.onBindClicked)

    def _addRigSelector(self):

        # Create a formlayout for the selector
        selectorLayout = QtWidgets.QFormLayout()
        self.main_layout.addLayout(selectorLayout)

        # Create a combobox to hold the active rigs
        self.rigComboBox = QtWidgets.QComboBox(self.main_widget)
        selectorLayout.addRow('Rig:', self.rigComboBox)

        # Connect the combobox to the rig switch signal
        self.rigComboBox.activated.connect(self.onRigSwitched)

    def _onRigSwitched(self):
        self.onRigSwitched.emit(self.rigComboBox.currentText())

    def _addScrollWidget(self):

        # Create a scroll area to house container
        scroll = QtWidgets.QScrollArea(self.main_widget)
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.main_layout.addWidget(scroll)

        self.scrollWidget = scroll

    def _addHorizontalLine(self):
        line = QtWidgets.QFrame(self.main_widget)
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        line.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        return line

    def closeEvent(self, event):
        self.logger.debug('Window close event received')
        self.onWindowClosed.emit()
        event.accept()

    # This is called by the controller to update the rig selector
    def _refreshActiveRigs(self, rigNames, activeRigName):
        self.logger.debug('Refreshing the active rigs. Active Rig: %s, Rig Names: %s', activeRigName, rigNames)

        # Clear the combobox
        self.rigComboBox.clear()

        # Add rigs to the combobox
        self.rigComboBox.addItems(rigNames)

        self.rigComboBox.setCurrentIndex(rigNames.index(activeRigName))

    ##### Controller Slots #####

    @Slot(dict, list, list, dict, list, str)
    # The controller calls this to regenerate the component ui
    # The dict is an updated version of the component Data
    def refreshComponentWidgets(self, componentData, componentTypeData, controlTypeData, componentSettings,
                                activeRigs, activeRig):

        self._refreshActiveRigs(activeRigs, activeRig)

        self.updateAddComponentMenus(componentTypeData)

        self.logger.debug('Refreshing component widgets')

        # Save the position of the scrollbar
        scrollValue = self.scrollWidget.verticalScrollBar().value()

        # Clear the component widget list
        del self._componentWidgets[:]

        # Create a widget to contain the components
        self.componentWidget = QtWidgets.QWidget()

        layout = QtWidgets.QVBoxLayout()
        layout.setAlignment(QtCore.Qt.AlignTop)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.componentWidget.setLayout(layout)

        # Add a horizontal line to start
        topLine = self._addHorizontalLine()
        layout.addWidget(topLine)

        # For each component in the components dictionary
        for id, data in componentData.iteritems():

            try:
                index = data['index']
            except KeyError:
                self.logger.info('%s Component did not have an index value, assigning a new one.', data['type'])
                index = len(componentData) + 1

            # Create a widget for the component
            widget = ComponentWidget(data['name'], componentData, self, id,
                                     componentTypeData,
                                     controlTypeData,
                                     componentSettings,
                                     index)

            # Connect the widgets signals
            widget.onAddSelected.connect(self.onAddSelectedClicked)
            widget.onRemoveComponentClicked.connect(self.onRemoveComponentClicked)

            # Add the widget to the component widget dict
            self._componentWidgets.append(widget)

        # Sort the widgets by index
        # Then add the widget to the layout
        list = sorted(self._componentWidgets, key= lambda widget: widget.index)
        for widget in list:
            # Add the widget
            layout.addWidget(widget)

            # Also add a horizontal line
            line = self._addHorizontalLine()
            layout.addWidget(line)

        # Then emit a signal to update all widgets that care about components
        self.onUpdateComponentWidgets.emit(componentData)

        self.scrollWidget.setWidget(self.componentWidget)

        self.scrollWidget.verticalScrollBar().setValue(scrollValue)

        self.logger.debug('refreshed components successfully')

    @Slot(list)
    def updateControlTypeData(self, controlTypeData):
        self.logger.debug('Updating component widgets with new control type data.')
        self.onUpdateControlTypeWidgets.emit(controlTypeData)

    @Slot(list)
    def updateComponentTypeData(self, componentTypeData):
        self.logger.debug('Updating component widgets with new component type data.')
        self.onUpdateComponentTypeWidgets.emit(componentTypeData)

    @Slot(list)
    def updateAddComponentMenus(self, componentTypeData):

        self.logger.debug('Updating add component menus with new component type data.')

        menu = QtWidgets.QMenu(self.main_widget)

        for componentType in componentTypeData:
            action = QtWidgets.QAction(self.addButton)
            action.setText(componentType)
            action.triggered.connect(self._onAddComponentGenerator(componentType))
            menu.addAction(action)

        self.addButton.setMenu(menu)

    @Slot()
    def createRigWidget(self):
        self._showComponentDataWidget()

    @Slot()
    def onSave(self):
        if self._directory is None:
            self.logger.info('No directory set, running a save as instead of a save')
            self.onSaveAs()
        else:
            self.onSaveRigClicked.emit()

    @Slot()
    def onSaveAs(self):
        # Create a popup and grab the name (the underscore stores the filter, we don't care about that)
        name, _ = QtWidgets.QFileDialog.getSaveFileName(self, 'Save New Rig', '', filter="All JSON files (*.json)")
        self._directory = name
        self.onSaveRigAsClicked.emit(name)

    @Slot()
    def onLoadRig(self):
        # Create a popup and grab the name (the underscore stores the filter, we don't care about that)
        name, _ = QtWidgets.QFileDialog.getOpenFileName(self, 'Load Rig', '', filter="All JSON files (*.json)")
        self._directory = name
        self.onLoadRigClicked.emit(name)

    @Slot(bool)
    def onLogToggled(self, value):
        self.logger.debug('Setting log to console mode to %s', value)
        if value:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.WARNING)

    @property
    def data(self):

        data = {}

        for component in self._componentWidgets:
            data[component.id] = component.value
        return data

    ##### Private Methods #####

    # This adds a menu action for the addComponent menu
    def _onAddComponentGenerator(self, componentName):

        def onAddComponent():
            self.onAddComponentClicked.emit(componentName)

        return onAddComponent

class MayaComponentWindow(MayaQWidgetDockableMixin, MainComponentWindow):

    def __init__(self, parent=None):
        super(MayaComponentWindow, self).__init__(parent=parent)

##############################
#      Component Widget      #
##############################

class ComponentWidget(QtWidgets.QWidget):
    '''
    A widget to display a single component.
    :param argumentDict: A dictionary from the rig dict containing argument information.
    '''

    # Window Signals
    # These alert the window to changes in the gui
    onAddSelected = Signal(str)
    onUpdateData = Signal(str, dict)

    # Widget Signals
    # These alert the ui to changes in the data
    onAddSelectedClicked = Signal()
    onRemoveComponentClicked = Signal(str)

    def __init__(self, name, componentData, parent, id, componentTypeData, controlTypeData, componentSettings, index):
        QtWidgets.QWidget.__init__(self)

        # Set up a logger
        self.logger = logging.getLogger(type(self).__name__)

        # Grab a reference to the parent widget
        self.parent = parent

        # Grab a reference to the component dictionary
        self.arguments = componentData[id]

        # Grab a reference to the data
        self.componentData = componentData
        self.componentTypeData = componentTypeData
        self.controlTypeData = controlTypeData
        self.componentSettings = componentSettings

        # Set the widgets title
        self.name = name


        # Set the widgets index
        self.id = id

        self.index = index

        # Connect some internal signals
        self.onAddSelectedClicked.connect(self.onAddSelectedSlot)

        self._setup()

    #### Private Methods #####

    def _setup(self):

        # Create a vertical layout to contain everything
        vertical_layout = QtWidgets.QVBoxLayout()
        vertical_layout.setAlignment(QtCore.Qt.AlignTop)
        vertical_layout.setSpacing(0)
        vertical_layout.setContentsMargins(5,1,5,1)
        self.setLayout(vertical_layout)

        self._addTitle()

        vertical_layout.addWidget(self.titleButton)

        # Create a container for the arguments
        self.argumentContainer = QtWidgets.QWidget(self)
        self.argumentContainer.setMinimumWidth(300)
        vertical_layout.addWidget(self.argumentContainer)

        # Create a vertical layout to house the groupboxes
        groupLayout = QtWidgets.QVBoxLayout()
        self.argumentContainer.setLayout(groupLayout)

        # Create a list to store argumentWidgets
        self.argumentWidgets = {}

        for groupTuple in COMPONENT_GROUPS:

            groupBox = self._addArgumentGroup(groupTuple)
            
            if groupBox:
                groupLayout.addWidget(groupBox)

        
        extraArguments = [argument for argument in self.arguments if argument not in self.argumentWidgets]

        if len(extraArguments) > 0:
            tuple = ('Other Attributes', extraArguments)
            groupBox = self._addArgumentGroup(tuple)

            if groupBox:
                groupLayout.addWidget(groupBox)
        

        self.argumentWidgets['name'].textChanged.connect(self._updateTitle)

        # Set the default state of visibility
        try:
            self.hidden = self.arguments['hidden']
        except KeyError:
            self.logger.info('No hidden argument found, setting hidden to default.')
            self.hidden = False

    def _addTitle(self):

        # Create a button for the title and connect it to the toggle visibility method
        self.titleButton = QtWidgets.QPushButton(self)
        self.titleButton.setFlat(True)
        self.titleButton.setStyleSheet("Text-align:left;")
        self.titleButton.clicked.connect(self._toggle_visibility)
        self.titleButton.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)
        self.titleButton.setMinimumSize(200, 25)

        # Create a layout for the title
        titleLayout = QtWidgets.QHBoxLayout()
        titleLayout.setContentsMargins(0, 0, 0, 0)
        self.titleButton.setLayout(titleLayout)
        titleLayout.setAlignment(QtCore.Qt.AlignLeft)

        size = QtCore.QSize(15, 15)

        # Add an arrow icon
        self.rightArrowLabel = QtWidgets.QLabel(self.titleButton)
        self.downArrowLabel = QtWidgets.QLabel(self.titleButton)
        rightArrow = QtGui.QIcon(':/arrowRight.png').pixmap(size)
        downArrow = QtGui.QIcon(':/arrowDown.png').pixmap(size)
        self.rightArrowLabel.setPixmap(rightArrow)
        self.downArrowLabel.setPixmap(downArrow)

        titleLayout.addWidget(self.rightArrowLabel)
        titleLayout.addWidget(self.downArrowLabel)

        # Try to add a maya icon to the button
        basePath = os.path.dirname(os.path.realpath(__file__))
        print basePath
        try:
            icon = QtGui.QIcon(basePath + self.componentTypeData[self.arguments['type']]['icon'])
        except KeyError:
            self.logger.info('Not Icon set in component settings, using icon for basicComponent instead')
            icon = QtGui.QIcon(basePath + self.componentTypeData['BasicComponent']['icon'])
        self.iconLabel = QtWidgets.QLabel()
        self.iconLabel.setPixmap(icon.pixmap(size))
        titleLayout.addWidget(self.iconLabel)

        # Add an enabling checkbox
        checkBox = QtWidgets.QCheckBox()
        titleLayout.addWidget(checkBox)

        # Add a title
        self.title = QtWidgets.QLabel(self._getTitle(self.name))
        titleLayout.addWidget(self.title)

        # Set the default state of enabled
        try:
            self.enabled = self.arguments['enabled']
        except KeyError:
            self.logger.info('No enabled state found in %s, setting to default', self.name)
            self.enabled = True
        checkBox.setChecked(self.enabled)
        checkBox.toggled.connect(self._toggleEnabled)

        # Add a settings button
        settingsButton = QtWidgets.QPushButton()
        settingsButton.setFlat(True)
        settingsIcon = QtGui.QIcon(':/gear.png')
        settingsButton.setIcon(settingsIcon)

        # Create a menu for the button
        settingsMenu = QtWidgets.QMenu(settingsButton)
        settingsAction = QtWidgets.QAction('Remove Component', settingsMenu)
        settingsAction.triggered.connect(self.onRemoveComponent)
        settingsMenu.addAction(settingsAction)
        settingsButton.setMenu(settingsMenu)

        # Add a layout for the settings button
        titleLayout.addStretch(1)
        titleLayout.addWidget(settingsButton)
        titleLayout.setAlignment(settingsButton, QtCore.Qt.AlignRight)

    def _toggle_visibility(self):
        self.hidden = not self.hidden
        try:
            self.arrowLabel.setPixmap(self.arrow2)
        except AttributeError:
            self.logger.info('Attempting to set arrow image in %s , but label widget does not exist', self.name)
            pass

        self.onValueChanged()

    def _toggleEnabled(self):
        self.enabled = not self.enabled
        self.onValueChanged()

    def _getTitle(self, name):
        return self.arguments['type'] + ' : ' + name

    def _createArgumentWidget(self, key, value):
        # Create the widget for the argument
        try:
            widget = self.componentSettings[key](self, self.componentData, self.componentTypeData, self.controlTypeData)
            widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
            widget.value = value
            self.argumentWidgets[key] = widget

            # Connect to the widget's value changed signal
            widget.onValueChanged.connect(self.onValueChanged)
            return widget
        except KeyError:
            if not key in COMPONENT_SETTINGS_DEBUG:
                self.logger.debug('Attempting to add an argument, but key is not in settings. Key: %s ', key)
            return None

    def _addArgumentGroup(self, groupTuple):

        groupName = groupTuple[0]
        types = groupTuple[1]

        widgets = []
        names = []

        # Create the argument widget and add it to the form layout
        for name in types:
            widget = None
            try:
                widget = self._createArgumentWidget(name, self.arguments[name])
            except KeyError:
                pass

            if widget is not None:
                widgets.append(widget)
                names.append(name)

        if len(widgets) > 0:
            groupBox = QtWidgets.QGroupBox(groupName)

            # Create a form layout to house the arguments
            form_layout = QtWidgets.QFormLayout()
            form_layout.setLabelAlignment(QtCore.Qt.AlignLeft)
            form_layout.setFormAlignment(QtCore.Qt.AlignLeft)
            groupBox.setLayout(form_layout)

            for index in range(len(widgets)):
                form_layout.addRow(names[index], widgets[index])

            return groupBox

        return None

    #### Properties #####

    @property
    def value(self):

        self.logger.debug('Generating data for %s', self.name)

        # Create a dictionary to reconstruct data
        data = {}

        # Iterate through widgets and grab their values
        for key, widget in self.arguments.iteritems():
            try:
                value = self.argumentWidgets[key].value
            except KeyError:
                self.logger.info('Value for %s not found, using original value instead', key)
                value = self.arguments[key]

            data[key] = value
        data['hidden'] = self.hidden
        data['enabled'] = self.enabled

        return data

    @property
    def hidden(self):
        return self.argumentContainer.isVisible()

    @hidden.setter
    def hidden(self, value):
        self.argumentContainer.setVisible(value)
        self.downArrowLabel.setVisible(value)
        self.rightArrowLabel.setVisible(not value)

    @property
    def enabled(self):
        return self.title.isEnabled()

    @enabled.setter
    def enabled(self, value):
        self.title.setEnabled(value)
        self.iconLabel.setEnabled(value)


    ##### Slots #####

    @Slot()
    def _updateTitle(self):
        self.title.setText(self._getTitle(self.argumentWidgets['name'].value))

    @Slot()
    # A widget calls this to let the component know something changed
    def onValueChanged(self):

        self.logger.debug('Value changed signal received, updating data for %s', self.name)

        # Send this components id and value
        self.onUpdateData.emit(self.id, self.value)

    @Slot()
    def onAddSelectedSlot(self):

        # Tell the window to update this component in the data
        self.onAddSelected.emit(self.id)

    @Slot()
    def onRemoveComponent(self):
        self.onRemoveComponentClicked.emit(self.id)


##############################
#      Argument Widgets      #
##############################

class ComponentArgumentWidget(QtCore.QObject):
    '''
    An inherited only class that adds signals every widget in a component should have
    '''

    # This is called when the value of a argument is changed
    onValueChanged = Signal()

    def __init__(self):
        # Set up a logger
        self.logger = logging.getLogger(type(self).__name__)
        self.onValueChanged.connect(self.valueChangedAlert)

    @property
    def value(self):
        return None

    @value.setter
    def value(self, value):
        pass

    @Slot()
    def valueChangedAlert(self):
        self.logger.debug('My Value Changed.')

class QTarget(QtWidgets.QWidget, ComponentArgumentWidget):
    def __init__(self, parent, componentData, componentTypeData, controlTypeData):

        QtWidgets.QWidget.__init__(self, parent)

        ComponentArgumentWidget.__init__(self)

        self.parent = parent

        # Create a layout to contain sub widgets
        self.layout = QtWidgets.QHBoxLayout()

        self.layout.setContentsMargins(0,0,0,0)
        self.setLayout(self.layout)

        # Create a list widget to hold deform targets
        self.list = QtWidgets.QLineEdit(self)
        self.list.setReadOnly(True)
        self.layout.addWidget(self.list)

        # Create an add button
        addButton = QtWidgets.QPushButton('+', self)
        self.layout.addWidget(addButton)
        addButton.clicked.connect(self.addButtonClicked)

    @property
    def value(self):
        return self.list.text()

    @value.setter
    def value(self, value):
        self.list.setText(value)

    @Slot()
    def addButtonClicked(self):
        self.logger.debug('Add button clicked')
        self.list.setText('')
        self.parent.onAddSelectedClicked.emit()

class QTargetList(QtWidgets.QWidget, ComponentArgumentWidget):
    def __init__(self, parent, componentData, componentTypeData, controlTypeData):
        QtWidgets.QWidget.__init__(self, parent)

        ComponentArgumentWidget.__init__(self)

        self.parent = parent

        self.setMaximumHeight(150)

        # Create a layout to contain sub widgets
        self.layout = QtWidgets.QVBoxLayout()
        self.setLayout(self.layout)

        # Create a list widget to hold deform targets
        self.list = QtWidgets.QListWidget(self)
        self.list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self.list.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)

        self.layout.addWidget(self.list)

        # Create a layout for the buttons
        buttonLayout = QtWidgets.QHBoxLayout()
        self.layout.addLayout(buttonLayout)

        # Create an add button
        addButton = QtWidgets.QPushButton('+', self)
        buttonLayout.addWidget(addButton)
        addButton.clicked.connect(self.addButtonClicked)

        # Create a remove button
        removeButton = QtWidgets.QPushButton('-', self)
        buttonLayout.addWidget(removeButton)
        removeButton.clicked.connect(self.removeButtonClicked)

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

    @Slot()
    def addButtonClicked(self):
        self.logger.debug('Add Button Clicked')
        self.parent.onAddSelectedClicked.emit()

    @Slot()
    def removeButtonClicked(self):

        self.logger.debug('Remove Button Clicked')

        # Remove the selected items from the list
        items = self.list.selectedItems()
        for item in items:
            self.list.takeItem(self.list.row(item))

        # Update the rig
        self.onValueChanged.emit()

class QControlComboBox(QtWidgets.QComboBox, ComponentArgumentWidget):
    def __init__(self, parent, componentData, componentTypeData, controlTypeData):

        QtWidgets.QComboBox.__init__(self, parent)

        ComponentArgumentWidget.__init__(self)

        # Alert the component when a value is changed
        self.activated.connect(self.onValueChanged)

        self.addItems(controlTypeData)

    @property
    def value(self):
        return self.currentText()

    @value.setter
    def value(self, value):
        self.setCurrentIndex(self.findText(value))

class QComponentComboBox(QtWidgets.QComboBox, ComponentArgumentWidget):
    def __init__(self, parent, componentData, componentTypeData, controlTypeData):
        QtWidgets.QComboBox.__init__(self, parent)

        ComponentArgumentWidget.__init__(self)

        # Alert the component when a value is changed
        self.activated.connect(self.onValueChanged)
        self.setEnabled(False)
        self.addItems([key for key, value in componentTypeData.iteritems()])

    @property
    def value(self):
        return self.currentText()

    @value.setter
    def value(self, value):
        self.setCurrentText(value)

class QRigComponentComboBox(QtWidgets.QComboBox, ComponentArgumentWidget):
    def __init__(self, parent, componentData, componentTypeData, controlTypeData):
        QtWidgets.QComboBox.__init__(self, parent)

        ComponentArgumentWidget.__init__(self)

        # Alert the component when a value is changed
        self.activated.connect(self.onValueChanged)

        # Grab a reference to the componentData
        self.componentData = componentData

        # Add all the components names from the componentData
        id = parent.id
        self.addItems([value['name'] for key, value in componentData.iteritems() if key is not id])
        self.addItem('world')

        # Grab a reference to the componentData
        self.componentData = componentData

        # Create a variable to hold the current selections id
        self._id = None

    @property
    def value(self):
        if self.currentText() is 'world':
            return None
        else:
            for key, value in self.componentData.iteritems():
                if value['name'] == self.currentText():
                    return key
            self.logger.error('The component %s does not exist')

    @value.setter
    def value(self, value):
        if value is None:
            self.setCurrentIndex(self.findText('world'))
        else:
            self._id = value
            self.setCurrentIndex(self.findText(self.componentData[value]['name']))

class QVectorWidget(QtWidgets.QWidget, ComponentArgumentWidget):
    def __init__(self, parent, componentData, componentTypeData, controlTypeData):
        QtWidgets.QWidget.__init__(self, parent)

        ComponentArgumentWidget.__init__(self)

        # Create a horizontal layout to hold text fields
        self.layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.layout)

        # Create three line edits and grab references to them
        self.spinBoxes = [QtWidgets.QDoubleSpinBox(self),
                           QtWidgets.QDoubleSpinBox(self),
                           QtWidgets.QDoubleSpinBox(self)]

        # Add each spinbox to the layout
        # And connect it to the value changed signal
        for spinBox in self.spinBoxes:
            self.layout.addWidget(spinBox)
            spinBox.valueChanged.connect(self.onValueChanged)

    @property
    def value(self):
        print [spinBox.value() for spinBox in self.spinBoxes]
        return [spinBox.value() for spinBox in self.spinBoxes]

    @value.setter
    def value(self, value):
        for num in range(3):
            self.spinBoxes[num].setValue(value[num])

class QAxisWidget(QtWidgets.QComboBox, ComponentArgumentWidget):

    def __init__(self, parent, componentData, componentTypeData, controlTypeData):
        QtWidgets.QComboBox.__init__(self, parent)

        ComponentArgumentWidget.__init__(self)

        # Alert the component when a value is changed
        self.activated.connect(self.onValueChanged)

        self.axisItems = {
            '+X': [1, 0, 0],
            '-X': [-1, 0, 0],
            '+Y': [0, 1, 0],
            '-Y': [0, -1, 0],
            '+Z': [0, 0, 1],
            '-Z': [0, 0, -1]
        }

        self.addItems([id for id, value in self.axisItems.iteritems()])

    @property
    def value(self):
        return self.axisItems[self.currentText()]

    @value.setter
    def value(self, value):

        for key, axis in self.axisItems.iteritems():
            if value == axis:
                self.setCurrentText(key)
                break

class QNameWidget(QtWidgets.QLineEdit, ComponentArgumentWidget):
    def __init__(self, parent, componentData, componentTypeData, controlTypeData):

        QtWidgets.QLineEdit.__init__(self, parent)

        ComponentArgumentWidget.__init__(self)

        self.oldText = ""

        # Alert the component widget when a value is changed
        self.textChanged.connect(self.onValueChanged)

    @property
    def value(self):
        return self.text()

    @value.setter
    def value(self, value):
        self.setText(value)
        self.oldText = value

class QScalarWidget(QtWidgets.QLineEdit, ComponentArgumentWidget):
    def __init__(self, parent, componentData, componentTypeData, controlTypeData):

        QtWidgets.QLineEdit.__init__(self, parent)

        ComponentArgumentWidget.__init__(self)

        self.setValidator(QtGui.QDoubleValidator(0, 100, 2, self))

        # Alert the component widget when a value is changed
        self.textChanged.connect(self.onValueChanged)

    @property
    def value(self):
        return float(self.text())

    @value.setter
    def value(self, value):
        self.setText(str(value))

class QReadOnlyStringWidget(QtWidgets.QLineEdit, ComponentArgumentWidget):

    def __init__(self, parent, componentData, componentTypeData, controlTypeData):

        QtWidgets.QLineEdit.__init__(self, parent)

        ComponentArgumentWidget.__init__(self)

        self.setReadOnly(True)
        self.setEnabled(False)

    @property
    def value(self):
        return None

    @value.setter
    def value(self, value):
        self.setText(str(value))

class QReadOnlyIntWidget(QtWidgets.QLineEdit, ComponentArgumentWidget):

    def __init__(self, parent, componentData, componentTypeData, controlTypeData):

        QtWidgets.QLineEdit.__init__(self, parent)

        ComponentArgumentWidget.__init__(self)

        self.setReadOnly(True)
        self.setEnabled(False)

    @property
    def value(self):
        return int(self.text())

    @value.setter
    def value(self, value):
        self.setText(str(value))

class QBoolWidget(QtWidgets.QCheckBox, ComponentArgumentWidget):
    def __init__(self, parent, componentData, componentTypeData, controlTypeData):

        QtWidgets.QCheckBox.__init__(self, parent)

        ComponentArgumentWidget.__init__(self)

        # Alert the component widget when a value is changed
        self.stateChanged.connect(self.onValueChanged)

    @property
    def value(self):
        return self.isChecked()

    @value.setter
    def value(self, value):
        self.setChecked(value)

class QReadOnlyBoolWidget(QBoolWidget):
    def __init__(self, *args, **kwargs):
        super(QReadOnlyBoolWidget, self).__init__(*args, **kwargs)

        ComponentArgumentWidget.__init__(self)

        self.setEnabled(False)

    @property
    def value(self):
        return self.isChecked()

    @value.setter
    def value(self, value):
        self.setChecked(value)


##############################
#       UI Settings         #
##############################

COMPONENT_SETTINGS = {
    'name': QNameWidget,
    'deformTargets': QTargetList,
    'mainControlType': QControlComboBox,
    'mainControlScale': QScalarWidget,
    'childControlType': QControlComboBox,
    'childControlScale': QScalarWidget,
    'aimAxis': QAxisWidget,
    'parentSpace': QRigComponentComboBox,
    'uprightSpace': QRigComponentComboBox,
    'stretchEnabled': QBoolWidget,
    'squashEnabled': QBoolWidget,
    'noFlipKnee': QBoolWidget,
    'poleCurveType': QControlComboBox,
    'poleCurveScale': QScalarWidget,
    'offsetCurveType': QControlComboBox,
    'offsetCurveScale': QScalarWidget,
    'baseCurveType': QControlComboBox,
    'baseCurveScale': QScalarWidget,
    'baseCurveParentSpace': QRigComponentComboBox,
    'baseCurveUprightSpace': QRigComponentComboBox,
    'target': QTarget,
    'spaceSwitchEnabled': QBoolWidget,
    'isLeafJoint': QBoolWidget,
    'aimControlType': QControlComboBox,
    'aimVector': QAxisWidget,
    'aimCurveDistance': QScalarWidget,
    'useCustomCurve': QBoolWidget
}

COMPONENT_SETTINGS_DEBUG = {
    'type': QComponentComboBox,
    'id': QReadOnlyStringWidget,
    'index': QReadOnlyIntWidget,
    'hidden': QReadOnlyBoolWidget,
    'enabled': QReadOnlyBoolWidget,
    'mainControlData': QReadOnlyStringWidget
}

COMPONENT_GROUPS = [
    ('General Settings', [
        'name',
        'target',
        'deformTargets',
        'isLeafJoint',
        'noFlipKnee'
    ]),
    ('Space Settings', [
        'parentSpace',
        'uprightSpace',
        'spaceSwitchEnabled'
    ]),
    ('Curve Settings', [
        'mainControlType',
        'mainControlScale',
        'mainControlColor',
        'useCustomCurve'
    ]),
    ('Squash and Stretch', [
        'stretchEnabled',
        'squashEnabled'
    ]),
    ('Secondary Curve Settings', [
        'baseCurveType',
        'baseCurveScale',
        'baseCurveParentSpace',
        'baseCurveUprightSpace',
        'secondaryParentSpace',
        'secondaryUprightSpace'
    ]),
    ('Extra Curve Settings', [
        'childControlType',
        'childControlScale',
        'offsetCurveType',
        'offsetCurveScale',
        'poleCurveScale',
        'poleCurveType',
        'spineControlType',
        'spineControlScale'
    ]),
    ('Debug', [
        'type',
        'id',
        'index',
        'hidden',
        'enabled',
        'mainControlData'
    ])
]

TEST_COMPONENT_TYPES = {
    'Component': {
        'name': 'defaultComponent',
        'type': 'Component',
        'mainControlType': 'default',
        'mainControlScale': 10.0,
        'target': None,
        'aimAxis': [0,1,0],
        'parentSpace': None,
        'uprightSpace': None,
        'icon': ":/cube.png"
    },
    'FKComponent': {
        'name': 'defaultFKComponent',
        'type': 'FKComponent',
        'mainControlType': 'default',
        'mainControlScale': 10.0,
        'target': None,
        'deformTargets': [],
        'aimAxis': [1,0,0],
        'parentSpace': None,
        'uprightSpace': None,
        'stretchEnabled': False,
        'squashEnabled': False,
        'icon': ":/joint.svg"
    },
    'IKComponent': {
        'name': 'defaultIKComponent',
        'type': 'IKComponent',
        'mainControlType': 'cube',
        'mainControlScale': 10.0,
        'target': None,
        'deformTargets': [],
        'aimAxis': [1,0,0],
        'parentSpace': None,
        'uprightSpace': None,
        'stretchEnabled': False,
        'squashEnabled': False,
        'icon': ":/ikHandle.svg"
    },
    'MultiFKComponent': {
            'name': 'defaultMultiFKComponent',
            'type': 'MultiFKComponent',
            'mainControlType': 'square',
            'mainControlScale': 20.0,
            'childControlType': 'default',
            'childControlScale': 10.0,
            'deformTargets': [],
            'aimAxis': [1,0,0],
            'parentSpace': None,
            'uprightSpace': None,
            'stretchEnabled': False,
            'squashEnabled': False,
            'icon': ":/ikHandle.svg",
            'enabled': True
        }
}

CONTROL_TYPES = [
    'default',
    'square',
    'circle',
    'cube',
    'star'
]

TEST_COMPONENT_DATA = {
    'legID': {
        'index': 0,
        'type': 'IKComponent',
        'name': 'leg_L',
        'deformTargets': ['ethan_thigh_L', 'ethan_knee_L', 'ethan_foot_L'],
        'mainControlType': 'cube',
        'mainControlScale': 10.0,
        'aimAxis': [1, 0, 0],
        'parentSpace': 'hipID',
        'uprightSpace': 'hipID',
        'hidden': False,
        'stretchEnabled': False,
        'squashEnabled': False
    },
    'hipID': {
        'index': 1,
        'type': 'FKComponent',
        'name': 'hips_M',
        'deformTargets': ['ethan_hips'],
        'mainControlType': 'square',
        'aimAxis': [1, 0, 0],
        'parentSpace': 'rootID',
        'uprightSpace': 'rootID',
        'hidden': False

    },
    'rootID': {
        'index': 2,
        'type': 'Component',
        'name': 'root_M',
        'deformTargets': ['ethan_root'],
        'mainControlType': 'circle',
        'aimAxis': [1, 0, 0],
        'parentSpace': None,
        'uprightSpace': None,
        'hidden': False
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
    logger.addHandler(stream_handler)
    logger.setLevel(logging.DEBUG)

    # Create a reference to the application
    app = QtWidgets.QApplication([])

    # Create the main window
    mainWindow = MainComponentWindow()

    # Create the ui controller
    controller = TestViewController(mainWindow, TEST_COMPONENT_DATA, CONTROL_TYPES, TEST_COMPONENT_TYPES)

    controller.loadRig('test')

    # Show the main window
    mainWindow.show()

    # Begin the event loop
    app.exec_()

if __name__ == '__main__':
    _test()

