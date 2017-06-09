import pymel.core as pmc
import pymel.core.datatypes as dt
import controltools


#### Utility Classes ####
class Signal():
    def __init__(self):
        self._handlers=[]

    def connect(self, handler):
        self._handlers.append(handler)

    def fire(self, *args, **kwargs):
        for handler in self._handlers:
            handler(**kwargs)

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

class Component(object):
    '''
    The base class of all components.
    '''

    defaultControl = ControlCurve()

    def __init__(self, name='default', deformTargets=[], mainControlType=defaultControl,
                 aimAxis=dt.Vector(0,1,0), rig=None, parentSpace=None,
                 uprightSpace=None, globalControl=None, **kwargs):
        self._name = name
        self._deformTargets = deformTargets
        self._mainControlType = mainControlType
        self._utilityNodes = {}
        self._aimAxis = aimAxis
        self._active = False
        self._bound = False
        self._constraints = []
        self._rig = rig
        self._globalControl = globalControl
        self._uprightSpace = uprightSpace
        self._parentSpace = parentSpace
        self._mainControl = None
        self.parentSpaceChanged = Signal()
        self.globalControlChanged = Signal()

        self.parentSpaceChanged.connect(self._resetParentSpace)


    #### Public Methods ####

    def build(self):
        if not self.active:

            # Create a component group to contain all component DAG nodes
            self.componentGroup = pmc.group(empty=True, name=self.name+'_com')

            # Create the main control curve
            self._mainControl = self._mainControlType.create(upVector=self._aimAxis, name=self.name+'_main')

            # Create the local space for the control
            # This is better at preserving transforms than freezing transforms
            self.localSpaceBuffer = pmc.group(empty=True, name=self.name+'_localSpace_srtBuffer')

            # Transform/Scale/Rotate localSpaceGroup and parent the control curve to it
            pmc.parent(self.mainControl, self.localSpaceBuffer, relative=True)

            # Add parentSpace and uprightSpace groups and connections
            self._addParentSpaceNodes()

            # Snap the controls to the deform targets
            self.zero()

            # Parent the parentSpaceBuffer to the component group
            pmc.parent(self.parentSpaceBuffer, self.componentGroup)

            # Set the 'active' bool to True
            self._active = True

            return self.componentGroup

    def parent(self):
        # Set the parentSpace
        self._resetParentSpace()

    def zero(self):
        # Sets the default localspacebuffer position
        pass

    def snap(self):
        # Snap controls to the positions of the deform targets
        pass

    def bake(self, frame):

        pmc.setKeyframe(self.mainControl, t=frame)

    def bakeDeforms(self, frame):

        # Key every deform target
        for joint in self._deformTargets:
            pmc.setKeyframe(joint, t=frame)

    def bind(self):
        if not self._bound:
            # Apply the parent space
            self._resetParentSpace()

            # Apply a parent constraint to each deform target
            for target in self._deformTargets:
                self._constraints.append(pmc.parentConstraint(self._mainControl, target, mo=True))
                self._constraints.append(pmc.scaleConstraint(self._mainControl, target))

            self._bound = True

    def unbind(self):

        if self._bound:

            # Delete all parent constraints
            for constraint in self._constraints:
                pmc.delete(constraint)

            # Mark this component as inactive
            self.bound = False

    def remove(self):

        if self._bound:
            self.unbind()

        if self._active:

            # Delete the component group
            pmc.delete(self.componentGroup)

            # Mark this component as inactive
            self._active = False


    #### Private Methods ####

    def _addParentSpaceNodes(self):
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
        self._utilityNodes['uprightMultMatrixNode'] = uprightMultMatrixNode
        self._utilityNodes['parentMultMatrixNode'] = parentMultMatrixNode
        self._utilityNodes['uprightDecomposeMatrixNode'] = uprightDecomposeMatrixNode
        self._utilityNodes['parentDecomposeMatrixNode'] = parentDecomposeMatrixNode

        # For now set the parentSpace and upright space to world (The identity Matrix)
        # Then set the parentSpace variable to none
        identityMatrix = dt.Matrix()
        pmc.setAttr(parentMultMatrixNode.matrixIn[0], identityMatrix)
        pmc.setAttr(uprightMultMatrixNode.matrixIn[0], identityMatrix)

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

    def _resetParentSpace(self):

        # Only change the space if the skeleton is active
        if self.active:

            # Grab the localSpaceBuffer's current orientation
            oldMatrix = self.localSpaceBuffer.getMatrix(worldSpace=True)

            # If uprightSpace is set to None, parent to worldSpace
            if self._uprightSpace is None:

                # Set the worldSpaceMatrix to the identity Matrix
                identityMatrix = dt.Matrix()

                pmc.setAttr(self._utilityNodes['uprightMultMatrixNode'].matrixIn[0], identityMatrix,
                                force=True)
            else:
                # Connect the components worldSpaceMatrix to this components multiply matrix utility node
                pmc.connectAttr(self._uprightSpace.worldSpaceMatrix,
                                self._utilityNodes['uprightMultMatrixNode'].matrixIn[0],
                                force=True)

            if self._parentSpace is None:

                # Set the worldSpaceMatrix to the identity Matrix
                identityMatrix = dt.Matrix()

                pmc.setAttr(self._utilityNodes['parentMultMatrixNode'].matrixIn[0], identityMatrix,
                        force=True)
            else:
                # Connect the components worldSpaceMatrix to this components multiply matrix utility node
                pmc.connectAttr(self._parentSpace.worldSpaceMatrix,
                                self._utilityNodes['parentMultMatrixNode'].matrixIn[0],
                                force=True)

            # Move the localSpaceBuffer back into its original orientation
            self.localSpaceBuffer.setMatrix(oldMatrix, worldSpace=True)


    #### Public Properties ####

    @property
    def name(self):
        return self._name

    @property
    def active(self):
        return self._active

    @property
    def worldSpaceMatrix(self):
        if self._mainControl is not None:
            return self._mainControl.worldMatrix[0]
        else:
            return None

    @property
    def metaData(self):
        def getName(target):
            try:
                return str(target.name)
            except AttributeError:
                return 'None'

        data = []
        data.append('')
        data.append('#####  ' + self.name + '  #####')
        data.append('Component Type: ' + str(self.__class__))
        data.append('Rig: ' + getName(self._rig))
        data.append('Global Controller: ' + getName(self._globalControl))
        data.append('Parent Space: ' + getName(self.parentSpace))
        data.append('Upright Space: ' + getName(self.uprightSpace))
        data.append('Main Control Shape: ' + self._mainControlType.curveType)
        data.append('Aim Axis: ' + str(self._aimAxis))
        data.append('Deform Targets:')
        for target in self._deformTargets:
            data.append("   - " + str(target))

        data.append('')

        return ('\n').join(data)

    @property
    def globalControl(self):
        return self._globalControl

    @globalControl.setter
    def globalControl(self, value):
        self._globalControl = value
        self.globalControlChanged.fire(self)

    @property
    def parentSpace(self):
        return self._parentSpace

    @parentSpace.setter
    def parentSpace(self, value):
        self._parentSpace = value
        self.parentSpaceChanged.fire(self)

    @property
    def uprightSpace(self):
        return self._uprightSpace

    @uprightSpace.setter
    def uprightSpace(self, value):
        self._uprightSpace = value
        self.parentSpaceChanged.fire(self)

    @property
    def uprightAndParentSpace(self):
        return self._uprightSpace, self._parentSpace

    @uprightAndParentSpace.setter
    def uprightAndParentSpace(self, value):
        self._uprightSpace = value
        self._parentSpace = value
        self.parentSpaceChanged.fire(self)

    @property
    def mainControl(self):
        return self._mainControl

