from Qt import QtCore, QtWidgets, QtGui
Signal = QtCore.Signal


class ControlCreatorController(QtCore.QObject):
    controllerLibraryChanged = Signal(list)


class ControlWindow(QtWidgets.QMainWindow):
    createAtOriginClicked = Signal(str, str, str, str, str, str, str, bool, str)
    createAtSelectionClicked = Signal(str, str, str, str, str, str, str, bool, str)
    addShapeClicked = Signal(str)
    removeShapeClicked = Signal(str)


def create_window(controller, parent = None):
    ##### The Window #####
    window = ControlWindow(parent)
    window.setWindowTitle('Coles Control Creator')

    mainContainer = QtWidgets.QWidget(window)
    mainLayout = QtWidgets.QHBoxLayout(mainContainer)
    mainContainer.setLayout(mainLayout)



    ##### The Control Side #####
    controlCreationContainer = QtWidgets.QWidget(mainContainer)
    controlCreationLayout = QtWidgets.QVBoxLayout(controlCreationContainer)
    controlCreationContainer.setLayout(controlCreationLayout)
    mainLayout.addWidget(controlCreationContainer)

    # Control Name Settings
    controlNameContainer = QtWidgets.QWidget(controlCreationContainer)
    controlNameLayout = QtWidgets.QHBoxLayout(controlNameContainer)
    controlNameContainer.setLayout(controlNameLayout)
    controlCreationLayout.addWidget(controlNameContainer)

    nameLabel = QtWidgets.QLabel('Control Name: ', controlNameContainer)
    controlNameLayout.addWidget(nameLabel)

    nameLineEdit = QtWidgets.QLineEdit(controlNameContainer)
    controlNameLayout.addWidget(nameLineEdit)

    # Rotate Settings
    rotateContainer = QtWidgets.QWidget(controlCreationContainer)
    rotateLayout = QtWidgets.QHBoxLayout(rotateContainer)
    rotateContainer.setLayout(rotateLayout)
    controlCreationLayout.addWidget(rotateContainer)

    rotateLabel = QtWidgets.QLabel('Rotate X Y Z', rotateContainer)
    rotateLayout.addWidget(rotateLabel)

    rotateScaleValidator = QtGui.QDoubleValidator()

    rotateXLineEdit = QtWidgets.QLineEdit(rotateContainer)
    rotateLayout.addWidget(rotateXLineEdit)
    rotateXLineEdit.setValidator(rotateScaleValidator)
    rotateXLineEdit.setText("0.0")
    rotateYLineEdit = QtWidgets.QLineEdit(rotateContainer)
    rotateLayout.addWidget(rotateYLineEdit)
    rotateYLineEdit.setValidator(rotateScaleValidator)
    rotateYLineEdit.setText("0.0")
    rotateZLineEdit = QtWidgets.QLineEdit(rotateContainer)
    rotateLayout.addWidget(rotateZLineEdit)
    rotateZLineEdit.setValidator(rotateScaleValidator)
    rotateZLineEdit.setText("0.0")

    # Scale Settings
    scaleContainer = QtWidgets.QWidget(controlCreationContainer)
    scaleLayout = QtWidgets.QHBoxLayout(scaleContainer)
    scaleContainer.setLayout(scaleLayout)
    controlCreationLayout.addWidget(scaleContainer)

    scaleLabel = QtWidgets.QLabel('Scale X Y Z', scaleContainer)
    scaleLayout.addWidget(scaleLabel)

    scaleXLineEdit = QtWidgets.QLineEdit(scaleContainer)
    scaleLayout.addWidget(scaleXLineEdit)
    scaleXLineEdit.setValidator(rotateScaleValidator)
    scaleXLineEdit.setText("1.0")
    scaleYLineEdit = QtWidgets.QLineEdit(scaleContainer)
    scaleLayout.addWidget(scaleYLineEdit)
    scaleYLineEdit.setValidator(rotateScaleValidator)
    scaleYLineEdit.setText("1.0")
    scaleZLineEdit = QtWidgets.QLineEdit(scaleContainer)
    scaleLayout.addWidget(scaleZLineEdit)
    scaleZLineEdit.setValidator(rotateScaleValidator)
    scaleZLineEdit.setText("1.0")

    #Freeze Transform Setting
    FTransformCheckBox = QtWidgets.QCheckBox('Freeze Transforms', controlCreationContainer)
    controlCreationLayout.addWidget(FTransformCheckBox)

    #Create Buttons
    createButtonContainer = QtWidgets.QWidget(controlCreationContainer)
    createButtonLayout = QtWidgets.QHBoxLayout(createButtonContainer)
    createButtonContainer.setLayout(createButtonLayout)
    controlCreationLayout.addWidget(createButtonContainer)

    createAtOriginButton = QtWidgets.QPushButton('Create at Origin', createButtonContainer)
    createButtonLayout.addWidget(createAtOriginButton)

    def onCreateAtOriginButtonClicked():
        if shapeList.selectedItems().count > 0:
            window.createAtOriginClicked.emit(nameLineEdit.text(), rotateXLineEdit.text(), rotateYLineEdit.text(), rotateZLineEdit.text(), scaleXLineEdit.text(), scaleYLineEdit.text(), scaleZLineEdit.text(), FTransformCheckBox.isChecked(), shapeList.selectedItems()[0].text())
    createAtOriginButton.clicked.connect(onCreateAtOriginButtonClicked)

    createAtSelectionButton = QtWidgets.QPushButton('Create at Selection', createButtonContainer)
    createButtonLayout.addWidget(createAtSelectionButton)

    def onCreateAtSelectionButtonClicked():
        if shapeList.selectedItems().count > 0:
            window.createAtSelectionClicked.emit(nameLineEdit.text(), rotateXLineEdit.text(), rotateYLineEdit.text(), rotateZLineEdit.text(), scaleXLineEdit.text(), scaleYLineEdit.text(), scaleZLineEdit.text(), FTransformCheckBox.isChecked(), shapeList.selectedItems()[0].text())
    createAtSelectionButton.clicked.connect(onCreateAtSelectionButtonClicked)



    ##### The Shape Side #####
    shapeManagementContainer = QtWidgets.QWidget(mainContainer)
    shapeManagementLayout = QtWidgets.QVBoxLayout(shapeManagementContainer)
    shapeManagementContainer.setLayout(shapeManagementLayout)
    mainLayout.addWidget(shapeManagementContainer)

    #Shape Library
    shapeLabel = QtWidgets.QLabel("Shape Library", shapeManagementContainer)
    shapeManagementLayout.addWidget(shapeLabel)

    shapeList = QtWidgets.QListWidget(shapeManagementContainer)
    shapeManagementLayout.addWidget(shapeList)


    def update_shapeList(newShapeList):
        shapeList.clear()
        for shape in newShapeList:
            shapeList.addItem( str(shape) )
            shapeList.repaint()
        if len(shapeList.selectedItems()) == 0:
            shapeList.setCurrentRow(0)
    controller.controllerLibraryChanged.connect(update_shapeList)

    #Shape Name
    shapeNameContainer = QtWidgets.QWidget(shapeManagementContainer)
    shapeNameLayout = QtWidgets.QHBoxLayout(shapeNameContainer)
    shapeNameContainer.setLayout(shapeNameLayout)
    shapeManagementLayout.addWidget(shapeNameContainer)

    shapeNameLabel = QtWidgets.QLabel('Shape Name: ', shapeNameContainer)
    shapeNameLayout.addWidget(shapeNameLabel)

    shapeNameLineEdit = QtWidgets.QLineEdit(shapeNameContainer)
    shapeNameLayout.addWidget(shapeNameLineEdit)

    #Shape Buttons
    shapeButtonContainer = QtWidgets.QWidget(shapeManagementContainer)
    shapeButtonLayout = QtWidgets.QHBoxLayout(shapeButtonContainer)
    shapeButtonContainer.setLayout(shapeButtonLayout)
    shapeManagementLayout.addWidget(shapeButtonContainer)

    addShapeButton = QtWidgets.QPushButton("Add Shape", shapeButtonContainer)
    shapeButtonLayout.addWidget(addShapeButton)

    def onAddShapeButtonClicked():
        if not shapeNameLineEdit.text() == "":
            window.addShapeClicked.emit(shapeNameLineEdit.text())
    addShapeButton.clicked.connect(onAddShapeButtonClicked)

    removeShapeButton = QtWidgets.QPushButton("Remove Shape", shapeButtonContainer)
    shapeButtonLayout.addWidget(removeShapeButton)

    def onRemoveShapeButtonClicked():
        if shapeList.count() > 1:
            window.removeShapeClicked.emit(shapeList.selectedItems()[0].text())
    removeShapeButton.clicked.connect(onRemoveShapeButtonClicked)



    window.setCentralWidget(mainContainer)

    return window


