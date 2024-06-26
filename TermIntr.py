import TermUI as tui
import TermCanvas as tc
import Terminal as trm
from threading import Thread as thread
from time import sleep

class Interactive: 
	iparent=None
	enabled=False
	def root(self):
		return self.grandparent(IntrRoot)

	def grandparent(self,variant):
		parent=self.iparent
		try:
			while not type(parent) is variant:
				parent=parent.iparent
			return parent
		except AttributeError:
			return None

	def key(self,key):
		raise NotImplementedError

	def adopt(self,iparent):
		self.iparent=iparent

	def orphan(self):
		if self.enabled:
			self.disable()
		self.iparent=None

	def enable(self):
		self.enabled=True

	def disable(self):
		self.enabled=False

class IvContainer(Interactive):
	children=None
	def addIChild(self,child):
		child.adopt(self)
		self.children.append(child)
		if self.enabled and self.enabling(child):
			child.enable()

	def orphanIChild(self,child):
		self.children.pop(self.children.index(child))
		child.orphan()

	def key(self,key):
		if self.passKey(key):
			for child in self.children:
				if child.enabled:
					child.key(key)

	def passKey(self,key):
		raise NotImplementedError

	def disable(self):
		self.enabled=False
		for child in self.children:
			child.disable()

	def enabling(self,child):
		raise NotImplementedError

	def enable(self):
		self.enabled=True
		for child in self.children:
			if self.enabling(child):
				child.enable()

class IvEl(Interactive):
	activated=False
	box=None # tui.LineSet 
	dramaticDisable=False
	def shading(self,ui):
		if (not self.enabled) and self.dramaticDisable:
			ui=ui.alter({
					"flags":lambda char,x,y: char.flags | {'d'}
				})
		if self.activated:
			ui=ui.alter({
					"flags":lambda char,x,y: char.flags | {'r'}
				})
		return ui

	def border(self,ui): 
		if self.box:
			return ui.box(self.box)
		else:
			return ui

	def additions(self,ui):
		return self.shading(self.border(ui))

# actual stuff

class IntrRoot(IvContainer):
	def __init__(self,frames,*children,start=True):
		self.children=[]
		self.focus=[]
		self.thread=None
		self.alive=False
		self.delay=0.01
		self.enable()
		self.frames=frames
		for child in children:
			self.addIChild(child)
		start and self.start()

	def passKey(self,key):
		return True

	def setFocus(self,focus):
		self.focus.append(focus)

	def unFocus(self,focus):
		assert(self.focus[-1]==focus)
		self.focus.pop()

	def key(self,key):
		if not self.focus:
			if self.passKey(key):
				for child in self.children:
					if child.enabled:
						child.key(key)
		else:
			self.focus[-1].key(key)

	def enabling(self,child):
		return True

	def start(self):
		assert(self.thread is None)
		self.thread=thread(target=self.watch)
		self.thread.start()

	def stop(self):
		self.alive=False

	def watch(self):
		self.alive=True
		while self.alive and not tc.DIED:
			for key in trm.keys(leave=True):
				self.key(key)
			sleep(self.delay) 

class Group(IvContainer): #group of interactives
	def __init__(self,*children):
		self.children=[]
		for child in children:
			self.addIChild(child)

	def passKey(self,key):
		return True

	def enabling(self,child):
		return True

class Switcher(IvContainer):
	def __init__(self,selected,*children):
		self.children=[]
		for child in children:
			self.addIChild(child)
			child.disable()
		if selected is not None:
			self.selected=children[selected]
		else:
			self.selected=None

	def passKey(self,key):
		return True

	def select(self,index):
		if index is None or (not self.children):
			self.selected.disable()
			self.selected=None
			return
		index=index%len(self.children)
		if self.selected is not None:
			self.selected.disable()
		self.selected=self.children[index]
		self.selected.enable()

	def enabling(self,child):
		if child==self.selected:
			return True
		else:
			return False

	def orphanIChild(self,child):
		if self.selected is not None:
			index=self.children.index(self.selected)
		else:
			index=None
		super().orphanIChild(child)
		if index is not None:
			self.select(index)

class Nothing(Interactive):
	def __init__(self):
		pass

	def key(self,key):
		pass

