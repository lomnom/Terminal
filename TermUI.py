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

def lagCallback(frames,lag):
	# raise ValueError(f"Lagging! ({lag=}s behind)")
	pass #modify

class NoFrame: #returned from frame callback to signal that no render needed
	pass

class Frames:
	def __init__(self,fps,root,resize=True):
		self.stopwatch=trm.Stopwatch()
		self.fps=fps
		self.running=True
		self.frame=1
		self.requested={}
		self.root=root
		trm.sizereceivers[hash(self)]=lambda r,c: self.schedule(1,sched.framesLater)

	shouldRender=lambda *args: None  

	@property
	def delay(self):
		return 1/self.fps

	def schedule(self,value,variety,callback=None): #add conditional frame
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
		else:
			callbacks.append(self.shouldRender)

	def run(self):
		self.stopwatch.start()

		while self.running and not tc.DIED:
			lag=False
			try:
				#pray all same-frame schedules happen here.
				sleep(self.delay*self.frame-self.stopwatch.time())
			except ValueError:
				lagCallback(self,self.stopwatch.time()-self.delay*self.frame) #Called on lag
				lag=self.stopwatch.time()-self.delay*self.frame
			if self.frame in self.requested:
				callbacks=self.requested[self.frame]
				result=False
				for callback in callbacks:
					result=result or (callback(self) is not NoFrame)
				if result:
					if lag:
						self.root.render(debugText=f"Lagging! ({round(lag*100000)/100}ms behind)")
					else:
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

smallArrows=['↑','↓','→','←']
filledArrows=['▲','▼','►','◄']

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

	def whatChild(self,x,y,h,w): #Iterator -> (child, (x,y,h,w))
		raise NotImplementedError

# parent class of all containers with multiple children
class MultiContainer(Container): # children have to implement render()
	children=None
	def setChild(self,child,index):  # (Element,index), where index is position of child
		if not (index<=len(self.children) or index<0):
			self.disownChild(self.children[index])
		return self.insertChild(child,index)

	def insertChild(self,child,index): # (Element, int) -> int (-1 as index appends)
		if index<=len(self.children) and index>=0:
			self.children.insert(index,child)
			child.adopted(self)
			return index
		else:
			self.children.append(child)
			child.adopted(self)
			return len(self.children)-1

	updateChild=setChild

	def disownChild(self,child):
		child.disowned()
		self.children.remove(child)
		return child

	def addChild(self,child):
		return self.insertChild(child,-1)

	def __len__(self):
		return len(self.children)

class Generated:
	def size(self):
		return self.innards().size()

	def render(self,cnv,x,y,ph,pw):
		self.innards().render(cnv,x,y,ph,pw)

	def innards(self):
		raise NotImplementedError

class GenMultiContainer(Generated,MultiContainer):
	def whatChild(self,x,y,ph,pw):
		innards=self.innards()
		yield from innards.whatChild(x,y,ph,pw)

class GenContainer(Generated,Container):
	def whatChild(self,x,y,ph,pw):
		innards=self.innards()
		yield from innards.whatChild(x,y,ph,pw)

class GenElement(Generated,Element):
	pass

# actual elements

class ElementSwitcher(MultiContainer): # shows child no. self.visible
	def __init__(self,*children,visible=0):
		self.children=[]
		for index,child in enumerate(children):
			self.setChild(child,index)
		self.visible=visible

	def switchTo(self,index):
		self.visible=index

	def size(self):
		if self.visible is not None:
			return self.children[self.visible].size()
		else:
			return (0,0)

	def whatChild(self,x,y,h,w):
		if self.visible is not None:
			yield (self.children[self.visible],(x,y,h,w))

	def render(self,cnv,x,y,ph,pw):
		if self.visible is not None:
			self.children[self.visible].render(cnv,x,y,ph,pw)

	def disownChild(self,child): 
		super().disownChild(child)
		self.switchTo(self.visible)

	def switchTo(self,index):
		if len(self.children) and index is not None:
			self.visible=index%len(self.children)
		else:
			self.visible=None

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

	def whatChild(self,x,y,h,w):
		for child in self.children:
			yield (child,(x,y,h,w))

	def render(self,cnv,x,y,ph,pw):
		for child,alloc in self.whatChild(x,y,ph,pw):
			child.render(cnv,*alloc)

