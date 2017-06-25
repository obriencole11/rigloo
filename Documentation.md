## Components
Components represent a self contained part of the rig. By design, a component should be as decoupled from other components as possible. A component should not be confused with a control or a body part, a component can consist of one or many of those. An example of a component is an IK chain for a foot or arm. The pole vector control for the chain however would not be it own component, in concept it is tightly coupled to the chain and as such should be a part of the IK component.

### Basic Component
The simplest idea of a component. Consists of a single control curve. It is created at a target position and can be parented as well as have parents. While it follows the position, it does not actually control the position. 
Example uses:
* Decorative curves
* Grouping controls (such as a center of gravity control)

### FK Component
The simplest form of joint based components. Basically just a basic component that controls the position of its target. Adds some additional handy features such as squash and stretch. Probably the most common component.
* Basically any single FK joint

### Multi-FK Component

### Aim FK Component

### Simple IK Component

### Standard IK Component

### Complex IK Component

### Leg IK Component

### Spine IK Component

### Multi-IK Component