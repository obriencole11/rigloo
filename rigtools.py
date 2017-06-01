import pymel.core as pmc
import pymel.core.datatypes as dt
import skeltools
import nametools
import controltools


#### Settings Classes ####
class ControlCurve():
    def __init__(self, curveType='default', scale=1.0, color=dt.Color.blue):
        self.curveType = curveType
        self.scale = scale
        self.color = color

    def create(self, name='default', upVector=dt.Vector(0,1,0)):

        # Use curve tools to generate a control from the control library
        control = controltools.create_control_curve(self.curveType)

        # Rename the control curve
        pmc.rename(control, name+'_ctrl')

        # Set the base scale of the curve
        match_scale(control, self.scale)

        # Rotate the control cvs to the desired orientation
        match_target_orientation(target=None, object=control, upVector=upVector)

        # Set the override color of the curve
        shape = control.getShape()
        shape.drawOverrideColor = self.color

        return control

defaultFKControl = ControlCurve(scale=10.0)

defaultMasterControl = ControlCurve(scale=30.0, curveType='cross')

defaultPoleControl = ControlCurve(scale=2.0, curveType='triangle')

defaultSpineControl = ControlCurve(scale=20.0)

defaultIKControl = ControlCurve(scale=10.0, curveType='cube')

#### Control Classes ####
class Rig():
    def __init__(self):
        pass

    def build(self):
        pass


# Prototype Component to be updated later
class Component_Prototype():
    '''
    Represents a basic control component.
    Contains input and output interfaces.
    :param name: A string to describe the component as a whole.
    :param mainControlType: The control string to use to generate the main control curve
    :param deformTargets: Pynodes that the component will deform.
    '''

    def __init__(self, name='default', mainControlType='default', deformTargets=[], **kwargs):
        self.name = name
        self.mainControlType=mainControlType
        self.deformTargets=deformTargets
        self.deformJoints = []
        self.inputs = {}
        self.outputs = {}

    def build(self):
        # Create an empty group to house all parts of the component
        self.comGroup = pmc.group(empty=True, name=self.name+'_com')

        # Add an input, output, control and deform group
        # These are just for organization purposes
        self.inputGroup = pmc.group(empty=True, name='input')
        pmc.parent(self.inputGroup, self.comGroup)
        self.outputGroup = pmc.group(empty=True, name='output')
        pmc.parent(self.outputGroup, self.comGroup)
        self.controlGroup = pmc.group(empty=True, name='control')
        pmc.parent(self.controlGroup, self.comGroup)
        self.deformGroup = pmc.group(empty=True, name='deform')
        pmc.parent(self.deformGroup, self.comGroup)

        # Add a local world input
        # This controls the local offset for the localSpace buffer
        # Essentially zeroing out the control transforms
        self.addInput('localWorld')

        # Add two buffers and parent the localWorld input to them
        # These will connect the parent space and upright space to the local world space
        tBuffer = pmc.group(empty=True, name='localWorldSpace_tBuffer')
        rBuffer = pmc.group(empty=True, name='localWorldSpace_rBuffer')
        pmc.parent(self.getInput('localWorld'), rBuffer)
        pmc.parent(self.getInput('uprightSpace'), self.getInput('parentSpace'))

        # Add a parentspace and uprightspace input
        # These controls the space the localSpace buffer inhabits
        self.addInput('parentSpace')
        self.addInput('uprightSpace')

        # Add a main space output
        # This will allow for other components to inhabit its space
        self.addOutput('main_srt')

        # For each deform target, create a deform output
        lastJoint = None
        for target in self.deformTargets:
            # Create a joint to bind the deform target to
            joint = pmc.joint(name=target.name() + '_srt')

            # Match the targets transform, and constrain it to the joint
            joint.setMatrix(target.getMatrix(worldSpace=True), worldSpace=True)
            pmc.parentConstraint(joint, target)

            # If this is not the first target, parent it to the previous
            # Otherwise mark it as the startjoint
            if lastJoint is not None:
                pmc.parent(joint, lastJoint)
            else:
                pmc.parent(joint, self.deformGroup)
                self.startJoint = joint

            # Add the joint to a joint list
            self.deformJoints.append(joint)

            # Set the lastTarget to the joint
            lastTarget = joint

        # Mark the final joint as the endJoint
        self.endJoint = lastJoint

        # Create a space buffer for the control
        self.mainControlBuffer = pmc.group(empty=True, name=self.name+'_srtBuffer')
        pmc.parent(self.mainControlBuffer, self.controlGroup)

        # Connect the control space buffer to the local world input
        connect_transforms(self.inputs['localWorld'], self.mainControlBuffer)

        # Create the main control
        self.mainControl = controltools.create_control_curve(self.mainControlType)
        pmc.rename(self.mainControl, self.name+'_main_ctrl')
        match_target_orientation(target=None, object=self.mainControl, upVector=dt.Vector(0,1,0))
        pmc.parent(self.mainControl, self.mainControlBuffer, r=False)

        # If there is a endJoint, move the localWorldGroup to that worldPosition
        # Otherwise
        #if self.endJoint is not None:
            #self.getInput('localWorld').setMatrix(self.endJoint.getMatrix(worldSpace=True), worldSpace=True)

    def addInput(self, inputName):
        # Create an empty group to house input properties
        input = pmc.group(empty=True, name=inputName)
        self.inputs[inputName] = input
        pmc.parent(input, self.inputGroup)

        return input

    def addOutput(self, outputName):
        # Create an empty group to house output properties
        output = pmc.group(empty=True, name=outputName)
        self.outputs[outputName] = output
        pmc.parent(output, self.outputGroup)

        return output

    def getInput(self, inputName):
        input = None
        try:
            input = self.inputs[inputName]
        except KeyError:
            raise
        return input


