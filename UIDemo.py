import TermUI as tui
import TermCanvas as tc
import Terminal as trm
import TermIntr as ti
from time import sleep

@tc.canvasApp # wrapper that initialises the terminal and passes the canvas to you
def main(cnv):
	# Text formatting uses \f[foreground colour] and \b[background colour]
	slideNumber=tui.Text("")
	slides=tui.ElementSwitcher(
		tui.Text("\f[cyan]_*:)*_\f[default]"),
		tui.Text("\f[red]_*>:)*_\f[default]"),
		tui.Text("\f[blue]_`:(`_\f[default]"),
		tui.Text("\f[magenta]_:\\|_\f[default]")
	)
	poof=tui.Wrapper(
		tui.Text("bye")
	)
	def byebye(frames):
		poof.visible=not poof.visible
		root.frames.schedule(0.5,tui.sched.secondsLater,callback=byebye) # update what is shown on screen


	button=ti.Button("lmao","e")
	group1=ti.Group(button)
	group2=ti.Group()
	selector=ti.Selector(
		0,
		group1,
		group2,
	)

	root=tui.Root(
		cnv,
		tui.VStack(
			slideNumber
				.align(alignH="left",alignV="bottom"),
			slides,
			button
		),
	)

	root=ti.IntrRoot(selector,root.frames)

	byebye(root.frames)

	def switch(*_):
		slides.visible=(slides.visible+1) % len(slides.children)

	@button.onPress
	def onPress(*_):
		switch()

	root.frames.schedule(0,tui.sched.framesLater) # update what is shown on screen
	root.frames.schedule(5,tui.sched.secondsLater,callback=switch) # update what is shown on screen
	sleep(6)
	return

	keyIter=trm.keys() # key iterator, instantlty yields keys because canvasApp enabled raw()
