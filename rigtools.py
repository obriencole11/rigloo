import pymel.core as pmc
import pymel.core.datatypes as dt
import skeltools
import nametools
import controltools


#### Control Classes ####
class Rig():
    def __init__(self):
        pass

    def build(self):
        pass

class Control():
    '''
    Represents a very basic control.
    Supports:
        - A control curve
        - A position to spawn at
        - A parent space
        - Variable scale
        - A local up vector
    '''

    def __init__(self, transform=None, name='defaultControl', curve='default', parent=None, parentSpace=None, uprightSpace=None, upVector=dt.Vector(0,1,0), scale=(10.0, 10.0, 10.0), **kwargs):
        self.transform = transform
        self.name = name
        self.curve = curve
        self.parent = parent
        self.parentSpace = parentSpace
        self.uprightSpace = uprightSpace
        if uprightSpace is None:
            uprightSpace = parentSpace
        self.upVector = upVector
        self.scale = scale
        self.utilityNodes = {}

    def build(self):
        # Create the main control curve
        self.control = controltools.create_control_curve(self.curve)
        pmc.rename(self.control, self.name+'_CTRL')
        match_target_orientation(target=None, object=self.control, upVector=self.upVector)

        # Create the local space for the control
        # This is better at preserving transforms than freezing transforms
        self.localSpaceGroup = pmc.group(empty=True, name=self.name+'_LOC_SPC')

        # Transform/Scale/Rotate localSpaceGroup and parent the control curve to it
        #controltools.move_to_transform(self.localSpaceGroup, self.transform, self.upVector)
        if self.transform is not None:
            match_target_orientation(self.transform, self.localSpaceGroup, self.upVector)
        self.localSpaceGroup.setScale(scale=self.scale)
        pmc.parent(self.control, self.localSpaceGroup, relative=True)

        # Add parentSpace and uprightSpace groups and connections
        add_parent_space(self)

        return self.control

    def remove(self):
        raise NotImplementedError()

class Stretchable():
    '''
    Squash and stretch support for controls
    '''

    def __init__(self, stretchJoints=[], globalControl=None, stretchEnabled=False, squashEnabled=False,
                 scaleAxis=None, stretchScale=2.0, stretchMin=0.0, **kwargs):
        self.stretchJoints = stretchJoints
        self.globalControl = globalControl
        self.stretchEnabled = stretchEnabled
        self.squashEnabled = squashEnabled
        self.scaleAxis = scaleAxis
        if scaleAxis is None:
            self.scaleAxis = self.upVector
        self.stretchScale = stretchScale
        self.stretchMin = stretchMin

    def build(self):
        if self.stretchEnabled:
            add_squash_and_stretch(self)

class FKControl(Control, Stretchable):
    '''
    Represents a basic joint control. 
    Features a target joint that is driven by the control curve.
    '''
    def __init__(self, targetJoint, **kwargs):
        Control.__init__(self, **kwargs)
        Stretchable.__init__(self, **kwargs)

        self.targetJoint = targetJoint

    def build(self):
        # Build the basic control curve structure
        Control.build(self)

        # Connect the target joint to the controller
        connect_joint_to_controller(self)

        Stretchable.build(self)

        return self.control

class IKControl(Control, Stretchable):
    '''
    A basic IK control
    '''

    def __init__(self, targetJoint, endJoint, rotatePlaneSolver=False, poleJoint=None, **kwargs):
        Control.__init__(self, **kwargs)
        Stretchable.__init__(self, **kwargs)

        self.targetJoint = targetJoint
        self.endJoint = endJoint
        self.rotatePlaneSolver = rotatePlaneSolver
        self.poleJoint = poleJoint
        self.stretchMin = 1.0

    def build(self):
        Control.build(self)

        add_ik_handle(self)

        if self.rotatePlaneSolver is True:
            add_pole_vector(self)

        self.constraint = pmc.orientConstraint(self.control, self.targetJoint, mo=True)

        Stretchable.build(self)

        return self.control

    # add_squash_and_stretch(self):
        #add_squash_and_stretch_complex(self)

class GlobalControl(Control):
    '''
    Represents the global controller.
    Features scale control.
    '''
    def __init__(self, scaleGroup, **kwargs):
        Control.__init__(self, **kwargs)
        self.scaleGroup = scaleGroup

    def build(self):
        Control.build(self)
        pmc.parentConstraint(self.control, self.scaleGroup, mo=True)
        pmc.connectAttr(self.control.scale, self.scaleGroup.scale)

        return self.control



