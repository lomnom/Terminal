import TermUI as tui
import TermCanvas as tc
import Terminal as trm

line=tui.Lines

@tc.canvasApp
def main(cnv):
	keyText=tui.Text("\f[green]Type stuff\f[default]")
	root=tui.Root(
		cnv,
		tui.ZStack(
			tui.HAlloc(
				(
					tui.VAlloc(
						(
							tui.Text("*_HELLO WORLD_*")
								.box(line.double),
						"7"),
						(
							tui.Text("_*ctrl+z* to quit btw_")
								.box(line.thick)
								.pad(top=1,left=2,bottom=1,right=3),
						"40%")
					),
				"50%"),
				(
					tui.Text("^Lmao^")
						.box(line.thin)
						.squish(squishV=10),
				"5"),
				(
					tui.Nothing(),
				"12"),
				(
					keyText
						.box(line.thin)
						.squish(squishV=3),
				"50%")
			),
			tui.Text("\f[cyan]_*:)*_\f[default]")
				.squish(squishH=2,squishV=1)
				.align(alignH="right",alignV="bottom")
		).box(line.thin)
		 .squish(squishH=70,squishV=30)
		 .align(alignH="middle",alignV="middle")

	)
	root.render()

	keyIter=trm.keys()
	while True:
		key=next(keyIter)
		if key=='ctrl z':
			return
		keyText.text=f"\f[green]You pressed: *{key}*\f[default]"
		root.render()