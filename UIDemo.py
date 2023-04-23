import TermUI as tui
import TermCanvas as tc
import Terminal as trm
import TermIntr as ti
from threading import Lock as lock

from time import sleep

class List(tui.GenContainer,tui.MultiContainer):
	def __init__(self,*children,padding=0):
		self.children=[]
		self.padding=padding
		for index,child in enumerate(children):
			self.setChild(child,index)

	def innards(self):
		return tui.VStack(*[
			tui.HStack(
				tui.Text(str(index+1)+'.').pad(right=1),
				child
			).pad(bottom=self.padding) for index,child in enumerate(self.children)
		])

class Priority(tui.GenContainer):
	def __init__(self,name,visual):
		self.name=name
		self.visual=visual

	def innards(self):
		return tui.HStack(
			self.name
				.align(alignV="middle",alignH="middle")
				.expand(expandH=16,expandV=5)
				.alter({
					"bcolor":lambda chr,x,y: 233
				}),
			self.visual
				.align(alignV="middle",alignH="middle")
				.expand(expandH=14,expandV=3)
				.box(tui.lines.curvy)
		).alter({
			"bcolor":lambda chr,x,y: 233
		})

priorityList=List(padding=1)

def addPriority(name,visual,insert):
	priorityList.insertChild(
		Priority(
			tui.Text(name),
			tui.Text(visual)
		)
	,insert)	

addPriority(
	"Code",
	"*7* files\n"
	"\f[green]*594*\f[.] additions\n"
	"\f[red]*497*\f[.] deletions",
	-1
)

priorityInputs=ti.Group(
	(visual:= ti.Textbox('ctrl v') ),
	(name:= ti.Textbox('ctrl n') ),
	(index:= ti.Roller(["Add new"],0,"horizontal") ),
	(create:= ti.Button(tui.Text("Press c to create!"),'c') )
)

priorities=priorityList.children
def updateIndexes():
	index.values=["Add New",*range(1,len(priorities)+1)]
updateIndexes()

@create.onToggle
def onCreate(_):
	position=index.value
	if position=="Add New":
		position=-1
	else:
		position-=1

	addPriority(name.text,visual.text,position)
	name.text=""
	visual.text=""
	updateIndexes()

@tc.canvasApp # wrapper that initialises the terminal and passes the canvas to you
def main(cnv):
	quitlock=lock()
	quitlock.acquire()
	quitButton=ti.Button(
		tui.Text("Press q to quit")
	,"q")
	@quitButton.onToggle
	def onPress(*_):
		quitlock.release()

	root=tui.Root(
		cnv,
		tui.VStack(
			tui.Text("*_My priorities_*"),
			priorityList,
			tui.Box(
				tui.VStack(
					tui.HStack(tui.Text("*Name:* "),name),
					tui.HStack(tui.Text("*Visual:* "),visual),
					tui.HStack(tui.Text("*Insert at:* "),index),
					create
				).pad(left=1,right=1),
			tui.lines.thin,
			label="*Create a priority*"),
			quitButton
		).align(alignH="middle",alignV="middle")
	)

	intrRoot=ti.IntrRoot(root.frames,ti.Group(quitButton,priorityInputs))
	root.frames.schedule(0,tui.sched.framesLater)
	quitlock.acquire()