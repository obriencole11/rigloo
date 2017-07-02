# Fossil
### Fossil is a Component-Based autorigger for Maya

Fossil was built with the following goals in mind:
* Allow for **fast** rig prototyping and iteration
* Be **flexible** and support a diverse selection of characters
* Make rigging **accessible** without sacrifising flexibility
* Be **adaptive** and allow for working off of existing animation data

Fossil is **component based**. Rigs are constructed with common rig parts that can be customized to fit each character. This design choice was essential to support a variety of body types, as the rig makes very few assumptions on the construction of the users character. Other tools like HIK and Motionbuilders control rig make strict assumptions on character construction and would not work for the project in mind.

Fossil is **code driven**. Rigs are built and attached dynamically, meaning it can fit to any skeleton shape. Additionally this was essential to allow for baking the rig to existing animation data. This means the tool can be used for motion capture cleanup or even animation created with other rigs.

### Inspiration

Functionally the tool is inspired by Blizzard's code based rigging for Overwatch, as seen in their GDC 2017 talk "The Animation Pipeline of Overwatch". Visually the tool is reminiscent of Unity's component editor, an engine I have much experience with.

## Installation

Currently fossil only supports a manual installation. To do so, download the zip of this project and place the entire folder in: `C:\Users\*User*\Documents\maya\*version*\scripts`

Then Maya's script editor add the following text and run it:
```
import fossil_main; fossil_main.load()
```
The main window should then appear. You can then use this code to create your own shelf button. A custom icon for adding to a shelf is available in `icon/icon-logoShelf.svg`

## Features

Fossil includes the following features:
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

For a detailed description of how the tool works, consult the [documentation](https://github.com/obriencole11/fossil/blob/master/Documentation.md).

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
