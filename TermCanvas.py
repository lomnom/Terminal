import Terminal as term
from uuid import uuid4 as uuid

fg={
	"red":"31",
	"green":"32",
	"yellow":"33",
	"blue":"34",
	"magenta":"35",
	"cyan":"36",
	"default":"39"
}
bg={
	"red":"41",
	"green":"42",
	"yellow":"43",
	"blue":"44",
	"magenta":"45",
	"cyan":"46",
	"default":"49"
}

def fromRgb(rgb):
	return (((rgb>>16) & 255),((rgb>>8) & 255),(rgb & 255))

class Colors:
	blank=4
	rgb=3
	xterm=1
	retro=0

class Retro:
	red=1
	green=2
	yellow=3
	blue=4
	magenta=5
	cyan=6

	@staticmethod
	def bg(color):
		return color+4

class Color:
	def __init__(self,rgb=None,xterm=None,retro=None):
		if rgb is not None:
			if type(rgb)==tuple:
				self.r,self.g,self.b=rgb
				return
			if type(rgb) is str:
				rgb=int(rgb,16)
			self.r,self.g,self.b=fromRgb(rgb)
			self.type=Colors.rgb
		elif xterm is not None:
			self.xterm=xterm
			self.type=Colors.xterm
		elif retro is not None:
			self.retro=retro
			self.type=Colors.retro
		else:
			self.type=Colors.blank

bold="1"
dim="2"
resetweight="22"

class _Diff:
	def __init__(self,original,fcolor="",bcolor="",bold=None,dim=None):
		self.fcolor=fcolor
		self.bcolor=bcolor
		self.bold=bold
		self.dim=dim
		self.original=original
	def __str__(self):
		nums=[]
		if self.fcolor:
			nums+=[fg[self.fcolor]]
		if self.bcolor:
			nums+=[bg[self.bcolor]]
		if (self.bold==False) or (self.dim==False):
			nums+=[resetweight]
			if self.original.bold and self.bold:
				nums+=[bold]
			if self.original.dim and self.dim:
				nums+=[dim]
		else:
			if self.bold==True:
				nums+=[bold]
			if self.dim==True:
				nums+=[dim]
		return ("\033["+(";".join(nums))+"m" if nums else "")

class Char:
	def __init__(self,char,fcolor="default",bcolor="default",bold=False,dim=False):
		assert(fcolor in fg)
		assert(bcolor in bg)
		assert(len(char)==1)
		self.char=char
		self.fcolor=fcolor
		self.bcolor=bcolor
		self.bold=bold
		self.dim=dim

	def __str__(self):
		return "\033["+fg[self.fcolor]+";"+bg[self.bcolor]+\
		       (";"+bold if self.bold else "")+(";"+dim if self.dim else "")+"m"+self.char

	def __sub__(self,other): 
		return _Diff(
			self,
			fcolor=(other.fcolor if other.fcolor!=self.fcolor else ""),
			bcolor=(other.bcolor if other.bcolor!=self.bcolor else ""),
			bold=(other.bold if other.bold!=self.bold else None),
			dim=(other.dim if other.dim!=self.dim else None)
		)

class Cursor:
	def __init__(self,x,y,fcolor="default",bcolor="default",bold=False,dim=False):
		self.x=x
		self.y=y
		self.bound()
		self.fcolor=fcolor
		self.bcolor=bcolor
		self.bold=bold
		self.dim=dim

	def bound(self):
		self.x=self.x%term.columns
		self.y=self.y%term.rows

	def nostyle(self):
		self.fcolor="default"
		self.bcolor="default"
		self.bold=False
		self.dim=False

	def addCh(self,char,term):
		term.matrix[self.y][self.x]=Char(
			char,
			fcolor=self.fcolor,
			bcolor=self.bcolor,
			bold=self.bold,
			dim=self.dim
		)

	def __add__(self,other):
		self.x+=other[0]
		self.y+=other[1]
		self.bound()
		return self

	def __sub__(self,other):
		self.x-=other[0]
		self.y-=other[1]
		self.bound()
		return self

	def goto(self,x,y):
		self.x=x
		self.y=y
		self.bound()

class Terminal:
	def __init__(self):
		self.matrix=[]
		self.id=uuid()
		term.sizereceivers[self.id]=self.resize
		self.filler=" "
		self.resize(term.rows,term.columns)
		self.cursor=Cursor(0,0)

	def clear(self):
		for row in range(term.rows):
			for col in range(term.columns):
				self.matrix[row][col]=Char(" ")

	def __del__(self):
		del term.sizereceivers[self.id]

	def resize(self,rows,cols):
		if rows>len(self.matrix):
			for _ in range(rows-len(self.matrix)):
				self.matrix+=[[]]
				for _ in range(term.columns):
					self.matrix[-1]+=[Char(self.filler)]
		else:
			self.matrix=self.matrix[:rows]

		if cols>len(self.matrix[0]):
			for col in range(len(self.matrix)):
				for _ in range(cols-len(self.matrix[col])):
					self.matrix[col]+=[Char(self.filler)]
		else:
			for row in range(len(self.matrix)):
				self.matrix[row]=self.matrix[row][:cols]

	def _render(self):
		prev=None
		res=""
		for row in self.matrix:
			for char in row:
				if prev==None:
					res+=str(char)
				else:
					res+=str(prev-char)+char.char
				prev=char
			res+="\n"
		res=res[:-1]+term.homecursor
		return res

	def render(self):
		term.fprint(self._render())

	def print(self,data,inc=(1,0)):
		pos=0
		while not pos==(len(data)-1):
			self.cursor.addCh(data[pos],self)
			self.cursor+=inc
			pos+=1

	def sprint(self,data,inc=(1,0)): #aaAAAAAAA
		pos=0
		proccessFg=False
		proccessBg=False
		escaped=False
		while not pos>=len(data):
			if data[pos]=="\\":
				escaped=True
				pos+=1
				continue
			elif not escaped:
				if data[:2]=="\f\b" or data[:2]=="\b\f":
					pos+=2
					proccessFg=True
					proccessBg=True
					continue
				elif data[pos]=="\f":
					pos+=1
					proccessFg=True
					continue
				elif data[pos]=="\b":
					pos+=1
					proccessBg=True
					continue
				elif data[pos]=="*":
					self.cursor.bold=not self.cursor.bold
					pos+=1
					continue
				elif data[pos]=="^":
					self.cursor.dim=not self.cursor.dim
					pos+=1
					continue
				elif data[pos]=="\n":
					self.cursor.y+=1
					self.cursor.x=0
					self.cursor.bound()
					pos+=1
					continue
			else:
				escaped=False

			if proccessBg or proccessFg:
				if data[pos]=="[":
					pos+=1
					split=data[pos:].split("]")
					if len(split)<=1:
						pos-=1
						continue
					else:
						if proccessFg:
							assert(split[0] in fg) #make sure color in \f[] is valid
							self.cursor.fcolor=split[0]
						if proccessBg:
							assert(split[0] in bg) #make sure color in \b[] is valid
							self.cursor.bcolor=split[0]
						pos+=len(split[0])+1
						proccessFg=False
						proccessBg=False
						continue

			self.cursor.addCh(data[pos],self)
			self.cursor+=inc
			pos+=1