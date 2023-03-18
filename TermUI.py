import TermCanvas as tc
import Terminal as trm
from time import sleep
from threading import Thread as thread

#top bottom left right
#vertical, horizontal
class LineSet:
	def __init__(self,h,v,tl,tr,bl,br):
		self.h=h
		self.v=v
		self.tr=tr
		self.tl=tl
		self.br=br
		self.bl=bl

class sched:
	secondsLater=0
	framesLater=1
	frame=2

class Frames:
	def __init__(self,fps,root):
		self.stopwatch=trm.Stopwatch()
		self.fps=fps
		self.running=True
		self.frame=1
		self.requested={}
		self.root=root

	@property
	def delay(self):
		return 1/self.fps

	def schedule(self,value,variety,callback=None):
		frame=None
		if variety==sched.secondsLater:
			frame=self.frame+value*self.fps
		elif variety==sched.framesLater:
			frame=self.frame+value
		elif variety==sched.frame:
			frame=value
		else:
			raise ValueError("Invalid schedule variety")

		if frame not in self.requested:
			self.requested[frame]=[]

		callbacks=self.requested[frame]
		if callback:
			callbacks.append(callback)

	def run(self):
		self.stopwatch.start()

		while self.running and not tc.DIED:
			sleep(self.delay*self.frame-self.stopwatch.time())
			if self.frame in self.requested:
				callbacks=self.requested[self.frame]
				for callback in callbacks:
					callback(self)
				self.root.render()
				del self.requested[self.frame]
			self.frame+=1

		self.running=False
		self.stopwatch.stop()

	def start(self):
		self.thread=thread(target=self.run)
		self.thread.start()

	def stop(self):
		self.running=False

class lines:
	thin=LineSet('─','│','┌','┐','└','┘')
	thick=LineSet('━','┃','┏','┓','┗','┛')
	dotted=LineSet('┄','┊','┌','┐','└','┘')
	fatDotted=LineSet('┅','┋','┏','┓','┗','┛')
	double=LineSet('═',"║","╔","╗","╚","╝")
	curvy=LineSet('─','│','╭','╮','╰','╯')

class gradients:
	block=[" ","░","▒","▓","█"]
	horizbar=[" ","▏","▎","▍","▌","▋","▊","▉","█"]
	vertbar=[" ","▁","▂","▃","▄","▅","▆","▇","█"]

class block:
	topLeft=0b1000
	topRight=0b0100
	bottomLeft=0b0010
	bottomRight=0b0001

blocks={
	# 0bXXXX
	#   |||^bottomRight
	#   ||^bottomLeft
	#   |^topRight
	#   ^topLeft
	0b0010:"▖",
	0b0001:"▗",
	0b1000:"▘",
	0b0100:"▝",
	0b1011:"▙",
	0b1001:"▚",
	0b0110:"▞",
	0b1110:"▛",
	0b1101:"▜",
	0b0111:"▟",
	0b1100:"▀",
	0b0011:"▄",
	0b1010:"▌",
	0b0101:"▐",
	0b1111:"█",
	0b0000:" "
}

# parent class of all elements
class Element: # children must implement render
	parent=None

	def size(self): # () -> (rows,cols), None for any value of unsure (or return minimum)
		raise NotImplementedError(f"THIS IS NEEDED LOL (type {type(self)} has no size function) ")

	def render(self,cnv,x,y,h,w): # (canvas,render x,render y,allocHeight,width) -> None
		raise NotImplementedError 

	def adopted(self,parent): # called when parent set
		self.parent=parent

	def disowned(self): # called when removed
		self.parent=None

	extensions={}
	def __getattr__(self,attr):
		return self.extensions[attr](self)

# parent class of all containers
class Container(Element): # children only have to implement render()
	child=None
	def setChild(self,child):
		if self.child is not None:
			self.child.disowned()
		self.child=child
		child.adopted(self)

	def disownChild(self,child):
		self.child.disowned()
		self.child=None

# parent class of all containers with multiple children
class MultiContainer(Container): # children have to implement render()
	children=None
	def setChild(self,child,index):  # (Element,index), where index is position of child
		if index<=len(self.children):
			self.children.append(child)
		else:
			self.children[index]=child
		child.adopted(self)

	updateChild=setChild

	def disownChild(self,child):
		child.disowned()
		self.children.remove(child)
		return child

	def __len__(self):
		return len(self.children)

class ElementSwitcher(MultiContainer): # shows child no. self.visible
	def __init__(self,*children,visible=0):
		self.children=[]
		for index,child in enumerate(children):
			self.setChild(child,index)
		self.visible=visible

	def size(self):
		return self.children[self.visible].size()

	def render(self,cnv,x,y,ph,pw):
		self.children[self.visible].render(cnv,x,y,ph,pw)

