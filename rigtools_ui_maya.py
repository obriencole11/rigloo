import rigtools
import rigtools_ui as ui
import controltools
import pymel.core as pmc
import logging
from Qt import QtCore, QtWidgets
from Qt.QtCore import Slot, Signal
import os

##############################
#          Logging           #
##############################

logging.basicConfig(filename=os.path.join(os.environ['MAYA_APP_DIR'],'fossil.log'),
                    format='%(levelname)s:%(name)s:%(message)s',
                    level=logging.WARNING)

class ModelController(ui.ViewController):

    def __init__(self, *args, **kwargs):
        ui.ViewController.__init__(self, *args, **kwargs)

        try:
            self._currentRig = self._model.activeRigs[0]
            self.logger.debug('Found an active rig in the model, setting it as the current rig')
            self.onNewRig.emit()
            self._refreshView()

        except IndexError:
            self.logger.info('No active rigs found, creating a new one')
            self.createRig()

    ##### View Slots #####

    @Slot(str, dict)
    def setComponentValue(self, id, data):
        # This takes the data from the ui
        # And sends it to the model for storage
        self.logger.debug('Updating component data for %s', data['name'])

        for argument, value in data.iteritems():
            self._model.setComponentValue(self._currentRig, id, argument, value)

        self._refreshView()

    @Slot(str)
    def addComponent(self, componentType):
        # Tells the model to add a new component
        # Then refreshes the view's components
        self.logger.debug('Adding a new %s component to the rig', str(componentType))

        self._loadViewData()
        id = self._model.addComponent(self._currentRig, componentType)
        self.addSelected(id)
        self._refreshView()

    @Slot(str)
    def removeComponent(self, id):
        # Tells the model to remove the specified component
        # Then refreshed the view
        self.logger.debug('Removing a %s component from the rig', self.componentData[id])
        self._loadViewData()
        self._model.removeComponent(self._currentRig, id)
        self._refreshView()

    @Slot(str)
    def addSelected(self, id):
        # Adds selected joints to the specified component
        # Then refresh the view
        self.logger.debug('Adding selected joints to a %s component', self.componentData[id])
        self._loadViewData()
        selected = pmc.selected()
        nameData = [target.name() for target in selected]
        oldData = self.componentData[id]

        try:
            oldData['deformTargets'].extend(nameData)
        except KeyError:
            try:
                oldData['target'] = nameData[0]
                self.logger.info('No deform targets found in data for %s, instead adding a target', self.componentData[id])
            except IndexError:
                self.logger.info('Looks like nothing is selected, ignoring add selected.')
                pass

        self.setComponentValue(id, oldData)

        self._refreshView()

    @Slot()
    def createRig(self):
        # Tells the model to create a rig with the specified name
        # Tells the view to show the componentData widget and refresh the components

        self.logger.debug('Creating a new rig')

        self._currentRig = self._model.createRig()
        self.onNewRig.emit()
        self._refreshView()

    @Slot(str)
    def loadRig(self, directory):
        # Tells the model to load the specified rig
        # tells the view to show the componentData and refresh the components
        self.logger.debug('Loading a rig from %s', directory)
        self._currentRig = self._model.loadRig(directory)
        self.onNewRig.emit()
        self._refreshView()

    @Slot()
    def saveRig(self):
        # Saves the active rig to the model's data
        self.logger.debug('Saving the rig')
        self._loadViewData()
        self._model.saveRig(self._currentRig)

    @Slot(str)
    def saveRigAs(self, directory):

        self.logger.debug('Saving rig in %s', directory)
        self._loadViewData()
        self._currentRig = self._model.saveRigAs(directory, self._currentRig)
        self.onNewRig.emit()
        self._refreshView()

    @Slot()
    def removeRig(self):
        self.logger.debug('Removing the current rig and clearing the cache')

        self._model.loadSceneData(self._currentRig)

        # Try to remove the current rig
        self._model.removeRig(self._currentRig)

        # Then remove the rig from fileInfo
        self._model.clearCache(self._currentRig)

    @Slot()
    def previewRig(self):

        if self._model.isReady(self._currentRig) is None:
            self.logger.debug('Rig is ready to build, refreshing the rig')

            # Remove the rig
            self.removeRig()

            self._loadViewData()

            # Then build the rig
            self._model.buildRig(self._currentRig)

        else:
            self.logger.debug('showing error')
            self._showError(self._model.isReady(self._currentRig))

    @Slot()
    def bindRig(self):
        self.logger.debug('Attempting to bind the current rig.')

        # Refresh the rig
        self.previewRig()

        # If bake mode is on, bake the rig first
        if self._bakeMode:
            self.logger.debug('Bake mode is set to True, baking to rig.')
            self._model.bakeRig(self._currentRig)

        # Then bind it to the skeleton
        self.logger.debug('Binding rig to skeleton, caching the rig.')
        self._model.bindRig(self._currentRig)

        # And cache the rig
        self._model.cacheRig(self._currentRig)

    @Slot(str)
    def switchActiveRig(self, rigName):
        # This will tell the model to switch the active rig
        self._loadViewData()
        self._currentRig = rigName
        self.logger.debug('Active rig switched to %s', rigName)
        self._refreshView()

    @Slot()
    def removePreview(self):
        # This removes the rig, but only when previewed
        # This is useful for when the window closes
        self.logger.debug('Removing the preview')
        self._model.loadSceneData()
        self._model.removePreview(self._currentRig)

    #### Private Methods ####

    def _refreshView(self):
        # Update the view's componentData
        # Tell the view to regenerate components
        self.logger.debug('Refreshing the view.')
        self.onRefreshComponents.emit(self.componentData, self.componentTypeData,
                                      self.controlTypeData, self.componentSettings,
                                      self._model.activeRigs, self._currentRig)

    def _loadViewData(self):
        # Update the model with new data from the view
        data = self._window.data

        for id, componentData in data.iteritems():
            self.setComponentValue(id, componentData)

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

        # Setup the loggers


        # Grab the maya application and the main maya window
        app = QtWidgets.QApplication.instance()
        mayaWindow = {o.objectName(): o for o in app.topLevelWidgets()}["MayaWindow"]

        # Create the window
        mainWindow = ui.MainComponentWindow(mayaWindow)

        # Create the data
        data = rigtools.RigToolsData()

        # Create the model
        model = rigtools.RigToolsModel(data)

        # Create the controller
        controller = MayaController(mainWindow, model)

    # Show the window
    #mainWindow.show(dockable=True, area='right', allowedArea = "right")
    mainWindow.show()

# from rigtools import rigtools_ui_maya; reload(rigtools_ui_maya); rigtools_ui_maya.show()