#### Control Functions ####
def add_parent_space(control):
    '''
    Adds a parentspace group and an uprightSpace group.
    Adds utility nodes to create a modular parent relationship.
    :param control: The Control object to operate on.
    :return: None
    '''

    # Grab the original position of the control
    oldMatrix = control.localSpaceGroup.getMatrix(worldSpace=True)

    # Create the parentSpace and uprightSpace groups and parent the controls to them
    control.uprightSpaceGroup = pmc.group(empty=True, name=control.name + '_UPR_SPC')
    pmc.parent(control.localSpaceGroup, control.uprightSpaceGroup)
    control.parentSpaceGroup = pmc.group(empty=True, name=control.name + '_PAR_SPC')
    pmc.parent(control.uprightSpaceGroup, control.parentSpaceGroup)

    # Create the matrix utility nodes
    uprightMultMatrixNode = pmc.createNode('multMatrix', name=control.name + '_UPR_MM_NODE')
    uprightDecomposeMatrixNode = pmc.createNode('decomposeMatrix', name=control.name + '_UPR_DEC_NODE')
    parentMultMatrixNode = pmc.createNode('multMatrix', name=control.name + '_PAR_MM_NODE')
    parentDecomposeMatrixNode = pmc.createNode('decomposeMatrix', name=control.name + '_PAR_DEC_NODE')

    # If a parent is specified, connect it to the multiply Matrix node
    # If not, connect the identity matrix
    # This will be the transformations to reach the parent's space
    if control.parentSpace is not None:
        pmc.connectAttr(control.parent.control.worldMatrix[0], parentMultMatrixNode.matrixIn[0])
    else:
        identityMatrix = dt.Matrix()
        pmc.setAttr(parentMultMatrixNode.matrixIn[0], identityMatrix)

    # Check if an uprightParent is specified, connect it to the multiply Matrix node
    # If not, connect the identity matrix
    if control.uprightSpace is not None:
        pmc.connectAttr(control.uprightSpace.control.worldMatrix[0], uprightMultMatrixNode.matrixIn[0])
    else:
        identityMatrix = dt.Matrix()
        pmc.setAttr(uprightMultMatrixNode.matrixIn[0], identityMatrix)

    # Connect the space group's inverse Matrix to the second matrix on the multiply Matrix node
    # This will reverse the transformations of the groups parent
    pmc.connectAttr(control.uprightSpaceGroup.parentInverseMatrix[0], uprightMultMatrixNode.matrixIn[1])
    pmc.connectAttr(control.parentSpaceGroup.parentInverseMatrix[0], parentMultMatrixNode.matrixIn[1])

    # Connect the multiply Matrix nodes into a corresponding decompose Matrix node
    # This will output the space transformations in vector format
    pmc.connectAttr(uprightMultMatrixNode.matrixSum, uprightDecomposeMatrixNode.inputMatrix)
    pmc.connectAttr(parentMultMatrixNode.matrixSum, parentDecomposeMatrixNode.inputMatrix)

    # Connect the decompose node's transformations to the corresponding groups transform values
    pmc.connectAttr(parentDecomposeMatrixNode.outputTranslate, control.parentSpaceGroup.translate)
    pmc.connectAttr(uprightDecomposeMatrixNode.outputRotate, control.uprightSpaceGroup.rotate)

    # Connect the parentSpace's scale to the parentSpace Group
    # This will allow the curves to scale with the global control
    pmc.connectAttr(parentDecomposeMatrixNode.outputScale, control.parentSpaceGroup.scale)

    # Move the localSpaceGroup back to its original position
    control.localSpaceGroup.setMatrix(oldMatrix, worldSpace=True)

    # Add the utility nodes into the control's utility node dictionary
    control.utilityNodes['uprightMultMatrixNode'] = uprightMultMatrixNode
    control.utilityNodes['parentMultMatrixNode'] = parentMultMatrixNode
    control.utilityNodes['uprightDecomposeMatrixNode'] = uprightDecomposeMatrixNode
    control.utilityNodes['parentDecomposeMatrixNode'] = parentDecomposeMatrixNode

def connect_joint_to_controller(jointControl):
    '''
    For now this just adds a parent constraint from the controller to the joint
    :param jointControl: The JointControl object.
    :return: None
    '''
    constraint = pmc.parentConstraint(jointControl.control, jointControl.targetJoint, mo=True)
    jointControl.constraint = constraint