class Component():
    '''
    The base class of all components.
    '''

    defaultControl = ControlCurve()

    def __init__(self, name='default', deformTargets=[], mainControlType=defaultControl,
                 aimAxis=dt.Vector(0,1,0), **kwargs):
        self.name = name
        self.deformTargets = deformTargets
        self.mainControlType = mainControlType
        self.utilityNodes = {}
        self.aimAxis = aimAxis
        self.active = False
        self.constraints = []

    #### Public Methods ####

    def build(self):

        if not self.active:

            # Create a component group to contain all component DAG nodes
            self.componentGroup = pmc.group(empty=True, name=self.name+'_com')

            # Create the main control curve
            self.mainControl = self.mainControlType.create(upVector=self.aimAxis)

            # Create the local space for the control
            # This is better at preserving transforms than freezing transforms
            self.localSpaceBuffer = pmc.group(empty=True, name=self.name+'_localSpace_srtBuffer')

            # Transform/Scale/Rotate localSpaceGroup and parent the control curve to it
            pmc.parent(self.mainControl, self.localSpaceBuffer, relative=True)

            # Add parentSpace and uprightSpace groups and connections
            self.add_parent_space()

            # Bind the deform targets to the component control
            self.bind_deform_targets()

            # Parent the parentSpaceBuffer to the component group
            pmc.parent(self.parentSpaceBuffer, self.componentGroup)

            # Set the 'active' bool to True
            self.active = True

            return self.mainControl

    def setParentSpace(self, component):

        # Grab the localSpaceBuffer's current orientation
        oldMatrix = self.localSpaceBuffer.getMatrix(worldSpace=True)

        # Connect the components worldSpaceMatrix to this components multiply matrix utility node
        pmc.connectAttr(component.worldSpaceMatrix, self.utilityNodes['parentMultMatrixNode'].matrixIn[0], force=True)

        # Move the localSpaceBuffer back into its original orientation
        self.localSpaceBuffer.setMatrix(oldMatrix, worldSpace=True)

        # Set the components parent space to the new parent component
        self.parentSpace = component

    def setUprightSpace(self, component):

        # Grab the localSpaceBuffer's current orientation
        oldMatrix = self.localSpaceBuffer.getMatrix(worldSpace=True)

        # Connect the components worldSpaceMatrix to this components multiply matrix utility node
        pmc.connectAttr(component.worldSpaceMatrix, self.utilityNodes['uprightMultMatrixNode'].matrixIn[0], force=True)

        # Move the localSpaceBuffer back into its original orientation
        self.localSpaceBuffer.setMatrix(oldMatrix, worldSpace=True)

        # Set the components upright space to the new parent component
        self.uprightSpace = component

    def remove(self):

        if self.active:

            # Delete all parent constraints
            for constraint in self.constraints:
                pmc.delete(constraint)

            # Delete the component group
            pmc.delete(self.componentGroup)

            # Mark this component as inactive
            self.active = False


    #### Private Methods ####

    def add_parent_space(self):
        '''
        Adds a parentspace group and an uprightSpace group.
        Adds utility nodes to create a modular parent relationship.
        :param control: The Control object to operate on.
        :return: None
        '''

        # Create the parentSpace and uprightSpace groups and parent the controls to them
        self.uprightSpaceBuffer = pmc.group(empty=True, name=self.name + '_uprightSpace_srtBuffer')
        pmc.parent(self.localSpaceBuffer, self.uprightSpaceBuffer)
        self.parentSpaceBuffer = pmc.group(empty=True, name=self.name + '_parentSpace_srtBuffer')
        pmc.parent(self.uprightSpaceBuffer, self.parentSpaceBuffer)

        # Create the matrix utility nodes
        # And add them into the control's utility node dictionary
        uprightMultMatrixNode = pmc.createNode('multMatrix', name=self.name + '_uprightSpace_matrix')
        uprightDecomposeMatrixNode = pmc.createNode('decomposeMatrix', name=self.name + '_uprightSpace_decompMatrix')
        parentMultMatrixNode = pmc.createNode('multMatrix', name=self.name + '_parentSpace_matrix')
        parentDecomposeMatrixNode = pmc.createNode('decomposeMatrix', name=self.name + '_parentSpace_decompMatrix')
        self.utilityNodes['uprightMultMatrixNode'] = uprightMultMatrixNode
        self.utilityNodes['parentMultMatrixNode'] = parentMultMatrixNode
        self.utilityNodes['uprightDecomposeMatrixNode'] = uprightDecomposeMatrixNode
        self.utilityNodes['parentDecomposeMatrixNode'] = parentDecomposeMatrixNode

        # For now set the parentSpace and upright space to world (The identity Matrix)
        # Then set the parentSpace variable to none
        identityMatrix = dt.Matrix()
        pmc.setAttr(parentMultMatrixNode.matrixIn[0], identityMatrix)
        pmc.setAttr(uprightMultMatrixNode.matrixIn[0], identityMatrix)
        self.parentSpace = None
        self.uprightSpace = None

        # Connect the space group's inverse Matrix to the second matrix on the multiply Matrix node
        # This will reverse the transformations of the groups parent
        pmc.connectAttr(self.uprightSpaceBuffer.parentInverseMatrix[0], uprightMultMatrixNode.matrixIn[1])
        pmc.connectAttr(self.parentSpaceBuffer.parentInverseMatrix[0], parentMultMatrixNode.matrixIn[1])

        # Connect the multiply Matrix nodes into a corresponding decompose Matrix node
        # This will output the space transformations in vector format
        pmc.connectAttr(uprightMultMatrixNode.matrixSum, uprightDecomposeMatrixNode.inputMatrix)
        pmc.connectAttr(parentMultMatrixNode.matrixSum, parentDecomposeMatrixNode.inputMatrix)

        # Connect the decompose node's transformations to the corresponding groups transform values
        pmc.connectAttr(parentDecomposeMatrixNode.outputTranslate, self.parentSpaceBuffer.translate)
        pmc.connectAttr(uprightDecomposeMatrixNode.outputRotate, self.uprightSpaceBuffer.rotate)

        # Connect the parentSpace's scale to the parentSpace Group
        # This will allow the curves to scale with the global control
        pmc.connectAttr(parentDecomposeMatrixNode.outputScale, self.parentSpaceBuffer.scale)

    def bind_deform_targets(self):

        # Apply a parent constraint to each deform target
        for target in self.deformTargets:
            self.constraints.append(pmc.parentConstraint(self.mainControl, target, mo=True))
            self.constraints.append(pmc.scaleConstraint(self.mainControl, target, mo=True))


    #### Outputs ####

    @property
    def worldSpaceMatrix(self):
        return self.mainControl.worldMatrix[0]