class Rig(object):
    def __init__(self, name='defaultRig'):
        self._name = name
        self._control = None
        self._components = {}
        self._globalControl = None
        self._bound = False

    #### Public Methods ####

    def build(self):
        # Create a master group for the rig
        self.rigGroup = pmc.group(empty=True, name=self._name + '_rig')

        # For each component in the rig, build it and parent it to the master group
        for com in self._components:
            self._components[com].globalControl = self._globalControl
            componentGroup = self._components[com].build()
            pmc.parent(componentGroup, self.rigGroup)

        # For each component, apply the parent space
        for com in self._components:
            self._components[com].parent()

    def bind(self):
        if not self._bound:
            # For each component in the rig, bind to its target
            for com in self._components:
                self._components[com].bind()

            self._bound = True

    def snap(self):
        # For each component in the rig, snap to its target
        for com in self._components:
            self._components[com].snap()

    def bake(self, components=None, frameRange=10):

        # Goes through every frame, snaps the controls and keys their position
        for frame in range(frameRange):
            pmc.setCurrentTime(frame)
            if components is not None:
                for com in components:
                    component = com
                    component.snap()
                    component.bake(frame)
            else:
                for com in self._components:
                    component = self._components[com]
                    component.snap()
                    component.bake(frame)
        pmc.setCurrentTime(1)

    def bakeDeforms(self, components=None, frameRange=10):

        # Goes through every frame, snaps the controls and keys their position
        for frame in range(frameRange):
            pmc.setCurrentTime(frame)
            if components is not None:
                for com in components:
                    self._components[com].bakeDeforms(frame)
            else:
                for com in self._components:
                    self._components[com].bakeDeforms(frame)
        pmc.setCurrentTime(1)

    def unbind(self):
        if self._bound:
            # For each component in the rig, unbind it
            for com in self._components:
                self._components[com].unbind()

            self._bound = False

    def delete(self):

        if self._bound:
            self.unbind()

        # For each component in the rig, remove it
        for com in self._components:
            self._components[com].remove()

        # Then delete the rig group
        pmc.delete(self.rigGroup)

    def addComponent(self, componentType, **kwargs):

        # Create the new component and add the rigs name to its name
        component = componentType(globalControl=self._globalControl, rig=self,  **kwargs)

        # Add the specified component to the rig
        self._components[component.name] = component

        # Add that component as an attribute to the class
        setattr(self, component.name, component)

    def removeComponent(self, name):

        # Grab the component
        component = self.components[name]

        # If it is built, remove it
        if component.active:
            component.remove()

        # Remove the component from the component dictionary
        self.components[name] = None


    #### Public Properties ####

    @property
    def metaData(self):

        def getName(target):
            try:
                return str(target.name)
            except AttributeError:
                return 'None'

        data = []
        data.append('')
        data.append('#####  ' + self._name + '  #####')
        data.append('Global Controller: ' + getName(self._globalControl))

        data.append('')

        print ('\n').join(data)

        for com in self._components:
            print self._components[com].metaData

    @property
    def globalControl(self):
        return self._globalControl

    @globalControl.setter
    def globalControl(self, value):

        self._globalControl = value

        # For each component, update its globalControl
        for com in self._components:
            self._components[com].globalControl = self._globalControl