def add_ik_handle(ikControl):
    handle = pmc.ikHandle(sj=ikControl.endJoint, ee=ikControl.targetJoint)
    pmc.parent(handle[0], ikControl.control)
    pmc.rename(handle[0], ikControl.name+'_HDL')
    pmc.rename(handle[1], ikControl.name+'_EFF')
    ikControl.handle = handle[0]

    pmc.addAttr(ikControl.control, ln='twist', at='double', k=True)
    pmc.connectAttr(ikControl.control.twist, ikControl.handle.twist)

def add_pole_vector(ikControl):
    ''' Creates an empty object at a correct polevector position'''

    # Grab the worldspace vectors of each points position
    startPoint = ikControl.endJoint.getTranslation(space='world')
    elbowPoint = ikControl.poleJoint.getTranslation(space='world')
    endPoint = ikControl.targetJoint.getTranslation(space='world')

    # Find the midpoint between the start and end joint
    averagePoint = (startPoint + endPoint) / 2

    # Find the direction from the midpoint to the elbow
    elbowDirection = elbowPoint - averagePoint

    # Multiply the direction by 2 to extend the range
    polePoint = (elbowDirection * 5) + averagePoint

    # Create empty transform and move it to the pole point
    poleObject = pmc.group(empty=True, name=ikControl.name+'_POLE_LOC')
    poleObject.setTranslation(polePoint, space='world')
    poleCurve = controltools.create_control_curve('triangle')
    pmc.rename(poleCurve, ikControl.name+'_POLE_CTRL')
    poleCurve.setMatrix(poleObject.getMatrix())
    poleCurve.setScale(scale=ikControl.scale)
    pmc.parent(poleObject, poleCurve)
    pmc.parent(poleCurve, ikControl.localSpaceGroup)

    # Normalize the polepoint, to get the direction to the elbow
    direction = polePoint.normal()

    # Get the Quaternion rotation needed to rotate from
    # the world up to the direction of the elbow
    rotation = (dt.Vector(0, 1, 0)).rotateTo(direction)

    # Rotate the locator by that ammount
    poleObject.rotateBy(rotation)

    pmc.poleVectorConstraint(poleObject, ikControl.handle)

    ikControl.poleControl = poleObject

def add_squash_and_stretch(control):

    # Settings
    scale = control.stretchScale
    min = control.stretchMin
    scaleAxis = control.scaleAxis

    # Create utility nodes
    # Float Math node is weird, 2 = Multiply, 3 = Divide, 5 = Max
    point1SpaceSwitch = pmc.createNode('multMatrix', name=control.name + '_P1_MM_NODE')
    point2SpaceSwitch = pmc.createNode('multMatrix', name=control.name + '_P2_MM_NODE')
    distanceBetween = pmc.createNode('distanceBetween', name=control.name + '_sqstrDist')
    maxDistanceDiv = pmc.createNode('floatMath', name=control.name + '_maxDistDiv')
    pmc.setAttr(maxDistanceDiv.operation, 3)
    scaleMult = pmc.createNode('floatMath', name=control.name + '_scaleMult')
    pmc.setAttr(scaleMult.operation, 2)
    outputMax = pmc.createNode('floatMath', name=control.name + '_max')
    pmc.setAttr(outputMax.operation, 5)
    inverseOutput = pmc.createNode('floatMath', name=control.name + '_inverse')
    pmc.setAttr(inverseOutput.operation, 3)

    # Create a locator to track the controller
    locator = pmc.spaceLocator()
    pmc.parent(locator, control.control, relative=True)

    # Calculate the max distance
    maxDistance = control.stretchJoints[0].getTranslation('world').distanceTo(control.control.getTranslation('world'))

    # Connect reference positions to matrix nodes to bring into globalControl space
    pmc.connectAttr(control.stretchJoints[0].worldMatrix[0], point1SpaceSwitch.matrixIn[0])
    pmc.connectAttr(control.globalControl.control.inverseMatrix, point1SpaceSwitch.matrixIn[1])
    pmc.connectAttr(locator.worldMatrix[0], point2SpaceSwitch.matrixIn[0])
    pmc.connectAttr(control.globalControl.control.inverseMatrix, point2SpaceSwitch.matrixIn[1])

    # Connect the matrix sums to distance node
    pmc.connectAttr(point1SpaceSwitch.matrixSum, distanceBetween.inMatrix1)
    pmc.connectAttr(point2SpaceSwitch.matrixSum, distanceBetween.inMatrix2)

    # Connect distance and max distance to division node
    pmc.connectAttr(distanceBetween.distance, maxDistanceDiv.floatA)
    pmc.setAttr(maxDistanceDiv.floatB, maxDistance * 2)

    # Connect normalized distance to multiply node
    pmc.connectAttr(maxDistanceDiv.outFloat, scaleMult.floatA)
    pmc.setAttr(scaleMult.floatB, scale)

    # Connect scaled output to the max node
    pmc.setAttr(outputMax.floatB, min)
    pmc.connectAttr(scaleMult.outFloat, outputMax.floatA)


    # Connect maxed output to the inverse node
    pmc.setAttr(inverseOutput.floatA, 1.0)
    pmc.connectAttr(outputMax.outFloat, inverseOutput.floatB)

    # Connect to stretch joint scales
    for joint in control.stretchJoints:
        axis = (joint.scaleX, joint.scaleY, joint.scaleZ)
        for x in range(3):
            if scaleAxis[x] == 1:
                pmc.connectAttr(outputMax.outFloat, axis[x])
            else:
                pmc.connectAttr(inverseOutput.outFloat, axis[x])

