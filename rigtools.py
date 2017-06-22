import pymel.core as pmc
import pymel.core.datatypes as dt
import controltools
import os
import json
import uuid
import maya.utils

##############################
#       Rig Settings         #
##############################

COMPONENT_TYPES = {
    'Component': {
        'name': 'defaultComponent',
        'type': 'Component',
        'mainControlType': 'default',
        'mainControlScale': 10.0,
        'deformTargets': [],
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
        'deformTargets': [],
        'aimAxis': [1,0,0],
        'parentSpace': None,
        'uprightSpace': None,
        'stretchEnabled': False,
        'squashEnabled': False,
        'icon': ":/ikHandle.svg"
    }
}

##############################
#     Utility Classes        #
##############################

class Signal():
    def __init__(self):
        self._handlers=[]

    def connect(self, handler):
        self._handlers.append(handler)

    def fire(self, *args, **kwargs):
        for handler in self._handlers:
            handler(**kwargs)


##############################
#     Settings Classes       #
##############################

class ControlCurve():
    def __init__(self, curveType='default', scale=1.0, color=dt.Color.blue):
        self.curveType = curveType
        self.scale = scale
        self.color = color

    def create(self, name='default', upVector=[0,1,0]):

        vector = dt.Vector(upVector)

        # Use curve tools to generate a control from the control library
        control = controltools.create_control_curve(self.curveType)

        # Rename the control curve
        pmc.rename(control, name+'_ctrl')

        # Set the base scale of the curve
        self._matchScale(control, self.scale)

        # Rotate the control cvs to the desired orientation
        self._matchTarget(object=control, upVector=vector)

        # Set the override color of the curve
        shape = control.getShape()
        shape.drawOverrideColor = self.color

        return control

    def _matchTarget(self, object, upVector):

        # The world up vector
        worldUp = dt.Vector(0, 1, 0)

        # The Transformation matrix of the target in world space
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

    def _matchScale(self, target, source):

        target.setScale((source, source, source))

        pmc.makeIdentity(target, apply=True, rotate=False, scale=True, translate=False)

defaultFKControl = ControlCurve(scale=10.0)

defaultMasterControl = ControlCurve(scale=30.0, curveType='cross')

defaultPoleControl = ControlCurve(scale=2.0, curveType='triangle')

defaultSpineControl = ControlCurve(scale=20.0)

defaultIKControl = ControlCurve(scale=10.0, curveType='cube')


##############################
#    Component Classes       #
##############################