class ZStack(MultiContainer): # layers all children above each other
	def __init__(self,*children):
		self.children=[]
		for index,child in enumerate(children):
			self.setChild(child,index)

	def size(self):
		heightM,widthM=(0,0)
		for child in self.children:
			height,width=child.size()
			if height==None or (height>heightM and heightM!=None):
				heightM=height
			if width==None or (width>widthM and widthM!=None):
				widthM=width
		return (heightM,widthM)

	def render(self,cnv,x,y,ph,pw):
		for child in self.children:
			child.render(cnv,x,y,ph,pw)

# class Alloc(MultiContainer): # percentages, absolutes and auto

# def VAlloc(*args,**kwargs):
# 	return Alloc('vertical',*args,**kwargs)

# def HAlloc(*args,**kwargs):
# 	return Alloc('horizontal',*args,**kwargs)

class Stack(MultiContainer):
	def __init__(self,axis,*children):
		self.children=[]
		assert(axis=="vertical" or axis=="horizontal")
		for index,child in enumerate(children):
			self.setChild(child,index)
		self.vertical=(axis=='vertical')

	def render(self,cnv,x,y,ph,pw):
		offset=0
		if self.vertical:
			for child in self.children:
				height=child.size()[0]
				child.render(cnv,x,y+offset,height,pw)
				offset+=height
		else:
			for child in self.children:
				width=child.size()[1]
				child.render(cnv,x+offset,y,ph,width)
				offset+=width

	def size(self):
		stacked=0
		if self.vertical:
			maxWidth=0
			for child in self.children:
				childSize=child.size()
				stacked+=childSize[0]
				if childSize[1]>maxWidth:
					maxWidth=childSize[1]
			return (stacked,maxWidth)
		else:
			maxHeight=0
			for child in self.children:
				childSize=child.size()
				stacked+=childSize[1]
				if childSize[0]>maxHeight:
					maxHeight=childSize[0]
			return (maxHeight,stacked)

def VStack(*args,**kwargs):
	return Stack('vertical',*args,**kwargs)

def HStack(*args,**kwargs):
	return Stack('horizontal',*args,**kwargs)

class Root(Container): # container that is the grandparent of everything, projects onto canvas
	def __init__(self,canvas,child,fps=30,run=True):
		self.canvas=canvas
		self.setChild(child)
		self.frames=Frames(fps,self)
		run and self.run()

	def run(self):
		self.frames.start()

	def size(self):
		return (trm.rows,trm.columns)

	def render(self):
		self.canvas.clear()
		self.child.render(self.canvas,0,0,trm.rows,trm.columns)
		self.canvas.render()

class Expander(Container): # Expand child to set size
	# (Element,expandH=int (horiz confine),expandV=int (vert confine))
	def __init__(self,child,expandH=None,expandV=None):
		self.setChild(child)
		self.expandH=expandH
		self.expandV=expandV

	def size(self):
		ch,cw=self.child.size()
		return ((ch if not self.expandV else self.expandV),
		        (cw if not self.expandH else self.expandH))

	def render(self,cnv,x,y,ph,pw):
		self.child.render(
			cnv,x,y,
			(ph if not self.expandV else self.expandV),
			(pw if not self.expandH else self.expandH)
		)

# any element can have expand called on it to wrap in expander
# Element.expand(expandH=int,expandV=int) -> Expander(Element)
Element.extensions['expand']=lambda self: lambda *args,**kwargs: Expander(self,*args,**kwargs)

class Padding(Container): # adds padding to allocated space
	def __init__(self,child,top=0,bottom=0,left=0,right=0):
		self.setChild(child)
		self.top,self.bottom,self.left,self.right=top,bottom,left,right

	def render(self,cnv,x,y,ph,pw):
		self.child.render(
			cnv,x+self.left,y+self.top,
			ph-(self.top+self.bottom),pw-(self.left+self.right)
		)

	def size(self):
		height,width=self.child.size()
		return (height+self.top+self.bottom,width+self.left+self.right)

Element.extensions['pad']=lambda self: lambda *args,**kwargs: Padding(self,*args,**kwargs)

class Nothing(Element):
	def __init__(self,height=0,width=0):
		self.height=height
		self.width=width

	def render(self,*_):
		pass

	def size(self):
		return (self.height,self.width)

