import TermUI as tui
import TermCanvas as tc
import Terminal as trm
from threading import Thread as thread
from time import sleep

class Interactive: 
	iparent=None

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
		self.iparent=None

class IntrRoot(Interactive):
	def __init__(self,child,frames,start=True):
		self.adopt(self)
		child.adopt(self)
		self.child=child
		self.thread=None
		self.alive=False
		self.delay=0.01
		self.frames=frames
		start and self.start()

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

	def key(self,key):
		self.child.key(key)

class Group(Interactive): #group of interactives
	def __init__(self,*children):
		self.children=[]
		for child in children:
			self.addChild(child)

	def key(self,key):
		for child in self.children:
			child.key(key)

	def addChild(self,child):
		child.adopt(self)
		self.children.append(child)

class Selector(Interactive):
	def __init__(self,selected,*children):
		self.children=[]
		for child in children:
			self.addChild(child)
		self.selected=selected

	def key(self,key):
		self.children[self.selected].key(key)

	def addChild(self,child):
		child.adopt(self)
		self.children.append(child)

class ToggleButton(Interactive,tui.Element): #super simple, please make your own
	def __init__(self,text,activator,activated=False):
		self.text=text+f" `({activator})`"
		self.activator=activator
		self.activated=activated
		self._onToggle=None
		self.updateTextUI()

	def updateTextUI(self):
		if self.activated:
			self.textUI=tui.Text("%"+self.text+"%")
		else:
			self.textUI=tui.Text(self.text)

	def size(self):
		return self.textUI.size()

	def key(self,key):
		if key==self.activator:
			self.activated=not self.activated
			self.updateTextUI()
			self.root().frames.schedule(0,tui.sched.framesLater) 
			if self._onToggle:
				self._onToggle(self.activated)

	def onToggle(self,func):
		self._onToggle=func

	def render(self,cnv,x,y,ph,pw):
		self.textUI.render(cnv,x,y,ph,pw)

class Button(Interactive,tui.Element):
	def __init__(self,text,activator):
		self.text=text+f" `({activator})`"
		self.activator=activator
		self._onPress=None
		self.activated=False
		self.updateTextUI()

	def updateTextUI(self):
		if self.activated:
			self.textUI=tui.Text("%"+self.text+"%")
		else:
			self.textUI=tui.Text(self.text)

	def size(self):
		return self.textUI.size()

	def key(self,key):
		if key==self.activator:
			self.activated=True
			self.updateTextUI()
			self.root().frames.schedule(0,tui.sched.framesLater) 
			self.root().frames.schedule(
				0.1,tui.sched.secondsLater,callback=lambda *args: self.updateTextUI()
			)
			if self._onPress:
				self._onPress()

	def onPress(self,func):
		self._onPress=func

	def render(self,cnv,x,y,ph,pw):
		self.textUI.render(cnv,x,y,ph,pw)
		self.activated=False