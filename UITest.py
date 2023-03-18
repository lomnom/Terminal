import TermUI as tui
import TermCanvas as tc
import Terminal as trm
# import TermIntr as ti

from time import sleep

@tc.canvasApp # wrapper that initialises the terminal and passes the canvas to you
def main(cnv):
	root=tui.Root(
		cnv,
		tui.HStack(
			tui.Text("Familliar?")
				.align(alignV="middle",alignH="middle")
				.expand(expandH=16,expandV=5)
				.alter({
					"bcolor":lambda chr,x,y: 233
				}),
			tui.VStack(
				tui.Text("\b[162]                \n                \b[default]"),
				tui.Text("\b[91]                \b[default]"),
				tui.Text("\b[20]                \n                \b[default]")
			)
		).align(alignH="middle",alignV="middle")
	)
	root.frames.schedule(0,tui.sched.framesLater)
	next(trm.keys()) 