class JointComponent(Component):
    '''
    Represents a component that specifically deforms joints
    '''

    def __init__(self, aimAxis=dt.Vector(1,0,0), **kwargs):
        Component.__init__(self, aimAxis=aimAxis, **kwargs)
        self._startJoint = self._getStartJoint()
        self._endJoint = self._getEndJoint()


    #### private methods ####

    def _getStartJoint(self):

        startJoint = None

        # Loop through deform joints
        # Return the joint who does not have a parent in the list
        for target in self._deformTargets:
            parents = []

            for otherTarget in self._deformTargets:
                if otherTarget.isParentOf(target):
                    parents.append(otherTarget)

            if len(parents) == 0:
                startJoint = target
                break
        return startJoint

    def _getEndJoint(self):

        endJoint = None

        # Loop through joint targets
        # Return the joint does not have any children
        for target in self._deformTargets:
            children = []

            for otherTarget in self._deformTargets:
                if otherTarget.isChildOf(target):
                    children.append(otherTarget)

            if len(children) == 0:
                endJoint = target
        return endJoint


    #### public methods ####

    def zero(self):

        # Set the local space buffer's orientation to the start joint's orientation
        self.localSpaceBuffer.setMatrix(self._endJoint.getMatrix(worldSpace=True), worldSpace=True)

    def snap(self):

        ''' TODO: Find a solution for FK Squash and Stretch
        
        # Grab the current Translation
        currentPos = self.mainControl.getTranslation(space='world')

        # Grab the target Translation
        targetPos = self.mainControl.getTranslation(space='world')

        # Calculate the difference in translation
        translationDiff = targetPos - currentPos

        # Move the main control into position
        self.mainControl.translateBy(translationDiff)
        '''
        '''
        # Grab the inverse of the current rotation
        currentRot = self.mainControl.getRotation().asQuaternion().invertIt()

        # Grab the target rotation
        targetRot = self._endJoint.getRotation().asQuaternion()

        # Get the quaternion difference
        difference = targetRot * currentRot

        # Rotate the mainControl by that rotation
        self.mainControl.rotateBy(difference) '''

        targetM = self.endJoint.getMatrix(worldSpace=True)

        self.mainControl.setMatrix(targetM, worldSpace=True)

    def bind(self):

        if not self._bound:
            # Set the parentSpace
            self._resetParentSpace()

            # Constrain the startJoint to the mainControl
            self._constraints.append(pmc.parentConstraint(self.mainControl, self._endJoint, name=self.name+'_mainControlConstraint'))

            self._bound = True


    #### public properties ####

    @property
    def startJoint (self):
        return self._startJoint

    @property
    def endJoint(self):
        return  self._endJoint