class JointComponent(Component):
    '''
    Represents a component that specifically deforms joints
    '''

    def __init__(self, aimAxis=dt.Vector(1,0,0), **kwargs):
        Component.__init__(self, aimAxis=aimAxis, **kwargs)
        self.startJoint = self.getStartJoint()
        self.endJoint = self.getEndJoint()

    def getStartJoint(self):

        startJoint = None

        # Loop through deform joints
        # Return the joint who does not have a parent in the list
        for target in self.deformTargets:
            parents = []

            for otherTarget in self.deformTargets:
                if otherTarget.isParentOf(target):
                    parents.append(otherTarget)

            if len(parents) == 0:
                startJoint = target
                break
        print 'startJoint: ' + startJoint.name()
        return startJoint

    def getEndJoint(self):

        endJoint = None

        # Loop through joint targets
        # Return the joint does not have any children
        for target in self.deformTargets:
            children = []

            for otherTarget in self.deformTargets:
                if otherTarget.isChildOf(target):
                    children.append(otherTarget)

            if len(children) == 0:
                endJoint = target
        print 'endJoint: ' + endJoint.name()
        return endJoint

    def bind_deform_targets(self):

        # Set the local space buffer's orientation to the start joint's orientation
        self.localSpaceBuffer.setMatrix(self.endJoint.getMatrix(worldSpace=True), worldSpace=True)

        # Constrain the startJoint to the mainControl
        self.constraints.append(pmc.parentConstraint(self.mainControl, self.endJoint))