class Listener(Interactive): #Listens to all keystrokes
	def __init__(self):
		self.handler=lambda: None

	def handle(self,handler):
		self.handler=handler

	def key(self,key):
		self.handler(key)

class Selector(IvContainer):
	def __init__(self,selected,*children):
		self.children=[]
		self.keys={}
		self.selected=children[selected][0]
		for child,key in children:
			self.addIChild(child)
			self.keys[key]=child
		self.views=[]

	def passKey(self,key):
		if key not in self.keys:
			return True
		else:
			self.selected.disable()
			self.selected=self.keys[key]
			self.selected.enable()
			if self.views:
				self.root().frames.schedule(0,tui.sched.framesLater) 
			return False

	def enabling(self,child):
		if child==self.selected:
			return True
		else:
			return False

	class SelectorView(tui.GenContainer):
		def __init__(self,child,iChild,key,selector,args):
			self.selector=selector
			self.setChild(child)
			self.iChild=iChild
			self.box=tui.Box(child,*args[0],**args[1])
			if self.box.label:
				self.box.label+=f" `({key})`"
			else:
				self.box.label=f"`({key})`"

		def innards(self):
			if self.selector.selected==self.iChild:
				self.box.style=self.box.style.replace('`','')
				if '*' not in self.box.style:
					self.box.style+='*'
			else:
				self.box.style=self.box.style.replace('*','')
				if '`' not in self.box.style:
					self.box.style+='`'
			return self.box

	def boxFor(self,iChild,child,*args,**kwargs):
		for key in self.keys:
			if self.keys[key]==iChild:
				break
		view=self.SelectorView(child,iChild,key,self,(args,kwargs))
		self.views.append(view)
		return view

class Button(IvEl,tui.GenContainer):
	def __init__(self,child,activator,activated=False,box=None,toggle=False):
		self.box=box
		if type(child) is str:
			child=tui.Text(f"Press {activator} to {child}!")
		self.child=child
		self.activator=activator
		self.activated=activated
		self._onToggle=None
		self.toggle=toggle #toggle button or press button

	def innards(self):
		return self.additions(
			tui.HStack(
				self.child,
				tui.Text(f"`({self.activator})`")
					.pad(left=1)
					.align(alignV="bottom")
			)
		)

	def key(self,key):
		if key==self.activator:
			self.activated=not self.activated
			self.root().frames.schedule(0,tui.sched.framesLater) 
			if not self.toggle:
				def deactivate(*_):
					self.activated=False
				self.root().frames.schedule(
					0.1,tui.sched.secondsLater,callback=deactivate
				)
			
			if self._onToggle:
				self._onToggle(self.activated)

	def onToggle(self,func):
		self._onToggle=func

	def onPress(self,func):
		self._onToggle=func

def asciify(string,exclude={'\b','\f','\n'}):
	result=""
	prev=0
	for index,char in enumerate(string):
		if (not 32<=ord(char)<=126) and (char not in exclude):
			result+=string[prev:index]
			prev=index+1
			result+=hex(ord(char))
	result+=string[prev:len(string)]
	return result

def styleless(string):
	return "\033"+string+"\033"