class StretchJointComponent(JointComponent):
    '''
    A Joint Component that supports squash and stretch.
    Doesn't nessesary have it active though.
    '''

    def __init__(self, stretchEnabled=False, squashEnabled=False, stretchScale=2.0,
                 stretchMin=0.0, **kwargs):
        JointComponent.__init__(self, **kwargs)
        self._stretchEnabled = stretchEnabled
        self._squashEnabled = squashEnabled
        self._stretchScale = stretchScale
        self._stretchMin = stretchMin

        self.globalControlChanged.connect(self._resetSquashStretch)


    #### Private Methods ####

    def _getStretchJoints(self):

        stretchJoints = []

        # Loop through deform joints
        # Return the joints with children in the list
        for target in self._deformTargets:
            for otherTarget in self._deformTargets:
                if otherTarget.isChildOf(target):
                    stretchJoints.append(target)
                    break

        return stretchJoints

    def _resetSquashStretch(self):
        # Update the squash and stretch nodes
        if self._active:
            pmc.connectAttr(self._globalControl.mainControl.inverseMatrix,
                            self._utilityNodes['point1SpaceSwitch'].matrixIn[1], force=True)
            pmc.connectAttr(self._globalControl.mainControl.inverseMatrix,
                            self._utilityNodes['point2SpaceSwitch'].matrixIn[1], force=True)


    #### Public Methods ####

    def build(self):

        # Create utility nodes
        # Float Math node is weird, 2 = Multiply, 3 = Divide, 5 = Max
        point1SpaceSwitch = pmc.createNode('multMatrix', name=self.name + '_point1_SpaceSwitch')
        point2SpaceSwitch = pmc.createNode('multMatrix', name=self.name + '_point2_SpaceSwitch')
        distanceBetween = pmc.createNode('distanceBetween', name=self.name + '_squashAndStretch_Distance')
        maxDistanceDiv = pmc.createNode('floatMath', name=self.name + '_maxDistance')
        pmc.setAttr(maxDistanceDiv.operation, 3)
        scaleMult = pmc.createNode('floatMath', name=self.name + '_scaleMult')
        pmc.setAttr(scaleMult.operation, 2)
        outputMax = pmc.createNode('floatMath', name=self.name + '_outputMax')
        pmc.setAttr(outputMax.operation, 5)
        inverseOutput = pmc.createNode('floatMath', name=self.name + '_inverse')
        pmc.setAttr(inverseOutput.operation, 3)
        startJointTranslateMatrix = pmc.createNode('composeMatrix',
                                                   name=self.name+'_startJointTranslate_to_Matrix')
        startJointTranslateWorldMatrix = pmc.createNode('multMatrix',
                                                        name=self.name+'_startJointTranslateMatrix_to_WorldMatrix')

        # Add utility nodes we care about into the utility nodes dictionary
        self._utilityNodes['point1SpaceSwitch'] = point1SpaceSwitch
        self._utilityNodes['point2SpaceSwitch'] = point2SpaceSwitch
        self._utilityNodes['outMax'] = outputMax
        self._utilityNodes['inverseOutput'] = inverseOutput

        # Grab the components stretchJoints
        self.stretchJoints = self._getStretchJoints()

        # Set the start joint
        self._startJoint = self._getStartJoint()

        # Set the end Joint
        self._endJoint = self._getEndJoint()

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

        # Connect the matrix sums to distance node
        pmc.connectAttr(point1SpaceSwitch.matrixSum, distanceBetween.inMatrix1)
        pmc.connectAttr(point2SpaceSwitch.matrixSum, distanceBetween.inMatrix2)

        # Connect distance and max distance to division node
        pmc.connectAttr(distanceBetween.distance, maxDistanceDiv.floatA)
        pmc.setAttr(maxDistanceDiv.floatB, maxDistance * 2)

        # Connect normalized distance to multiply node
        pmc.connectAttr(maxDistanceDiv.outFloat, scaleMult.floatA)
        pmc.setAttr(scaleMult.floatB, self._stretchScale)

        # Connect scaled output to the max node
        pmc.setAttr(outputMax.floatB, self._stretchMin)
        pmc.connectAttr(scaleMult.outFloat, outputMax.floatA)

        # Connect maxed output to the inverse node
        pmc.setAttr(inverseOutput.floatA, 1.0)
        pmc.connectAttr(outputMax.outFloat, inverseOutput.floatB)

    def bind(self):
        if self._bound:
            # Connect the global control
            self._resetSquashStretch()

            # Connect to stretch joint scales
            for joint in self.stretchJoints:
                axis = (joint.scaleX, joint.scaleY, joint.scaleZ)
                for x in range(3):
                    if self._aimAxis[x] == 1:
                        if self.stretchEnabled:
                            pmc.connectAttr(self._utilityNodes['outMax'].outFloat, axis[x], force=True)
                    else:
                        if self.squashEnabled:
                            pmc.connectAttr(self._utilityNodes['inverseOutput'].outFloat, axis[x], force=True)

            self._bound = True

    def unbind(self):
        if self._bound:
            # Disconnect stretchJoint scales
            for joint in self.stretchJoints:
                axis = (joint.scaleX, joint.scaleY, joint.scaleZ)
                for x in range(3):
                    if self._aimAxis[x] == 1:
                        try:
                            pmc.disconnectAttr(self._utilityNodes['outMax'].outFloat, axis[x])
                        except RuntimeError:
                            pass
                    else:
                        try:
                            pmc.disconnectAttr(self._utilityNodes['inverseOutput'].outFloat, axis[x])
                        except RuntimeError:
                            pass

            JointComponent.unbind(self)

            self._bound = False


    #### public properties ####

    @property
    def stretchEnabled(self):
        return self._stretchEnabled

    @stretchEnabled.setter
    def stretchEnabled(self, value):

        self._stretchEnabled = value

        # If the component is bound, bind squash and stretch
        if self.bound:
            self.build()

    @property
    def squashEnabled(self):
        return  self._squashEnabled

    @squashEnabled.setter
    def squashEnabled(self, value):

        self._squashEnabled = value

        # If the component is bound, bind squash and stretch
        if self.bound:
            self.build()

    @property
    def squashAndStretchEnabled(self):
        return self._squashEnabled, self._stretchEnabled

    @squashAndStretchEnabled.setter
    def squashAndStretchEnabled(self, value):

        self._squashEnabled = value
        self._stretchEnabled = value

        # If the component is bound, bind squash and stretch
        if self._bound:
            self.build()

