import TermCanvas as tc
import Terminal as trm

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

class Lines:
	thin=LineSet('─','│','┌','┐','└','┘')
	thick=LineSet('━','┃','┏','┓','┗','┛')
	dotted=LineSet('┄','┊','┌','┐','└','┘')
	fatDotted=LineSet('┅','┋','┏','┓','┗','┛')
	double=LineSet('═',"║","╔","╗","╚","╝")
	curvy=LineSet('─','│','╭','╮','╰','╯')

class Gradients:
	block=[" ","░","▒","▓","█"]
	horizbar=[" ","▏","▎","▍","▌","▋","▊","▉","█"]
	vertbar=[" ","▁","▂","▃","▄","▅","▆","▇","█"]

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
	index=None
	ridgid=True #Will not expand to fill space
	parent=None
	def size(self): # () -> (rows,cols)
		# return self.parent.allocSz(self)
		raise NotImplementedError("THIS IS NEEDED LOL")

	def render(self,cnv,x,y,h,w): # (canvas,render x,render y,allocHeight,width) -> None
		raise NotImplementedError 

	def pos(self): # -> (x,y)
		return self.parent.allocPos(self)

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
	def innerSize(self): # size of inner cavity. () -> (rows,cols)
		return self.size()

	def setChild(self,child):
		if self.child is not None:
			self.child.disowned()
		self.child=child
		child.adopted(self)

	def disownChild(self,child):
		self.child.disowned()
		self.child=None

	def innerPos(self): # start of inner cavity () -> (x,y)
		return self.pos()

	def allocPos(self,child): # position allocated to child (Element) -> (x,y)
		assert(child is self.child)
		return self.innerPos()

	def allocSz(self,child): # area allocated to child () -> (rows,cols)
		assert(child is self.child)
		return self.innerSize()

# parent class of all containers with multiple children
class MultiContainer(Container): # children have to implement allocPos, allocSz and render()
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

	def allocPos(self,child):
		raise NotImplementedError

	def allocSz(self,child):
		raise NotImplementedError

	def __len__(self):
		return len(self.children)

# parent class of all containers that have customisable element allocation 
class AllocatedMContainer(MultiContainer):
	allocations=None
	isVertical=None
	fixed=0 #concrete space constraint (all the allocations specified as absolute numbers)
	def setChild(self,child,allocation,index): # allocation can be in "int" or "float%"
		if index<=len(self.children):          
			self.allocations.append(allocation)
		else:
			if self.allocations[index][-1]!='%':
				self.fixed-=int(self.allocations[index])
			self.allocations[index]=allocation
		if allocation=='@':
			if self.isVertical:
				self.fixed+=child.size()[0]
			else:
				self.fixed+=child.size()[1]
		elif allocation[-1]!="%":
			self.fixed+=int(allocation)
		return super().setChild(child,index)

	updateChild=setChild

	def disownChild(self,child):
		index=self.children.index(child)
		if self.allocations[index][-1]!='%':
			self.fixed-=int(self.allocations[index])
		self.allocations.pop(index)
		return super().disownChild(child)

	def calcAlloc(self): # get allocated areas for all children () -> [int]
		raise NotImplementedError

class ElementSwitcher(MultiContainer): # shows child no. self.visible
	def __init__(self,*children,visible=0):
		self.children=[]
		for index,child in enumerate(children):
			self.setChild(child,index)
		self.visible=visible

	@property
	def ridgid(self):
		return self.children[self.visible].ridgid

	def allocPos(self,child):
		return self.parent.allocPos(self)

	def allocSz(self,child):
		return self.parent.allocSz(self)

	def size(self):
		return self.children[self.visible].size()

	def render(self,cnv,x,y,ph,pw):
		self.children[self.visible].render(cnv,x,y,ph,pw)

class ZStack(MultiContainer): # layers all children above each other
	def __init__(self,*children):
		self.children=[]
		for index,child in enumerate(children):
			self.setChild(child,index)

	def allocPos(self,child):
		return self.parent.allocPos(self)

	def allocSz(self,child):
		return self.parent.allocSz(self)

	def size(self):
		if self.ridgid:
			heightM,widthM=(0,0)
			for child in self.children:
				height,width=child.size()
				if height>heightM:
					heightM=height
				if width>widthM:
					widthM=width
			return (heightM,widthM)
		else:
			return (0,0)

	def render(self,cnv,x,y,ph,pw):
		for child in self.children:
			child.render(cnv,x,y,ph,pw)

	@property
	def ridgid(self):
		for child in self.children:
			if not child.ridgid:
				return False
		return True

