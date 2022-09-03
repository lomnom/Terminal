import TermUI as tui
import TermCanvas as tc
import Terminal as trm

@tc.canvasApp
def main(cnv):
	root=tui.Root(
		cnv,
		tui.VStack(
			tui.Squisher(
				tui.Box(
					tui.Text("*_HELLO WORLD_*"),
					tui.Lines.double
				),
				squishX=15,
				squishY=7
			),
			tui.Squisher(
				tui.Box(
					tui.Text("Lmao"),
					tui.Lines.thin
				),
				squishX=13,
				squishY=3
			)
		)
	)
	root.render()
	cnv.render()
	keyIter=trm.keys()
	next(keyIter)