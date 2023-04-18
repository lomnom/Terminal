import TermUI as tui
import TermCanvas as tc
import Terminal as trm
import TermIntr as ti
from threading import Lock as lock

@tc.canvasApp # wrapper that initialises the terminal and passes the canvas to you
def main(cnv):
	quitlock=lock()
	quitlock.acquire()
	quitButton=ti.Button("Press q to quit","q")
	@quitButton.onPress
	def onPress(*_):
		quitlock.release()

	colours=[
		"FFFFFF",
		"000000",
		"FF0000"
		"d60270",
		"c90574",
		"bb0977",
		"ae0c7a",
		"a0107e",
		"931382",
		"861685",
		"781a88",
		"6b1d8c",
		"5e2090",
		"502493",
		"432796",
		"362a9a",
		"282e9e",
		"1b31a1",
		"0d35a4",
		"0038a8"
	]

	root=tui.Root(
		cnv,
		tui.VStack(
			quitButton,
			tui.Text(" ".join(f"\b[#{colour}]  \b[.]" for colour in colours))
		).align(alignH="middle",alignV="middle")
	)

	intrRoot=ti.IntrRoot(quitButton,root.frames)
	root.frames.schedule(0,tui.sched.framesLater)
	quitlock.acquire()