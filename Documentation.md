# Fossil Documentation

## Core Features

### Rig Creation
On startup a new empty rig is automatically created for you. Rigs a customized by adding **components** through the add component menu. Each component comes with additional settings explained below. 

#### Previewing Rigs
Hitting the preview button generates the rig but does not attach it to your character. While previewed you can test the rig and fit the control shapes to your character. Hitting preview will generate the character again. 

#### Binding Rigs
Hitting bind will attach the controls to your character. Once attached you can easily detach it with the remove button or by simply undoing. When attached, deleting the rig group in the outline will be destructive. The tool should remember your rig and can be removed after. A simple work around however if you cannot remove the rig, is to select all bound joints and use key > bakesimulation. Then your rig will be safe to delete.

#### Baking Rigs
Under the settings menu, you can turn on 'bake on bind'. This means when bind is hit, it will first bake the targets animation to the control rig before attaching. This may take a little bit depending on rig complexity and animation length, so I do not recomend having this on when prototyping.

#### Saving and Loading Rigs
Rigs can be saved as .json files in the tool's file menu. The default save location being your maya script directory. When loading rigs, the rig is added to an active rig dropdown list. Active rigs can be switched with the dropdown list. Bound rigs should be automatically added to this dropdown when the tool opens.

#### Squash and Stretch
All multi-target components support squash and stretch. However, it is recomended you do so via leaf joints. With a leaf joint setup, each joint bound to the skin cluster does not have any children. This way when they are stretched, there are no space issues with the joints below it. This is also the recomended setup for exporting to game engines. There is a script included with this tool that will convert a bound skeleton to one set up with leaf joints. The tool can be run with:
```
import leafJointGenerator; leafJointGenerator.generate(*your skeleton*)
```

## Components
Components represent a self contained part of the rig. By design, a component should be as decoupled from other components as possible. A component should not be confused with a control or a body part, a component can consist of one or many of those. An example of a component is an IK chain for a foot or arm. The pole vector control for the chain however would not be it own component, in concept it is tightly coupled to the chain and as such should be a part of the IK component.

### Basic Component
The simplest idea of a component. Consists of a single control curve. It is created at a target position and can be parented as well as have parents. While it follows the position, it does not actually control the position. 
Example uses:
* Decorative curves
* Grouping controls (such as a center of gravity control)

Features:
* Name: A string to identify the component
* Target: A object in the scene for the component to follow. If none, the component is placed at the world origin.
* Parent Space: Another component that this components position should follow. The default is to parent to the world.
* Upright Space: Another component that this components rotation should follow. The default is to parent to the world.
* Space Switch Enabled: Whether to enable keyable space switching post-generating. Default is to off.
* Main Control Type: A shape preset for the main control.
* Main Control Scale: The base scale for the main control curve.
* Use Custom Curve: When this is true, control curves modifications will be saved when the preview is refreshed.

### Scale Component
An iteration of the basic component that has control over scale. In order to work well with squash and stretch, no other component allows for scale control. This component was designed to be used as the root component of a rig.

Features:
* See Basic Component

### FK Component
A slightly more advanced version of the basic component. Really just a basic component that controls the position of its target. Often these are used as subsets of more complex components.
Example uses
* Shoulder rotation control
* Hip control

Features:
* See Basic Component
* Is Leaf Joint: Whether the target is a leaf joint. This is for specific squash and stretch setups where bind joints do not have any children. This is the recomended method for squash and stretch setups with this tool (see above)

### Multi-FK Component
A grouping a two or more FK Components. This makes it easier to organize large FK chains when rigging. Only the top level component has parent space control. 
Example uses:
* FK Legs
* FK Arms
* Fingers

Features:
* See FK Component
* Targets: A selection of targets that the component should attach to.
* Stretch Enabled: Joints will scale to match their length
* Squash Enabled: Joints will expand and constract when length increases

### IK Component
A grouping of FK components that follows a simple IK chain. This allows for slight offsets from the reference IK chain. The start and end of the chain are a seperate FK component with parent space control.
Example Uses:
* IK Arms
* IK Legs

Features:
* See Multi-FK Component
* No Flip Knee: Whether the component should use a pole vector control.
* Pole Control Curve Type: The shape preset for the pole control.
* FK Offset Curve Type: The shape preset for the FK offset controls.

### Spine IK Component
While not a traditional spline-IK spine, this component allows for similar functionality with more control. An FK control is built for each spine joint, while the start and end gain parent space control.
Example Uses:
* Spines

Features:
* See Multi-FK Component
* Child Control Type: The base shape preset for the spine FK offset controls.
* Child Control Scale: The base scale for each spine offset contrl.

### Leg IK Component
A more complex form of the IK Component that is built specifically for humanoid legs. Requires a 4 joint chain, and provides the normal ik chain with the addition of reverse foot roll functionality.
Example Uses:
* IK Legs with feet

Features:
* See IK Component
