![Rigloo Logo](/images/logo-loop.gif)

# Rigloo
### Rigloo is a Component-Based autorigger for Maya

![Rigloo Banner](/images/banner.gif)

Rigloo was built with the following goals in mind:
* Allow for **fast** rig prototyping and iteration
* Be **flexible** and support a diverse selection of characters
* Make rigging **accessible** without sacrifising flexibility
* Be **adaptive** and allow for working off of existing animation data

Rigloo is **component based**. Rigs are constructed with common rig parts that can be customized to fit each character. This design choice was essential to support a variety of body types, as the rig makes very few assumptions on the construction of the users character. Other tools like HIK and Motionbuilders control rig make strict assumptions on character construction and would not work for the project in mind.

Rigloo is **code driven**. Rigs are built and attached dynamically, meaning it can fit to any skeleton shape. Additionally this was essential to allow for baking the rig to existing animation data. This means the tool can be used for motion capture cleanup or even animation created with other rigs.

## Philosophy
While there are plenty of existing solutions for simplifying rig construction, most will include restrictive assumptions about character design. Tools like Maya's HIK require your character to be humanoid, while others will specify humanoid or quadruped. Rigloo was built as a rigging tool that simplifies the rigging process but does not sacrifice the creative freedom we have as riggers.

As a rigger, I also desired something that I would be able to use to speed up my own iteration time. Often I would like to make a quick rig prototype, but will be restricted in the features I can add in a short amount of time. Complex features such as parent space switching and squash and stretch would need to be omitted unless I spent the time to write a script devoted to them. Rigloo is built to speed up the rigging process while allowing for commonly used and complex features to be added to prototype rigs.

### Inspiration

Functionally the tool is inspired by Blizzard's code based rigging for Overwatch, as seen in their GDC 2017 talk "The Animation Pipeline of Overwatch". Visually the tool is reminiscent of Unity's component editor, an engine I have much experience with.

## Features

#### Overview Video:
[![](/images/video-thumbnail.png)](https://vimeo.com/225499505)

Rigloo supports the following features:
* Rig saving/loading
* Rig baking to existing animation
* 7 components including:
  * IK component with FK offsets and squash and stretch
  * Spine IK Component with FK offsets
  * Leg IK Component featuring a reverse foot roll
* Global scale control
* Component naming
* Control curve generation with
  * Custom base size
  * Choice of shape preset
  * Optional control curve editing and saving
* Keyable space switching for every component
* Squash and Stretch for multi-target components with:
  * Individual stretch and squash control
  * Leaf joint support

For a detailed description of how the tool works, consult the [documentation](https://github.com/obriencole11/rigloo/blob/master/Documentation.md).

## Download

The latest release can be downloaded here:
https://github.com/obriencole11/rigloo/releases

## Installation

Currently rigloo only supports a manual installation:
1. Extract the 'rigloo' folder into your Maya scripts directory
2. In Maya's script editor(make sure its a python editor), add the following text and run it:
```
from rigloo import rigloo_main; rigloo_main.load()
```
3. The main window should then appear. You can then use this code to create your own shelf button. A custom icon for adding to a shelf is available in `icon/icon-logoShelf.svg`

## License

MIT License

Copyright (c) 2017 Cole O'Brien

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
