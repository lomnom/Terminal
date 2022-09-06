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
	thinD=LineSet('┄','┊','┌','┐','└','┘')
	thickD=LineSet('┅','┋','┏','┓','┗','┛')
	double=LineSet('═',"║","╔","╗","╚","╝")

class Element:
	index=None
	parent=None
	def size(self): # -> (rows,cols)
		return self.parent.allocSz(self)

	def render(self,cnv,x,y,mx,my): # (canvas,render x,render y,lim x,lim x) -> rendered sz (x,y) 
		raise NotImplementedError   # where lim and render are from allocated

	def pos(self): # -> (x,y)
		return self.parent.allocPos(self)

	def adopted(self,parent):
		self.parent=parent

	def disowned(self):
		self.parent=None

	extensions={}
	def __getattr__(self,attr):
		return self.extensions[attr](self)

class Container(Element):
	child=None
	def innerSize(self): # -> (rows,cols)
		return self.size()

	def setChild(self,child):
		if self.child is not None:
			self.child.disowned()
		self.child=child
		child.adopted(self)

	def disownChild(self,child):
		self.child.disowned()
		self.child=None

	def innerPos(self):
		return self.pos()

	def allocPos(self,child):
		assert(child is self.child)
		return self.innerPos()

	def allocSz(self,child):
		assert(child is self.child)
		return self.innerSize()

class MultiContainer(Container):
	children=None
	def setChild(self,child,index):
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

class AllocatedMContainer(MultiContainer):
	allocations=None
	fixed=0
	def setChild(self,child,allocation,index):
		if index<=len(self.children):
			self.allocations.append(allocation)
		else:
			if self.allocations[index][-1]!='%':
				self.fixed-=int(self.allocations[index])
			self.allocations[index]=allocation
		if allocation[-1]!='%':
			self.fixed+=int(allocation)
		return super().setChild(child,index)

	updateChild=setChild

	def disownChild(self,child):
		index=self.children.index(child)
		if self.allocations[index][-1]!='%':
			self.fixed-=int(self.allocations[index])
		self.allocations.pop(index)
		return super().disownChild(child)

	def calcAlloc(self):
		raise NotImplementedError

class Alloc(AllocatedMContainer):
	def __init__(self,orientation,*children):
		self.children=[]
		self.allocations=[]
		self.v= orientation=='vertical'
		for index,child in enumerate(children):
			self.setChild(child[0],child[1],index)

	def calcAlloc(self):
		ra,ca=self.parent.allocSz(self)
		alloced=ra if self.v else ca
		alloced=alloced-self.fixed
		offset=0
		allocs=[]
		for alloc in self.allocations:
			if alloc[-1]!='%':
				sz=int(alloc)
				allocs.append(sz)
			else:
				percent=float(alloc[:-1])
				sz=alloced*(percent/100)
				offset+=sz%1
				sz=int(sz)
				if offset>=1:
					sz+=1
					offset-=1
				allocs.append(sz)
		return allocs

	def allocPos(self,child):
		child=self.children.index(child)
		allocs=self.calcAlloc()[:child]
		px,py=self.parent.allocPos(self)
		return (px,py+sum(allocs)) if self.v else (px+sum(allocs),py)

	def allocSz(self,child):
		child=self.children.index(child)
		return (self.calcAlloc()[child],self.parent.allocSz(self)[1]) if self.v else \
		       (self.parent.allocSz(self)[0],self.calcAlloc()[child])

	def render(self,cnv,x,y,mx,my):
		allocs=self.calcAlloc()
		for index,child in enumerate(self.children):
			allocd=allocs[index]
			child.render(cnv,x,y,mx,allocd)
			if self.v: y+=allocd
			else: x+=allocd

def VAlloc(*args,**kwargs):
	return Alloc('vertical',*args,**kwargs)

def HAlloc(*args,**kwargs):
	return Alloc('horizontal',*args,**kwargs)

class Root(Container):
	def __init__(self,canvas,child):
		self.canvas=canvas
		self.setChild(child)

	def size(self):
		return (trm.rows,trm.columns)

	innerSize=size

	def render(self):
		self.child.render(self.canvas,0,0,trm.maxx,trm.maxy)

	def pos(self):
		return (0,0)

	innerPos=pos

class Squisher(Container):
	def __init__(self,child,squishX=None,squishY=None):
		self.setChild(child)
		self.squishX,self.squishY=squishX,squishY

	def size(self):
		ph,pw=self.parent.allocSz(self)
		return ((ph if not self.squishY else self.squishY+1),
		        (pw if not self.squishX else self.squishX+1))

	def render(self,cnv,x,y,mx,my):
		mr,mc=self.size()
		self.child.render(
			cnv,*self.parent.allocPos(self),
			mc-1,mr-1
		)

Element.extensions['squish']=lambda self: lambda *args,**kwargs: Squisher(self,*args,**kwargs)

class Box(Container):
	def __init__(self,child,lines):
		self.setChild(child)
		self.line=lines

	def innerSize(self):
		ph,pw=self.parent.allocSz(self)
		return (ph-2,pw-2)

	def innerPos(self):
		px,py=self.parent.allocPos(self)
		return (px+1,py+1)

	def render(self,cnv,x,y,mx,my):
		self.child.render(cnv,x+1,y+1,mx-2,my-2)
		cnv.cursor.goto(x,y)
		cnv.print(self.line.tl)
		cnv.line(self.line.h,mx-1)
		cnv.print(self.line.tr)
		cnv.cursor.goto(x,y+1)
		cnv.line(self.line.v,my-1,inc=(0,1))
		cnv.print(self.line.bl)
		cnv.line(self.line.h,mx-1)
		cnv.print(self.line.br,inc=(0,-1))
		cnv.line(self.line.v,my-1,inc=(0,-1))

class Aligner(Container):
	pass

class Text(Element):
	def __init__(self,text,raw=False):
		self.raw=raw
		self.text=text

	def size(self):
		lines=self.text.split("\n")
		return (len(lines),max(len(line) for line in lines))

	def render(self,cnv,x,y,mx,my):
		cnv.cursor.goto(x,y)
		self.raw or cnv.sprint(self.text)
		self.raw and cnv.print(self.text)