def _pytest():
    controller = ControlCreatorController()
    shapeList = {"Shape1", "Shape2", "Shape3"}

    def onCreateAtSelection(name, xRot, yRot, zRot, xScale, yScale, zScale, freeze, selection):
        print ("Create at Selection Clicked! \n Name: %s \n Rotate X: %s Y: %s Z: %s \n Scale X: %s Y: %s Z: %s \n Freeze: %s \n Selection: %s " % ( name, float(xRot), float(yRot), float(zRot), float(xScale), float(yScale), float(zScale), freeze, selection))
    def onCreateAtOrigin(name, xRot, yRot, zRot, xScale, yScale, zScale, freeze, selection):
        print ("Create at Selection Clicked! \n Name: %s \n Rotate X: %s Y: %s Z: %s \n Scale X: %s Y: %s Z: %s \n Freeze: %s \n Selection: %s " % (name, float(xRot), float(yRot), float(zRot), float(xScale), float(yScale), float(zScale), freeze, selection ))
    def onAddShape(name):
        controller.controllerLibraryChanged.emit(shapeList)
        print ("Add Shape Clicked!")
    def onRemoveShape(selection):
        print ("Remove Shape Clicked! \n Selected Object: " + selection)

    app = QtWidgets.QApplication([])
    win = create_window(controller)
    win.createAtOriginClicked.connect(onCreateAtOrigin)
    win.createAtSelectionClicked.connect(onCreateAtSelection)
    win.addShapeClicked.connect(onAddShape)
    win.removeShapeClicked.connect(onRemoveShape)
    win.show()
    app.exec_()


if __name__ == '__main__':
    _pytest()


