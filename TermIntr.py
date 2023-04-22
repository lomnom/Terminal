# UNSTABLE & TRASH

import TermUI as tui
import TermCanvas as tc
import Terminal as trm
from threading import Thread as thread
from time import sleep

class Interactive: 
	iparent=None
	enabled=False
	def root(self):
		parent=self.iparent
		while not type(parent) is IntrRoot:
			parent=parent.iparent
		return parent

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
		if self.enabling(child):
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
		for child in children:
			self.addIChild(child)
		self.focus=None
		self.thread=None
		self.alive=False
		self.delay=0.01
		self.frames=frames
		start and self.start()

	def passKey(self,key):
		return True

	def key(self,key):
		if not self.focus:
			if self.passKey(key):
				for child in self.children:
					if child.enabled:
						child.key(key)
		else:
			self.focus.key(key)

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

	class SelectorView(tui.Container):
		def __init__(self,child,iChild,key,selector,args):
			self.selector=selector
			self.setChild(child)
			self.iChild=iChild
			self.box=tui.Box(child,*args[0],**args[1])
			if self.box.label:
				self.box.label+=f" `({key})`"
			else:
				self.box.label=f"`({key})`"

		def whatChild(self,*args):
			return self.box.whatChild(*args)

		def render(self,cnv,x,y,ph,pw):
			if self.selector.selected==self.iChild:
				self.box.style=self.box.style.replace('`','')
				if '*' not in self.box.style:
					self.box.style+='*'
			else:
				self.box.style=self.box.style.replace('*','')
				if '`' not in self.box.style:
					self.box.style+='`'
			self.box.render(cnv,x,y,ph,pw)

		def size(self):
			h,w=self.child.size()
			return (h+2,w+2)

	def boxFor(self,iChild,child,*args,**kwargs):
		for key in self.keys:
			if self.keys[key]==iChild:
				break
		view=self.SelectorView(child,iChild,key,self,(args,kwargs))
		self.views.append(view)
		return view

class Button(IvEl,tui.Container): #super simple, please make your own
	def __init__(self,child,activator,activated=False,box=None,toggle=False):
		self.box=box
		self.child=child
		self.activator=activator
		self.activated=activated
		self._onToggle=None
		self.toggle=toggle #toggle button or press button

	def ui(self):
		return self.additions(
			tui.HStack(
				self.child,
				tui.Text(f"`({self.activator})`")
					.pad(left=1)
			)
		)

	def size(self):
		return self.ui().size()

	def whatChild(self,x,y,ph,pw):
		return (x,y,ph,pw)

	def key(self,key):
		if key==self.activator:
			self.activated=not self.activated
			self.root().frames.schedule(0,tui.sched.framesLater) 
			if self._onToggle:
				self._onToggle(self.activated)

			if not self.toggle:
				def deactivate(*_):
					self.activated=False
				self.root().frames.schedule(
					0.1,tui.sched.secondsLater,callback=deactivate
				)

	def onToggle(self,func):
		self._onToggle=func

	def render(self,cnv,x,y,ph,pw):
		self.ui().render(cnv,x,y,ph,pw)

class Textbox(IvEl,tui.Element):
	def __init__(self,text,cursor=0,box=None,enter="ctrl e"):
		self.box=box
		self.text=text
		self.typing=False
		self.enter=enter
		self._onPress=None
		self._onEnterExit=None
		self.textUI=tui.Text("")
		self.cursor=0
		self.updateTextUI()

	def updateTextUI(self):
		if self.text:
			if self.enabled:
				if not self.typing:
					enterText=f" `({self.enter} to type)`"
				else:
					enterText=f" `(exit w/{self.enter})`"
			else:
				enterText=""
			if self.cursor==len(self.text) or self.text[self.cursor]=="\n":
				self.textUI.text=self.text[:self.cursor]+"^*\\_*^"+self.text[self.cursor:]+enterText
			else:
				self.textUI.text=self.text[:self.cursor] +\
				"|"+self.text[self.cursor]+"|" +\
				self.text[self.cursor+1:]+enterText
		else:
			if self.enabled:
				if self.typing:
					self.textUI.text=f"`Press {self.enter} to escape...`"
				else:
					self.textUI.text=f"`Press {self.enter} to type...`"
			else:
				self.textUI.text="`Select to type...`"

	def size(self):
		return self.additions(self.textUI).size()

	def key(self,key):
		if key==self.enter:
			if self.typing:
				self.root().focus=None
			else:
				self.root().focus=self
			self.typing=not self.typing
			self.onEnterExit(self)
			self.updateTextUI()
			self.root().frames.schedule(0,tui.sched.framesLater) 
			return

		if not self.typing:
			return

		if key=="backspace":
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

		self.updateTextUI()
		self.root().frames.schedule(0,tui.sched.framesLater) 
		if self._onPress:
			self._onPress()

	def onPress(self,func):
		self._onPress=func

	def onEnterExit(self,func):
		self._onEnterExit=func

	def render(self,cnv,x,y,ph,pw):
		self.additions(self.textUI).render(cnv,x,y,ph,pw)

	def enable(self):
		self.enabled=True
		self.updateTextUI()

	def disable(self):
		self.enabled=False
		self.updateTextUI()