class FKComponent(StretchJointComponent):
    '''
    Represents a basic FK control.
    Might be useless? The name is nicer than saying "StretchJoint" when we mean FK
    '''
    def __init__(self, **kwargs):
        StretchJointComponent.__init__(self, stretchMin=0.0, **kwargs)

    def build(self):
        # Build the basic control curve structure
        Component.build(self)

        # Add Squash and Stretch
        StretchJointComponent.build(self)

        return self.componentGroup

    def bind(self):

        if not self._bound:

            # Bind the mainControl
            JointComponent.bind(self)

            # Attach squash and stretch
            StretchJointComponent.bind(self)

            self.bound = True

class IKComponent(StretchJointComponent):
    '''
    A basic IK control
    '''

    def __init__(self, noFlipKnee=False, poleControlCurveType=defaultPoleControl, **kwargs):
        StretchJointComponent.__init__(self, stretchMin=1.0, **kwargs)
        self._noFlipKnee = noFlipKnee
        self._poleControlCurveType = poleControlCurveType


    #### public methods ####

    def build(self):
        Component.build(self)

        StretchJointComponent.build(self)

        return self.componentGroup

    def bind(self):

        if not self._bound:

            # Set the parentSpace
            self._resetParentSpace()

            # Create the ikHandle and effector
            self._handle, self._effector = pmc.ikHandle(sj=self._startJoint, ee=self.endJoint)

            # Parent the handle to the main control
            pmc.parent(self._handle, self.mainControl)

            # Rename the handle and effector
            pmc.rename(self._handle, self.name + '_handle')
            pmc.rename(self._effector, self.name + '_effector')

            # Add a twist attribute to the main control and connect it to the handles twist
            pmc.addAttr(self.mainControl, ln='twist', at='double', k=True)
            pmc.connectAttr(self.mainControl.twist, self._handle.twist)

            # If not a no flip knee, constrain the polevector
            if not self._noFlipKnee:
                self._constraints.append(pmc.poleVectorConstraint(self._poleControl, self._handle,
                                                                  name=self.name+'_poleVectorConstraint'))

            # Add the mainControl constraint
            self._constraints.append( pmc.parentConstraint(self.mainControl, self.endJoint, st=('x','y','z'),
                                                           mo=True, name=self.name+'+mainControlConstraint'))

            StretchJointComponent.bind(self)

            self._bound = True


    def zero(self):

        # Set the local space buffer's orientation to the start joint's orientation
        #self.localSpaceBuffer.setMatrix(self.endJoint.getMatrix(worldSpace=True), worldSpace=True)
        self.localSpaceBuffer.setTranslation(self.endJoint.getTranslation('world'))

        # Grab the knee
        self.poleJoint = self._getPoleJoint()

        if not self._noFlipKnee:
            polePoint = self._getPolePoint()

            # Create empty transform and move it to the pole point
            poleObject = pmc.group(empty=True, name=self.name + '_poleVector_point')
            poleObject.setTranslation(polePoint, space='world')
            poleCurve = self._poleControlCurveType.create()
            pmc.rename(poleCurve, self.name + '_poleVector_ctrl')
            poleCurve.setMatrix(poleObject.getMatrix())
            pmc.parent(poleCurve, poleObject)
            pmc.parent(poleObject, self.localSpaceBuffer)

            # Normalize the polepoint, to get the direction to the elbow
            direction = polePoint.normal()

            # Get the Quaternion rotation needed to rotate from
            # the world up to the direction of the elbow
            rotation = (dt.Vector(0, 1, 0)).rotateTo(direction)

            # Rotate the locator by that ammount
            poleObject.rotateBy(rotation)

            self._poleControl = poleObject

    def snap(self):

        #### Main Control ####

        targetM = self.endJoint.getMatrix(worldSpace=True)

        self.mainControl.setMatrix(targetM, worldSpace=True)

        #### Pole Control ####

        if not self._noFlipKnee:

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

            self._poleControl.setTranslation(polePoint, space='world')

    def bake(self, frame):

        JointComponent.bake(self, frame)

        if not self._noFlipKnee:
            pmc.setKeyframe(self._poleControl, t=frame)

    def unbind(self):

        if self._bound:
            StretchJointComponent.unbind(self)
            pmc.delete(self._handle)

            self._bound = False




    #### private methods ####

    def _getPolePoint(self):
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

        return polePoint

    def _getPoleJoint(self):

        polejoint = None

        # For each deform target return the one that has a parent and child in the list
        for target in self._deformTargets:
            parents = []
            children = []
            for otherTarget in self._deformTargets:
                if otherTarget.isParentOf(target):
                    parents.append(otherTarget)
                if otherTarget.isChildOf(target):
                    children.append(otherTarget)
            if len(parents) > 0 and len(children) > 0:
                polejoint = target
                break

        return polejoint

