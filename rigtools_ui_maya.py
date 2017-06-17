import rigtools
import rigtools_ui as ui
import controltools
from Qt import QtCore, QtWidgets
from QtCore import Slot, Signal

class MayaController(ui.MainController):

    def __init__(self, window, parent=None):
        ui.MainController.__init__(self, window, parent)


    #### Public Properties ####

    @property
    def rig(self):
        return self._rig

    @rig.setter
    def rig(self, value):
        self._rig = value

        self.onRigUpdated.emit()

    @property
    def components(self):

        return rigtools.COMPONENT_TYPES

    @property
    def controls(self):
        controls = {}

        for key, value in controltools.control_shapes.iteritems():
            controls[key] = key

        return controls

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

# Stores the current instance of the window
window = None

def show():
    global window

    # If the window already exists, don't create a new one
    if window is None:

        # Grab the maya application and the main maya window
        app = QtWidgets.QApplication.instance()
        mayaWindow = {o.objectName(): o for o in app.topLevelWidgets()}["MayaWindow"]

        # Create the window
        window = ui.MainComponentWindow()

        # Create the controller
        controller = MayaController(window, mayaWindow)

    # Show the window
    window.show()