class StretchJointComponent(JointComponent):
    '''
    Squash and stretch support for controls
    '''

    def __init__(self, stretchEnabled=False, squashEnabled=False, stretchScale=2.0,
                 globalControl=None, stretchMin=0.0, **kwargs):
        JointComponent.__init__(self, **kwargs)
        self.stretchEnabled = stretchEnabled
        self.squashEnabled = squashEnabled
        self.stretchScale = stretchScale
        self.stretchMin = stretchMin
        self.globalControl = globalControl

    def build(self):

        # Create utility nodes
        # Float Math node is weird, 2 = Multiply, 3 = Divide, 5 = Max
        point1SpaceSwitch = pmc.createNode('multMatrix', name=self.name + '_point1_SpaceSwitch')
        point2SpaceSwitch = pmc.createNode('multMatrix', name=self.name + '_point2_SpaceSwitch')
        self.utilityNodes['point1SpaceSwitch'] = point1SpaceSwitch
        self.utilityNodes['point2SpaceSwitch'] = point2SpaceSwitch
        distanceBetween = pmc.createNode('distanceBetween', name=self.name + '_squashAndStretch_Distance')
        maxDistanceDiv = pmc.createNode('floatMath', name=self.name + '_maxDistance')
        pmc.setAttr(maxDistanceDiv.operation, 3)
        scaleMult = pmc.createNode('floatMath', name=self.name + '_scaleMult')
        pmc.setAttr(scaleMult.operation, 2)
        outputMax = pmc.createNode('floatMath', name=self.name + '_outputMax')
        pmc.setAttr(outputMax.operation, 5)
        inverseOutput = pmc.createNode('floatMath', name=self.name + '_inverse')
        pmc.setAttr(inverseOutput.operation, 3)
        startJointTranslateMatrix = pmc.createNode('composeMatrix', name=self.name+'_startJointTranslate_to_Matrix')
        startJointTranslateWorldMatrix = pmc.createNode('multMatrix', name=self.name+'_startJointTranslateMatrix_to_WorldMatrix')

        # Grab the components stretchJoints
        self.stretchJoints = self.getStretchJoints()

        # Set the start joint
        self.startJoint = self.getStartJoint()

        # Set the end Joint
        self.endJoint = self.getEndJoint()

        # Calculate the max distance
        maxDistance = self.startJoint.getTranslation('world').distanceTo(
            self.mainControl.getTranslation('world'))

        # Convert the startJoints local translation to a matrix
        pmc.connectAttr(self.startJoint.translate, startJointTranslateMatrix.inputTranslate)

        # Convert the startJoints local translation matrix to worldspace
        # By multiplying it by the startJoints parent Matrix
        # We do this to avoid creating an infinite node cycle
        pmc.connectAttr(startJointTranslateMatrix.outputMatrix, startJointTranslateWorldMatrix.matrixIn[0])
        pmc.connectAttr(self.startJoint.parentMatrix[0], startJointTranslateWorldMatrix.matrixIn[1])

        # Connect the worldTranslateMatrix of the startJoint and the worldMatrix of the mainControl
        # to a space switcher. This will compensate for the global rig scaling
        pmc.connectAttr(startJointTranslateWorldMatrix.matrixSum, point1SpaceSwitch.matrixIn[0])
        pmc.connectAttr(self.mainControl.worldMatrix[0], point2SpaceSwitch.matrixIn[0])

        # If there is a global control set, input it, otherwise leave the second matrix input empty
        if self.globalControl:
            self.setGlobalControl(self.globalControl)

        # Connect the matrix sums to distance node
        pmc.connectAttr(point1SpaceSwitch.matrixSum, distanceBetween.inMatrix1)
        pmc.connectAttr(point2SpaceSwitch.matrixSum, distanceBetween.inMatrix2)

        # Connect distance and max distance to division node
        pmc.connectAttr(distanceBetween.distance, maxDistanceDiv.floatA)
        pmc.setAttr(maxDistanceDiv.floatB, maxDistance * 2)

        # Connect normalized distance to multiply node
        pmc.connectAttr(maxDistanceDiv.outFloat, scaleMult.floatA)
        pmc.setAttr(scaleMult.floatB, self.stretchScale)

        # Connect scaled output to the max node
        pmc.setAttr(outputMax.floatB, self.stretchMin)
        pmc.connectAttr(scaleMult.outFloat, outputMax.floatA)

        # Connect maxed output to the inverse node
        pmc.setAttr(inverseOutput.floatA, 1.0)
        pmc.connectAttr(outputMax.outFloat, inverseOutput.floatB)

        # Connect to stretch joint scales
        for joint in self.stretchJoints:
            axis = (joint.scaleX, joint.scaleY, joint.scaleZ)
            for x in range(3):
                if self.aimAxis[x] == 1:
                    if self.stretchEnabled:
                        pmc.connectAttr(outputMax.outFloat, axis[x])
                else:
                    if self.squashEnabled:
                        pmc.connectAttr(inverseOutput.outFloat, axis[x])

    def getStretchJoints(self):

        stretchJoints = []

        # Loop through deform joints
        # Return the joints with children in the list
        for target in self.deformTargets:
            for otherTarget in self.deformTargets:
                if otherTarget.isChildOf(target):
                    stretchJoints.append(target)
                    break

        return stretchJoints

    def setGlobalControl(self, control):
        self.globalControl = control
        pmc.connectAttr(self.globalControl.mainControl.inverseMatrix,
                        self.utilityNodes['point1SpaceSwitch'].matrixIn[1], force=True)
        pmc.connectAttr(self.globalControl.mainControl.inverseMatrix,
                        self.utilityNodes['point2SpaceSwitch'].matrixIn[1], force=True)

    def setParentSpace(self, component):
        Component.setParentSpace(self, component)