class GlobalComponent(Component):
    '''
    A component built to be the global controller for a rig
    '''
    def __init__(self, scaleControl = None, **kwargs):
        self._scaleControl = scaleControl
        Component.__init__(self, **kwargs)

    def snap(self):

        # Set the control position to the orientation of the first joint
        targetM = self._deformTargets[0].getMatrix(worldSpace=True)

        self.mainControl.setMatrix(targetM, worldSpace=True)

        self.mainControl.setScale(self._scaleControl.getScale())

    def bind(self):

        if not self._bound:

            # Add a scale constraint to the scale target
            self._constraints.append(pmc.scaleConstraint(self._mainControl, self._scaleControl,
                                                         name=self.name+'_globalScaleConstraint'))

            Component.bind(self)

            self._bound = True

    def unbind(self):

        # Okay this is really silly but is works
        pass



    @property
    def scaleControl(self):
        return self._scaleControl

class MultiFKComponent(FKComponent):
    '''
    Represents a series of FK Controls.
    '''
    def __init__(self, extraDeformJoints, **kwargs):
        FKComponent.__init__(self, **kwargs)
        self.extraDeformJoints = [[]]
        self.extraComponents = []
        counter = 1
        for jointList in self.extraDeformJoints:
            com = FKComponent(name=self.name+str(counter), deformTargets=jointList, **kwargs)
            self.extraComponents.append(com)
            counter += 1


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
    group = pmc.PyNode('ethan_skeleton')
    root = pmc.PyNode('ethan_root_M')
    hips = pmc.PyNode('ethan_hips_M')
    upLeg = pmc.PyNode('ethan_thigh_L')
    leg = pmc.PyNode('ethan_knee_L')
    foot = pmc.PyNode('ethan_foot_L')
    spine = pmc.PyNode('ethan_spineBase_M')
    rUpLeg = pmc.PyNode('ethan_thigh_R')
    rLeg = pmc.PyNode('ethan_knee_R')
    rFoot = pmc.PyNode('ethan_foot_R')
    spine1 = pmc.PyNode('ethan_spine1_M')
    spine2 = pmc.PyNode('ethan_spine2_M')
    spine3 = pmc.PyNode('ethan_spine3_M')
    arm = pmc.PyNode('ethan_upperArm_R')
    foreArm = pmc.PyNode('ethan_foreArm_R')
    hand = pmc.PyNode('ethan_hand_R')

    ethanRig = Rig(name='Ethan')
    ethanRig.addComponent(GlobalComponent,
                          name='root',
                            deformTargets=[root],
                              mainControlType=defaultMasterControl,
                            scaleControl = group)

    ethanRig.globalControl = ethanRig.root

    ethanRig.addComponent(FKComponent,
                          name='hip',
                          deformTargets=[hips],
                          mainControlType=defaultSpineControl)
    ethanRig.hip.uprightAndParentSpace = ethanRig.root

    ethanRig.addComponent(FKComponent,
                          name='thigh',
                          deformTargets=[upLeg],
                          mainControlType=defaultFKControl)
    ethanRig.thigh.uprightAndParentSpace = ethanRig.hip

    ethanRig.addComponent(FKComponent,
                          name='knee',
                          deformTargets=[leg],
                          mainControlType=defaultFKControl)
    ethanRig.knee.uprightAndParentSpace = ethanRig.thigh

    ethanRig.addComponent(FKComponent,
                          name='foot',
                          deformTargets=[foot],
                          mainControlType=defaultFKControl)
    ethanRig.foot.uprightAndParentSpace = ethanRig.knee

    ethanRig.addComponent(IKComponent,
                          name='rLeg',
                          deformTargets=[rUpLeg,rLeg,rFoot],
                          mainControlType=defaultIKControl)
    ethanRig.rLeg.uprightAndParentSpace = ethanRig.hip
    ethanRig.rLeg.squashAndStretchEnabled = True

    ethanRig.build()

    ethanRig.bake()

    ethanRig.bind()

    print ethanRig.metaData

    ethanRig.bakeDeforms()

    ethanRig.delete()

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

