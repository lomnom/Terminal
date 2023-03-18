import TermUI as tui
import TermCanvas as tc
import Terminal as trm
import TermIntr as ti
from threading import Lock as lock

from time import sleep

@tc.canvasApp # wrapper that initialises the terminal and passes the canvas to you
def main(cnv):
	quitlock=lock()
	quitlock.acquire()
	quitButton=ti.Button("Press q\nto quit","q")
	@quitButton.onPress
	def onPress(*_):
		quitlock.release()

	root=tui.Root(
		cnv,
		tui.VStack(
			tui.Text("*_My priorities_*")
				.pad(bottom=1),

			tui.HStack(
				tui.Text("1.")
					.pad(right=2),
				tui.Text("Coding")
					.align(alignV="middle",alignH="middle")
					.expand(expandH=16,expandV=5)
					.alter({
						"bcolor":lambda chr,x,y: 233
					}),
				tui.Text(
					"*7* files\n"
					"\f[green]*594*\f[default] additions\n"
					"\f[red]*497*\f[default] deletions"
				)
					.align(alignV="middle",alignH="middle")
					.expand(expandH=14,expandV=3)
					.box(tui.lines.curvy)
					.alter({
						"bcolor":lambda chr,x,y: 233
					}),
			).pad(bottom=1),

			tui.HStack(
				tui.Text("2.")
					.pad(right=2),
				tui.Text("Reading \nfanfiction")
					.align(alignV="middle",alignH="middle")
					.expand(expandH=16,expandV=5)
					.alter({
						"bcolor":lambda chr,x,y: 233
					}),
				tui.VStack(
					tui.Text("\b[162]                \n                \b[default]"),
					tui.Text("\b[91]                \b[default]"),
					tui.Text("\b[20]                \n                \b[default]")
				),
			).pad(bottom=1),

			tui.HStack(
				tui.Text("∞.")
					.pad(right=2),
				tui.Text("Doing\nhomework")
					.align(alignV="middle",alignH="middle")
					.expand(expandH=16,expandV=5)
					.alter({
						"bcolor":lambda chr,x,y: 233
					}),
				quitButton
					.expand(expandH=14,expandV=3)
					.box(tui.lines.curvy)
					.alter({
						"bcolor":lambda chr,x,y: 233
					}),
			),
		).align(alignH="middle",alignV="middle")
	)

	intrRoot=ti.IntrRoot(quitButton,root.frames)
	root.frames.schedule(0,tui.sched.framesLater)
	quitlock.acquire()