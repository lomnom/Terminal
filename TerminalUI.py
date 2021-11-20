import terminal as term
from uuid import uuid4 as uuid

fg={
	"red":31,
	"green":32,
	"yellow":33,
	"blue":34,
	"magenta":35,
	"cyan":36,
	"default":39
}
fg={
	"red":41
	"green":42
	"yellow":43
	"blue":44
	"magenta":45
	"cyan":46
	"default":49
}
bold=1
dim=2
resetweight=22

class Char:
	def __init__(char,fcolor="",bcolor="",bold=False,dim=False):
		assert(fcolor in fg)
		assert(bcolor in bg)
		assert(len(char)==1)

class Terminal:
	def __init__(self):
		self.matrix=[]
		self.id=uuid()
		term.sizereceivers[self.id]=self.resize

	def clear(self):
		for _ in range(term.rows):
			self.matrix+=[[]]
			for _ in range(term.columns):
				self.matrix[-1]+=[Char(" ")]

	def __del__(self):
		del term.sizereceivers[self.id]

	def resize(self,rows,cols):
		if rows>len(self.matrix):
			for _ in range(rows-len(self.matrix)):
				self.matrix+=[]
				for _ in range(term.columns):
					self.matrix[-1]+=[Char(" ")]
		else:
			self.matrix=self.matrix[:rows]

		if cols>len(self.matrix[0]):
			for col in range(len(self.matrix)):
				for _ in range(cols-len(self.matrix[col])):
					self.matrix[col]+=[Char(" ")]
		else:
			for row in range(len(self.matrix)):
				self.matrix[row]=self.matrix[row][:col]
