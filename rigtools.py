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
        'target': None,
        'aimAxis': [0,1,0],
        'parentSpace': None,
        'uprightSpace': None,
        'icon': ":/cube.png",
        'enabled': True,
        'spaceSwitchEnabled': False
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
        'icon': ":/joint.svg",
        'enabled': True,
        'spaceSwitchEnabled': False
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
        'icon': ":/ikHandle.svg",
        'noFlipKnee': False,
        'poleControlCurveType': 'triangle',
        'enabled': True,
        'spaceSwitchEnabled': False
    },
    'MultiFKComponent': {
            'name': 'defaultMultiFKComponent',
            'type': 'MultiFKComponent',
            'mainControlType': 'square',
            'mainControlScale': 20.0,
            'childControlType': 'default',
            'childControlScale': 10.0,
            'deformTargets': [],
            'aimAxis': [1,0,0],
            'parentSpace': None,
            'uprightSpace': None,
            'stretchEnabled': False,
            'squashEnabled': False,
            'icon': ":/ikHandle.svg",
            'enabled': True,
            'spaceSwitchEnabled': False
    },
    'SpineIKComponent': {
            'name': 'defaultSpineIKComponent',
            'type': 'SpineIKComponent',
            'mainControlType': 'square',
            'mainControlScale': 30.0,
            'childControlType': 'default',
            'childControlScale': 25.0,
            'deformTargets': [],
            'aimAxis': [1,0,0],
            'parentSpace': None,
            'uprightSpace': None,
            'stretchEnabled': False,
            'squashEnabled': False,
            'icon': ":/ikHandle.svg",
            'enabled': True,
            'spaceSwitchEnabled': False
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

    def __init__(self, name='default', target=None, mainControlType='circle',
                 mainControlColor=dt.Color.blue, mainControlScale=10.0,
                 rig=None, parentSpace=None,
                 uprightSpace=None, spaceSwitchEnabled=False, **kwargs):
        self._name = name
        self._utilityNodes = {}
        self._active = False
        self._bound = False
        self._constraints = []
        self._rig = rig
        self._uprightSpace = uprightSpace
        self._parentSpace = parentSpace
        self._mainControl = None
        self.spaceSwitchEnabled = spaceSwitchEnabled

        if target is not None:
            self._target = pmc.PyNode(target)

        self._mainControlType = ControlCurve(curveType=mainControlType,
                                             scale=mainControlScale,
                                             color=mainControlColor)

    #### Public Methods ####

    def build(self):
        if not self.active:

            # Create a component group to contain all component DAG nodes
            self.componentGroup = pmc.group(empty=True, name=self.name+'_com')

            # Create the main control curve
            self._mainControl = self._mainControlType.create(upVector=[1,0,0], name=self.name+'_main')

            # Create the local space for the control
            # This is better at preserving transforms than freezing transforms
            self.localSpaceBuffer = pmc.group(empty=True, name=self.name+'_localSpace_srtBuffer')

            # Transform/Scale/Rotate localSpaceGroup and parent the control curve to it
            pmc.parent(self._mainControl, self.localSpaceBuffer, relative=True)

            # Add parentSpace and uprightSpace groups and connections
            self._addParentSpaceNodes()

            # Snap the controls to the deform targets
            self.zero()

            # Parent the parentSpaceBuffer to the component group
            pmc.parent(self.parentSpaceBuffer, self.componentGroup)

            # Set the 'active' bool to True
            self._active = True

            return self.componentGroup

    def parent(self, components):
        # Set the parentSpace
        self._addParentSpace(components)

    def zero(self):
        # Sets the default localspacebuffer position
        try:
            self.localSpaceBuffer.setMatrix(self._target.getMatrix(worldSpace=True), worldSpace=True)
        except AttributeError:
            pass

    def snap(self):
        # Snap controls to the positions of the deform targets
        pass

    def bake(self, frame):

        pmc.setKeyframe(self._mainControl, t=frame)

    def bakeDeforms(self, frame):
        pass

    def bind(self):
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

    def _addParentSpace(self, components):

        # Create a choice node to determine parentSpace
        parentSpaceChoiceNode = pmc.createNode('choice', name=self.name + '_parentSpaceChoice')
        uprightSpaceChoiceNode = pmc.createNode('choice', name=self.name + '_uprightSpaceChoice')
        self._utilityNodes['parentSpaceChoiceNode'] = parentSpaceChoiceNode
        self._utilityNodes['uprightSpaceChoiceNode'] = uprightSpaceChoiceNode

        if self.spaceSwitchEnabled:
            # Generate the names for the enums
            comNames = [str(value.name) for key, value in components.iteritems() if value.name is not self._name]
            names = ['world'] + comNames
            enumString = ':'.join(names)

            # Find the values for the selected space
            if self._parentSpace is None:
                startParentIndex = 0
            else:
                startParentIndex = names.index(components[self._parentSpace].name)
            if self._uprightSpace is None:
                startUprightIndex = 0
            else:
                startUprightIndex = names.index(components[self._uprightSpace].name)

            # Set the world option
            identityMatrix = dt.Matrix()

            worldParentMultMatrix = pmc.createNode('multMatrix', name=self.name + '_parentMult_0')
            self._utilityNodes['parentSpaceMult_0'] = worldParentMultMatrix
            pmc.setAttr(worldParentMultMatrix.matrixIn[0], self.worldSpaceMatrix)
            pmc.setAttr(worldParentMultMatrix.matrixIn[1], identityMatrix)
            pmc.connectAttr(worldParentMultMatrix.matrixSum, parentSpaceChoiceNode.input[0])

            worldUprightMultMatrix = pmc.createNode('multMatrix', name=self.name + '_uprightMult_0')
            self._utilityNodes['uprightSpaceMult_0'] = worldUprightMultMatrix
            pmc.setAttr(worldUprightMultMatrix.matrixIn[0], self.worldSpaceMatrix)
            pmc.setAttr(worldUprightMultMatrix.matrixIn[1], identityMatrix)
            pmc.connectAttr(worldUprightMultMatrix.matrixSum, uprightSpaceChoiceNode.input[0])

            # Create options for the rest
            for index in range(len(comNames)):
                parentComponent = [value for key, value in components.iteritems()
                                   if value.name == comNames[index]][0]

                multMatrix = pmc.createNode('multMatrix', name=self.name + '_parentMult_' + str(index+1))
                self._utilityNodes['parentSpaceMult_' + str(index+1)] = multMatrix
                pmc.setAttr(multMatrix.matrixIn[0], self.worldSpaceMatrix)
                pmc.setAttr(multMatrix.matrixIn[1], parentComponent.worldSpaceMatrix.inverse())
                pmc.connectAttr(parentComponent.matrixOutput.worldMatrix[0], multMatrix.matrixIn[2])
                pmc.connectAttr(multMatrix.matrixSum, parentSpaceChoiceNode.input[index+1])
            for index in range(len(comNames)):
                parentComponent = [value for key, value in components.iteritems()
                                   if value.name == comNames[index]][0]
                multMatrix = pmc.createNode('multMatrix', name=self.name + '_uprightMult_' + str(index+1))
                self._utilityNodes['uprightSpaceMult_' + str(index+1)] = multMatrix
                pmc.setAttr(multMatrix.matrixIn[0], self.worldSpaceMatrix)
                pmc.setAttr(multMatrix.matrixIn[1], parentComponent.worldSpaceMatrix.inverse())
                pmc.connectAttr(parentComponent.matrixOutput.worldMatrix[0], multMatrix.matrixIn[2])
                pmc.connectAttr(multMatrix.matrixSum, uprightSpaceChoiceNode.input[index+1])

            # Create an attribute on the mainControl for switching space
            pmc.addAttr(self._mainControl, sn='ps', ln='parentSpace', at='enum', en=enumString, h=False, k=True)
            pmc.addAttr(self._mainControl, sn='us', ln='uprightSpace',at='enum',  en=enumString, h=False, k=True)

            # Connect it to the choice value
            pmc.connectAttr(self._mainControl.parentSpace, parentSpaceChoiceNode.selector)
            pmc.connectAttr(self._mainControl.uprightSpace, uprightSpaceChoiceNode.selector)

            # Set them to the default values
            self._mainControl.setAttr('parentSpace', startParentIndex)
            self._mainControl.setAttr('uprightSpace', startUprightIndex)
        else:
            # Set the world option
            identityMatrix = dt.Matrix()

            # Just add the current parentSpace...
            multMatrix = pmc.createNode('multMatrix', name=self.name + '_parentMult')
            self._utilityNodes['parentSpaceMult'] = multMatrix
            pmc.setAttr(multMatrix.matrixIn[0], self.worldSpaceMatrix)
            try:
                pmc.setAttr(multMatrix.matrixIn[1], self.parentSpace.worldSpaceMatrix.inverse())
                pmc.connectAttr(self.parentSpace.matrixOutput.worldMatrix[0], multMatrix.matrixIn[2])
            except AttributeError:
                pmc.setAttr(multMatrix.matrixIn[1], identityMatrix)
            pmc.connectAttr(multMatrix.matrixSum, parentSpaceChoiceNode.input[0])

            # ...and the uprightSpace
            multMatrix = pmc.createNode('multMatrix', name=self.name + '_uprightMult')
            self._utilityNodes['uprightSpaceMult'] = multMatrix
            pmc.setAttr(multMatrix.matrixIn[0], self.worldSpaceMatrix)
            try:
                pmc.setAttr(multMatrix.matrixIn[1], self.uprightSpace.worldSpaceMatrix.inverse())
                pmc.connectAttr(self.uprightSpace.matrixOutput.worldMatrix[0], multMatrix.matrixIn[2])
            except AttributeError:
                pmc.setAttr(multMatrix.matrixIn[1], identityMatrix)
            pmc.connectAttr(multMatrix.matrixSum, uprightSpaceChoiceNode.input[0])


        # Connect the output of the choices to their corresponding multMatrix
        pmc.connectAttr(parentSpaceChoiceNode.output, self._utilityNodes['parentMultMatrixNode'].matrixIn[0])
        pmc.connectAttr(uprightSpaceChoiceNode.output, self._utilityNodes['uprightMultMatrixNode'].matrixIn[0])

        # Set the position of the localSpace
        self.localSpaceBuffer.setMatrix(identityMatrix, objectSpace=True)

    def _getParentSpace(self, component):
        return self._rig.getComponent(component)

    #### Public Properties ####

    @property
    def name(self):
        return self._name

    @property
    def active(self):
        return self._active

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
        arguments['target'] = str(self.target)
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

    @property
    def uprightSpace(self):
        if self._uprightSpace is not None:
            return self._rig.getComponent(self._uprightSpace)
        else:
            return None

    @uprightSpace.setter
    def uprightSpace(self, value):
        self._uprightSpace = value

    @property
    def uprightAndParentSpace(self):
        return self._uprightSpace, self._parentSpace

    @uprightAndParentSpace.setter
    def uprightAndParentSpace(self, value):
        self._uprightSpace = value
        self._parentSpace = value

    @property
    def matrixOutput(self):
        # This is the output connection for parent space connections
        return self._mainControl

    @property
    def buffer(self):
        return self.localSpaceBuffer

    @property
    def worldSpaceMatrix(self):
        # This is the worldspace matrix value
        return self._mainControl.getMatrix(worldSpace=True)

    @property
    def target(self):
        # This is a reference position, usually the origin for the main control
        return self._target

    @property
    def ready(self):
        return None

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
            # Check if component is set to 'enabled'
            if com['enabled']:

                # Create an instance of the component's class
                component = self._createComponent(componentType=com['type'],**com)

                # Add the component to this rigs active component dictionary
                self._components[id] = component

                # Build the components and grab the group they're spawned in...
                componentGroup = self._components[id].build()

                # And parent it to this rigs group
                pmc.parent(componentGroup, self.rigGroup)

        # For each component, apply the parent space
        # This ensures that all components exist before parenting occurs
        for id, com in self._components.iteritems():
            com.parent(self._components)

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

    @property
    def ready(self):
        # This iterates through all components and checks if they can be built

        error = None

        message = []

        # For each component in the component data...
        for id, com in self._componentData.iteritems():

            # Create an instance of the component's class
            component = self._createComponent(componentType=com['type'], **com)

            # Check if component is set to 'enabled'
            if component.ready is not None:
                message.append(com['type'] + ': ' + component.ready)

            del component

        if len(message) > 0:
            error = "\n".join(message)

        return error

class JointComponent(Component):
    '''
    Represents a component that specifically deforms joints
    '''

    def __init__(self, deformTargets=[], target=None, **kwargs):
        Component.__init__(self, **kwargs)

        self._deformTargets = [pmc.PyNode(target) for target in deformTargets]
        self._outputs = []
        self._outputOrients = []
        self._outputBuffers = []
        self._startJoint = None
        self._endJoint = None

    #### private methods ####

    def _getStartIndex(self):
        # Outputs and deform targets are stored in similar lists
        # This will output the index that corresponds to the starting target

        startIndex = None

        # Loop through deform joints
        # Return the joint who does not have a parent in the list
        for index in range(len(self._deformTargets)):
            target = self._deformTargets[index]

            parents = []

            for otherTarget in self._deformTargets:
                if otherTarget.isParentOf(target):
                    parents.append(otherTarget)

            if len(parents) == 0:
                startIndex = index
                break

        return startIndex

    def _getEndIndex(self):
        # Outputs and deform targets are stored in similar lists
        # This will output the index that corresponds to the last target

        endIndex = None

        # Loop through joint targets
        # Return the joint does not have any children
        for index in range(len(self._deformTargets)):
            target = self._deformTargets[index]

            children = []

            for otherTarget in self._deformTargets:
                if otherTarget.isChildOf(target):
                    children.append(otherTarget)

            if len(children) == 0:
                endIndex = index

        return endIndex

    def _getMiddleIndexList(self):
        joints = []

        # Loop through deform joints
        # Return the joint who does not have a parent in the list
        for target in self._deformTargets:

            if target is not self.startJoint and target is not self.endJoint:
                joints.append(target)

        middleJoints = []

        # Order the list by parenting
        for joint in joints:
            if len(middleJoints) == 0:
                middleJoints.append(joint)
            else:
                childIndex = None
                for index in range(len(middleJoints)):
                    if joint.isChildOf(middleJoints[index]):
                        pass
                    else:
                        childIndex = index + 1

                if childIndex is None:
                    childIndex = len(middleJoints)

                middleJoints.insert(childIndex, joint)

        # Return a list of the joints index value inside of the deform targets
        return [self._deformTargets.index(joint) for joint in middleJoints]

    def _getChildJoint(self, joint):

        childJoint = None

        # Loop through joint targets
        # Return the joint that is a child of the specified joint
        for target in self._deformTargets:
            if target.isChildOf(joint):
                childJoint.append(target)

        return childJoint

    def _addDeformOutputs(self):

        # Create a group to house outputs
        self.outputGroup = pmc.group(empty=True, name='output')
        pmc.parent(self.outputGroup, self.componentGroup)

        # Create a duplicate joint for each deform target
        for target in self._deformTargets:

            # Clear the selection cause of dumb reasons
            pmc.select(clear=True)

            # Create a joint duplicate at the same location
            joint = pmc.duplicate(target, po=True)[0]
            pmc.parent(joint, world=True)

            # Store a reference to it
            self._outputs.append(joint)


        # Create a orient buffer for each output
        for index in range(len(self._deformTargets)):

            # Create an orient buffer for the joint
            buffer = pmc.group(empty=True, name=self._outputs[index].name() + '_orientBuffer')
            self._outputOrients.append(buffer)
            buffer.setMatrix(self._deformTargets[index].getMatrix(worldSpace=True), worldSpace=True)

            # Orient the buffer towards the next target
            self._orientBuffer(index)

            # Then parent it to the output group
            pmc.parent(self._outputOrients, self.outputGroup)

            # Parent the output to it
            pmc.parent(self._outputs[index], self._outputOrients[index])

            # Create a srt buffer
            srtBuffer = pmc.group(empty=True)
            pmc.parent(buffer, srtBuffer)
            self._outputBuffers.append(srtBuffer)
            pmc.parent(srtBuffer, self.outputGroup)

    def _orientBuffer(self, index):

        # Find the child of the buffer's target
        child = None

        for target in self._deformTargets:
            if self._deformTargets[index].isChildOf(target):
                child = target

        if child:
            constraint = pmc.aimConstraint(child, self._outputOrients[index], mo=False)
        else:
            constraint = pmc.aimConstraint(self._deformTargets[index].getParent(),
                                           self._outputOrients[index],
                                           aimVector=(-1, 0, 0), mo=False)

        pmc.delete(constraint)

    def _connectToOutput(self, input, index):

        output = self._outputBuffers[index]

        orientPos = self._outputOrients[index].getMatrix(worldSpace=True)

        multMatrix = pmc.createNode('multMatrix')
        decompMatrix = pmc.createNode('decomposeMatrix')

        pmc.connectAttr(input.worldMatrix[0], decompMatrix.inputMatrix)

        pmc.connectAttr(decompMatrix.outputTranslate, output.translate)
        pmc.connectAttr(decompMatrix.outputRotate, output.rotate)

        self._outputOrients[index].setMatrix(orientPos, worldSpace=True)

    #### public methods ####

    def build(self):
        Component.build(self)

        self._addDeformOutputs()

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

        self._mainControl.setMatrix(targetM, worldSpace=True)

    def bind(self):

        if not self._bound:

            # For each deform target, connect its corresponding output to it
            for index in range(len(self._deformTargets)):

                # Create all the nodes needed
                parentSpaceMult = pmc.createNode('multMatrix', name=self.name+'_parentSpaceMult_' + str(index))
                jointOrientMult = pmc.createNode('multMatrix', name=self.name+'_jointOrientMult_' + str(index))
                jointOrientCompose = pmc.createNode('composeMatrix', name=self.name+'_jointOrientCompose_' + str(index))
                transposeMatrix = pmc.createNode('transposeMatrix', name=self.name+'_jointOrientInverseMult_' + str(index))
                translateDecompose = pmc.createNode('decomposeMatrix', name=self.name+'_parentSpaceDecomp_' + str(index))
                rotateDecompose = pmc.createNode('decomposeMatrix', name=self.name+'_jointOrientDecomp_' + str(index))
                self._utilityNodes['parentSpaceMult'+str(index)] = parentSpaceMult
                self._utilityNodes['jointOrientMult' + str(index)] = jointOrientMult
                self._utilityNodes['jointOrientCompose' + str(index)] = jointOrientCompose
                self._utilityNodes['transposeMatrix' + str(index)] = transposeMatrix
                self._utilityNodes['translateDecompose' + str(index)] = translateDecompose
                self._utilityNodes['rotateDecompose' + str(index)] = rotateDecompose

                # Connect the parentspace conversion mult matrix
                # This will bring the output into the targets space
                pmc.connectAttr(self._outputs[index].worldMatrix[0], parentSpaceMult.matrixIn[0])
                pmc.connectAttr(self._deformTargets[index].parentInverseMatrix[0], parentSpaceMult.matrixIn[1])

                # Connect the targets joint orient to the compose matrix's input
                # This will create a matrix from the joint orient
                pmc.connectAttr(self._deformTargets[index].jointOrient, jointOrientCompose.inputRotate)

                # Connect the Compose matrix to a transpose matrix, this will invert the joint orient
                pmc.connectAttr(jointOrientCompose.outputMatrix, transposeMatrix.inputMatrix)

                # Connect the transpose to the other multiply matrix node
                # This will compensate the parent space switch for the joint orient
                pmc.connectAttr(parentSpaceMult.matrixSum, jointOrientMult.matrixIn[0])
                pmc.connectAttr(transposeMatrix.outputMatrix, jointOrientMult.matrixIn[1])

                # Turn the joint orient matrix mult back into rotation values
                # Then connect it to the target
                pmc.connectAttr(jointOrientMult.matrixSum, rotateDecompose.inputMatrix)
                pmc.connectAttr(rotateDecompose.outputRotate, self._deformTargets[index].rotate)

                # Turn the parent space matrix into a translate and scale
                # Input those into the target
                pmc.connectAttr(parentSpaceMult.matrixSum, translateDecompose.inputMatrix)
                pmc.connectAttr(translateDecompose.outputTranslate, self._deformTargets[index].translate)
                pmc.connectAttr(translateDecompose.outputScale, self._deformTargets[index].scale)

            self._connectToOutput(self._mainControl, self._getStartIndex())


            self._bound = True

    def bakeDeforms(self, frame):
        # Key every deform target
        for joint in self._deformTargets:
            pmc.setKeyframe(joint, t=frame)

    #### public properties ####

    @property
    def startJoint (self):
        if not self._startJoint:
            self._startJoint = self._deformTargets[self._getStartIndex()]

        return self._startJoint

    @property
    def endJoint(self):
        if not self._endJoint:
            self._endJoint = self._deformTargets[self._getEndIndex()]

        return  self._endJoint

    @property
    def middleJoints(self):
        if not self._middleJoints:
            self._middleJoints = [self._deformTargets[index] for index in self._getMiddleIndexList()]

        return self._middleJoints

    @property
    def ready(self):
        # This property determines whether the component can be built
        # with its current values
        # A value of None is considered ready

        error = None

        if len(self._deformTargets) < 1:
            error = 'Requires at least one deform target.'

        return error

    @property
    def target(self):
        return self.startJoint

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
        arguments['target'] = str(self.target)
        arguments['deformTargets'] = [str(target) for target in self._deformTargets]
        arguments['controlTypes'] = self._mainControlType.curveType
        arguments['aimAxis'] = [axis for axis in self._aimAxis]
        arguments['parentSpace'] = getName(self.parentSpace)
        arguments['uprightSpace'] = getName(self.uprightSpace)
        arguments['type'] = self.__class__.__name__

        return arguments


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
                pmc.connectAttr(self.parentSpace.matrixOutput.parentInverseMatrix,
                                self._utilityNodes['point1SpaceSwitch'].matrixIn[1], force=True)
                pmc.connectAttr(self.parentSpace.matrixOutput.parentInverseMatrix,
                                self._utilityNodes['point2SpaceSwitch'].matrixIn[1], force=True)
                pmc.connectAttr(self.parentSpace.matrixOutput.inverseMatrix,
                                self._utilityNodes['point1SpaceSwitch'].matrixIn[2], force=True)
                pmc.connectAttr(self.parentSpace.matrixOutput.inverseMatrix,
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

        # Calculate the max distance
        maxDistance = self.startJoint.getTranslation('world').distanceTo(
            self._mainControl.getTranslation('world'))

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
        pmc.connectAttr(self.matrixOutput.worldMatrix[0], point2SpaceSwitch.matrixIn[0])

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
        JointComponent.build(self)

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

    def __init__(self, noFlipKnee=False, poleControlCurveType='triangle', **kwargs):
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

            # Create the ikHandle and effector
            self._handle, self._effector = pmc.ikHandle(sj=self._startJoint, ee=self.endJoint)

            # Parent the handle to the main control
            pmc.parent(self._handle, self._mainControl)

            # Rename the handle and effector
            pmc.rename(self._handle, self.name + '_handle')
            pmc.rename(self._effector, self.name + '_effector')

            # Add a twist attribute to the main control and connect it to the handles twist
            pmc.addAttr(self._mainControl, ln='twist', at='double', k=True)
            pmc.connectAttr(self._mainControl.twist, self._handle.twist)

            # If not a no flip knee, constrain the polevector
            if not self._noFlipKnee:
                self._constraints.append(pmc.poleVectorConstraint(self._poleControl, self._handle,
                                                                  name=self.name+'_poleVectorConstraint'))

            # Add the mainControl constraint
            self._constraints.append( pmc.parentConstraint(self._mainControl, self.endJoint, st=('x','y','z'),
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
            poleCurve = ControlCurve(curveType=self._poleControlCurveType).create()
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

        self._mainControl.setMatrix(targetM, worldSpace=True)

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


    ### Public Properties

    @property
    def ready(self):
        # This property determines whether the component can be built
        # with its current values
        # A value of None is considered ready

        error = None

        if len(self._deformTargets) < 3:
            error = 'Requires at least three deform targets'

        return error

    @property
    def target(self):
        return self.endJoint


class MultiFKComponent(FKComponent):
    '''
    Represents a series of FK Controls.
    '''
    def __init__(self, name='DefaultMultiFKComponent', mainControlType='default', mainControlScale=10.0,
                 childControlScale=10.0,
                 childControlControlType='default', deformTargets=[], rig=None,
                 spaceSwitchEnabled = False,
                 **kwargs):

        # Create a starting variable for the middle joints
        self._middleJoints = None


        # Init the base class (this will set up a ton of starting variables we need)
        FKComponent.__init__(self, mainControlType=mainControlType,
                             name=name,
                             mainControlScale=mainControlScale,
                             deformTargets=deformTargets,
                             spaceSwitchEnabled=spaceSwitchEnabled,
                             rig=rig,
                             **kwargs)

        # Create a child component for the startJoint
        self.startJointComponent = FKComponent(deformTargets=[self.startJoint],
                                                  name=self.name + '_subComponent_base',
                                                  mainControlType=childControlControlType,
                                                  mainControlScale=childControlScale,
                                                  spaceSwitchEnabled = spaceSwitchEnabled,
                                                  rig = self,
                                                  **kwargs)

        # Create a child component for each middle component
        self.middleJointComponents = []
        for index in range(len(self.middleJoints)):
            self.middleJointComponents.append(FKComponent(deformTargets=[self.middleJoints[index]],
                                                             name = self.name + '_subComponent_' + str(index),
                                                             mainControlType=childControlControlType,
                                                             mainControlScale=childControlScale,
                                                             spaceSwitchEnabled=False,
                                                             rig=self,
                                                             **kwargs))

        # Create a child component for the endJoint
        self.endJointComponent = FKComponent(deformTargets=[self.endJoint],
                                                name=self.name + '_subComponent_end',
                                                mainControlType=childControlControlType,
                                                mainControlScale=childControlScale,
                                                spaceSwitchEnabled=False,
                                                rig=self,
                                                **kwargs)

    #### public methods ####

    def build(self):
        if not self.active:

            # Create a component group to contain all component DAG nodes
            self.componentGroup = pmc.group(empty=True, name=self.name+'_com')

            # Build the start component, and set its parentSpace
            self.startJointComponent.parentSpace = self._parentSpace
            self.startJointComponent.uprightSpace = self._parentSpace
            self.startJointComponent.build()
            pmc.parent(self.startJointComponent.componentGroup, self.componentGroup)

            # Build the middle components
            for index in range(len(self.middleJointComponents)):
                com = self.middleJointComponents[index]

                if index == 0:
                    com.parentSpace = self.startJointComponent
                    com.uprightSpace = self.startJointComponent
                else:
                    com.parentSpace = self.middleJointComponents[index-1]
                    com.uprightSpace = self.middleJointComponents[index-1]

                com.build()
                pmc.parent(com.componentGroup, self.componentGroup)

            # Build the endComponent
            self.endJointComponent.parentSpace = self.middleJointComponents[len(self.middleJointComponents)-1]
            self.endJointComponent.uprightSpace = self.middleJointComponents[len(self.middleJointComponents)-1]
            self.endJointComponent.build()
            pmc.parent(self.endJointComponent.componentGroup, self.componentGroup)

            # Set the 'active' bool to True
            self._active = True

            return self.componentGroup

    def parent(self, components):
        # Set the parentSpace for each component
        self.startJointComponent.parent(components)

        for com in self.middleJointComponents:
            com.parent(components)

        self.endJointComponent.parent(components)

    def zero(self):
        # Zero each of the child components
        self.startJointComponent.zero()

        for com in self.middleJointComponents:
            com.zero()

        self.endJointComponent.zero()

    def bind(self):
        # Bind each of the child components
        self.startJointComponent.bind()

        for com in self.middleJointComponents:
            com.bind()

        self.endJointComponent.bind()

    def bakeDeforms(self, frame):
        pass

    def bake(self, frame):
        pass

    def unbind(self):
        pass

    def remove(self):
        pass

    def getComponent(self, component):
        # This replaces the function intended for a rig
        # Just return the component inputed
        return component

    #### public propeties ####

    @property
    def target(self):
        return self.startJoint

    @property
    def matrixOutput(self):
        return self.endJointComponent.matrixOutput

    @property
    def worldSpaceMatrix(self):
        return self.endJointComponent.worldSpaceMatrix


class SpineIKComponent(MultiFKComponent):
    '''
    A Modified series of FK components built to emulate the behavior
    of a spline IK setup
    '''

    def __init__(self, **kwargs):
        MultiFKComponent.__init__(self, **kwargs)


    #### Private Methods #####

    def _addChildParentSpace(self, childComponent, index):

        # This is an override to the traditional way of parenting components
        pass


    ##### Public Methods #####

    def build(self):
        if not self.active:

            # Create a component group to contain all component DAG nodes
            self.componentGroup = pmc.group(empty=True, name=self.name+'_com')

            # Build the start component, and set its parentSpace
            self.startJointComponent.parentSpace = self._parentSpace
            self.startJointComponent.uprightSpace = self._uprightSpace
            self.startJointComponent.build()
            pmc.parent(self.startJointComponent.componentGroup, self.componentGroup)

            # Build the endComponent
            self.endJointComponent.parentSpace = self._parentSpace
            self.endJointComponent.uprightSpace = self._uprightSpace
            self.endJointComponent.build()
            pmc.parent(self.endJointComponent.componentGroup, self.componentGroup)

            # Build the middle components
            for index in range(len(self.middleJointComponents)):
                # Build the component
                com = self.middleJointComponents[index]
                com.build()
                pmc.parent(com.componentGroup, self.componentGroup)

                # Create two empty objects, one for the start, and one for the end
                startLocator = pmc.group(empty=True, name=self.name + '_startLocator_' + str(index))
                endLocator = pmc.group(empty=True, name=self.name + '_endLocator_' + str(index))

                # Set the locators position, and parent them to the corresponding component
                startLocator.setMatrix(self.middleJoints[index].getMatrix(worldSpace=True), worldSpace=True)
                pmc.parent(startLocator, self.startJointComponent.matrixOutput)
                endLocator.setMatrix(self.middleJoints[index].getMatrix(worldSpace=True), worldSpace=True)
                pmc.parent(endLocator, self.endJointComponent.matrixOutput)

                # Create a decompose matrix for each locator, to extract the worldspacematrix
                startDecompose = pmc.createNode('decomposeMatrix', name=self.name + '_startlocatorDecomp_' + str(index))
                endDecompose = pmc.createNode('decomposeMatrix', name=self.name + '_endlocatorDecomp_' + str(index))
                self._utilityNodes['startDecompose_' + str(index)] = startDecompose
                self._utilityNodes['endDecompose_' + str(index)] = endDecompose

                # Connect the locators worldMatrix to their decompose matrix
                pmc.connectAttr(startLocator.worldMatrix[0], startDecompose.inputMatrix)
                pmc.connectAttr(endLocator.worldMatrix[0], endDecompose.inputMatrix)

                # Create a pair blend node and connect the outputs from the decomp nodes
                pairBlend = pmc.createNode('pairBlend', name=self.name+'_pairBlend+' + str(index))
                self._utilityNodes['pairBlend_' + str(index)] = pairBlend
                pmc.connectAttr(startDecompose.outputTranslate, pairBlend.inTranslate1)
                pmc.connectAttr(startDecompose.outputRotate, pairBlend.inRotate1)
                pmc.connectAttr(endDecompose.outputTranslate, pairBlend.inTranslate2)
                pmc.connectAttr(endDecompose.outputRotate, pairBlend.inRotate2)

                # Create an attribute for the blend, and set a default value to it
                pmc.addAttr(com.matrixOutput,
                            ln='startEndWeight', sn='sew', nn='State End Weight', type='double',
                            defaultValue=float(index+1)/float(len(self.middleJointComponents)+1),
                            hasMinValue=True, minValue=0.0,
                            hasMaxValue=True, maxValue=1.0,
                            k=True, hidden=False)
                pmc.connectAttr(com.matrixOutput.startEndWeight, pairBlend.weight)

                # Connect the output to the child component's local space buffer
                pmc.connectAttr(pairBlend.outTranslate, com.buffer.translate)
                pmc.connectAttr(pairBlend.outRotate, com.buffer.rotate)

                # Zero out the components localSpaceBuffer
                com.zero()

            # Set the 'active' bool to True
            self._active = True

            return self.componentGroup

    def parent(self, components):
        # Set the parentSpace for each component
        self.startJointComponent.parent(components)

        self.endJointComponent.parent(components)

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

    def createRig(self):

        # Grab the name from the path
        name = 'newRig'

        # Create a new set of component data
        componentData = {}

        # Create a rig and add it to the active rig list
        self._activeRigs[name] = Rig(name, componentData, None)

        return name

    def saveRigAs(self, directory, rigName):

        # Grab the name from the path
        name = os.path.basename(os.path.splitext(directory)[0])

        componentData = self._activeRigs[rigName].componentData

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

    def isReady(self, rigName):
        # Checks if the current rig can be built

        if self._activeRigs[rigName].ready is None:
            return None
        else:
            return self._activeRigs[rigName].ready

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

