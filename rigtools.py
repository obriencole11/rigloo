import pymel.core as pmc
import pymel.core.datatypes as dt
import controltools
import os
import json
import uuid
import math
import maya.utils

##############################
#       Rig Settings         #
##############################

COMPONENT_TYPES = {
    'BasicComponent': {
        'name': 'defaultComponent',
        'type': 'BasicComponent',
        'mainControlType': 'default',
        'mainControlScale': 10.0,
        'target': None,
        'parentSpace': None,
        'uprightSpace': None,
        'icon': ":/holder.svg",
        'enabled': True,
        'spaceSwitchEnabled': False
    },
    'ScaleComponent': {
            'name': 'defaultScaleComponent',
            'type': 'ScaleComponent',
            'mainControlType': 'default',
            'mainControlScale': 10.0,
            'target': None,
            'parentSpace': None,
            'uprightSpace': None,
            'icon': ":/holder.svg",
            'enabled': True,
            'spaceSwitchEnabled': False
        },
    'FKComponent': {
        'name': 'defaultFKComponent',
        'type': 'FKComponent',
        'mainControlType': 'default',
        'mainControlScale': 10.0,
        'target': None,
        'parentSpace': None,
        'uprightSpace': None,
        'icon': ":/HIKCharacterToolFK.png",
        'enabled': True,
        'spaceSwitchEnabled': False,
        'isLeafJoint': False
    },
    'AimComponent': {
        'name': 'defaultAimComponent',
        'type': 'AimComponent',
        'mainControlType': 'default',
        'mainControlScale': 10.0,
        'target': None,
        'parentSpace': None,
        'uprightSpace': None,
        'icon': ":/HIKCharacterToolFK.png",
        'enabled': True,
        'spaceSwitchEnabled': False,
        'isLeafJoint': False,
        'aimControlType': 'default',
        'aimVector': [1,0,0],
        'aimCurveDistance': 50.0
    },
    'IKComponent': {
        'name': 'defaultIKComponent',
        'type': 'IKComponent',
        'mainControlType': 'cube',
        'mainControlScale': 10.0,
        'deformTargets': [],
        'parentSpace': None,
        'uprightSpace': None,
        'stretchEnabled': False,
        'squashEnabled': False,
        'icon': ":/ikHandle.svg",
        'noFlipKnee': False,
        'poleControlCurveType': 'triangle',
        'enabled': True,
        'spaceSwitchEnabled': False,
        'isLeafJoint': False,
        'fkOffsetCurveType': 'sphere'
    },
    'LegIKComponent': {
            'name': 'defaultLegIKComponent',
            'type': 'LegIKComponent',
            'mainControlType': 'cube',
            'mainControlScale': 10.0,
            'deformTargets': [],
            'parentSpace': None,
            'uprightSpace': None,
            'stretchEnabled': False,
            'squashEnabled': False,
            'icon': ":/ikHandle.svg",
            'noFlipKnee': False,
            'poleControlCurveType': 'triangle',
            'enabled': True,
            'spaceSwitchEnabled': False,
            'isLeafJoint': False,
            'fkOffsetCurveType': 'sphere'
        },
    'MultiFKComponent': {
            'name': 'defaultMultiFKComponent',
            'type': 'MultiFKComponent',
            'mainControlType': 'default',
            'mainControlScale': 10.0,
            'deformTargets': [],
            'parentSpace': None,
            'uprightSpace': None,
            'stretchEnabled': False,
            'squashEnabled': False,
            'icon': ":/ikRPsolver.svg",
            'enabled': True,
            'spaceSwitchEnabled': False,
            'isLeafJoint': False
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
            'icon': ":/HIKCharacterToolSkeleton_100",
            'enabled': True,
            'spaceSwitchEnabled': False,
            'isLeafJoint': False
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

class safeCreate(object):

    def __init__(self, rig):
        self._rig = rig

    def __enter__(self):
        pmc.undoInfo(openChunk=True)

    def __exit__(self, exc_type, exc_val, exc_tb):
        pmc.undoInfo(closeChunk=True)
        if exc_val is not None:
            pmc.undo()

##############################
#     Settings Classes       #
##############################

class ControlCurve():
    def __init__(self, curveType='default', scale=1.0, color=dt.Color.blue):
        self.curveType = curveType
        self.scale = scale
        self.color = color

    def create(self, name='default', upVector=[1,0,0]):

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

class Space(object):
    '''
    A class that components can be parented to.
    This allows for components to be parented to locators and joints.
    '''

    def __init__(self, transform):
        self._transform = transform

    @property
    def worldSpaceMatrix(self):
        # This is the worldspace matrix value
        return self._transform.getMatrix(worldSpace=True)

    @property
    def matrixOutput(self):
        # This is the output connection for parent space connections
        return self._transform


class BasicComponent(object):
    '''
    The base class of all components.
    Bakes to a position, but does not deform the target (this binding does nothing)
    Has a parentspace, so can be parented and parented to other spaces.
    '''

    defaultControl = ControlCurve()

    def __init__(self, name='default', target=None, mainControlType='circle', parentSpace=None, uprightSpace=None,
                 mainControlColor=dt.Color.blue, mainControlScale=10.0, spaceSwitchEnabled=False, utilityNodes=None, **kwargs):

        # Set the standard variables
        self._name = name
        self._utilityNodes = {}
        self._active = False
        self._bound = False
        self._constraints = []
        self._mainControl = None
        self._mainControlScale = mainControlScale
        self._mainControlColor = mainControlColor
        self.spaceSwitchEnabled = spaceSwitchEnabled
        self._orientToTarget = False
        self._orientOffset = None

        # These will be overriden when parent() is called
        # But we want them to have a value to determine if its none or not
        self._parentSpace = parentSpace
        self._uprightSpace = uprightSpace

        # Target is just a name, so grab the actual pynode for it, if it exists
        if target is not None:
            self._target = pmc.PyNode(target)
        else:
            self._target = None

        # Create a control curve instance based on the input settings
        self._mainControlType = ControlCurve(curveType=mainControlType,
                                             scale=mainControlScale,
                                             color=mainControlColor)

        # Grab references to any existing utility nodes
        if utilityNodes:
            self._utilityNodes = {name: pmc.PyNode(node) for name, node in utilityNodes}

    #### Public Methods ####

    def build(self):
        '''
        This builds the base framework for the component.
        Doesn't make any connections, but sets them up.
        '''

        if not self.active:

            # Create a component group to contain all component DAG nodes
            self._componentGroup = pmc.group(empty=True, name=self.name+'_com')

            # Create the main control curve
            self._createMainControl()

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
            pmc.parent(self.parentSpaceBuffer, self._componentGroup)

            # Set the 'active' bool to True
            self._active = True

            return self._componentGroup

    def parent(self, components, parentComponent, uprightComponent):
        '''
        This sets up the parent connections.
        This is called separately from build so baking doesn't mess with parentSpace.
        Also so all components exist before parenting.
        :param components: A list of active components
        '''

        # Grab a reference to the parentSpace and upright Space components
        # This is because parentspace and uprightspace are just the id of the component
        self._parentSpace = parentComponent
        self._uprightSpace = uprightComponent

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
            if parentComponent is None:
                startParentIndex = 0
            else:
                startParentIndex = names.index(parentComponent.name)
            if uprightComponent is None:
                startUprightIndex = 0
            else:
                startUprightIndex = names.index(uprightComponent.name)

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
                pmc.setAttr(multMatrix.matrixIn[1], parentComponent.worldSpaceMatrix.inverse())
                pmc.connectAttr(parentComponent.matrixOutput.worldMatrix[0], multMatrix.matrixIn[2])
            except AttributeError:
                pmc.setAttr(multMatrix.matrixIn[1], identityMatrix)
            pmc.connectAttr(multMatrix.matrixSum, parentSpaceChoiceNode.input[0])

            # ...and the uprightSpace
            multMatrix = pmc.createNode('multMatrix', name=self.name + '_uprightMult')
            self._utilityNodes['uprightSpaceMult'] = multMatrix
            pmc.setAttr(multMatrix.matrixIn[0], self.worldSpaceMatrix)
            try:
                pmc.setAttr(multMatrix.matrixIn[1], uprightComponent.worldSpaceMatrix.inverse())
                pmc.connectAttr(uprightComponent.matrixOutput.worldMatrix[0], multMatrix.matrixIn[2])
            except AttributeError:
                pmc.setAttr(multMatrix.matrixIn[1], identityMatrix)
            pmc.connectAttr(multMatrix.matrixSum, uprightSpaceChoiceNode.input[0])


        # Connect the output of the choices to their corresponding multMatrix
        pmc.connectAttr(parentSpaceChoiceNode.output, self._utilityNodes['parentMultMatrixNode'].matrixIn[0])
        pmc.connectAttr(uprightSpaceChoiceNode.output, self._utilityNodes['uprightMultMatrixNode'].matrixIn[0])

        # Set the position of the localSpace
        self.localSpaceBuffer.setMatrix(identityMatrix, objectSpace=True)

    def zero(self):
        '''
        Sets the localSpaceBuffers position based on the target.
        If there is no target, set it to the identity matrix
        '''

        try:
            self.localSpaceBuffer.setMatrix(self.target.getMatrix(worldSpace=True), worldSpace=True)
        except AttributeError:
            self.localSpaceBuffer.setMatrix(dt.Matrix(), worldSpace=True)

    def snap(self):
        '''
        Snap controls to the position of the target
        '''

        try:
            targetM = self.target.getMatrix(worldSpace=True)
        except AttributeError:
            targetM = dt.Matrix()

        self._mainControl.setMatrix(targetM, worldSpace=True)

    def bake(self, frame):
        '''
        Sets a keyframe for the main control.
        '''

        pmc.setKeyframe(self._mainControl, t=frame)

    def bind(self):
        # Not really implemented for the base Component
        self._bound = True

    def unbind(self):

        if self._bound:

            # Mark this component as inactive
            self.bound = False

    def remove(self):
        '''
        Cleans up leftover components and deletes the component
        '''

        if self._bound:
            self.unbind()

        if self._active:

            # Delete the component group
            pmc.delete(self._componentGroup)

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

    def _createMainControl(self):
        self._mainControl = self._mainControlType.create(upVector=[0,1,0], name=self.name+'_main')


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
        arguments['utilityNodes'] = {name: node.name() for name, node in self._utilityNodes.iteritems()}

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
        return self._parentSpace

    @property
    def uprightSpace(self):
        return self._uprightSpace

    @property
    def matrixOutput(self):
        # This is the output connection for parent space connections
        return self._mainControl

    @property
    def componentGroup(self):
        return self._componentGroup

    @property
    def buffer(self):
        return self.localSpaceBuffer

    @property
    def worldSpaceMatrix(self):
        # This is the worldspace matrix value
        return self._mainControl.getMatrix(worldSpace=True)

    @property
    def targets(self):
        # Returns a list of all targets this component effects
        return None

    @property
    def ready(self):

        return None

    @property
    def target(self):
        return self._target

class Rig(object):
    '''
    An object for building components from a set of component data.
    '''

    def __init__(self, name, componentData, directory, built=False, bound=False, baked=False, rigGroup=None):

        # Assign a name, this is mostly for display purposes
        self._name = name

        # Assign the save location for the rig
        self._directory = directory

        # Assign a key to access data
        self._componentData = componentData

        # Create a dictionary to hold all active components
        self._components = {}

        # Some simple state bools
        self._bound = bound
        self._built = built
        self._baked = baked

        # If this rig has been built, grab its riggroup
        if rigGroup:
            self.rigGroup = pmc.PyNode(rigGroup)

        # If built, fill the active component list
        if self._built:
            # For each component in the component data...
            for id, com in self._componentData.iteritems():
                # Check if component is set to 'enabled'
                if com['enabled']:
                    # Create an instance of the component's class
                    component = self._createComponent(componentType=com['type'], **com)

                    # Add the component to this rigs active component dictionary
                    self._components[id] = component

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

            try:
                parent = self._components[self._componentData[id]['parentSpace']]
            except KeyError:
                parent = None

            try:
                upright = self._components[self._componentData[id]['uprightSpace']]
            except KeyError:
                upright = None

            com.parent(self._components, parent, upright)

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

    def bake(self, frameRange=10):

        if not self._built:
            self.build()

        # Create a list to store sorted components
        sortedComponents = []

        # Create a recursive method that adds a components parent before the component
        def addCom(id):
            if id not in sortedComponents:
                if self._components[id].parentSpace is not None:
                    if self._components[id].parentSpace not in sortedComponents:
                        addCom(self._components[id].parentSpace)

                if self._components[id].uprightSpace is not None:
                    if self._components[id].uprightSpace not in sortedComponents:
                        addCom(self._components[id].uprightSpace)

                sortedComponents.append(id)
            else:
                pass

        # Iterate through the list, sort so that parents are always before children
        for id, com in self._components.iteritems():
            addCom(id)

        # Goes through every frame, snaps the controls and keys their position
        for frame in range(frameRange):
            pmc.setCurrentTime(frame)
            for id in sortedComponents:
                com = self._components[id]
                com.snap()
                com.bake(frame)
        pmc.setCurrentTime(1)

        self._baked = True

    def bakeDeforms(self, frameRange=10):

        targetList = []

        for id, com in self._components.iteritems():
            targetList += com.targets

        pmc.bakeSimulation(targetList, t=(0,frameRange), hi='none')

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
                try:
                    com.remove()
                except:
                    pass

            # Then delete the rig group
            pmc.delete(self.rigGroup)

            # And reset the value of rigGroup
            self.rigGroup = None

            # And finally, clear out the dictionary of active components
            self._components.clear()

            self._built = False
            self._baked = False

    def addComponent(self, **kwargs):

        # Create the id of the new component
        id = uuid.uuid4().hex

        # Create a unique name for the component
        uniqueName = 'newComponent' + str(len(self._componentData)+1)

        # Add the component data to the data dictionary
        self._componentData[id] = kwargs

        # Set the id of the component
        self._componentData[id]['id'] = id

        # Set the name of the component
        self._componentData[id]['name'] = uniqueName

        # Set the index of the component
        self._componentData[id]['index'] = len(self._componentData) + 1

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

        component = componentType(**kwargs)

        return component

    #### Public Properties ####

    @property
    def componentData(self):
        return self._componentData

    @property
    def data(self):
        ''' Return data that can be used to recreate this rig '''

        try:
            rigGroup = self.rigGroup.name()
        except AttributeError:
            rigGroup = None

        rigData = {
            'name': self._name,
            'directory': self._directory,
            'componentData': self._componentData,
            'built': self._built,
            'bound': self._bound,
            'baked': self._baked,
            'rigGroup': rigGroup
        }

        return rigData

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

class FKComponent(BasicComponent):
    '''
    Represents a component that deforms a joint target.
    Also includes some squash and stretch functionality, but cannot use on its own.
    '''

    def __init__(self, stretchTarget=None, stretchEnabled=False, squashEnabled=False,
                 isLeafJoint=False, aimAtChild=True, **kwargs):
        BasicComponent.__init__(self, **kwargs)

        # Establish the direction to be used when orienting
        self._aimAxis = dt.Vector(1,0,0)
        self._inverseAxis = dt.Vector(-1,0,0)

        # Add references to the output parts
        self._output = None
        self._outputOrient = None
        self._outputBuffer = None

        # Grab the squash and stretch values
        self._stretchTarget = stretchTarget
        self._stretchEnabled = stretchEnabled
        self._squashEnabled = squashEnabled
        self._stretchScale = 2.0
        self._stretchMin = 0.0
        self._isLeafJoint = isLeafJoint
        self._aimAtChild = aimAtChild

    #### private methods ####

    def _orientBuffer(self):
        '''
        Orient the orientBuffer towards its parent
        :return: 
        '''

        # Grab a list of all the targets children
        children = self.target.getChildren()

        # If we're using leaf joints, make sure to remove the leaf joint
        if self._isLeafJoint:
            children.remove(self._target)

        # If theres just one real child, aim at that
        if len(children) == 1:
            constraint = pmc.aimConstraint(children[0],
                                           self._outputOrient,
                                           aimVector=self._aimAxis, mo=False)
        # Otherwise aim at the parent
        else:
            constraint = pmc.aimConstraint(self.target.getParent(),
                                           self._outputOrient,
                                           aimVector=self._inverseAxis, mo=False)


        pmc.delete(constraint)

    def _connectToOutput(self, input):

        # Grab the current location of the orient
        orientPos = self._outputOrient.getMatrix(worldSpace=True)

        # Create a decompose matrix to convert the inputs world location to srt values
        decompMatrix = pmc.createNode('decomposeMatrix', name='outputConnectionDecomp')
        self._utilityNodes['outputConnectionDecomp'] = decompMatrix
        pmc.connectAttr(input.worldMatrix[0], decompMatrix.inputMatrix)

        # Connect the output to the output buffer
        pmc.connectAttr(decompMatrix.outputTranslate, self._outputBuffer.translate)
        pmc.connectAttr(decompMatrix.outputRotate, self._outputBuffer.rotate)

        # Move the orient back to its original world position
        self._outputOrient.setMatrix(orientPos, worldSpace=True)

    def _createMainControl(self):
        '''
        Creates the main control, except orients based on the outputOrient, rather than the 
        actual target joint
        '''

        # Create the main control curve
        self._mainControl = self._mainControlType.create(upVector=[1,0,0], name=self.name+'_main')

        # Grab the orientation of the target
        jointRotation = self.target.getRotation(space='world', quaternion=True)

        # Grab the orientation of the aimed buffer
        aimRotation = self._outputOrient.getRotation(space='world', quaternion=True)

        # Calculate the difference between the two orientationse
        difference = aimRotation * jointRotation.invertIt()

        # Rotate the control by that difference then freeze the rotation
        self._mainControl.rotateBy(difference)
        pmc.makeIdentity(self._mainControl, apply=True, rotate=True, translate=False, scale=False, jointOrient=False)

        # Create a control output group, this will allow for offset transformations from the control (such as aiming)
        self._mainControlOutput = pmc.group(empty=True)
        self._mainControlOutput.setMatrix(self._mainControl.getMatrix(worldSpace=True), worldSpace=True)
        pmc.parent(self._mainControlOutput, self._mainControl)

    def _buildSquashAndStretch(self):

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

        # Grab the two points we will base distance on
        point1 = self._stretchTarget.matrixOutput
        point2 = self.matrixOutput

        # Add utility nodes we care about into the utility nodes dictionary
        self._utilityNodes['point1SpaceSwitch'] = point1SpaceSwitch
        self._utilityNodes['point2SpaceSwitch'] = point2SpaceSwitch
        self._utilityNodes['outMax'] = outputMax
        self._utilityNodes['inverseOutput'] = inverseOutput

        # Calculate the max distance
        maxDistance = point1.getTranslation('world').distanceTo(point2.getTranslation('world'))

        # Convert the startJoints local translation to a matrix
        pmc.connectAttr(point1.translate, startJointTranslateMatrix.inputTranslate)

        # Convert the startJoints local translation matrix to worldspace
        # By multiplying it by the startJoints parent Matrix
        # We do this to avoid creating an infinite node cycle
        pmc.connectAttr(startJointTranslateMatrix.outputMatrix, startJointTranslateWorldMatrix.matrixIn[0])
        pmc.connectAttr(point1.parentMatrix[0], startJointTranslateWorldMatrix.matrixIn[1])

        # Connect the worldTranslateMatrix of the startJoint and the worldMatrix of the mainControl
        # to a space switcher. This will compensate for the global rig scaling
        pmc.connectAttr(startJointTranslateWorldMatrix.matrixSum, point1SpaceSwitch.matrixIn[0])
        pmc.connectAttr(point2.worldMatrix[0], point2SpaceSwitch.matrixIn[0])

        # Connect the matrix sums to distance node
        pmc.connectAttr(point1SpaceSwitch.matrixSum, distanceBetween.inMatrix1)
        pmc.connectAttr(point2SpaceSwitch.matrixSum, distanceBetween.inMatrix2)

        # Connect distance and max distance to division node
        pmc.connectAttr(distanceBetween.distance, maxDistanceDiv.floatA)
        pmc.setAttr(maxDistanceDiv.floatB, maxDistance * 2)

        # Connect normalized distance to multiply node
        pmc.connectAttr(maxDistanceDiv.outFloat, scaleMult.floatA)
        pmc.addAttr(self._mainControl, ln='squashAndStretchScale', sn='sass', nn='Squash and Stretch Scale',
                    hasMinValue=True, minValue=self._stretchMin, hidden=False, keyable=True)
        pmc.setAttr(self._mainControl.squashAndStretchScale, self._stretchScale)
        pmc.connectAttr(self._mainControl.squashAndStretchScale, scaleMult.floatB)

        # Connect scaled output to the max node
        pmc.setAttr(outputMax.floatB, self._stretchMin)
        pmc.connectAttr(scaleMult.outFloat, outputMax.floatA)

        # Connect maxed output to the inverse node
        pmc.setAttr(inverseOutput.floatA, 1.0)
        pmc.connectAttr(outputMax.outFloat, inverseOutput.floatB)

        # Connect to the parent space
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

        # Connect to stretch joint scales
        if self.stretchEnabled:
            pmc.connectAttr(self._utilityNodes['outMax'].outFloat, self._stretchTarget.stretchInput.scaleX, force=True)
        if self.squashEnabled:
            pmc.connectAttr(self._utilityNodes['inverseOutput'].outFloat, self._stretchTarget.stretchInput.scaleY, force=True)
            pmc.connectAttr(self._utilityNodes['inverseOutput'].outFloat, self._stretchTarget.stretchInput.scaleZ, force=True)

    #### public methods ####

    def build(self):
        '''
        Builds the base component and additionally adds the output groups
        '''

        # Create an orient buffer for the joint
        buffer = pmc.group(empty=True, name=self.name + '_orientBuffer')
        self._outputOrient = buffer
        buffer.setMatrix(self.target.getMatrix(worldSpace=True), worldSpace=True)

        # Orient the buffer towards the next target
        self._orientBuffer()

        # Create the base component, this sets up a lot of standard parts
        BasicComponent.build(self)

        # Create a group to house outputs
        self.outputGroup = pmc.group(empty=True, name='output')
        pmc.parent(self.outputGroup, self._componentGroup)

        # Create a joint duplicate at the same location
        joint = pmc.duplicate(self.target, po=True, name=self.name + '_outputJoint')[0]
        pmc.parent(joint, world=True)

        # Store a reference to it
        self._output = joint

        # Then parent it to the output group
        pmc.parent(self._outputOrient, self.outputGroup)

        # Parent the output to it
        pmc.parent(self._output, self._outputOrient)

        # Create a srt buffer
        srtBuffer = pmc.group(empty=True, name=self.name + '_output_srtBuffer')
        pmc.parent(buffer, srtBuffer)
        self._outputBuffer = srtBuffer
        pmc.parent(srtBuffer, self.outputGroup)

        # Connect the main control to the buffer
        self._connectToOutput(self._mainControlOutput)

        return self._componentGroup

    def bind(self):
        '''
        Binds the output joint to the target joint.
        '''

        if not self._bound:

            # Clear all keyframes on the target
            timeSliderEnd = int(pmc.playbackOptions(query=True, aet=True))
            pmc.cutKey(self.target, time=(0,timeSliderEnd))


            # Create all the nodes needed
            parentSpaceMult = pmc.createNode('multMatrix', name=self.name+'_parentSpaceMult')
            jointOrientMult = pmc.createNode('multMatrix', name=self.name+'_jointOrientMult')
            jointOrientCompose = pmc.createNode('composeMatrix', name=self.name+'_jointOrientCompose')
            transposeMatrix = pmc.createNode('transposeMatrix', name=self.name+'_jointOrientInverseMult')
            translateDecompose = pmc.createNode('decomposeMatrix', name=self.name+'_parentSpaceDecomp')
            rotateDecompose = pmc.createNode('decomposeMatrix', name=self.name+'_jointOrientDecomp')
            scaleDecompose = pmc.createNode('decomposeMatrix', name=self.name+'_scaleDecomp')
            self._utilityNodes[self.name+'parentSpaceMult'] = parentSpaceMult
            self._utilityNodes[self.name+'jointOrientMult'] = jointOrientMult
            self._utilityNodes[self.name+'jointOrientCompose'] = jointOrientCompose
            self._utilityNodes[self.name+'transposeMatrix'] = transposeMatrix
            self._utilityNodes[self.name+'translateDecompose'] = translateDecompose
            self._utilityNodes[self.name+'rotateDecompose'] = rotateDecompose
            self._utilityNodes[self.name+'scaleCompose'] = scaleDecompose

            # Connect the parentspace conversion mult matrix
            # This will bring the output into the targets space
            pmc.connectAttr(self._output.worldMatrix[0], parentSpaceMult.matrixIn[0])

            pmc.connectAttr(self.target.parentInverseMatrix[0], parentSpaceMult.matrixIn[1])

            # Connect the targets joint orient to the compose matrix's input
            # This will create a matrix from the joint orient
            pmc.connectAttr(self.target.jointOrient, jointOrientCompose.inputRotate)

            # Connect the Compose matrix to a transpose matrix, this will invert the joint orient
            pmc.connectAttr(jointOrientCompose.outputMatrix, transposeMatrix.inputMatrix)

            # Connect the transpose to the other multiply matrix node
            # This will compensate the parent space switch for the joint orient
            pmc.connectAttr(parentSpaceMult.matrixSum, jointOrientMult.matrixIn[0])
            pmc.connectAttr(transposeMatrix.outputMatrix, jointOrientMult.matrixIn[1])

            # Turn the joint orient matrix mult back into rotation values
            # Then connect it to the target
            pmc.connectAttr(jointOrientMult.matrixSum, rotateDecompose.inputMatrix)
            pmc.connectAttr(rotateDecompose.outputRotate, self.target.rotate, force=True)

            # Connect the outputs worldmatrix to the scale decompose
            # This will get us the raw scale
            pmc.connectAttr(self._output.worldMatrix[0], scaleDecompose.inputMatrix)

            # Turn the parent space matrix into a translate and scale
            # Input those into the target
            pmc.connectAttr(parentSpaceMult.matrixSum, translateDecompose.inputMatrix, force=True)
            pmc.connectAttr(translateDecompose.outputTranslate, self.target.translate, force=True)

            # Remember, scale is special, it operates on _target not target
            # (this is different if leaf joint is checked)
            pmc.connectAttr(scaleDecompose.outputScale, self._target.scale, force=True)

            # If the component has a stretch target, set up squash and stretch
            if self._stretchTarget is not None:

                if self._aimAtChild:
                    pmc.aimConstraint(self._mainControlOutput, self._stretchTarget._mainControlOutput,
                                  wut='none', mo=True)

                self._buildSquashAndStretch()

            self._bound = True

    def unbind(self):
        if self._bound:

            # Disconnect the target
            pmc.disconnectAttr(self.target.rotate)
            pmc.disconnectAttr(self.target.translate)
            pmc.disconnectAttr(self.target.scale)

            # Delete all bind related utility nodes
            pmc.delete(self._utilityNodes[self.name+'translateDecompose'])
            pmc.delete(self._utilityNodes[self.name+'rotateDecompose'])

            self._bound = False

    def zero(self):
        '''
        Sets the localSpaceBuffers position based on the target.
        '''

        self.localSpaceBuffer.setMatrix(self.target.getMatrix(worldSpace=True), worldSpace=True)

    #### public properties ####

    @property
    def target(self):
        if self._isLeafJoint:
            return self._target.getParent()
        else:
            return self._target

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
        arguments['utilityNodes'] = {name: node.name() for name, node in self._utilityNodes.iteritems()}

        return arguments

    @property
    def targets(self):
        # Returns a list of all targets this component effects
        return [self._target]

    @property
    def stretchEnabled(self):
        return self._stretchEnabled

    @property
    def orientBuffer(self):
        return self._outputBuffer

    @property
    def squashEnabled(self):
        return self._squashEnabled

    @property
    def squashAndStretchEnabled(self):
        return self._squashEnabled, self._stretchEnabled

    @property
    def stretchTarget(self):
        return self._stretchTarget

    @property
    def stretchInput(self):
        return self._outputOrient

    @property
    def ready(self):
        error = None

        if self.target is None:
            error = 'Needs at least one target'

        return error

class MultiFKComponent(FKComponent):
    '''
    Represents a series of Controls.
    This is a very powerful node to inherit from, basically any complex component will do so.
    Basically this is a 'fake' component, its really just outputing all commands to its child components.
    '''

    def __init__(self, deformTargets=[], **kwargs):

        # Init the base class (this will set up a ton of starting variables we need)
        FKComponent.__init__(self, **kwargs)

        # Grab a reference to all input deform targets
        self._deformTargets = [pmc.PyNode(target) for target in deformTargets]

        # Sort the deform targets by hierarchy
        self._sortTargets()

        # Generate the sub components:
        self._generateChildComponents()

    ##### Private Methods #####

    def _generateChildComponents(self):

        # Create a list to hold all child components
        self._childComponents = []

        # Create a child component for the base component (This will be the base parent)
        # This is also the only component without squash and stretch control
        self._childComponents.append(FKComponent(name=self.name + str(1),
                                               target=self._deformTargets[self.startIndex],
                                               spaceSwitchEnabled=self.spaceSwitchEnabled,
                                               stretchTarget=None,
                                               stretchEnabled=False,
                                               squashEnabled=False,
                                               mainControlType=self._mainControlType.curveType,
                                               mainControlScale=self._mainControlScale,
                                               mainControlColor=self._mainControlColor,
                                               isLeafJoint=self._isLeafJoint
                                               ))

        # Create a child component for each middle component
        # For parent space we just use the index of the parent component in our child component list
        for index in self.middleIndex:
            self._childComponents.append(FKComponent(name=self.name + str(index+1),
                                                     target=self._deformTargets[index],
                                                     spaceSwitchEnabled=False,
                                                     stretchTarget = self._childComponents[index - 1],
                                                     stretchEnabled=self._squashEnabled,
                                                     squashEnabled=self._stretchEnabled,
                                                     mainControlType=self._mainControlType.curveType,
                                                     mainControlScale=self._mainControlScale,
                                                     mainControlColor=self._mainControlColor,
                                                    isLeafJoint=self._isLeafJoint
                                                     ))

        # Create a child component for the endJoint
        self._childComponents.append(FKComponent(name=self.name + str(self.endIndex+1),
                                                 target=self._deformTargets[self.endIndex],
                                                 spaceSwitchEnabled=False,
                                                 stretchTarget=self._childComponents[self.endIndex-1],
                                                 stretchEnabled=self._squashEnabled,
                                                 squashEnabled=self._stretchEnabled,
                                                 mainControlType=self._mainControlType.curveType,
                                                 mainControlScale=self._mainControlScale,
                                                 mainControlColor=self._mainControlColor,
                                                 isLeafJoint=self._isLeafJoint
                                                 ))

    def _sortTargets(self):

        # Create a list to hold the sorted deform targets
        sortedTargets = []

        # Add each deform target to the list, children placed after their parents
        for target in self._deformTargets:
            for index in range(len(sortedTargets)):
                if self._isLeafJoint:
                    target1 = target.getParent()
                    target2 = sortedTargets[index].getParent()
                else:
                    target1 = target
                    target2 = sortedTargets[index]

                if len(target2.listRelatives(ad=True, type='joint')) > len(target1.listRelatives(ad=True, type='joint')):
                    pass
                else:
                    sortedTargets.insert(index, target)
                    break

            if target not in sortedTargets:
                sortedTargets.append(target)

        # Update the deform target list
        self._deformTargets = sortedTargets

    #### public methods ####

    def build(self):
        if not self.active:

            # Create a component group to contain all component DAG nodes
            self._componentGroup = pmc.group(empty=True, name=self.name+'_com')

            # Build the child components and parent them to the componentGroup
            for child in self._childComponents:
                child.build()
                pmc.parent(child.componentGroup, self._componentGroup)

            # Set the 'active' bool to True
            self._active = True

            return self._componentGroup

    def parent(self, components, parentComponent, uprightComponent):

        for index in range(len(self._childComponents)):

            if index == 0:
                self._childComponents[index].parent(components, parentComponent, uprightComponent)
            else:
                previousParent = self._childComponents[index - 1]
                self._childComponents[index].parent(self._childComponents, previousParent, previousParent)

    def zero(self):
        # Zero each of the child components
        for child in self._childComponents:
            child.zero()

    def bind(self):

        # Bind each of the child components
        for child in self._childComponents:
            child.bind()

        self.bound = True

    def snap(self):
        for child in self._childComponents:
            child.snap()

    def bake(self, frame):
        for child in self._childComponents:
            child.bake(frame)

    def unbind(self):

        if self._bound:
            for child in self._childComponents:
                child.unbind()

            self._bound = False

    def remove(self):

        # Make sure the component is unbound
        if self._bound:
            self.unbind()

        # Remove all children
        for child in self._childComponents:
            child.remove()

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

    #### public propeties ####

    @property
    def targets(self):
        return self._deformTargets

    @property
    def matrixOutput(self):
        return self._childComponents[self.startIndex].matrixOutput

    @property
    def worldSpaceMatrix(self):
        return self._childComponents[self.startIndex].worldSpaceMatrix

    @property
    def startIndex (self):
        return 0

    @property
    def endIndex(self):
        return len(self._deformTargets)-1

    @property
    def middleIndex(self):
        return [index for index in range(len(self._deformTargets))
                if index is not 0 and index is not len(self._deformTargets) - 1]

    @property
    def ready(self):
        error = None

        if self._deformTargets < 2:
            error = 'Needs at least 2 deform targets'

        return error

class IKComponent(MultiFKComponent):
    '''
    A multiFK Component in which all controls are parented to an ik chain.
    '''

    def __init__(self, noFlipKnee=False, poleControlCurveType='triangle', fkOffsetCurveType='sphere', **kwargs):

        # Store the IK variables
        self._noFlipKnee = noFlipKnee
        self._fkOffsetCurveType = fkOffsetCurveType

        # Create the multifk components
        MultiFKComponent.__init__(self, **kwargs)

        # Create the control curve instance for the pole vector
        self._poleControlCurveType = ControlCurve(curveType=poleControlCurveType,
                                                  color=self._mainControlColor,
                                                  scale=5.0)

        # Create a component for the ik handle
        self.ikComponent = BasicComponent(name=self.name + '_IKControl',
                                                 target=self._deformTargets[self.endIndex],
                                                 spaceSwitchEnabled= True,
                                                 mainControlType=self._mainControlType.curveType,
                                                 mainControlScale=self._mainControlScale,
                                                 mainControlColor=self._mainControlColor)

        # Create a component for the base controller
        self.baseComponent = BasicComponent(name=self.name + '_IKControl',
                                                 target=self._deformTargets[self.startIndex],
                                                 spaceSwitchEnabled= True,
                                                 mainControlType=self._mainControlType.curveType,
                                                 mainControlScale=self._mainControlScale,
                                                 mainControlColor=self._mainControlColor)

    #### public methods ####

    def build(self):
        if not self.active:

            # Create a component group to contain all component DAG nodes
            self._componentGroup = pmc.group(empty=True, name=self.name+'_com')

            # Create the main IK control
            self.ikComponent.build()
            pmc.parent(self.ikComponent.componentGroup, self._componentGroup)

            # Create the base control
            self.baseComponent.build()
            pmc.parent(self.baseComponent.componentGroup, self._componentGroup)

            # If not using a no flip knee setup, create the pole control
            if not self._noFlipKnee:
                self._poleControl = self._poleControlCurveType.create(upVector=[0,1,0], name=self.name+'_main')
                pmc.parent(self._poleControl, self.baseComponent.matrixOutput)
                self._poleControl.setTranslation(self._getPolePoint(), worldSpace=True)

            # Build the child components and parent them to the componentGroup
            for child in self._childComponents:
                child.build()
                pmc.parent(child.componentGroup, self._componentGroup)

            # Create the ik chain
            self._createIKChain()

            # Set the 'active' bool to True
            self._active = True

            return self._componentGroup

    def parent(self, components, parentComponent, uprightComponent):

        # Parent each sub component to the corresponding joint
        for index in range(len(self._childComponents)):
            self._childComponents[index].parent(self.ikChainSpaces, self.ikChainSpaces[index], self.ikChainSpaces[index])

        # Parent the ikComponent
        self.ikComponent.parent(components, parentComponent, uprightComponent)

        #Parent the base components
        self.baseComponent.parent(components, parentComponent, uprightComponent)

    def snap(self):

        self.ikComponent.snap()

        self.baseComponent.snap()

        if not self._noFlipKnee:
            self._poleControl.setTranslation(self._getPolePoint(), worldSpace=True)

        for index in range(len(self._childComponents)):
            self._childComponents[index].matrixOutput.setMatrix(
                self._deformTargets[index].getMatrix(worldSpace=True), worldSpace=True)

    def bake(self, frame):

        self.ikComponent.bake(frame=frame)

        self.baseComponent.bake(frame=frame)

        if not self._noFlipKnee:
            pmc.setKeyframe(self._poleControl, t=frame)

        for index in range(len(self._childComponents)):
            self._childComponents[index].bake(frame)


    #### private methods ####

    def _generateChildComponents(self):
        # Create a list to hold all child components
        self._childComponents = []

        # Create a child component for the base component (This will be the base parent)
        # This is also the only component without squash and stretch control
        self._childComponents.append(FKComponent(name=self.name + str(1),
                                                 target=self._deformTargets[self.startIndex],
                                                 spaceSwitchEnabled= False,
                                                 stretchTarget=None,
                                                 stretchEnabled=False,
                                                 squashEnabled=False,
                                                 mainControlType=self._fkOffsetCurveType,
                                                 mainControlScale=5.0,
                                                 mainControlColor=self._mainControlColor,
                                                 isLeafJoint=self._isLeafJoint
                                                 ))

        # Create a child component for each middle component
        # For parent space we just use the index of the parent component in our child component list
        for index in self.middleIndex:
            self._childComponents.append(FKComponent(name=self.name + str(index + 1),
                                                     target=self._deformTargets[index],
                                                     spaceSwitchEnabled=False,
                                                     stretchTarget=self._childComponents[index - 1],
                                                     stretchEnabled=self._squashEnabled,
                                                     squashEnabled=self._stretchEnabled,
                                                     mainControlType=self._fkOffsetCurveType,
                                                     mainControlScale=5.0,
                                                     mainControlColor=self._mainControlColor,
                                                     isLeafJoint=self._isLeafJoint
                                                     ))

        # Create a child component for the endJoint
        self._childComponents.append(FKComponent(name=self.name + str(self.endIndex + 1),
                                                 target=self._deformTargets[self.endIndex],
                                                 spaceSwitchEnabled=False,
                                                 stretchTarget=self._childComponents[self.endIndex - 1],
                                                 stretchEnabled=self._squashEnabled,
                                                 squashEnabled=self._stretchEnabled,
                                                 mainControlType=self._fkOffsetCurveType,
                                                 mainControlScale=5.0,
                                                 mainControlColor=self._mainControlColor,
                                                 isLeafJoint=self._isLeafJoint
                                                 ))

    def _createIKChain(self):

        # Create a list to hold the duplicate chain
        self.ikChain = []

        # Create a list to hold the spaces for the ik chain
        # This will allow the child components to be parented to the joints
        self.ikChainSpaces = []

        # Create a group to hold the chain
        self.ikChainGroup = pmc.group(empty=True, name='reference')
        pmc.parent(self.ikChainGroup, self.componentGroup)

        # Create a duplicate of each deform joint
        for index in range(len(self._deformTargets)):
            joint = self._deformTargets[index]
            duplicate = pmc.duplicate(joint, po=True, name=joint.name() + '_ikchain')[0]
            pmc.hide(duplicate)
            self.ikChain.append(duplicate)

            # Parent the duplicates
            if index == 0:
                pmc.parent(duplicate, self.baseComponent.matrixOutput)
            else:
                pmc.parent(duplicate, self.ikChain[index-1])

            # Create a space for the joint
            self.ikChainSpaces.append(Space(duplicate))

        # Create the ikHandle and effector
        self._handle, self._effector = pmc.ikHandle(sj=self.ikChain[0], ee=self.ikChain[self.endIndex])

        # Parent the handle to the main control
        pmc.parent(self._handle, self.ikComponent.matrixOutput)

        # Rename the handle and effector
        pmc.rename(self._handle, self.name + '_handle')
        pmc.rename(self._effector, self.name + '_effector')

        # Add a twist attribute to the main control and connect it to the handles twist
        pmc.addAttr(self.ikComponent.matrixOutput, ln='twist', sn='tw', nn='Twist', k=True)
        pmc.connectAttr(self.ikComponent.matrixOutput.twist, self._handle.twist)

        # If not a no flip knee, constrain the polevector
        if not self._noFlipKnee:
            self._constraints.append(pmc.poleVectorConstraint(self._poleControl, self._handle,
                                                              name=self.name + '_poleVectorConstraint'))

        # If squash and stretch enabled, setup squash and stretch
        if self._squashEnabled or self._stretchEnabled:

            # Create the nodes needed
            point1SpaceSwitch = pmc.createNode('multMatrix', name=self.name + '_point1_SpaceSwitch')
            point2SpaceSwitch = pmc.createNode('multMatrix', name=self.name + '_point2_SpaceSwitch')
            scaleCompose = pmc.createNode('composeMatrix', name=self.name+'_scaleCompose')
            scaleInverse = pmc.createNode('inverseMatrix', name=self.name+'_scaleInverse')
            ikChainLength = pmc.createNode('distanceBetween', name=self.name + '_ikChainDistance')
            lengthNormalize = pmc.createNode('floatMath', name=self.name + '_lengthNormalize')
            pmc.setAttr(lengthNormalize.operation, 3)
            outputMax = pmc.createNode('floatMath', name=self.name + '_outputMax')
            pmc.setAttr(outputMax.operation, 5)
            self._utilityNodes['ikChainLength'] = ikChainLength
            self._utilityNodes['lengthNormalize'] = lengthNormalize
            self._utilityNodes['outputMax'] = outputMax
            self._utilityNodes['point1SpaceSwitch'] = point1SpaceSwitch
            self._utilityNodes['point2SpaceSwitch'] = point2SpaceSwitch

            # Grab the inverse of the ik components parent
            # This removes global scale from the distance calculation
            pmc.connectAttr(self.ikComponent.parentSpaceBuffer.scale, scaleCompose.inputScale)
            pmc.connectAttr(scaleCompose.outputMatrix, scaleInverse.inputMatrix)

            # Connect the inverse scale to a spaceswitch for the basecomponent
            pmc.connectAttr(self.baseComponent.matrixOutput.worldMatrix[0], point1SpaceSwitch.matrixIn[0])
            pmc.connectAttr(scaleInverse.outputMatrix, point1SpaceSwitch.matrixIn[1])

            # Do the same for the ik component
            pmc.connectAttr(self.ikComponent.matrixOutput.worldMatrix[0], point2SpaceSwitch.matrixIn[0])
            pmc.connectAttr(scaleInverse.outputMatrix, point2SpaceSwitch.matrixIn[1])

            # Connect the outputs to the distance node
            pmc.connectAttr(point1SpaceSwitch.matrixSum, ikChainLength.inMatrix1)
            pmc.connectAttr(point2SpaceSwitch.matrixSum, ikChainLength.inMatrix2)

            # Connect the distance to a node that will normalize the value (divide by the start distance)
            pmc.connectAttr(ikChainLength.distance, lengthNormalize.floatA)
            pmc.setAttr(lengthNormalize.floatB, pmc.getAttr(ikChainLength.distance))

            # Connect that to a max node, since we only want the component to stretch further than the start
            pmc.connectAttr(lengthNormalize.outFloat, outputMax.floatA)
            pmc.setAttr(outputMax.floatB, 1.0)

            # Hook up the ik chain scale
            pmc.connectAttr(outputMax.outFloat, self.ikChain[0].scaleX)
            pmc.connectAttr(outputMax.outFloat, self.ikChain[1].scaleX)

        # Constrain the last ik chain to the ikControl
        pmc.orientConstraint(self.ikComponent.matrixOutput, self.ikChain[2], mo=True)

    def _getPolePoint(self):
        # Grab the worldspace vectors of each points position
        startPoint = self._deformTargets[0].getTranslation(space='world')
        elbowPoint = self._deformTargets[1].getTranslation(space='world')
        endPoint = self._deformTargets[self.endIndex].getTranslation(space='world')

        # Find the midpoint between the start and end joint
        averagePoint = (startPoint + endPoint) / 2

        # Find the direction from the midpoint to the elbow
        elbowDirection = elbowPoint - averagePoint

        # Multiply the direction by 2 to extend the range
        polePoint = (elbowDirection * 5) + averagePoint

        return polePoint


    ### Public Properties

    @property
    def ready(self):
        # This property determines whether the component can be built
        # with its current values
        # A value of None is considered ready

        error = None

        if not len(self._deformTargets) < 3:
            error = 'Requires at least three deform targets'

        return error

    @property
    def target(self):
        return self._deformTargets[self.endIndex]

    @property
    def targets(self):
        return self._deformTargets

    @property
    def ready(self):
        error = None

        if self._deformTargets < 3:
            error = 'Needs at least 3 deform targets'

        return error

class SpineIKComponent(MultiFKComponent):
    '''
    A Modified series of FK components built to emulate the behavior
    of a spline IK setup
    '''

    def __init__(self, spineControlType='default', secondaryParentSpace=None, secondaryUprightSpace=None, **kwargs):

        # Set up initial variables
        self._spineControlType = spineControlType
        self._secondaryParentSpace = secondaryParentSpace
        self._secondaryUprightSpace = secondaryUprightSpace

        # Initialize the base class
        MultiFKComponent.__init__(self, **kwargs)


    #### Private Methods #####

    def _generateChildComponents(self):

        # Create a list to hold all child components
        self._childComponents = []

        # Create a child component for the base of the spine (This will be the base parent)
        # This is also the only component without squash and stretch control
        self._childComponents.append(FKComponent(name=self.name + '_base',
                                                 target=self._deformTargets[self.startIndex],
                                                 spaceSwitchEnabled=True,
                                                 stretchTarget=None,
                                                 stretchEnabled=False,
                                                 squashEnabled=False,
                                                 mainControlType=self._mainControlType.curveType,
                                                 mainControlScale=self._mainControlScale,
                                                 mainControlColor=self._mainControlColor,
                                                 isLeafJoint=self._isLeafJoint,
                                                 aimAtChild=False
                                                 ))
        self.baseComponent = self._childComponents[0]

        # Create a child component for each middle component
        # For parent space we just use the index of the parent component in our child component list
        for index in self.middleIndex:
            self._childComponents.append(FKComponent(name=self.name + str(index + 1),
                                                     target=self._deformTargets[index],
                                                     spaceSwitchEnabled=False,
                                                     stretchTarget=self._childComponents[index - 1],
                                                     stretchEnabled=self._squashEnabled,
                                                     squashEnabled=self._stretchEnabled,
                                                     mainControlType=self._spineControlType,
                                                     mainControlScale=self._mainControlScale,
                                                     mainControlColor=self._mainControlColor,
                                                     isLeafJoint=self._isLeafJoint,
                                                     aimAtChild=False
                                                     ))

        # Create a child component for the endJoint
        self._childComponents.append(FKComponent(name=self.name + str(self.endIndex + 1),
                                                 target=self._deformTargets[self.endIndex],
                                                 spaceSwitchEnabled=True,
                                                 stretchTarget=self._childComponents[self.endIndex - 1],
                                                 stretchEnabled=self._squashEnabled,
                                                 squashEnabled=self._stretchEnabled,
                                                 mainControlType=self._mainControlType.curveType,
                                                 mainControlScale=self._mainControlScale,
                                                 mainControlColor=self._mainControlColor,
                                                 isLeafJoint=self._isLeafJoint,
                                                 aimAtChild=False
                                                 ))
        self.endComponent= self._childComponents[self.endIndex]

    def _createSpineSpaces(self):

        # Create a list to hold spineSpaces
        self._spineSpaces = []

        # Create a group to contain the spaces
        referenceGroup = pmc.group(empty=True, name='reference')
        pmc.parent(referenceGroup, self._componentGroup)

        # Build the middle spine spaces
        for index in self.middleIndex:

            # Create a space for the component, the target being an empty group
            spaceGroup = pmc.group(empty=True, name=self.name +'_space_' + str(index))
            space = Space(spaceGroup)
            space.matrixOutput.setMatrix(self._childComponents[index].matrixOutput.getMatrix(worldSpace=True), worldSpace=True)
            self._spineSpaces.append(space)

            # Parent the space to the reference group
            pmc.parent(spaceGroup, referenceGroup)

            # Create two empty objects, one for the start, and one for the end
            startLocator = pmc.group(empty=True, name=self.name + '_startLocator_' + str(index))
            endLocator = pmc.group(empty=True, name=self.name + '_endLocator_' + str(index))

            # Set the locators position, and parent them to the corresponding component
            startLocator.setMatrix(self._childComponents[index].matrixOutput.getMatrix(worldSpace=True), worldSpace=True)
            pmc.parent(startLocator, self.baseComponent.matrixOutput)
            endLocator.setMatrix(self._childComponents[index].matrixOutput.getMatrix(worldSpace=True), worldSpace=True)
            pmc.parent(endLocator, self.endComponent.matrixOutput)

            # Create a decompose matrix to grab the base components scale
            scaleDecompose = pmc.createNode('decomposeMatrix', name=self.name+'_scaleDecomp'+str(index))
            self._utilityNodes['scaleDecompose_'+str(index)] = scaleDecompose
            pmc.connectAttr(self.baseComponent.matrixOutput.worldMatrix[0], scaleDecompose.inputMatrix)
            pmc.connectAttr(scaleDecompose.outputScale, space.matrixOutput.scale)

            # Create a decompose matrix for each locator, to extract the worldspacematrix
            startDecompose = pmc.createNode('decomposeMatrix', name=self.name + '_startlocatorDecomp_' + str(index))
            endDecompose = pmc.createNode('decomposeMatrix', name=self.name + '_endlocatorDecomp_' + str(index))
            self._utilityNodes['startDecompose_' + str(index)] = startDecompose
            self._utilityNodes['endDecompose_' + str(index)] = endDecompose

            # Connect the locators worldMatrix to their decompose matrix
            pmc.connectAttr(startLocator.worldMatrix[0], startDecompose.inputMatrix)
            pmc.connectAttr(endLocator.worldMatrix[0], endDecompose.inputMatrix)

            # Create a pair blend node and connect the outputs from the decomp nodes
            pairBlend = pmc.createNode('pairBlend', name=self.name + '_pairBlend+' + str(index))
            self._utilityNodes['pairBlend_' + str(index)] = pairBlend
            pmc.connectAttr(startDecompose.outputTranslate, pairBlend.inTranslate1)
            pmc.connectAttr(startDecompose.outputRotate, pairBlend.inRotate1)
            pmc.connectAttr(endDecompose.outputTranslate, pairBlend.inTranslate2)
            pmc.connectAttr(endDecompose.outputRotate, pairBlend.inRotate2)

            # Create an attribute for the blend, and set a default value to it
            pmc.addAttr(self._childComponents[index].matrixOutput,
                        ln='startEndWeight', sn='sew', nn='State End Weight', type='double',
                        defaultValue=float(index + 1) / float(len(self.middleIndex) + 1),
                        hasMinValue=True, minValue=0.0,
                        hasMaxValue=True, maxValue=1.0,
                        k=True, hidden=False)
            pmc.connectAttr(self._childComponents[index].matrixOutput.startEndWeight, pairBlend.weight)

            # Connect the output to the child component's local space buffer
            pmc.connectAttr(pairBlend.outTranslate, space.matrixOutput.translate)
            pmc.connectAttr(pairBlend.outRotate, space.matrixOutput.rotate)

    ##### Public Methods #####

    def build(self):
        if not self.active:

            # Create a component group to contain all component DAG nodes
            self._componentGroup = pmc.group(empty=True, name=self.name+'_com')

            # Create the base component
            self.baseComponent.build()
            pmc.parent(self.baseComponent.componentGroup, self._componentGroup)

            # Create the base control
            self.endComponent.build()
            pmc.parent(self.endComponent.componentGroup, self._componentGroup)

            # Build the child components and parent them to the componentGroup
            for index in self.middleIndex:
                self._childComponents[index].build()
                pmc.parent(self._childComponents[index].componentGroup, self._componentGroup)

            # Create the ik chain
            self._createSpineSpaces()

            # Set the 'active' bool to True
            self._active = True

            return self._componentGroup

    def parent(self, components, parentComponent, uprightComponent):

        # Parent each middle component to its corresponding space
        for index in self.middleIndex:
            self._childComponents[index].parent(self._spineSpaces,
                                                self._spineSpaces[index-1],
                                                self._spineSpaces[index-1])
        # Parent the ikComponent
        self.baseComponent.parent(components, parentComponent, uprightComponent)

        #Parent the base components
        self.endComponent.parent(components, parentComponent, uprightComponent)

    def snap(self):

        for index in range(len(self._childComponents)):
            self._childComponents[index].snap()

    def bake(self, frame):

        for index in range(len(self._childComponents)):
            self._childComponents[index].bake(frame)

    @property
    def ready(self):
        error = None

        if self._deformTargets < 3:
            error = 'Needs at least 3 deform targets'

        return error

class LegIKComponent(IKComponent):

    def __init__(self, **kwargs):
        IKComponent.__init__(self, **kwargs)


    def _generateChildComponents(self):
        # Create a list to hold all child components
        self._childComponents = []

        # Create a child component for the base component (This will be the base parent)
        # This is also the only component without squash and stretch control
        self._childComponents.append(FKComponent(name=self.name + str(1),
                                                 target=self._deformTargets[self.startIndex],
                                                 spaceSwitchEnabled= False,
                                                 stretchTarget=None,
                                                 stretchEnabled=False,
                                                 squashEnabled=False,
                                                 mainControlType=self._fkOffsetCurveType,
                                                 mainControlScale=5.0,
                                                 mainControlColor=self._mainControlColor,
                                                 isLeafJoint=self._isLeafJoint
                                                 ))

        # Create a child component for each middle component
        # For parent space we just use the index of the parent component in our child component list
        for index in self.middleIndex:
            self._childComponents.append(FKComponent(name=self.name + str(index + 1),
                                                     target=self._deformTargets[index],
                                                     spaceSwitchEnabled=False,
                                                     stretchTarget=self._childComponents[index - 1],
                                                     stretchEnabled=self._squashEnabled,
                                                     squashEnabled=self._stretchEnabled,
                                                     mainControlType=self._fkOffsetCurveType,
                                                     mainControlScale=5.0,
                                                     mainControlColor=self._mainControlColor,
                                                     isLeafJoint=self._isLeafJoint
                                                     ))

        # Create a child component for the endJoint
        self._childComponents.append(FKComponent(name=self.name + str(self.endIndex + 1),
                                                 target=self._deformTargets[self.endIndex+1],
                                                 spaceSwitchEnabled=False,
                                                 stretchTarget=self._childComponents[self.endIndex - 1],
                                                 stretchEnabled=self._squashEnabled,
                                                 squashEnabled=self._stretchEnabled,
                                                 mainControlType=self._fkOffsetCurveType,
                                                 mainControlScale=5.0,
                                                 mainControlColor=self._mainControlColor,
                                                 isLeafJoint=self._isLeafJoint
                                                 ))

    def _createIKChain(self):
        IKComponent._createIKChain(self)

        rollLocator = pmc.group(empty=True, name=self.name + '_rollLocator')
        rollLocator.setRotationOrder('XZY', True)
        pmc.parent(rollLocator, self.ikComponent.matrixOutput)
        rollLocator.setMatrix(self._childComponents[3].orientBuffer.getMatrix(worldSpace=True), worldSpace=True)

        pmc.setAttr(rollLocator.rotateZ, 0)
        self.rollSpace = Space(rollLocator)

        pmc.addAttr(self.ikComponent.matrixOutput, ln='footRoll', sn='fr', nn='Reverse Foot Roll', k=True,
                    type='double', hidden=False)
        pmc.connectAttr(self.ikComponent.matrixOutput.footRoll, rollLocator.rotateZ)

        pmc.parent(self._handle, rollLocator)

    def parent(self, components, parentComponent, uprightComponent):

        # Parent each of the main sub components, to their corresponding space
        self._childComponents[0].parent(self.ikChainSpaces, self.ikChainSpaces[0], self.ikChainSpaces[0])
        self._childComponents[1].parent(self.ikChainSpaces, self.ikChainSpaces[1], self.ikChainSpaces[1])
        self._childComponents[2].parent(self.ikChainSpaces, self.ikChainSpaces[2], self.ikChainSpaces[2])
        self._childComponents[3].parent(self.ikChainSpaces, self.ikComponent, self.ikComponent)

        # Parent the ikComponent
        self.ikComponent.parent(components, parentComponent, uprightComponent)

        #Parent the base components
        self.baseComponent.parent(components, parentComponent, uprightComponent)

    def bake(self, frame):

        self.ikComponent.bake(frame=frame)

        self.baseComponent.bake(frame=frame)

        if not self._noFlipKnee:
            pmc.setKeyframe(self._poleControl, t=frame)

        for index in range(len(self._childComponents)):
            self._childComponents[index].bake(frame)

    @property
    def ready(self):
        error = None

        if len(self._deformTargets) is not 4:
            error = 'Needs 4 deform targets'

        return error

    @property
    def endIndex(self):
        return len(self._deformTargets) - 2

class AimComponent(FKComponent):

    def __init__(self, aimControlType='default', aimCurveDistance = 50.0, aimVector=[1,0,0], **kwargs):
        FKComponent.__init__(self, **kwargs)

        # Grab variables
        self._aimCurveDistance = aimCurveDistance
        self._aimVector = aimVector

        # Create a curve class for the aim control
        self._aimComponent = BasicComponent(name=self.name + '_Aim',
                                             target=self._target,
                                             spaceSwitchEnabled=False,
                                             mainControlType=aimControlType,
                                             mainControlScale=self._mainControlScale,
                                             mainControlColor=self._mainControlColor)

    def build(self):

        # Build the base component
        FKComponent.build(self)

        # Build the aim Component
        aimComponentGroup = self._aimComponent.build()
        pmc.parent(aimComponentGroup, self.componentGroup)

        # Create a target for the aimComponent to snap to
        self.aimTarget = pmc.group(empty=True, name=self.name+'aimTarget')
        self.aimTarget.setMatrix(self.matrixOutput.getMatrix(worldSpace=True), worldSpace=True)
        pmc.parent(self.aimTarget, self.matrixOutput)
        self.aimTarget.setAttr('translate', self._aimCurveDistance * dt.Vector(self._aimVector))

        self._aimComponent.matrixOutput.setMatrix(self.aimTarget.getMatrix(worldSpace=True), worldSpace=True)

        pmc.aimConstraint(self._aimComponent.matrixOutput,self.matrixOutput, wut='scene', mo=True)


        return self.componentGroup

    def parent(self, components, parentComponent, uprightComponent):
        FKComponent.parent(self, components, parentComponent, uprightComponent)

        self._aimComponent.parent(components, parentComponent, uprightComponent)


    def snap(self):
        FKComponent.snap(self)

        #self._aimComponent.matrixOutput.setMatrix(self.aimTarget.getMatrix(worldSpace=True), worldSpace=True)
        self._aimComponent.matrixOutput.setTranslation(self._target.getTranslation(world=True))

    def bind(self):
        FKComponent.bind(self)


    def bake(self, frame):
        FKComponent.bake(self, frame)

        pmc.setKeyframe(self._aimComponent.matrixOutput, t=frame)

class ScaleComponent(BasicComponent):
    '''
    A basic component that scales its target
    '''

    def __init__(self, **kwargs):
        BasicComponent.__init__(self, **kwargs)

    def bind(self):

        pmc.connectAttr(self.matrixOutput.scale, self._target.scale)

        self._bound = True

    def unbind(self):

        if self._bound:

            pmc.disconnectAttr(self._target.scale)

            # Mark this component as inactive
            self.bound = False

    @property
    def ready(self):
        error = None

        if self._target is None:
            error = 'Needs at least one target'

        return  error

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
        self._activeRigs = self._loadFromScene()

        # Grab the data handler
        self._data = data

    ##### Private Methods #####

    def _loadFromScene(self):

        try:
            rigData = eval(pmc.fileInfo['rigs'])
            print rigData
            rigs = {rigName: Rig(rigName, rigData['componentData'], rigData['directory'],
                                 built=rigData['built'], baked=rigData['baked'], bound=rigData['bound'],
                                 rigGroup=rigData['rigGroup'])
                                for rigName, rigData in rigData.iteritems()}

        except KeyError:
            rigs = {}

        return rigs


    def _saveToScene(self):
        pmc.fileInfo['rigs'] = repr(self.data)

    ##### Public Methods #####

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

        with safeCreate(self._activeRigs[rigName]):
            # Remove the rig
            self._activeRigs[rigName].remove()

            # Rebuild the rig
            self._activeRigs[rigName].build()

            # Save the data to the scene
            self._saveToScene()

    def bindRig(self, rigName):

        with safeCreate(self._activeRigs[rigName]):
            # Remove the rig()
            self._activeRigs[rigName].remove()

            # Build and bind the rig
            self._activeRigs[rigName].bind()

            # Save the data to the scene
            self._saveToScene()

    def bakeRig(self, rigName):

        with safeCreate(self._activeRigs[rigName]):
            # Remove the rig
            self._activeRigs[rigName].remove()

            # Rebuild, bake, and bind the rig
            frameRange = int(pmc.playbackOptions(query=True, aet=True))
            self._activeRigs[rigName].bake(frameRange=frameRange)
            self._activeRigs[rigName].bind()

            # Save the data to the scene
            self._saveToScene()

    def bakeDeforms(self, rigName):

        with safeCreate(self._activeRigs[rigName]):
            frameRange = int(pmc.playbackOptions(query=True, aet=True))
            self._activeRigs[rigName].bakeDeforms(frameRange=frameRange)
            self._activeRigs[rigName].remove()

            # Save the data to the scene
            self._saveToScene()

    def unbindRig(self, rigName):

        with safeCreate(self._activeRigs[rigName]):
            self._activeRigs[rigName].unbind()

            # Save the data to the scene
            self._saveToScene()

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

        # Save the data to the scene
        self._saveToScene()

    def removeRig(self, rigName):

        # Remove the rig
        self._activeRigs[rigName].remove()

        # Save the data to the scene
        self._saveToScene()

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
        id = self._activeRigs[rigName].addComponent(**COMPONENT_TYPES[type])
        return id

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

    @property
    def data(self):
        '''Return each active rig with instructions on how to replicate them'''
        return {rigName: rig.data for rigName, rig in self._activeRigs.iteritems()}

    @property
    def activeRigs(self):
        ''' Return active rigs as a list'''
        return [name for name, rig in self._activeRigs.iteritems()]


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

