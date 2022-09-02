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
	parent=None
	flexible=False
	def size(self): # -> (rows,cols)
		raise NotImplementedError

	def render(self,cnv,x,y,mx,my): # (canvas,render x,render y,lim x,lim x) -> rendered sz (x,y) 
		raise NotImplementedError

	def pos(self): # -> (x,y)
		raise NotImplementedError

class Container(Element):
	child=None
	def innerSize(self): # -> (rows,cols)
		raise NotImplementedError

	def setChild(self,child):
		self.child=child
		child.parent=self

	def innerPos(self):
		raise NotImplementedError

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
		ph,pw=self.parent.innerSize()
		return ((ph if not self.squishY else self.squishY+1),
			    (pw if not self.squishX else self.squishX+1))

	innerSize=size

	def render(self,cnv,x,y,mx,my):
		ph,pw=self.parent.innerSize()
		self.child.render(
			cnv,*self.parent.innerPos(),
			(pw-1 if not self.squishX else self.squishX-1),
			(ph-1 if not self.squishY else self.squishY-1)
		)

	def pos(self):
		return self.parent.pos()

	innerPos=pos

class Box(Container):
	def __init__(self,child,lines):
		self.setChild(child)
		self.line=lines

	def size(self):
		return self.parent.innerSize()

	def innerSize(self):
		ph,pw=self.parent.innerSize()
		return (ph-2,pw-2)

	def pos(self):
		return self.parent.innerPos()

	def innerPos(self):
		px,py=self.parent.innerPos()
		return (px+1,py+1)

	def render(self,cnv,x,y,mx,my):
		self.child.render(cnv,x+1,y+1,mx-1,my-2)
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

import textwrap
class Text(Element):
	def __init__(self,text,raw=False):
		self.raw=raw
		self.text=text
		self.flexible=True

	def size(self):
		lines=self.text.split("\n")
		return (len(lines),max(len(line) for line in lines))

	def render(self,cnv,x,y,mx,my):
		cnv.cursor.goto(x,y)
		wrapped=textwrap.wrap(self.text,width=mx+1)
		wrapped=wrapped[:my]
		self.raw or cnv.sprint("\n".join(wrapped))
		self.raw and cnv.print("\n".join(wrapped))
		return (len(wrapped),max(len(line) for line in wrapped))