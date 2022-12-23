from TermUI import *

class Interactive:
	group=None
	parent=None

	def interact(self,key):
		raise NotImplementedError

	selectable=False
	def select(self):
		raise NotImplementedError(f"Selectable is set to {selectable}")

	def adopted(self,parent):
		self.parent=parent

class IntrGroup:
	def __init__(self,children):
		self.children=children
		for child in children:
			child.adopted(self)
