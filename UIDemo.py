import TermUI as tui
import TermCanvas as tc
import Terminal as trm

line=tui.Lines

@tc.canvasApp # wrapper that initialises the terminal and passes the canvas to you
def main(cnv):
	# Text formatting uses \f[foreground colour] and \b[background colour]
	keyText=tui.Text("\f[56]Type stuff\f[default]")
	quitText=tui.Text("_*ctrl+z* to quit btw_")
	faces=tui.ElementSwitcher(
		tui.Text(" \f[cyan]_*:)*_\f[default]"),
		tui.Text("\f[red]_*>:)*_\f[default]"),
		tui.Text(" \f[blue]_`:(`_\f[default]"),
		tui.Text(" \f[magenta]_:\\|_\f[default]")
	)
	root=tui.Root(
		cnv,
		tui.ZStack( # this stack layers the smiley on line 42 above the horizontal stack below
			tui.HAlloc( # Horizontal allocator
				(
					tui.VAlloc( # Vertical allocator
						(
							tui.Text("*_HELLO WORLD_*") # you can use markdown-style * and _
								.expandTo(tui.Alloc,offX=-2,offY=-2)
								.box(line.double), # fill the space allocated to this with a double-lined box
						"7"), # 7 rows allocated to this
						(
							quitText
								.pad(top=1,left=2,bottom=1,right=3)
								.box(line.thick),
						"40%") # 40% of space excluding fixed allocations (such as the 7 above)
					),
				"50%"),
				(
					tui.Text("^Lmao^") # ^ for blinking text
						.expand(expandV=10) # squish the allocated space to 10 rows, stopping the box from stretching all the way down.
						.box(line.dotted),
				"5"),
				(
					tui.Nothing(),
				"12"), # 12 columns of nothing (space)
				(
					tui.VAlloc(
						(
							keyText
								.expand(expandV=3)
								.box(line.thin,style="\f[104]")
								.align(alignH="middle"),
						"25%"),
						(
							tui.HAlloc(
								(
									tui.Text("\f[172]_|Other libs|_\n   Hard\f[default]")
										.align(alignH="middle"),
								"50%"),
								(
									tui.Seperator("vertical",line.dotted.v),
								"1"),
								(
									tui.Text("_\f[82]|_This_|\n Ez\f[default]_")
										.align(alignH="middle"),
								"50%"),
							).pad(top=1,bottom=2),
						"75%")
					),
				"50%")
			),
			faces # this collection of faces is layered above the HAlloc above
				.align(alignH="right",alignV="bottom") # align the text to the bottom right
			,
			tui.Text("`Press *f* to change my face btw`")
				.align(alignH="left",alignV="bottom") # align the text to the bottom right
			,
		).expand(expandH=70,expandV=30)
		 .box(line.curvy,style="\f[34]",label="*Random trash*") # Add a box around everything, with color 34/255 and a label
		 # .alter({
		 # 	"bcolor":lambda chr,x,y: 253
		 # })
		 .align(alignH="middle",alignV="middle") # Align ridgid box to middle of screen
	)
	root.render() # update what is shown on screen

	keyIter=trm.keys() # key iterator, instantlty yields keys because canvasApp enabled raw()
	timer=trm.Stopwatch()
	while True:
		key=next(keyIter)
		if key=='ctrl z':
			return
		elif key=='f':
			faces.visible=(faces.visible+1)%len(faces)
			key="f`_(ace)_`"
		elif key=='s':
			timer.start()
		elif key=='e':
			timer.stop()
		elif key=='d':
			quitText.text=f"_^{str(timer.time()*1000)}^_"
		elif key=='r':
			timer.reset()
		keyText.text=f"\f[56]You pressed: *{key}*\f[default]" # Update the keyText
		root.render() # update the screen