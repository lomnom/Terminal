# Terminal, a python library for all terminal-related needs (\*nix only)!
## Structure

This library is split into 3 parts:
- `Terminal`: Low-level utilities, such as:
	- `keys()`: to get keystrokes
	- `cleartoeos`, and many other escapes
	- `KeyHandler`: an asynchronous key handler
	- `raw()`, and other terminal status changers
	- ...
- `TermCanvas`: a layer of abstraction above the terminal, which contains:
	- `Terminal`: a terminal buffer
	- `Char`: representation of a terminal character
	- `CanvasApp`: a wrapper for an application using the canvas
	- ...
- `TermUI`: An element-based UI library, built upon the other two layers, which has: 
	- `Root`: the parent element that projects onto the terminal
	- `Alloc`: a static space allocator for elements
	- `Text`: text
	- `Box`: a box
	- and many more elements for convenient and easy UI creation
- `TermIntr`: A library for interactive elements, for example:
	- `Button`: a button
	- `ToggleButton`: a togglable burron
	- ...

Documentation is not written yet, and will be started on after the End-Of-Year exams.

For now, you can read the borderline comprehensible code, and try to understand the demo scripts, `CvDemo.py` and `UIDemo.py`