class Textbox(IvEl,tui.GenElement):
	def __init__(self,enter,cursor=0,box=None,text="",focusOnLone=False,formatters=None):
		self.box=box
		self.text=text
		self.typing=False
		self.enter=enter
		self._onPress=None
		self._onEnterExit=None
		self.focusOnLone=focusOnLone
		self.cursor=0
		if formatters is None:
			self.formatters=[]
		else:
			self.formatters=formatters

		self.display=None
		self.oldText=None

	def innards(self):
		textOut="This should never appear (ti.Textbox.innards)"
		self.cursor=self.cursor%(len(self.text)+1)
		if self.text:
			if self.typing:
				enterText=f" `(exit w/{self.enter})`"
				if self.cursor==len(self.text) or self.text[self.cursor]=="\n":
					textOut=self.text[:self.cursor]+"^*\\_*^"+self.text[self.cursor:]+enterText
				else:
					textOut=self.text[:self.cursor] +\
					"|"+self.text[self.cursor]+"|" +\
					self.text[self.cursor+1:]+enterText
			else:
				textOut=self.text+f" `(edit w/{self.enter})`"
		else:
			if self.enabled:
				if self.typing:
					textOut=f"`Press {self.enter} to escape...`"
				else:
					textOut=f"`Press {self.enter} to type...`"
			else:
				textOut="`Select to type...`"
		for formatter in self.formatters:
			textOut=formatter(textOut)

		if textOut==self.oldText:
			self.oldText=textOut
			return self.display
		else:
			self.oldText=textOut
			self.display=tui.Text(textOut)
			return self.display

	def setFocus(self,state):
		if state==self.typing:
			return
		if state:
			self.root().setFocus(self)
			self.typing=True
		else:
			self.root().unFocus(self)
			self.typing=False
		self.onEnterExit(self)
		self.root().frames.schedule(0,tui.sched.framesLater) 

	def key(self,key):
		if key==self.enter:
			self.setFocus(not self.typing)
			return

		if not self.typing:
			return

		if key=="backspace":
			if self.cursor!=0:
				self.text=self.text[:self.cursor-1]+self.text[self.cursor:]
				self.cursor-=1
		elif key=="right":
			self.cursor+=1
		elif key=="left":
			self.cursor-=1
		elif key=="down":
			self.cursor=len(self.text)
		elif key=="up":
			self.cursor=0
		else:
			if self.cursor==len(self.text):
				self.text+=key
			else:
				self.text=self.text[:self.cursor]+key+self.text[self.cursor:]
			self.cursor+=1
		self.cursor=self.cursor%(len(self.text)+1)

		self.root().frames.schedule(0,tui.sched.framesLater) 
		if self._onPress:
			self._onPress()

	def onPress(self,func):
		self._onPress=func

	def onEnterExit(self,func):
		self._onEnterExit=func

	def enable(self):
		self.enabled=True
		if self.focusOnLone:
			lone=True
			for child in self.iparent.children:
				if self.iparent.enabling(child) and not child==self:	
					lone=False
					break
			self.setFocus(lone)

class Roller(IvEl,tui.GenElement):
	def __init__(self,values,position,axis,up="up",down="down"):
		self.values=values
		self.position=position
		self.up=up
		self.vertical=(axis=="vertical")
		self.down=down
		self._onChange=lambda *args: None

	def onChange(self,onChange):
		self._onChange=onChange

	def key(self,key):
		if self.position is None:
			return
		if key==self.up:
			position=self.position+1
		elif key==self.down:
			position=self.position-1
		else:
			return
		self.setPosition(position)

	def removeIndex(self,index):
		self.values.pop(index)
		self.setPosition(self.position)

	def addValue(self,value):
		self.values.append(value) 

	def setPosition(self,position):
		if not self.values:
			self.position=None
		elif position is not None:
			self.position=position%len(self.values)
		self._onChange(self.position,self.value)
		self.root().frames.schedule(0,tui.sched.framesLater) 

	def innards(self):
		if self.vertical:
			return tui.VStack(
				tui.Text(f"^ `{self.up}`")
					.align(alignH="middle"),
				tui.Text(f"|{self.value}|")
					.align(alignH="middle"),
				tui.Text(f"v `{self.down}`")
					.align(alignH="middle")
			)
		else:
			return tui.Text(f"< `{self.down}` |{self.value}| `{self.up}` >")

	@property
	def value(self):
		if self.position is not None:
			return self.values[self.position]
		else:
			return "None"

#get all interactives in an element
def allInteractives(element):
	results=[]
	if isinstance(element,Interactive):
		results.append(element)
	if isinstance(element,tui.MultiContainer):
		for child in element.children:
			if isinstance(child,Interactive):
				results.append(child)
			else:
				results+=allInteractives(child)
	elif isinstance(element,tui.Container):
		results+=allInteractives(element.child)
	return results

# inputs=[up,down,left,right], none if unbound
def scrollerInput(scroller,frames,inputs=["up","down","left","right"]):
	listener=Listener()
	@listener.handle
	def pressed(key):
		if key==None:
			return
		if key==inputs[0]:
			scroller.cy-=1
		elif key==inputs[1]:
			scroller.cy+=1
		elif key==inputs[2]:
			scroller.cx-=1
		elif key==inputs[3]:
			scroller.cx+=1
		frames.schedule(1,tui.sched.framesLater) 
	return listener

tui.Element.extensions['interactives']=lambda self: lambda *args,**kwargs: allInteractives(self)