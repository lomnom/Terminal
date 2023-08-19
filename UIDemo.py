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
		if self.children:
			return tui.VStack(*[
				tui.HStack(
					tui.Text(str(index+1)+'.').pad(right=1),
					child
				).pad(bottom=self.padding) for index,child in enumerate(self.children)
			])
		else:
			return tui.Text("`(Empty list)`")

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
	"\f[green]*3905*\f[.] additions\n"
	"\f[red]*1984*\f[.] deletions",
	-1
)

priorityInputs=ti.Group(
	(visual:= ti.Textbox('ctrl v') ),
	(name:= ti.Textbox('ctrl n') ),
	(index:= ti.Roller(["Add new"],0,"horizontal") ),
	(create:= ti.Button("create",'c') )
)

deleteInputs=ti.Group(
	index,
	(deleter:= ti.Button("delete",'d') )
)

selector=ti.Selector(0,
	(priorityInputs,"C"),
	(deleteInputs,"D")
)

priorities=priorityList.children
def updateIndexes():
	index.values=["Add New",*range(1,len(priorities)+1)]
	index.position%=len(index.values)
updateIndexes()

@create.onToggle
def onCreate(_):
	if not name.text+visual.text:
		return
	position=index.value
	if position=="Add New":
		position=-1
	else:
		position-=1

	addPriority(name.text,visual.text,position)
	name.text=""
	visual.text=""
	updateIndexes()

@deleter.onToggle
def onDelete(_):
	position=index.value
	if position=="Add New":
		position=-1
	else:
		position-=1
	priorityList.disownChild(priorityList.children[position])
	updateIndexes()

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
			tui.Text("*_My priorities_*"),
			priorityList,
			selector.boxFor(priorityInputs,
				tui.VStack(
					tui.HStack(tui.Text("*Name:* "),name),
					tui.HStack(tui.Text("*Visual:* "),visual),
					tui.HStack(tui.Text("*Insert at:* "),index),
					create
				).pad(left=1,right=1),
				tui.lines.thin,label="*Create a priority*"
			),
			selector.boxFor(deleteInputs,
				tui.VStack(
					tui.HStack(tui.Text("*Delete at:* "),index),
					deleter
				).pad(left=1,right=1),
				tui.lines.thin,label="*Remove a priority*"
			),
			quitButton,
			tui.Text("\f[232]\b[10]L\b[11]B\b[9]X\b[13]V\b[12]R\b[14]K\b\f[.]")
		).align(alignH="middle",alignV="middle")
	)

	intrRoot=ti.IntrRoot(root.frames,ti.Group(quitButton,selector))
	root.frames.schedule(0,tui.sched.framesLater)
	quitlock.acquire()