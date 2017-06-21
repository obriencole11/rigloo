import rigtools
import rigtools_ui as ui
import controltools
import pymel.core as pmc
import uuid
import logging
from Qt import QtCore, QtWidgets
from Qt.QtCore import Slot, Signal


##############################
#          Logging           #
##############################

# Create a logger for this module
logger = logging.getLogger(__name__)

# Create a formatter for all log statements
formatter = logging.Formatter('%(levelname)s:%(message)s')

# Create a handler for logging to the console
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
stream_handler.setLevel(logging.DEBUG)

# Enable logging to the console
logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)


class ModelController(ui.ViewController):

    def __init__(self, *args, **kwargs):
        ui.ViewController.__init__(self, *args, **kwargs)

        self._currentRig = None


    ##### View Slots #####

    @Slot(str, dict)
    def setComponentValue(self, id, data):
        # This takes the data from the ui
        # And sends it to the model for storage
        for argument, value in data.iteritems():
            self._model.setComponentValue(self._currentRig, id, argument, value)

        self._refreshView()

    @Slot(str)
    def addComponent(self, componentType):
        # Tells the model to add a new component
        # Then refreshes the view's components
        self._model.addComponent(self._currentRig, componentType)
        self._refreshView()

    @Slot(str)
    def addSelected(self, id):
        # Adds selected joints to the specified component
        # Then refresh the view
        logger.info('Model Controller: Add Selected signal received. Value: ' + id)

        selected = pmc.selected()
        print selected
        nameData = [target.name() for target in selected]
        print nameData
        oldData = self.componentData[id]
        oldData['deformTargets'].extend(nameData)
        print oldData
        self.setComponentValue(id, oldData)

        self._refreshView()

    @Slot()
    def createRig(self):
        # Tells the model to create a rig with the specified name
        # Tells the view to show the componentData widget and refresh the components

        logger.info('Model Controller: CreateRig Signal Received')

        self._currentRig = self._model.createRig(uuid.uuid1().hex)
        self.onNewRig.emit()
        self._refreshView()

    @Slot()
    def loadRig(self):
        # Tells the model to load the specified rig
        # tells the view to show the componentData and refresh the components
        logger.info('Model Controller: LoadRig Signal Received')
        raise NotImplementedError
        #self._model.loadRig(name)
        #self.onNewRig.emit()
        #self._refreshView()

    @Slot()
    def saveRig(self):
        # Saves the active rig to the model's data
        logger.info('Model Controller: SaveRig Signal Received')
        self._model.saveRig(self._currentRig)

    @Slot()
    def buildRig(self):
        # If the model is not built, build it, otherwise remove it
        # Send update button signal on view
        if self.built:
            self._model.removeRig(self._currentRig)
        else:
            self._model.buildRig(self._currentRig)

        self.onBuiltStateChange.emit(self.built)

    @Slot()
    def bakeRig(self):
        # If the model is baked, bake it, otherwise unbake it
        # Send the update button signal for view
        if self.baked:
            self._model.bakeDeforms(self._currentRig)
        else:
            self._model.bakeRig(self._currentRig)

        self.onBakedStateChange.emit(self.baked)

    @Slot()
    def refreshRig(self):
        # Tell the model to refresh the rig
        self._model.refreshRig(self._currentRig)

    @Slot()
    def bindRig(self):
        # If the model is not bound, bind it, otherwise unbind it
        # Send the update button signal for view
        if self.bound:
            self._model.unbindRig(self._currentRig)
        else:
            self._model.bindRig(self._currentRig)

        self.onBoundStateChange.emit(self.bound)


    #### Private Methods ####

    def _refreshView(self):
        # Update the view's componentData
        # Tell the view to regenerate components
        self.onRefreshComponents.emit(self.componentData, self.componentTypeData, self.controlTypeData)


    ##### private properties #####

    @property
    def componentData(self):
        # Return the latest version of the model's componet Data
        return self._model.rigData(self._currentRig)

    @property
    def controlTypeData(self):
        # Return a list of just the keys from the controltools
        return [key for key, value in controltools.control_shapes.iteritems()]

    @property
    def componentTypeData(self):
        return rigtools.COMPONENT_TYPES

    @property
    def bound(self):
        # Return whether the rig is bound or not
        return self._model.isBound(self._currentRig)

    @property
    def built(self):
        # Return whether the rig is built or not
        return self._model.isBuilt(self._currentRig)

    @property
    def baked(self):
        # Return whether the rig is baked or not
        return self._model.isBaked(self._currentRig)


class MayaController(ModelController):

    def __init__(self, *args, **kwargs):
        ModelController.__init__(self, *args, **kwargs)

# Create a variable for the controller and the mainWindow
# This is so they will not be garbage-collected
mainWindow = None
controller = None


def show():
    global mainWindow
    global controller

    # If the window already exists, don't create a new one
    if mainWindow is None:

        # Grab the maya application and the main maya window
        app = QtWidgets.QApplication.instance()
        mayaWindow = {o.objectName(): o for o in app.topLevelWidgets()}["MayaWindow"]

        # Create the window
        mainWindow = ui.MayaComponentWindow(mayaWindow)
        #mainWindow = MyWindow(mayaWindow)
        #mayaWindow.addDockWidget(QtCore.Qt.LeftDockWidgetArea, mainWindow)

        # Create the data
        data = rigtools.RigToolsData()

        # Create the model
        model = rigtools.RigToolsModel(data)

        # Create the controller
        controller = MayaController(mainWindow, model)

    # Show the window
    mainWindow.show(dockable=True, area='right', allowedArea = "right")

# from rigtools import rigtools_ui_maya; reload(rigtools_ui_maya); rigtools_ui_maya.show()