# Terminal, a loosely swiftui-inspired python library for all TUI-related needs (\*nix only)!
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
	- `VStack` & `HStack`: a dynamic space allocator for elements
	- `Text`: text that supports markdown-like fonts
	- `Aligner`: a container that aligns elements
	- and many more elements for convenient and easy UI creation
- `TermIntr`: A library for interactive elements, for example:
	- `Button`: a button
	- `Textbox`: a textbox
	- ...

As this library is still constantly evolving, I have chosen not to write documentation untill a stable release is created.

For now, you can read the source code, and study applications made with this library, such as the demo script `UIDemo.py` and the Befunge IDE [Fungelet](https://github.com/lomnom/Fungelet).