def match_target_orientation(target, object, upVector=dt.Vector(1, 0, 0)):
    '''
    Sets the object's matrix to the matrix of the target.
    Additionally applies the specified upVector.
    :param target: The transform to match.
    :param object: The object to transform. 
    :param upVector: The direction to point the space.
    :return: 
    '''

    # The world up vector
    worldUp = dt.Vector(0, 1, 0)

    # The Transformation matrix of the target in world space
    if target:
        targetSpace = target.getMatrix(worldSpace=True)
    else:
        targetSpace = dt.Matrix()

    # The input upVector transformed into target rotation space
    targetUp = upVector.rotateBy(targetSpace)

    # Create a Quaternion  to represent the rotation
    # From the object orientation to the target orientation
    rotation = worldUp.rotateTo(targetUp)
    object.setRotation(rotation, space='world')
    pmc.makeIdentity(object, apply=True, rotate=True, scale=False, translate=False)

    # Transform the object into the target space
    object.setMatrix(targetSpace, worldSpace=True)


def add_control_curve(transform, curveName='default', upVector=dt.Vector(0,1,0)):
    ''''''
    try:
        curve = controltools.create_control_curve(curveName)
    except KeyError:
        curve = controltools.create_control_curve('default')
    controltools.move_to_transform(curve, transform, upVector=upVector)
    controltools.freeze_transforms(curve)
    return curve






def set_control_scale(control):
    control.control.setScale(scale = (control.controlScale, control.controlScale, control.controlScale))
    pmc.makeIdentity(control.control, apply=True, translate=False, rotate=False, scale=True)

def switch_parent_space(control, parent=True, uprightParent=True):
    oldMatrix = control.jointspace.getMatrix(worldSpace=True)

    parentMultMatrixNode = control.utilityNodes['parentMultMatrixNode']
    uprightMultMatrixNode = control.utilityNodes['uprightMultMatrixNode']

    if parent:
        if control.parent is not None:
            pmc.connectAttr(control.parent.control.worldMatrix[0], parentMultMatrixNode.matrixIn[0], force=True)
        else:
            identityMatrix = dt.Matrix()
            pmc.disconnectAttr(parentMultMatrixNode.matrixIn[0])
            pmc.setAttr(parentMultMatrixNode.matrixIn[0], identityMatrix, force=True)

    if uprightParent:
        if control.uprightParent is not None:
            pmc.connectAttr(control.uprightParent.control.worldMatrix[0], uprightMultMatrixNode.matrixIn[0], force=True)
        else:
            identityMatrix = dt.Matrix()
            pmc.disconnectAttr(uprightMultMatrixNode.matrixIn[0])
            pmc.setAttr(uprightMultMatrixNode.matrixIn[0], identityMatrix, force=True)

    control.jointspace.setMatrix(oldMatrix, worldSpace=True)