class Alloc(AllocatedMContainer): # allocates all children in an axis
	def __init__(self,side,*children): # ("vertical"|"horizontal",*(Element,str) -> Alloc
		self.children=[]
		self.allocations=[]
		self.isVertical = (side=='vertical') #True if vertical, false if horizontal
		for index,child in enumerate(children):
			if type(child) is not tuple:
				self.setChild(child,"@",index)
			else:
				self.setChild(child[0],child[1],index)

	@property
	def ridgid(self):
		for child in self.children:
			if not child.ridgid:
				return False

		for allocation in self.allocations:
			if allocation[-1]=="%":
				return False

		return True

	def calcAlloc(self):
		rowsA,colsA=self.parent.allocSz(self)
		alloced=rowsA if self.isVertical else colsA
		alloced=alloced-self.fixed
		offset=0
		allocs=[]
		for index,alloc in enumerate(self.allocations):
			if alloc[-1]=='%':
				percent=float(alloc[:-1])
				size=alloced*(percent/100)
				offset+=size%1
				size=int(size)
				if offset>=1:
					size+=1
					offset-=1
				allocs.append(size)
			elif alloc=="@":
				child=self.children[index]
				if self.isVertical:
					allocs.append(child.size()[0])
				else:
					allocs.append(child.size()[1])
			else:
				size=int(alloc) #size allocated to element
				allocs.append(size)
		return allocs

	def allocPos(self,child):
		child=self.children.index(child)
		allocs=self.calcAlloc()[:child]
		px,py=self.parent.allocPos(self)
		return (px,py+sum(allocs)) if self.isVertical else (px+sum(allocs),py)

	def allocSz(self,child):
		child=self.children.index(child)
		return (self.calcAlloc()[child],self.parent.allocSz(self)[1]) if self.isVertical else \
		       (self.parent.allocSz(self)[0],self.calcAlloc()[child])

	def render(self,cnv,x,y,h,w):
		allocs=self.calcAlloc()
		for index,child in enumerate(self.children):
			allocd=allocs[index]
			if self.isVertical: 
				child.render(cnv,x,y,allocd,w)
				y+=allocd
			else: 
				child.render(cnv,x,y,h,allocd)
				x+=allocd

def VAlloc(*args,**kwargs):
	return Alloc('vertical',*args,**kwargs)

def HAlloc(*args,**kwargs):
	return Alloc('horizontal',*args,**kwargs)

class Root(Container): # container that is the grandparent of everything, projects onto canvas
	ridgid=True
	def __init__(self,canvas,child):
		self.canvas=canvas
		self.setChild(child)

	def size(self):
		return (trm.rows,trm.columns)

	innerSize=size

	def render(self):
		self.canvas.clear()
		self.child.render(self.canvas,0,0,trm.rows,trm.columns)
		self.canvas.render()

	def pos(self):
		return (0,0)

	innerPos=pos

class Expander(Container): # Expand child to set size
	# (Element,expandH=int (horiz confine),expandV=int (vert confine))
	def __init__(self,child,expandH=None,expandV=None):
		self.setChild(child)
		self.expandH=expandH
		self.expandV=expandV
		self.ridgid = child.ridgid or ((expandH is not None) and (expandV is not None))

	def size(self):
		ch,cw=self.child.size()
		return ((ch if not self.expandV else self.expandV),
		        (cw if not self.expandH else self.expandH))

	def innerSize(self):
		return self.size()

	def render(self,cnv,x,y,ph,pw):
		self.child.render(
			cnv,x,y,
			(ph if not self.expandV else self.expandV),
			(pw if not self.expandH else self.expandH)
		)

# any element can have expand called on it to wrap in expander
# Element.expand(expandH=int,expandV=int) -> Expander(Element)
Element.extensions['expand']=lambda self: lambda *args,**kwargs: Expander(self,*args,**kwargs)

