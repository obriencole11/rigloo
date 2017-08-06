import rigloo_tools
import rigloo_ui as ui
import controltools
import pymel.core as pmc
import logging
from Qt import QtCore, QtWidgets, QtGui
from Qt.QtCore import Slot, Signal
import os
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin

##############################
#          Logging           #
##############################

file_handler = logging.FileHandler(os.path.join(os.environ['MAYA_APP_DIR'],'fossil.log'))
file_handler.setFormatter(logging.Formatter('%(asctime)s : %(name)s : %(levelname)s : %(message)s'))
file_handler.setLevel(logging.DEBUG)

LOGS = []
FILE_LOGS = []
LOG_LEVEL = logging.DEBUG

def addLogger(name=__name__):

    # Add a logger for the specified name
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)

    # Add a logger for printing to a log file
    fileLogger = logging.getLogger(name+'_file')
    fileLogger.propagate = False

    # Add the module file handler
    fileLogger.handlers = []
    fileLogger.addHandler(file_handler)

    # Add the logger to a list of logs
    LOGS.append(logger)
    FILE_LOGS.append(fileLogger)

    return logger

def setLogLevel(level):

    global LOG_LEVEL

    LOG_LEVEL = level

    for logger in LOGS:
        logger.setLevel(level)

    ui.setLogLevel(level)
    rigloo_tools.setLogLevel(level)

def removeLogHandlers():

    for logger in LOGS:
        logger.debug('Removed handler')
        del logger

    for logger in FILE_LOGS:
        logger.debug('Removed handler')

        for handler in logger.handlers:
            handler.close()

        del logger

    ui.removeLogHandlers()
    rigloo_tools.removeLogHandlers()


##############################
#     Utility Functions      #
##############################

def maya_api_version():
    return int(pmc.about(api=True))

##############################
#       Window Classes       #
##############################

class MayaComponentWindow(MayaQWidgetDockableMixin, ui.MainComponentWindow):
    '''
    A version specific to maya that works with Maya's docking.
    Based on source code from: https://gist.github.com/liorbenhorin/217bfb7e54c6f75b9b1b2b3d73a1a43a
    '''

    MAYA2014 = 201400
    MAYA2015 = 201500
    MAYA2016 = 201600
    MAYA2016_5 = 201650
    MAYA2017 = 201700

    def __init__(self, parent=None):

        # Grab a reference to the maya main window (presumably the parent)
        self.mayaMainWindow = parent

        # Remove any instances of this window
        self.deleteInstances()

        # Init the base window class
        super(MayaComponentWindow, self).__init__(parent=parent)

        # Makes Qt delete this widget when the widget has accepted the close event
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Repaint the main widget, this fixes some maya updating issues
        self.repaint()


    def deleteInstances(self):

        def delete2016():
            # Go through main window's children to find any previous instances
            for obj in self.mayaMainWindow.children():

                if str(type(
                        obj)) == "<class 'maya.app.general.mayaMixin.MayaQDockWidget'>":  # ""<class 'maya.app.general.mayaMixin.MayaQDockWidget'>":

                    if obj.widget().__class__.__name__ == "MayaComponentWindow":  # Compare object names

                        obj.setParent(None)
                        obj.deleteLater()

        def delete2017():
            '''
            Look like on 2017 this needs to be a little diffrents, like in this function,
            However, i might be missing something since ive done this very late at night :)
            '''

            for obj in self.mayaMainWindow.children():

                if str(type(obj)) == "<class '{}.MayaComponentWindow'>".format(os.path.splitext(
                        os.path.basename(__file__)[0])):  # ""<class 'moduleName.mayaMixin.MyDockingWindow'>":

                    if obj.__class__.__name__ == "MayaComponentWindow":  # Compare object names

                        obj.setParent(None)
                        obj.deleteLater()

        if maya_api_version() < MayaComponentWindow.MAYA2017:
            delete2016()
        else:
            delete2017()

    def deleteControl(self, control):

        if pmc.workspaceControl(control, q=True, exists=True):
            pmc.workspaceControl(control, e=True, close=True)
            pmc.deleteUI(control, control=True)

    # Show window with docking ability
    def run(self):
        '''
        2017 docking is a little different...
        '''

        def run2017():

            self.setObjectName("MayaComponentWindow")

            # The deleteInstances() dose not remove the workspace control, and we need to remove it manually
            workspaceControlName = self.objectName() + 'WorkspaceControl'
            self.deleteControl(workspaceControlName)

            # this class is inheriting MayaQWidgetDockableMixin.show(), which will eventually call maya.cmds.workspaceControl.
            # I'm calling it again, since the MayaQWidgetDockableMixin dose not have the option to use the "tabToControl" flag,
            # which was the only way i found i can dock my window next to the channel controls, attributes editor and modelling toolkit.
            self.show(dockable=True, area='right', floating=False)
            pmc.workspaceControl(workspaceControlName, e=True, ttc=["AttributeEditor", -1], wp="preferred",
                                  mw=350)
            self.raise_()

            # size can be adjusted, of course
            self.setDockableParameters(width=350)


        def run2016():
            self.setObjectName("MayaComponentWindow")
            # on maya < 2017, the MayaQWidgetDockableMixin.show() magiclly docks the window next
            # to the channel controls, attributes editor and modelling toolkit.
            self.show(dockable=True, area='left', floating=True)
            self.raise_()
            # size can be adjusted, of course
            self.setDockableParameters(width=300)
            self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Preferred)
            self.setMinimumWidth(300)
            self.setMaximumWidth(600)

        if maya_api_version() < MayaComponentWindow.MAYA2017:
            run2016()
        else:
            run2017()