# class Alloc(MultiContainer): # percentages, absolutes and auto

# def VAlloc(*args,**kwargs):
# 	return Alloc('vertical',*args,**kwargs)

# def HAlloc(*args,**kwargs):
# 	return Alloc('horizontal',*args,**kwargs)

# add percentages

floor=lambda n: round(n-0.5)
class Stack(MultiContainer):
	def __init__(self,axis,*children):
		self.children=[]
		self.percentages={} #0-100
		assert(axis=="vertical" or axis=="horizontal")
		for index,child in enumerate(children):
			if type(child) is tuple:
				self.percentages[child[0]]=child[1]
				self.setChild(child[0],index)
			else:
				self.setChild(child,index)
		self.vertical=(axis=='vertical')

	def setPercentage(self,child):
		self.percentages[child]=percentage
		assert(sum(self.percentages.values)<=100)

	def getPercentage(self,child):
		try:
			return self.percentages[child]
		except KeyError:
			return -1 #child size

	def removePercentage(self,child):
		del self.percentages[child]

	def whatChild(self,x,y,ph=None,pw=None):
		sizes={}
		for child in self.children:
			sizes[child]=child.size()
		allocated=ph is not None and pw is not None
		if allocated:
			freeSpace=(ph if self.vertical else pw)-sum(
				[ sizes[child][not self.vertical] for child in sizes if child not in self.percentages]
			)
		else:
			freeSpace=0

		offset=0
		inaccuracy=0
		
		for child in self.children:
			if child not in self.percentages or not allocated:
				stacking=sizes[child][not self.vertical]
			else:
				stacking=((self.percentages[child]/100)*freeSpace)+inaccuracy
				if stacking>=sizes[child][not self.vertical]:
					inaccuracy+=stacking%1
					stacking=round(stacking)
				else:
					stacking=sizes[child][not self.vertical]
			if self.vertical:
				yield (child,(x,y+offset,stacking,sizes[child][1] if not allocated else pw))
			else:
				yield (child,(x+offset,y,sizes[child][0] if not allocated else ph,stacking))
			offset+=stacking

	def render(self,cnv,x,y,ph,pw):
		for child,alloc in self.whatChild(x,y,ph,pw):
			child.render(cnv,*alloc)

	def size(self): # rewrite to use whatChild
		height=0
		width=0
		for alloc in self.whatChild(0,0):
			if self.vertical:
				height+=alloc[1][2]
				if alloc[1][3]>width:
					width=alloc[1][3]
			else:
				width+=alloc[1][3]
				if alloc[1][2]>height:
					height=alloc[1][2]
		return (height,width)

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

	def render(self,debugText=None):
		self.canvas.clear()
		self.child.render(self.canvas,0,0,trm.rows,trm.columns)
		if debugText:
			self.canvas.cursor.goto(0,len(self.canvas.matrix)-1)
			self.canvas.print(debugText)
		self.canvas.render()

class Expander(Container): # Expand child to set size
	# (Element,expandH=int (horiz confine),expandV=int (vert confine))
	def __init__(self,child,expandH=None,expandV=None):
		self.setChild(child)
		self.expandH=expandH
		self.expandV=expandV

	def size(self):
		ch,cw=self.child.size()
		return ((ch if (not self.expandV) else self.expandV),
		        (cw if (not self.expandH) else self.expandH))


	def whatChild(self,x,y,ph,pw):
		yield (self.child,(x,y,
			(ph if (not self.expandV) else self.expandV),
		    (pw if (not self.expandH) else self.expandH))
		)

	def render(self,cnv,x,y,ph,pw):
		for child,alloc in self.whatChild(x,y,ph,pw):
			child.render(
				cnv,*alloc
			)

# any element can have expand called on it to wrap in expander
# Element.expand(expandH=int,expandV=int) -> Expander(Element)
Element.extensions['expand']=lambda self: lambda *args,**kwargs: Expander(self,*args,**kwargs)

