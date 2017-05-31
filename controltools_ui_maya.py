import controltools
import controltools_ui as ui
from Qt import QtCore, QtWidgets
import pymel.core as pmc
Signal = QtCore.Signal

window = None

def show():
    global window
    if window is None:
        controller = ui.ControlCreatorController()
        def emit_libraryChanged():
            library = []
            for shape in controltools.control_shapes:
                library.append(shape)
            controller.controllerLibraryChanged.emit(library)

        app = QtWidgets.QApplication.instance()
        mainWindow = {o.objectName(): o for o in app.topLevelWidgets()}["MayaWindow"]
        parent = mainWindow
        window = ui.create_window(controller, parent)

        def onCreateAtSelection(name, xRot, yRot, zRot, xScale, yScale, zScale, freeze, selection):
            sel = pmc.ls(selection = True)
            curve = controltools.co_create_control_curve(selection)
            pmc.select(sel)
            controltools.co_move_to_selection(curve)
            controltools.co_rotate_curve(float(xRot), float(yRot), float(zRot), curve)
            controltools.co_scale_curve(float(xScale), float(yScale), float(zScale), curve)
            if freeze:
                controltools.co_freeze_transforms(curve)
            controltools.co_name_curve(name, curve)
        window.createAtSelectionClicked.connect(onCreateAtSelection)

        def onCreateAtOrigin(name, xRot, yRot, zRot, xScale, yScale, zScale, freeze, selection):
            curve = controltools.co_create_control_curve(selection)
            controltools.co_rotate_curve( float(xRot), float(yRot), float(zRot), curve)
            controltools.co_scale_curve(float(xScale), float(yScale), float(zScale), curve)
            if freeze:
                controltools.co_freeze_transforms(curve)
            controltools.co_name_curve(name, curve)
        window.createAtOriginClicked.connect(onCreateAtOrigin)

        def onAddShape(name):
            controltools.co_cache_selected_curve(name)
            emit_libraryChanged()
        window.addShapeClicked.connect(onAddShape)

        def onRemoveShape(selection):
            controltools.co_remove_curve(selection)
            emit_libraryChanged()
        window.removeShapeClicked.connect(onRemoveShape)



    window.show()
    emit_libraryChanged()