class FKComponent(StretchJointComponent):
    '''
    Represents a basic joint control. 
    Features a target joint that is driven by the control curve.
    '''
    def __init__(self, **kwargs):
        StretchJointComponent.__init__(self, stretchMin=0.0, **kwargs)

    def build(self):
        # Build the basic control curve structure
        Component.build(self)

        # Add Squash and Stretch
        StretchJointComponent.build(self)

        return self.mainControl

class IKComponent(StretchJointComponent):
    '''
    A basic IK control
    '''

    def __init__(self, noFlipKnee=False, poleControlCurveType=defaultPoleControl, **kwargs):
        StretchJointComponent.__init__(self, stretchMin=1.0, **kwargs)
        self.noFlipKnee = noFlipKnee
        self.poleControlCurveType = poleControlCurveType

    def build(self):
        Component.build(self)

        StretchJointComponent.build(self)

        return self.mainControl

    def bind_deform_targets(self):
        #JointComponent.bind_deform_targets(self)

        # Set the local space buffer's orientation to the start joint's orientation
        self.localSpaceBuffer.setMatrix(self.endJoint.getMatrix(worldSpace=True), worldSpace=True)

        self.addIKHandle()

        self.poleJoint = self.getPoleJoint()

        if not self.noFlipKnee:
            self.addPoleVector()

        self.constraints.append( pmc.orientConstraint(self.mainControl, self.endJoint, mo=True) )

    def addIKHandle(self):

        # Create the ikHandle and effector
        self.handle, self.effector = pmc.ikHandle(sj=self.startJoint, ee=self.endJoint)

        # Parent the handle to the main control
        pmc.parent(self.handle, self.mainControl)

        # Rename the handle and effector
        pmc.rename(self.handle, self.name + '_handle')
        pmc.rename(self.effector, self.name + '_effector')

        # Add a twist attribute to the main control and connect it to the handles twist
        pmc.addAttr(self.mainControl, ln='twist', at='double', k=True)
        pmc.connectAttr(self.mainControl.twist, self.handle.twist)

    def addPoleVector(self):

        # Grab the worldspace vectors of each points position
        startPoint = self.startJoint.getTranslation(space='world')
        elbowPoint = self.poleJoint.getTranslation(space='world')
        endPoint = self.endJoint.getTranslation(space='world')

        # Find the midpoint between the start and end joint
        averagePoint = (startPoint + endPoint) / 2

        # Find the direction from the midpoint to the elbow
        elbowDirection = elbowPoint - averagePoint

        # Multiply the direction by 2 to extend the range
        polePoint = (elbowDirection * 5) + averagePoint

        # Create empty transform and move it to the pole point
        poleObject = pmc.group(empty=True, name=self.name + '_poleVector_srtBuffer')
        poleObject.setTranslation(polePoint, space='world')
        poleCurve = self.poleControlCurveType.create()
        pmc.rename(poleCurve, self.name + '_poleVector_ctrl')
        poleCurve.setMatrix(poleObject.getMatrix())
        pmc.parent(poleObject, poleCurve)
        pmc.parent(poleCurve, self.localSpaceBuffer)

        # Normalize the polepoint, to get the direction to the elbow
        direction = polePoint.normal()

        # Get the Quaternion rotation needed to rotate from
        # the world up to the direction of the elbow
        rotation = (dt.Vector(0, 1, 0)).rotateTo(direction)

        # Rotate the locator by that ammount
        poleObject.rotateBy(rotation)

        pmc.poleVectorConstraint(poleObject, self.handle)

        self.poleControl = poleObject

    def getPoleJoint(self):

        polejoint = None

        # For each deform target return the one that has a parent and child in the list
        for target in self.deformTargets:
            parents = []
            children = []
            for otherTarget in self.deformTargets:
                if otherTarget.isParentOf(target):
                    parents.append(otherTarget)
                if otherTarget.isChildOf(target):
                    children.append(otherTarget)
            if len(parents) > 0 and len(children) > 0:
                polejoint = target
                break

        return polejoint