##############################
#     Controller Classes     #
##############################

class ModelController(ui.ViewController):

    def __init__(self, *args, **kwargs):
        ui.ViewController.__init__(self, *args, **kwargs)

        try:
            self._currentRig = self._model.activeRigs[0]
            self._currentRigBuilt = True
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

    @Slot(str, bool)
    def moveComponent(self, id, moveUp):
        self.logger.debug('Moving a %s component', self.componentData[id])
        self._loadViewData()
        self._model.moveComponent(self._currentRig, id, moveUp)
        self._refreshView()

    @Slot(str)
    def duplicateComponent(self, id):
        self.logger.debug('Duplicating a %s component', self.componentData[id])
        self._loadViewData()
        self._model.duplicateComponent(self._currentRig, id)
        self._refreshView()

    @Slot(str)
    def addSelected(self, id):
        # Adds selected joints to the specified component
        # Then refresh the view
        self.logger.debug('Adding selected joints to a %s component', self.componentData[id])
        self._loadViewData()
        selected = pmc.selected()
        oldData = self.componentData[id]

        try:
            nameData = [target.name() for target in selected if
                        target not in oldData['bindTargets'] and isinstance(target, pmc.nodetypes.DagNode)]

            oldData['bindTargets'].extend(nameData)
        except KeyError:
            try:
                nameData = [target.name() for target in selected if isinstance(target, pmc.nodetypes.DagNode)]
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
        self._currentRigBuilt = False

    @Slot(str)
    def loadRig(self, directory):
        # Tells the model to load the specified rig
        # tells the view to show the componentData and refresh the components
        self.logger.debug('Loading a rig from %s', directory)
        self._currentRig = self._model.loadRig(directory)
        self._currentRigBuilt = False
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

        self._loadViewData()

        self._model.loadSceneData(self._currentRig)

        self._refreshView()

        # Try to remove the current rig
        self._model.removeRig(self._currentRig, bakeMode=self.bakeMode)

        # Then remove the rig from fileInfo
        self._model.clearCache(self._currentRig)

        self._currentRigBuilt = False

    @Slot()
    def previewRig(self):

        if self._model.isReady(self._currentRig) is None:
            self.logger.debug('Rig is ready to build, refreshing the rig')

            # Remove the rig
            if self._currentRigBuilt:
                self.logger.debug('Rig is built, removing')
                self.removeRig()
            else:
                self.logger.debug('Rig is not built, skipping remove')
                self._loadViewData()

            # Then build the rig
            self._model.buildRig(self._currentRig)

            self._currentRigBuilt = True

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
        self.removePreview()
        self._currentRig = rigName
        self.logger.debug('Active rig switched to %s ', rigName)
        self._refreshView()

    @Slot()
    def removePreview(self):
        # This removes the rig, but only when previewed
        # This is useful for when the window closes
        self.logger.debug('Removing the preview')

        if self._currentRigBuilt:
            self.logger.debug('Rig is built, grabbing scene data')
            self._model.loadSceneData(self._currentRig)
        self._model.removePreview(self._currentRig)
        self._currentRigBuilt = False

    @Slot()
    def stopLogging(self):
        removeLogHandlers()

    #### Private Methods ####


    def _refreshView(self):
        # Update the view's componentData
        # Tell the view to regenerate components
        self.logger.debug('Refreshing the view.')
        self.onRefreshComponents.emit(self.componentData, self.componentTypeData,
                                      self.controlTypeData, self.componentSettings,
                                      self._model.activeRigs, self._currentRig)
        self.logger.debug('Refreshed view successfully')

    def _loadViewData(self):
        # Update the model with new data from the view

        for id, componentData in self._window.data.iteritems():
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
        return rigloo_tools.COMPONENT_TYPES

class MayaController(ModelController):

    def __init__(self, *args, **kwargs):
        ModelController.__init__(self, *args, **kwargs)

# Create a variable for the controller and the mainWindow
# This is so they will not be garbage-collected
mainWindow = None
controller = None

def load(debug=False):
    global mainWindow
    global controller
    global LOG_LEVEL

    logging.basicConfig(level=logging.DEBUG, filename=os.path.join(os.environ['MAYA_APP_DIR'],'rigloo.log'),
                        format=logging.Formatter('%(name)s : %(levelname)s : %(message)s'))

    if debug is True:
        LOG_LEVEL = setLogLevel(logging.DEBUG)
    else:
        LOG_LEVEL = setLogLevel(logging.WARNING)

    # If the window already exists, don't create a new one
    if mainWindow is None:

        # Grab the maya application and the main maya window
        app = QtWidgets.QApplication.instance()
        mayaWindow = {o.objectName(): o for o in app.topLevelWidgets()}["MayaWindow"]

        # Create the window
        mainWindow = MayaComponentWindow(mayaWindow)

        # Create the data
        data = rigloo_tools.RigToolsData()

        # Create the model
        model = rigloo_tools.RigToolsModel(data)

        # Create the controller
        controller = MayaController(mainWindow, model)

    # Show the window
    mainWindow.run()

# from rigloo_tools import rigloo_tools_ui_maya; reload(rigloo_tools_ui_maya); rigloo_tools_ui_maya.show()