def connect_joint_to_controller(jointControl):
    '''
    For now this just adds a parent constraint from the controller to the joint
    :param jointControl: The JointControl object.
    :return: None
    '''
    constraint = pmc.parentConstraint(jointControl.control, jointControl.targetJoint, mo=True)
    jointControl.constraint = constraint


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
            self.mainControlType = mainControlType
            self.deformTargets = deformTargets
            self.deformJoints = []
            self.inputs = {}
            self.outputs = {}

        def build(self):
            # Create an empty group to house all parts of the component
            self.comGroup = pmc.group(empty=True, name=self.name + '_com')

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
            self.mainControlBuffer = pmc.group(empty=True, name=self.name + '_srtBuffer')
            pmc.parent(self.mainControlBuffer, self.controlGroup)

            # Connect the control space buffer to the local world input
            connect_transforms(self.inputs['localWorld'], self.mainControlBuffer)

            # Create the main control
            self.mainControl = controltools.create_control_curve(self.mainControlType)
            pmc.rename(self.mainControl, self.name + '_main_ctrl')
            match_target_orientation(target=None, object=self.mainControl, upVector=dt.Vector(0, 1, 0))
            pmc.parent(self.mainControl, self.mainControlBuffer, r=False)

            # If there is a endJoint, move the localWorldGroup to that worldPosition
            # Otherwise
            # if self.endJoint is not None:
            # self.getInput('localWorld').setMatrix(self.endJoint.getMatrix(worldSpace=True), worldSpace=True)

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