# Legacy classes:
class GlobalControl(Component):
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
def connect_transforms(input, output, translate=True, rotate=True, scale=True):
    '''
    Connects the transform attributes of one transform to another
    :param input: The source transform.
    :param output: The target transform.
    :param translate: A bool to determine whether to connect translation.
    :param rotate: A bool to determine whether to connect rotation.
    :param scale: A bool to determine whether to connect scale.
    :return: None
    '''

    if translate:
        pmc.connectAttr(input.translate, output.translate)
    if rotate:
        pmc.connectAttr(input.rotate, output.rotate)
    if scale:
        pmc.connectAttr(input.scale, output.scale)

def connect_joint_to_controller(jointControl):
    '''
    For now this just adds a parent constraint from the controller to the joint
    :param jointControl: The JointControl object.
    :return: None
    '''
    constraint = pmc.parentConstraint(jointControl.control, jointControl.targetJoint, mo=True)
    jointControl.constraint = constraint




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

def match_scale(transform, scale):
    '''
    Sets the scale of a transform, and freezes the transformations.
    :param target: The transform to operate on
    :param scale: The target scale
    '''

    # Set the scale
    transform.setScale(scale=(scale, scale, scale))

    # Freeze scale values
    pmc.makeIdentity(transform, apply=True, translate=False, rotate=False, scale=True)


