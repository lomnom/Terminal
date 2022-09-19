import TermUI as tui
import TermCanvas as tc
import Terminal as trm

line=tui.Lines

@tc.canvasApp # wrapper that initialises the terminal and passes the canvas to you
def main(cnv):
	# Text formatting uses \f[foreground colour] and \b[background colour]
	keyText=tui.Text("\f[56]Type stuff\f[default]")
	faces=tui.ElementSwitcher(
		tui.Text(" \f[cyan]_*:)*_\f[default]"),
		tui.Text("\f[red]_*>:)*_\f[default]"),
		tui.Text(" \f[blue]_`:(`_\f[default]"),
		tui.Text(" \f[magenta]_:\\|_\f[default]")
	)
	root=tui.Root(
		cnv,
		tui.ZStack( # this stack layers the smily on line 42 above the horizontal stack below
			tui.HAlloc( # Horizontal allocator
				(
					tui.VAlloc( # Vertical allocator
						(
							tui.Text("*_HELLO WORLD_*") # you can use markdown-style * and _
								.box(line.double), # fill the space allocated to this with a double-lined box
						"7"), # 7 rows allocated to this
						(
							tui.Text("_*ctrl+z* to quit btw_")
								.box(line.thick)
								.pad(top=1,left=2,bottom=1,right=3), # add padding around the box that fills allocated space
						"40%") # 40% of space excluding fixed allocations (such as the 7 above)
					),
				"50%"),
				(
					tui.Text("^Lmao^") # ^ for blinking text
						.box(line.thinD)
						.squish(squishV=10), # squish the allocated space to 10 rows, stopping the box from stretching all the way down.
				"5"),
				(
					tui.Nothing(),
				"12"), # 12 columns of nothing (space)
				(
					keyText
						.box(line.thin,style="\f[104]")
						.squish(squishV=3),
				"50%")
			),
			faces # this collection of faces is layered above the HAlloc above
				.squish(squishH=3,squishV=1) # make the text ridgid by solidly defining its size
				.align(alignH="right",alignV="bottom"), # align the text to the bottom right
			tui.Text("`Press *f* to change my face btw`")
				.squish(squishH=29,squishV=1) # make the text ridgid by solidly defining its size
				.align(alignH="left",alignV="bottom") # align the text to the bottom right
		).box(line.thinC,style="\f[34]",label="*Random trash*") # Add a box around everything, with color 34/255 and a label
		 .squish(squishH=70,squishV=30)
		 .align(alignH="middle",alignV="middle") # Align ridgid box to middle of screen

	)
	root.render() # update what is shown on screen

	keyIter=trm.keys() # key iterator, instantlty yields keys because canvasApp enabled raw()
	while True:
		key=next(keyIter)
		if key=='ctrl z':
			return
		elif key=='f':
			faces.visible=(faces.visible+1)%len(faces)
			key="f`_(ace)_`"
		keyText.text=f"\f[56]You pressed: *{key}*\f[default]" # Update the keyText
		root.render() # update the screen