def _test_rigtools():
    pmc.undoInfo(openChunk=True)
    '''
    joint1 = pmc.PyNode('joint1')
    joint2 = pmc.PyNode('joint2')
    joint3 = pmc.PyNode('joint3')
    ikHandle = create_ik_handle(joint1, joint3, solver='ikRPsolver')
    handle = ikHandle[0]
    effector = ikHandle[1]
    curve = add_control_curve(joint3, curveName='circle')
    attach_ik_controller(handle, curve)
    create_pole_vector_controller(joint2, handle)
    '''
    root = pmc.PyNode('EthanSkeleton')
    hips = pmc.PyNode('EthanHips')
    upLeg = pmc.PyNode('EthanLeftUpLeg')
    leg = pmc.PyNode('EthanLeftLeg')
    foot = pmc.PyNode('EthanLeftFoot')
    spine = pmc.PyNode('EthanSpine')
    rUpLeg = pmc.PyNode('EthanRightUpLeg')
    rLeg = pmc.PyNode('EthanRightLeg')
    rFoot = pmc.PyNode('EthanRightFoot')

    masterControl = GlobalControl(root, scale=(50.0, 50.0, 50.0))
    masterControl.build()

    hipControl = FKControl(targetJoint=spine, transform=spine, parent=masterControl, parentSpace=masterControl, upVector=dt.Vector(1,0,0),
                           name='hip', scale=(30.0,30.0,30.0))
    hipControl.build()

    upLegControl = FKControl(targetJoint=rUpLeg, transform=rUpLeg, parent=hipControl, upVector=dt.Vector(1, 0, 0),
                             parentSpace=hipControl, uprightSpace=hipControl,
                           name='upLeg', scale=(10.0, 10.0, 10.0), globalControl=masterControl, stretchEnabled=False,
                           squashEnabled=False, stretchJoints=[])
    upLegControl.build()

    legControl = FKControl(targetJoint=rLeg, transform=rLeg, parent=upLegControl, parentSpace=upLegControl,
                           uprightSpace=upLegControl, upVector=dt.Vector(1,0,0),
                             name='leg', scale=(10.0,10.0,10.0), globalControl=masterControl, stretchEnabled=True,
                             squashEnabled=True, stretchJoints=[rUpLeg])
    legControl.build()

    #legControl = FKControl(rLeg, rUpLeg, masterControl, stretchEnabled=True, parent=upLegControl, uprightParent=upLegControl, name='leg')
    #legControl.build()
    #footControl = FKControl(rFoot, rLeg, masterControl, stretchEnabled=True, parent=legControl, uprightParent=legControl, name='foot')
    #footControl.build()


    footIKControl = IKControl(foot, upLeg, transform=foot, parent=masterControl, parentSpace=masterControl,
                              uprightSpace=masterControl, name='foot', curve='cube', rotatePlaneSolver=False,
                              poleJoint=leg, stretchEnabled=True, squashEnabled=True, globalControl=masterControl,
                              scaleAxis=dt.Vector(1,0,0), stretchJoints=[upLeg,leg])
    footIKControl.build()

    #pmc.undoInfo(openChunk=False)

# from rigtools import rigtools; reload(rigtools); rigtools._test_rigtools()

#### Legacy Squash and Stretch
def add_squash_and_stretch_simple(control):

    point1SpaceSwitch = pmc.createNode('multMatrix', name=control.name + '_P1_MM_NODE')
    point2SpaceSwitch = pmc.createNode('multMatrix', name=control.name + '_P2_MM_NODE')
    stretchMult = pmc.createNode('multiplyDivide', name=control.name + '_STR_MD_NODE')
    squashMult = pmc.createNode('multiplyDivide', name=control.name + '_SQ_MD_NODE')
    distanceBetween = pmc.createNode('distanceBetween', name=control.name + '_DIST_NODE')

    pmc.connectAttr(control.stretchTarget.worldMatrix[0], point1SpaceSwitch.matrixIn[0])
    pmc.connectAttr(control.root.control.inverseMatrix, point1SpaceSwitch.matrixIn[1])
    pmc.connectAttr(control.control.worldMatrix[0], point2SpaceSwitch.matrixIn[0])
    pmc.connectAttr(control.root.control.inverseMatrix, point2SpaceSwitch.matrixIn[1])

    pmc.connectAttr(point1SpaceSwitch.matrixSum, distanceBetween.inMatrix1)
    pmc.connectAttr(point2SpaceSwitch.matrixSum, distanceBetween.inMatrix2)

    pmc.connectAttr(distanceBetween.distance, stretchMult.input1X)
    pmc.setAttr(stretchMult.input2X, pmc.getAttr(distanceBetween.distance))
    pmc.setAttr(stretchMult.operation, 'Divide')

    pmc.connectAttr(stretchMult.outputX, squashMult.input2X)
    pmc.setAttr(squashMult.input1X, 1.0)
    pmc.setAttr(squashMult.operation, 'Divide')

    pmc.connectAttr(stretchMult.outputX, control.stretchTarget.scaleX)
    pmc.connectAttr(squashMult.outputX, control.stretchTarget.scaleY)
    pmc.connectAttr(squashMult.outputX, control.stretchTarget.scaleZ)