class ExpandTo(Container):
	ridgid=False
	def __init__(self,child,destination,depth=0,horiz=True,vert=True,offX=0,offY=0):
		self.setChild(child)
		self.destination=destination
		self.depth=depth
		self.offX=offX
		self.offY=offY
		self.vert=vert
		self.horiz=horiz

	def fakeParent(self):
		depth=self.depth
		parent=self.parent
		fakeChild=self
		while parent:
			if (type(parent) == self.destination):
				if depth:
					depth-=1
				else:
					break
			fakeChild=parent
			parent=parent.parent
		if not parent:
			raise FileNotFoundError
		return (parent,fakeChild)

	def size(self):
		fakeParent,fakeChild=self.fakeParent()
		ph,pw=fakeParent.allocSz(fakeChild)
		ph+=self.offY
		pw+=self.offX
		ch,cw=self.child.size()
		return ((ch if not self.vert else ph),
		        (cw if not self.horiz else pw))

	def innerSize(self):
		return self.size()

	def render(self,cnv,x,y,ph,pw):
		self.child.render(
			cnv,x,y,
			*self.innerSize()
		)

Element.extensions['expandTo']=lambda self: lambda *args,**kwargs: ExpandTo(self,*args,**kwargs)

class Padding(Container): # adds padding to allocated space
	def __init__(self,child,top=0,bottom=0,left=0,right=0):
		self.setChild(child)
		self.top,self.bottom,self.left,self.right=top,bottom,left,right

	def innerSize(self):
		ph,pw=self.parent.allocSz(self)
		return (ph-(self.top+self.bottom),pw-(self.left+self.right))

	def innerPos(self):
		px,py=self.parent.allocPos(self)
		return (px+self.left,py+self.top)

	def render(self,cnv,x,y,ph,pw):
		self.child.render(
			cnv,*self.innerPos(),
			ph-(self.top+self.bottom),pw-(self.left+self.right)
		)

	def size(self):
		height,width=self.child.size()
		return (height+self.top+self.bottom,width+self.left+self.right)

	@property
	def ridgid(self):
		return self.child.ridgid

Element.extensions['pad']=lambda self: lambda *args,**kwargs: Padding(self,*args,**kwargs)

class Nothing(Element):
	ridgid=True
	def __init__(self,height=0,width=0):
		pass

	def render(self,*_):
		pass

	def size():
		return (self.height,self.width)

class Box(Container): # adds box around child, style can be all special formatting, eg '*^'
	# (Element, LineSet, style=str, label=str)
	def __init__(self,child,lines,style="",label=None,labelPos="left"): 
		self.setChild(child)
		self.line=lines
		self.label=label
		self.style=style
		self.labelPos=labelPos

	def innerSize(self):
		ph,pw=self.parent.allocSz(self)
		return (ph-2,pw-2)

	def innerPos(self):
		px,py=self.parent.allocPos(self)
		return (px+1,py+1)

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
	ridgid=False
	def __init__(self,child,alignH=None,alignV=False):
		assert(child.ridgid)
		self.setChild(child)
		self.alignH=alignH
		self.alignV=alignV

	def innerPos(self):
		ch,cw=self.child.size()
		xs,ys=self.pos()
		sh,sw=self.parent.allocSz(self)
		if self.alignH:
			if self.alignH=="right":
				xs+=sw-cw
			elif self.alignH=="middle":
				xs+=(sw-cw)//2
		if self.alignV:
			if self.alignV=="bottom":
				ys+=sh-ch
			elif self.alignV=="middle":
				ys+=(sh-ch)//2
		return (xs,ys)

	def size(self):
		height,width=(0,0)
		ch,cw=self.child.size()
		if not self.alignH:
			width=cw
		if not self.alignV:
			height=ch
		return (height,width)

	def render(self,cnv,x,y,ph,pw):
		ch,cw=self.child.size()
		self.child.render(cnv,*self.innerPos(),ph,pw)

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
	ridgid=True
	def __init__(self,text,inc=(1,0),raw=False):
		self.raw=raw
		self.text=text
		self.inc=inc

	def size(self):
		return tc.ssize(self.text,inc=self.inc)

	def render(self,cnv,x,y,ph,pw):
		cnv.cursor.goto(x,y)
		self.raw or cnv.sprint(self.text,inc=self.inc)
		self.raw and cnv.print(self.text,inc=self.inc)

class Seperator(Element):
	ridgid=False
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
	def __init__(self,canvas,height,width,x=0,y=0): #x and y are canvas coordinates of rendered top left
		self.canvas=canvas
		self.x=x
		self.y=y
		self.height=height
		self.width=width

	def size(self):
		return (self.height,self.width)

	def render(self,cnv,x,y,ph,pw):
		self.canvas.render(cnv,x,y,self.height,self.width,self.x,self.y)

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