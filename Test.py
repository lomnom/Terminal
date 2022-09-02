import TermUI as tui
import TermCanvas as tc
import Terminal as trm

@tc.canvasApp
def main(cnv):
	root=tui.Root(
		cnv,
		tui.Squisher(
			tui.Box(
				tui.Text("*_HELLO WORLD_*"),
				tui.Lines.double
			),
			squishX=15,
			squishY=7
		)
	)
	root.render()
	cnv.render()
	keyIter=trm.keys()
	next(keyIter)