def add_squash_and_stretch_complex(control):

    startJointSpaceSwitch = pmc.createNode('multMatrix', name=control.name + '_SJ_MM_NODE')
    endJointSpaceSwitch = pmc.createNode('multMatrix', name=control.name + '_EJ_MM_NODE')
    controlSpaceSwitch = pmc.createNode('multMatrix', name=control.name + '_CTRL_MM_NODE')
    stretchMult = pmc.createNode('multiplyDivide', name=control.name + '_STR_MD_NODE')
    squashMult = pmc.createNode('multiplyDivide', name=control.name + '_SQ_MD_NODE')
    distanceToJoint = pmc.createNode('distanceBetween', name=control.name + '_JNT_DIST_NODE')
    distanceToControl = pmc.createNode('distanceBetween', name=control.name + '_CTRL_DIST_NODE')

    # Create a second chain for reference
    newStartJoint = pmc.duplicate(control.endJoint, po=True, name=control.name + '_CTRL_JNT_START')[0]
    pmc.parent(newStartJoint, world=True)
    newPoleJoint = pmc.duplicate(control.poleJoint, po=True, name=control.name + '_CTRL_JNT_MID')[0]
    pmc.parent(newPoleJoint, newStartJoint)
    newEndJoint = pmc.duplicate(control.targetJoint, po=True, name=control.name + '_CTRL_JNT_END')[0]
    pmc.parent(newEndJoint, newPoleJoint)
    newHandle = pmc.ikHandle(sj=newStartJoint, ee=newEndJoint)[0]
    pmc.parentConstraint(control.control, newHandle)
    pmc.poleVectorConstraint(control.poleControl, newHandle)
    pmc.connectAttr(control.control.twist, newHandle.twist)
    newGroup = pmc.group(newHandle, newStartJoint, name=control.name + '_squashHelpers')
    pmc.parentConstraint(control.globalControl.control, newGroup, mo=True)
    pmc.scaleConstraint(control.parent.control, newGroup)

    pmc.connectAttr(control.endJoint.worldMatrix[0], startJointSpaceSwitch.matrixIn[0])
    pmc.connectAttr(control.globalControl.control.inverseMatrix, startJointSpaceSwitch.matrixIn[1])
    pmc.connectAttr(newEndJoint.worldMatrix[0], endJointSpaceSwitch.matrixIn[0])
    pmc.connectAttr(control.globalControl.control.inverseMatrix, endJointSpaceSwitch.matrixIn[1])
    pmc.connectAttr(control.control.worldMatrix[0], controlSpaceSwitch.matrixIn[0])
    pmc.connectAttr(control.globalControl.control.inverseMatrix, controlSpaceSwitch.matrixIn[1])

    pmc.connectAttr(startJointSpaceSwitch.matrixSum, distanceToJoint.inMatrix1)
    pmc.connectAttr(endJointSpaceSwitch.matrixSum, distanceToJoint.inMatrix2)
    pmc.connectAttr(startJointSpaceSwitch.matrixSum, distanceToControl.inMatrix1)
    pmc.connectAttr(controlSpaceSwitch.matrixSum, distanceToControl.inMatrix2)

    pmc.connectAttr(distanceToControl.distance, stretchMult.input1X)
    pmc.connectAttr(distanceToJoint.distance, stretchMult.input2X)
    #pmc.setAttr(stretchMult.input2X, pmc.getAttr(distanceBetween.distance))
    pmc.setAttr(stretchMult.operation, 'Divide')

    pmc.connectAttr(stretchMult.outputX, squashMult.input2X)
    pmc.setAttr(squashMult.input1X, 1.0)
    pmc.setAttr(squashMult.operation, 'Divide')

    for joint in control.stretchJoints:
        pmc.connectAttr(stretchMult.outputX, joint.scaleX)
        pmc.connectAttr(squashMult.outputX, joint.scaleY)
        pmc.connectAttr(squashMult.outputX, joint.scaleZ)