def add_control_curve(transform, curveName='default', upVector=dt.Vector(0,1,0)):
    ''''''
    try:
        curve = controltools.create_control_curve(curveName)
    except KeyError:
        curve = controltools.create_control_curve('default')
    controltools.move_to_transform(curve, transform, upVector=upVector)
    controltools.freeze_transforms(curve)
    return curve







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
    spine1 = pmc.PyNode('EthanSpine1')
    spine2 = pmc.PyNode('EthanSpine2')
    arm = pmc.PyNode('EthanLeftArm')
    foreArm = pmc.PyNode('EthanLeftForeArm')
    hand = pmc.PyNode('EthanLeftHand')

    masterControl = Component(name='root',
                              deformTargets=[root],
                              mainControlType=defaultMasterControl)
    masterControl.build()

    hipControl = FKComponent(name='hip',
                             deformTargets=[spine],
                             mainControlType=defaultSpineControl)
    hipControl.build()
    hipControl.setParentSpace(masterControl)
    hipControl.setUprightSpace(masterControl)

    rLegFKControl = FKComponent(name='rLeg',
                               deformTargets=[rLeg, rUpLeg],
                               mainControlType=defaultFKControl,
                               stretchEnabled=True,
                               squashEnabled=True,
                                globalControl=masterControl)
    rLegFKControl.build()
    rLegFKControl.setParentSpace(hipControl)
    rLegFKControl.setUprightSpace(hipControl)

    rFootFKControl = FKComponent(name='rFoot',
                               deformTargets=[rLeg, rFoot],
                               mainControlType=defaultFKControl,
                               stretchEnabled=True,
                               squashEnabled=True,
                                 globalControl=masterControl)
    rFootFKControl.build()
    rFootFKControl.setParentSpace(rLegFKControl)
    rFootFKControl.setUprightSpace(rLegFKControl)

    footIKControl = IKComponent(name='lFoot',
                                deformTargets=[upLeg, leg, foot],
                                mainControlType=defaultFKControl,
                                stretchEnabled=True,
                                squashEnabled=True,
                                globalControl=masterControl
                                )
    footIKControl.build()
    footIKControl.setParentSpace(masterControl)
    footIKControl.setUprightSpace(masterControl)

    spine1Control = FKComponent(name='spine1',
                                deformTargets=[spine, spine1],
                                mainControlType=defaultSpineControl,
                                stretchEnabled=True,
                                squashEnabled=True,
                                globalControl=masterControl)
    spine1Control.build()
    spine1Control.setParentSpace(hipControl)
    spine1Control.setUprightSpace(hipControl)

    spine2Control = FKComponent(name='spine2',
                                deformTargets=[spine1, spine2],
                                mainControlType=defaultSpineControl,
                                stretchEnabled=True,
                                squashEnabled=True,
                                globalControl=masterControl)
    spine2Control.build()
    spine2Control.setParentSpace(spine1Control)
    spine2Control.setUprightSpace(spine1Control)

    armIKControl = IKComponent(name='arm',
                               upAxis=dt.Vector(0,0,1),
                               deformTargets=[arm, foreArm, hand],
                               mainControlType=defaultIKControl,
                               stretchEnabled=True,
                               squashEnabled=True,
                               globalControl=masterControl)
    armIKControl.build()
    armIKControl.setParentSpace(spine2Control)
    armIKControl.setUprightSpace(spine2Control)


    '''
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
    '''
    pmc.undoInfo(openChunk=False)

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
