import TermUI as tui
import TermCanvas as tc
import Terminal as trm

@tc.canvasApp
def main(cnv):
	keyText=tui.Text("\f[green]Type stuff\f[default]")
	root=tui.Root(
		cnv,
		tui.HAlloc(
			(
				tui.Box(
					tui.Text("*_HELLO WORLD_*"),
					tui.Lines.double
				).squish(squishY=7),
			"50%"),
			(
				tui.Box(
					tui.Text("Lmao"),
					tui.Lines.thin
				).squish(squishY=30),
			"5"),
			(
				tui.Box(
					keyText,
					tui.Lines.thin
				).squish(squishY=3),
			"50%")
		)
	)
	root.render()
	cnv.render()
	keyIter=trm.keys()
	next(keyIter)