class Padding(Container): # adds padding to allocated space
	def __init__(self,child,top=0,bottom=0,left=0,right=0):
		self.setChild(child)
		self.top,self.bottom,self.left,self.right=top,bottom,left,right

	def whatChild(self,x,y,ph,pw):
		yield (self.child,(
			x+self.left,y+self.top,
			ph-(self.top+self.bottom),pw-(self.left+self.right)
		))

	def render(self,cnv,x,y,ph,pw):
		for child,alloc in self.whatChild(x,y,ph,pw):
			child.render(
				cnv,*alloc
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
	def __init__(self,child,lines,style="",label=None,labelPos="left",greedy=False): 
		self.setChild(child)
		self.line=lines
		self.label=label
		self.style=style
		self.labelPos=labelPos
		self.greedy=greedy

	def size(self):
		ch,cw=self.child.size()
		return (ch+2,cw+2)

	def whatChild(self,x,y,ph,pw):
		yield (self.child,x+1,y+1,ph-2,pw-2)

	def render(self,cnv,x,y,ph,pw):
		if self.greedy:
			rh,rw=ph,pw
		else:
			rh,rw=self.child.size()
			rh+=2
			rw+=2
		self.child.render(cnv,x+1,y+1,ph-2,pw-2)
		cnv.cursor.goto(x,y)
		cnv.sprint(self.style)
		cnv.print(self.line.tl)
		cnv.line(self.line.h,rw-2)
		cnv.print(self.line.tr)
		cnv.cursor.goto(x,y+1)
		cnv.line(self.line.v,rh-2,inc=(0,1))
		cnv.print(self.line.bl)
		cnv.line(self.line.h,rw-2)
		cnv.print(self.line.br,inc=(0,-1))
		cnv.line(self.line.v,rh-2,inc=(0,-1))
		if self.label:
			if self.labelPos=="left":
				cnv.cursor.goto(x+1,y)
			elif self.labelPos=="right":
				cnv.cursor.goto(x+cw-len(self.label) -1,y)
			elif self.labelPos=="middle":
				cnv.cursor.goto(int(x+(cw-len(self.label))/2 ),y)
			cnv.print(self.line.tr)
			cnv.cursor.nostyle()
			cnv.sprint(self.label,opaque=True)
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

	def whatChild(self,x,y,ph,pw):
		ch,cw=self.child.size()
		if self.alignH:
			if self.alignH=="right":
				x+=pw-cw
			elif self.alignH=="middle":
				x+=(pw-cw)//2
			else:
				raise ValueError(f"Invalid align ({self.alignH})")
		if self.alignV:
			if self.alignV=="bottom":
				y+=ph-ch
			elif self.alignV=="middle":
				y+=(ph-ch)//2
			else:
				raise ValueError(f"Invalid align ({self.alignV})")
		try:
			assert(ph>=ch)
			assert(pw>=cw)
		except:
			raise AssertionError(str(type(self.child))+str((ph>=ch,pw>=cw,ph,pw,ch,cw,self.size())))
		yield (self.child,(x,y,(ch if self.alignV else ph),(cw if self.alignH else pw)))

	def render(self,cnv,x,y,ph,pw):
		for child,alloc in self.whatChild(x,y,ph,pw):
			child.render(
				cnv,*alloc
			)

Element.extensions['align']=lambda self: lambda *args,**kwargs: Aligner(self,*args,**kwargs)

class Wrapper(Container):
	def __init__(self,child,visible=True):
		self.setChild(child)
		self.visible=visible

	def render(self,*args):
		self.visible and self.child.render(*args)

	def whatChild(self,x,y,h,w):
		yield (self.child,(x,y,h,w))

	def size(self):
		if self.visible:
			return self.child.size()
		else:
			return (0,0)

Element.extensions['wrap']=lambda self: lambda *args,**kwargs: Wrapper(self,*args,**kwargs)

circles="○◔◑◕●"
class FrameRoller(Element):
	def __init__(self):
		self.count=0

	def size(self):
		return (1,1)

	def render(self,cnv,x,y,ph,pw):
		cnv.cursor.goto(x,y)
		cnv.print(circles[self.count%len(circles)])
		self.count+=1

class BarTheme:
	def __init__(self,full,start,end):
		self.full=full
		self.start=start
		self.end=end

class bars:
	horizbar=BarTheme(
		tc.Char(gradients.horizbar[-1]),
		list(map(lambda char: tc.Char(char,flags={'r'}),gradients.horizbar[1:-1]))[::-1],
		list(map(lambda char: tc.Char(char),gradients.horizbar[1:-1]))
	)
	vertbar=BarTheme(
		tc.Char(gradients.vertbar[-1]),
		list(map(lambda char: tc.Char(char),gradients.vertbar[1:-1])),
		list(map(lambda char: tc.Char(char,flags={'r'}),gradients.vertbar[1:-1]))[::-1]
	)
	block=BarTheme(
		tc.Char(gradients.block[-1]),
		list(map(lambda char: tc.Char(char),gradients.block[1:-1]))[::-1],
		list(map(lambda char: tc.Char(char),gradients.block[1:-1]))
	)

floor=lambda n: round(n-0.5)
ceil=lambda n: round(n+0.5)
def snip(n,k):
	v=n%k
	if v==0:
		if n-k > 0:
			return (k,n-k)
		else:
			return (0,0)
	else:
		return (v,n-v)

class Bar(Element): #top to bottom, left to right
	def __init__(self,chars,start,end,orientation="horizontal"): #start and end percentages from 0-1
		self.v=(orientation=="vertical")
		self.start=start
		self.end=end
		self.chars=chars

	def size(self):
		return (1,1)

	def findBar(self,percent,gradient,full):
		choices=len(gradient)
		index=round(percent*choices)
		if index!=choices:
			return gradient[index]
		else:
			return full

	def render(self,cnv,x,y,ph,pw):
		size=(ph if self.v else pw)
		step=(int(not self.v),int(self.v))
		start,frontSpace=snip(size*self.start,1)
		start=1-start
		start=self.findBar(start,self.chars.start,self.chars.full)
		end,backSpace=snip(size*self.end,1)
		end=self.findBar(end,self.chars.end,self.chars.full)
		middle=backSpace-(frontSpace+1)

		cnv.cursor.goto(x,y)
		cnv.cursor+=[step[0]*int(frontSpace),step[1]*int(frontSpace)]
		cnv.cursor.putCh(start,cnv)
		cnv.cursor+=step
		for _ in range(int(middle)):
			cnv.cursor.putCh(self.chars.full,cnv)
			cnv.cursor+=step
		cnv.cursor.putCh(end,cnv)

upperbound=lambda a,b: b if a>b else a
lowerbound=lambda a,b: b if a<b else a 

#cx and cy point to the child character rendered at the top left conner
class Scroller(Container):
	def __init__(self,child,cx=0,cy=0):
		self.setChild(child)
		self.cx=cx
		self.cy=cy
		self.ph=1
		self.pw=1
		self.buffer=tc.Canvas(1,1)
		self.buffer.cursor=tc.BoundedCursor(0,0,0,0, 0,0)

	def getView(self):
		ch,cw=self.child.size()
		if cw-self.pw <= 0:
			cx=0
		else:
			cx=self.cx%(cw-self.pw)
		if ch-self.ph <= 0:
			cy=0
		else:
			cy=self.cy%(ch-self.ph)
		return (cx,cy,upperbound(ch-cy,self.ph),upperbound(cw-cx,self.pw),ch,cw)

	def render(self,cnv,x,y,ph,pw):
		ch,cw=self.child.size()
		self.buffer.resize(ch,cw)
		self.buffer.clear()

		#assigning bounded values to the position to get rid of jitter is disgusting but
		#neccessary
		if cw-pw <= 0: self.cx=0
		else: self.cx=self.cx%(cw-pw) 
		if ch-ph <= 0: self.cy=0
		else: self.cy=self.cy%(ch-ph)

		rh=upperbound(ch-self.cy,ph)
		rw=upperbound(cw-self.cx,pw)
		cursor=self.buffer.cursor
		cursor.limx=self.cx
		cursor.limy=self.cy
		cursor.limh=rh
		cursor.limw=rw
		self.child.render(self.buffer,0,0,ch,cw)
		
		self.ph=ph # issue: the size will always be one frame behind
		self.pw=pw
		self.buffer.renderGlass(cnv,x,y,rh,rw,self.cx,self.cy,filler=tc.Char(cnv.filler))

	def whatChild(self,x,y,h,w):
		ch,cw=self.child.size()
		yield (self.child,(x-self.cx,y-self.cy,ch,cw))

	def size(self):
		return (0,0)

class ScrollBox(GenContainer): # [up,down,left,right] AND [vertical,horizontal]
	def __init__(self,child,style=[False,True,True,False],cx=0,cy=0,axes=[True,True]):
		self.scroller=Scroller(child,cx=0,cy=0)
		self.setChild(self.scroller)
		self.vertBar=Bar(bars.vertbar,0,0,"vertical")
		self.horizBar=Bar(bars.horizbar,0,0,"horizontal")
		self.style=style
		self.axes=axes

	def innards(self):
		if self.axes!=[True,True]:
			ch,cw=self.scroller.child.size()
		stack=VStack(
			*([self.horizBar] if self.style[0] else []),
			(HStack(
				*([self.vertBar] if self.style[2] else []),
				(
					self.scroller
						.expand(
							expandH=(None if self.axes[1] else cw),
							expandV=(None if self.axes[0] else ch)
						)
				,100),
				*([self.vertBar] if self.style[3] else [])
			),100),
			*([self.horizBar] if self.style[1] else [])
		)
		return stack

	def render(self,cnv,x,y,ph,pw):
		ch,cw=self.scroller.child.size()
		if self.axes[0]:
			self.scroller.ph=ph-self.style[0]-self.style[1]
		else:
			self.scroller.ph=ch
		if self.axes[1]:
			self.scroller.pw=pw-self.style[2]-self.style[3]
		else:
			self.scroller.pw=cw
		cx,cy,vh,vw,ch,cw=self.scroller.getView()
		self.vertBar.start=cy/ch
		self.vertBar.end=(cy+vh)/ch
		self.horizBar.start=cx/cw
		self.horizBar.end=(cx+vw)/cw
		self.innards().render(cnv,x,y,ph,pw)

class Text(Element): # just text
	def __init__(self,text,inc=(1,0),raw=False,opaque=False):
		self.raw=raw
		self._inc=inc
		self.text=text
		self.opaque=opaque

	@property
	def text(self):
		return self._text

	def updateSize(self):
		if not self.raw:
			self._size=tc.ssize(self.text,inc=self.inc)
		else:
			text=self.text.split("\n")
			self._size=(len(text),max([len(line) for line in text]))
		self.touched=False

	@text.setter
	def text(self,value):
		self._text=value
		self.touched=True

	@property
	def inc(self):
		return self._inc

	@inc.setter
	def inc(self,value):
		self._inc=value
		self.touched=True

	def size(self):
		if self.touched:
			self.updateSize()
		return self._size

	def render(self,cnv,x,y,ph,pw):
		cnv.cursor.goto(x,y)
		self.raw or cnv.sprint(self.text,inc=self.inc,opaque=self.opaque) and cnv.cursor.nostyle()
		self.raw and cnv.print(self.text,inc=self.inc)

class Seperator(Element):
	def __init__(self,orientation,character,style=None):
		self.v= orientation=='vertical'
		self.character=character
		self.style=style

	def render(self,cnv,x,y,ph,pw):
		cnv.cursor.goto(x,y)
		self.style and cnv.sprint(self.style)
		if self.v:
			cnv.line(self.character,ph,inc=(0,1))
		else:
			cnv.line(self.character,pw)
		self.style and cnv.sprint(self.style)

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

	def whatChild(self,x,y,h,w):
		yield (self.child,(x,y,h,w))

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