class Box(Container): # adds box around child, style can be all special formatting, eg '*^'
	# (Element, LineSet, style=str, label=str)
	def __init__(self,child,lines,style="",label=None,labelPos="left"): 
		self.setChild(child)
		self.line=lines
		self.label=label
		self.style=style
		self.labelPos=labelPos

	def size(self):
		ch,cw=self.child.size()
		return (ch+2,cw+2)

	def render(self,cnv,x,y,ph,pw):
		self.child.render(cnv,x+1,y+1,ph-2,pw-2)
		ch,cw=self.child.size()
		cnv.cursor.goto(x,y)
		cnv.sprint(self.style)
		cnv.print(self.line.tl)
		cnv.line(self.line.h,cw)
		cnv.print(self.line.tr)
		cnv.cursor.goto(x,y+1)
		cnv.line(self.line.v,ch,inc=(0,1))
		cnv.print(self.line.bl)
		cnv.line(self.line.h,cw)
		cnv.print(self.line.br,inc=(0,-1))
		cnv.line(self.line.v,ch,inc=(0,-1))
		if self.label:
			if self.labelPos=="left":
				cnv.cursor.goto(x+1,y)
			elif self.labelPos=="right":
				cnv.cursor.goto(x+cw-len(self.label) -1,y)
			elif self.labelPos=="middle":
				cnv.cursor.goto(int(x+(cw-len(self.label))/2 ),y)
			cnv.print(self.line.tr)
			cnv.cursor.nostyle()
			cnv.sprint(self.label)
			cnv.sprint(self.style)
			cnv.print(self.line.tl)
		cnv.cursor.nostyle()

Element.extensions['box']=lambda self: lambda *args,**kwargs: Box(self,*args,**kwargs)

class Aligner(Container): # aligns child, (Element,alignH="right"|"middle",alignV="bottom"|'middle')
	def __init__(self,child,alignH=None,alignV=False):
		self.setChild(child)
		self.alignH=alignH
		self.alignV=alignV

	def size(self): #minimum size
		return self.child.size()

	def render(self,cnv,x,y,ph,pw):
		ch,cw=self.child.size()
		if self.alignH:
			if self.alignH=="right":
				x+=pw-cw
			elif self.alignH=="middle":
				x+=(pw-cw)//2
		if self.alignV:
			if self.alignV=="bottom":
				y+=ph-ch
			elif self.alignV=="middle":
				y+=(ph-ch)//2
		assert(ph>=ch)
		assert(pw>=cw)
		self.child.render(cnv,x,y,ch,cw)

Element.extensions['align']=lambda self: lambda *args,**kwargs: Aligner(self,*args,**kwargs)

class Wrapper(Container):
	def __init__(self,child,visible=True):
		self.setChild(child)
		self.visible=visible

	def render(self,*args):
		self.visible and self.child.render(*args)

	def size(self):
		if self.visible:
			return self.child.size()
		else:
			return (0,0)

Element.extensions['wrap']=lambda self: lambda *args,**kwargs: Wrapper(self,*args,**kwargs)

class Text(Element): # just text
	def __init__(self,text,inc=(1,0),raw=False):
		self.raw=raw
		self._inc=inc
		self.text=text

	@property
	def text(self):
		return self._text

	def updateSize(self):
		self._size=tc.ssize(self.text,inc=self.inc)

	@text.setter
	def text(self,value):
		self._text=value
		self.updateSize()

	@property
	def inc(self):
		return self._inc

	@inc.setter
	def inc(self,value):
		self._inc=value
		self.updateSize()

	def size(self):
		return self._size

	def render(self,cnv,x,y,ph,pw):
		cnv.cursor.goto(x,y)
		self.raw or cnv.sprint(self.text,inc=self.inc)
		self.raw and cnv.print(self.text,inc=self.inc)

class Seperator(Element):
	def __init__(self,orientation,character):
		self.v= orientation=='vertical'
		self.character=character

	def render(self,cnv,x,y,ph,pw):
		cnv.cursor.goto(x,y)
		if self.v:
			cnv.line(self.character,ph,inc=(0,1))
		else:
			cnv.line(self.character,pw)

	def size(self):
		return (0,1) if self.v else (1,0)

class CanvasDisplay(Element):
	def __init__(
		self,canvas,x=0,y=0,function="render"
	): #x and y are canvas coordinates of rendered top left
		self.canvas=canvas
		self.x=x
		self.y=y
		self.function=function

	def size(self):
		return (0,0)

	def render(self,cnv,x,y,ph,pw):
		getattr(self.canvas,self.function)(cnv,x,y,ph,pw,self.x,self.y)

class Mutate(Container): #Run a function on every character
	def __init__(self,trans,child,before=True):
		self.trans=trans #the function
		self.setChild(child)
		self.before=before

	def size(self):
		return self.child.size()

	def render(self,cnv,x,y,ph,pw):
		self.before and self.child.render(cnv,x,y,ph,pw)
		ch,cw=self.child.size()
		for chrY in range(y,y+ch):
			for chrX in range(x,x+cw):
				self.trans(cnv.matrix[chrY][chrX],chrX,chrY)
		self.before or self.child.render(cnv,x,y,ph,pw)

def multiAlter(obj,alterations,args=()):
	for alteration in alterations:
		value=alterations[alteration]
		setattr(obj,alteration,value(obj,*args))

Element.extensions['alter']=lambda self: lambda alterations,**kwargs: Mutate(
	lambda obj,x,y: multiAlter(obj,alterations,args=(x,y),**kwargs),self
)