class Component(object):
    '''
    The base class of all components.
    '''

    defaultControl = ControlCurve()

    def __init__(self, name='default', deformTargets=[], mainControlType='circle',
                 mainControlColor=dt.Color.blue, mainControlScale=10.0,
                 aimAxis=dt.Vector(1,0,0), rig=None, parentSpace=None,
                 uprightSpace=None, **kwargs):
        self._name = name
        self._utilityNodes = {}
        self._aimAxis = aimAxis
        self._active = False
        self._bound = False
        self._constraints = []
        self._rig = rig
        self._uprightSpace = uprightSpace
        self._parentSpace = parentSpace
        self._mainControl = None
        self.parentSpaceChanged = Signal()

        self._deformTargets = [pmc.PyNode(target) for target in deformTargets]

        self._mainControlType = ControlCurve(curveType=mainControlType,
                                             scale=mainControlScale,
                                             color=mainControlColor)

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
            for joint in self._deformTargets:

                self._constraints.append(pmc.parentConstraint(self._mainControl, joint, mo=True))
                self._constraints.append(pmc.scaleConstraint(self._mainControl, joint))

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

            # Remove all utility nodes
            for key, value in self._utilityNodes.iteritems():
                try:
                    pmc.delete(value)
                except:
                    pass

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
            if self.uprightSpace is None:

                # Set the worldSpaceMatrix to the identity Matrix
                identityMatrix = dt.Matrix()

                pmc.setAttr(self._utilityNodes['uprightMultMatrixNode'].matrixIn[0], identityMatrix,
                                force=True)
            else:
                # Connect the components worldSpaceMatrix to this components multiply matrix utility node
                pmc.connectAttr(self.uprightSpace.worldSpaceMatrix,
                                self._utilityNodes['uprightMultMatrixNode'].matrixIn[0],
                                force=True)

            if self.parentSpace is None:

                # Set the worldSpaceMatrix to the identity Matrix
                identityMatrix = dt.Matrix()

                pmc.setAttr(self._utilityNodes['parentMultMatrixNode'].matrixIn[0], identityMatrix,
                        force=True)
            else:
                # Connect the components worldSpaceMatrix to this components multiply matrix utility node
                pmc.connectAttr(self.parentSpace.worldSpaceMatrix,
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
    def data(self):

        def getName(target):
            try:
                return str(target.name)
            except AttributeError:
                return 'None'

        arguments = {}

        arguments['name'] = self.name
        arguments['componentType'] = None
        arguments['deformTargets'] = [str(target) for target in self._deformTargets]
        arguments['controlTypes'] = self._mainControlType.curveType
        arguments['aimAxis'] = [axis for axis in self._aimAxis]
        arguments['parentSpace'] = getName(self.parentSpace)
        arguments['uprightSpace'] = getName(self.uprightSpace)
        arguments['type'] = self.__class__.__name__

        return arguments

    @property
    def printData(self):
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
    def id(self):
        return self._id

    @property
    def parentSpace(self):
        if self._parentSpace is not None:
            return self._rig.getComponent(self._parentSpace)
        else:
            return None

    @parentSpace.setter
    def parentSpace(self, value):
        self._parentSpace = value
        self.parentSpaceChanged.fire(self)

    @property
    def uprightSpace(self):
        if self._uprightSpace is not None:
            return self._rig.getComponent(self._uprightSpace)
        else:
            return None

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
    '''
    An object for building components from a set of component data.
    '''

    def __init__(self, name, componentData, directory):

        # Assign a name, this is mostly for display purposes
        self._name = name

        # Assign the save location for the rig
        self._directory = directory

        # Assign a key to access data
        self._componentData = componentData

        # Create a dictionary to hold all active components
        self._components = {}

        # Some simple state bools
        self._bound = False
        self._built = False
        self._baked = False


    #### Public Methods ####

    def build(self):
        # Create a master group for the rig
        self.rigGroup = pmc.group(empty=True, name=self._name + '_rig')

        # For each component in the component data...
        for id, com in self._componentData.iteritems():
            # Create an instance of the component's class
            component = self._createComponent(**com)

            # Add the component to this rigs active component dictionary
            self._components[id] = component

            # Build the components and grab the group they're spawned in...
            componentGroup = self._components[id].build()

            # And parent it to this rigs group
            pmc.parent(componentGroup, self.rigGroup)

        # For each component, apply the parent space
        # This ensures that all components exist before parenting occurs
        for id, com in self._components.iteritems():
            com.parent()

        self._built = True

    def bind(self):

        # If the rig is not built, build it
        if not self._built:
            self.build()

        if not self._bound:
            # For each component in the rig, bind to its target
            for id, com in self._components.iteritems():
                com.bind()

            self._bound = True

    def snap(self):

        # For each component in the rig, snap to its target
        for id, com in self._components.iteritems():
            com.snap()

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
                for id, com in self._components.iteritems():
                    com.snap()
                    com.bake(frame)
        pmc.setCurrentTime(1)

        self._baked = True

    def bakeDeforms(self, components=None, frameRange=10):

        # Goes through every frame, snaps the controls and keys their position
        for frame in range(frameRange):
            pmc.setCurrentTime(frame)
            if components is not None:
                for com in components:
                    com.bakeDeforms(frame)
            else:
                for id, com in self._components.iteritems():
                    com.bakeDeforms(frame)
        pmc.setCurrentTime(1)

        self._baked = False

    def unbind(self):
        if self._bound:
            # For each component in the rig, unbind it
            for id, com in self._components.iteritems():
                com.unbind()

            self._bound = False

    def remove(self):

        if self._bound:
            self.unbind()

        if self.built:

            # For each component in the rig, remove it
            for id, com in self._components.iteritems():
                com.remove()

            # Then delete the rig group
            pmc.delete(self.rigGroup)

            # And reset the value of rigGroup
            self.rigGroup = None

            # And finally, clear out the dictionary of active components
            self._components.clear()

            self._built = False
            self._baked = False

    def addComponent(self, **kwargs):

        # Grab the idea of the new component
        id = uuid.uuid4().hex

        # Add the component data to the data dictionary
        self._componentData[id] = kwargs

        # Set the id of the component
        self._componentData[id]['id'] = id

        return id

    def removeComponent(self, id):

        # Try to remove the selected component
        try:
            self._components[id].remove()
        except KeyError:
            pass

        # Remove the component from the component dictionary
        del self._componentData[id]

    def setComponent(self, id, attr, value):

        # Set the attribute in the component data
        self._componentData[id][attr] = value

    def getComponent(self, id):
        '''
        Returns the active component of a specific ID
        '''

        return self._components[id]

    def getComponentData(self, id):
        '''
        Returns the component data of a specific IK
        '''

        return self._componentData[id]

    def printData(self):

        def getName(target):
            try:
                return str(target.name)
            except AttributeError:
                return 'None'

        data = []
        data.append('')
        data.append('#####  ' + self._name + '  #####')

        data.append('')

        print ('\n').join(data)

        for com in self._components:
            print self._components[com].printData


    #### Private Methods ####

    def _createComponent(self, componentType='FKComponent', **kwargs):
        '''
        Creates a new component instance based on inputed data\
        :param componentType: A string with the name of the component class
        '''
        print componentType
        componentType = eval(componentType)

        component = componentType(rig=self, **kwargs)

        return component


    #### Public Properties ####

    @property
    def componentData(self):
        return self._componentData

    @property
    def directory(self):
        return self._directory

    @property
    def built(self):
        return self._built

    @property
    def bound(self):
        return self._bound

    @property
    def baked(self):
        return self._baked


class JointComponent(Component):
    '''
    Represents a component that specifically deforms joints
    '''

    def __init__(self, aimAxis=dt.Vector(1,0,0), **kwargs):
        Component.__init__(self, aimAxis=aimAxis, **kwargs)
        self._startJoint = None
        self._endJoint = None


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

    def _getChildJoint(self, joint):

        childJoint = None

        # Loop through joint targets
        # Return the joint that is a child of the specified joint
        for target in self._deformTargets:
            if target.isChildOf(joint):
                childJoint.append(target)

        return childJoint

    #### public methods ####

    def zero(self):

        # Set the local space buffer's orientation to the start joint's orientation
        self.localSpaceBuffer.setMatrix(self.endJoint.getMatrix(worldSpace=True), worldSpace=True)

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
        if not self._startJoint:
            self._startJoint = self._getStartJoint()

        return self._startJoint

    @property
    def endJoint(self):
        if not self._endJoint:
            self._endJoint = self._getEndJoint()

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
            try:
                pmc.connectAttr(self.parentSpace.mainControl.parentInverseMatrix,
                                self._utilityNodes['point1SpaceSwitch'].matrixIn[1], force=True)
                pmc.connectAttr(self.parentSpace.mainControl.parentInverseMatrix,
                                self._utilityNodes['point2SpaceSwitch'].matrixIn[1], force=True)
                pmc.connectAttr(self.parentSpace.mainControl.inverseMatrix,
                                self._utilityNodes['point1SpaceSwitch'].matrixIn[2], force=True)
                pmc.connectAttr(self.parentSpace.mainControl.inverseMatrix,
                                self._utilityNodes['point2SpaceSwitch'].matrixIn[2], force=True)
            except AttributeError:
                identityMatrix = dt.Matrix()
                pmc.setAttr(self._utilityNodes['point1SpaceSwitch'].matrixIn[1], identityMatrix, force=True)
                pmc.setAttr(self._utilityNodes['point2SpaceSwitch'].matrixIn[1], identityMatrix, force=True)


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
            pmc.parent(poleObject, poleCurve)
            pmc.parent(poleCurve, self.localSpaceBuffer)

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

        print self._deformTargets

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


##############################
#       Model Classes        #
##############################

class RigToolsData(object):

    def __init__(self, dir=os.environ['MAYA_APP_DIR']):
        self.dir = dir

    def _getDir(self, rigName):
        return os.path.join(self.dir, rigName + '.json')

    def load(self, directory):

        try:
            with open(directory) as c:
                return json.load(c)
        except IOError:
            return {}

    def save(self, directory, componentData):

        with open(directory, 'w') as c:
            json.dump(componentData, c, indent=4)


class RigToolsModel(object):
    '''
    The class in charge of handling all mutable data as well as the maya scene.
    '''

    def __init__(self, data):

        # Set up initial variables
        self._activeRigs = {}

        # Grab the data handler
        self._data = data

    def createRig(self, directory):

        # Grab the name from the path
        name = os.path.basename(os.path.splitext(directory)[0])

        # Create a new set of component data
        componentData = {}

        # Create a rig and add it to the active rig list
        self._activeRigs[name] = Rig(name, componentData, directory)

        # Save a file for the rig
        self._data.save(directory, componentData)

        return name

    def buildRig(self, rigName):

        # Remove the rig
        self._activeRigs[rigName].remove()

        # Rebuild the rig
        self._activeRigs[rigName].build()

    def bindRig(self, rigName):

        # Remove the rig()
        self._activeRigs[rigName].remove()

        # Build and bind the rig
        self._activeRigs[rigName].bind()

    def bakeRig(self, rigName):

        # Remove the rig
        self._activeRigs[rigName].remove()

        # Rebuild, bake, and bind the rig
        self._activeRigs[rigName].bake()
        self._activeRigs[rigName].bind()

    def bakeDeforms(self, rigName):
        self._activeRigs[rigName].bakeDeforms()

    def unbindRig(self, rigName):
        self._activeRigs[rigName].unbind()

    def refreshRig(self, rigName):

        # Check the state of the rig
        built = self._activeRigs[rigName].built
        bound = self._activeRigs[rigName].bound
        baked = self._activeRigs[rigName].baked

        # Remove the rig
        if built:
            self._activeRigs[rigName].build()
        if baked:
            self._activeRigs[rigName].bake()
        if bound:
            self._activeRigs[rigName].bound()

    def removeRig(self, rigName):

        # Remove the rig
        self._activeRigs[rigName].remove()

    def saveRig(self, rigName):
        self._data.save(self._activeRigs[rigName].directory, self._activeRigs[rigName].componentData)

    def loadRig(self, directory):

        name = os.path.basename(os.path.splitext(directory)[0])

        componentData = self._data.load(directory)

        self._activeRigs[name] = Rig(name, componentData, directory)

        return name

    def rigData(self, rigName):
        return self._activeRigs[rigName].componentData

    def addComponent(self, rigName, type):
        '''
        Adds a component to the rig based on a string for rig name and componentType
        '''

        return self._activeRigs[rigName].addComponent(**COMPONENT_TYPES[type])

    def removeComponent(self, rigName, id):

        return self._activeRigs[rigName].removeComponent(id)

    def setComponentValue(self, rigName, id, attr, value):
        self._activeRigs[rigName].setComponent(id, attr, value)

    def isBuilt(self, rigName):
        return self._activeRigs[rigName].built

    def isBound(self, rigName):
        return self._activeRigs[rigName].bound

    def isBaked(self, rigName):
        return self._activeRigs[rigName].baked


##############################
#     Test Functions         #
##############################

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


    data = RigToolsData()
    model = RigToolsModel(data)

    model.createRig('Ethan')
    #model.loadRig('Ethan')


    rootID = model.addComponent('Ethan', name='root',
                       componentType= 'Component',
                       deformTargets=['ethan_skeleton'],
                       mainControlScale=50,
                       mainControlType='cross',
                       aimAxis=[0,1,0]
                       )

    '''
    cogID = model.addComponent('Ethan',
                       name='hip',
                       componentType='Component',
                       mainControlType=defaultSpineControl.curveType,
                       mainControlScale=40.0)
    model.setComponentValue('Ethan', cogID, 'parentSpace', rootID)
    model.setComponentValue('Ethan', cogID, 'uprightSpace', rootID)
    '''

    hipID = model.addComponent('Ethan',
                       name='hip',
                       componentType='FKComponent',
                       deformTargets=['ethan_hips_M'],
                       mainControlType=defaultSpineControl.curveType,
                       mainControlScale=defaultSpineControl.scale)
    model.setComponentValue('Ethan', hipID, 'parentSpace', rootID)
    model.setComponentValue('Ethan', hipID, 'uprightSpace', rootID)

    rLegID = model.addComponent('Ethan',
                                name='Leg_R',
                                componentType='IKComponent',
                                deformTargets=['ethan_thigh_R', 'ethan_knee_R', 'ethan_foot_R'],
                                mainControlType=defaultIKControl.curveType,
                                mainControlScale=defaultIKControl.scale)
    model.setComponentValue('Ethan', rLegID, 'parentSpace', hipID)
    model.setComponentValue('Ethan', rLegID, 'uprightSpace', hipID)
    model.setComponentValue('Ethan', rLegID, 'squashEnabled', True)
    model.setComponentValue('Ethan', rLegID, 'stretchEnabled', True)

    model.buildRig('Ethan')

    model.bindRig('Ethan')

    #model.saveRig('Ethan')

    pmc.undoInfo(openChunk=False)

# from rigtools import rigtools; reload(rigtools); rigtools._test_rigtools()

