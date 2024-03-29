import TermUI as tui
import TermCanvas as tc
import Terminal as trm
import TermIntr as ti
from threading import Lock as lock

@tc.canvasApp # wrapper that initialises the terminal and passes the canvas to you
def main(cnv):
	quitlock=lock()
	quitlock.acquire()
	quitButton=ti.Button("quit","q")
	@quitButton.onToggle
	def onPress(*_):
		quitlock.release()

	root=tui.Root(
		cnv,
		tui.VStack(
			quitButton
		).align(alignH="middle",alignV="middle")
	)

	intrRoot=ti.IntrRoot(
		root.frames,
		quitButton
	)
	root.frames.schedule(0,tui.sched.framesLater)

	quitlock.acquire()