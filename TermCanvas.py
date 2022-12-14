import Terminal as term
from uuid import uuid4 as uuid

bold="1"
dim="2"
resetweight="22"

flags=[
	"b12*", #bold
	"d22`", #dim
	"i33_", #italic
	"u44|", #underline
	"f55^", #flashing
	"r77%", #inverse
	"h88", #hidden
	"s99~"  #strikethrough
]

h256colors={
	"black":"0",
	"red":"1",
	"green":"2",
	"yellow":"3",
	"blue":"4",
	"magenta":"5",
	"cyan":"6",
	"white":"7"
}

f2m={}
for item in flags:
	f2m[item[0]]=item[1:]
s2m={}
for item in flags:
	if len(item)==4:
		s2m[item[3]]=item[:-1]

class Char:
	def __init__(self,char,fcolor="default",bcolor="default",flags=None):
		assert(len(char)==1)
		self.char=char
		self.fcolor=fcolor
		self.bcolor=bcolor
		if flags is None:
			self.flags=set()
		else:
			self.flags=set(flags)

	def __str__(self):
		colors=(term.f256(self.fcolor) if not self.fcolor=="default" else term.fdefault) + \
		       (term.b256(self.bcolor) if not self.bcolor=="default" else term.bdefault)

		effects=""
		for flag in self.flags:
			effects+=f2m[flag][0]+";"
		effects=f"\033[{effects[:-1]}m"

		return colors+effects+self.char

	def __sub__(self,other): 
		nums=""
		for flag in other.flags:
			if flag not in self.flags:
				nums+=f2m[flag][0]+";"
		if self.fcolor != other.fcolor:
			nums+=f"38;5;{other.fcolor};" if not other.fcolor=="default" else "39;"
		if self.bcolor != other.bcolor:
			nums+=f"48;5;{other.bcolor};" if not other.bcolor=="default" else "49;"
		for flag in self.flags:
			if flag not in other.flags:
				nums+="2"+f2m[flag][1]+";"
				if flag in "bd":
					if 'b' in other.flags:
						nums+=f2m['b'][0]+";"
					elif 'd' in other.flags:
						nums+=f2m['d'][0]+";"

		return (f"\033[{nums[:-1]}m" if nums else "")

	def isNothing(self):
		return self.char==" " and ('r' not in self.flags) and ('u' not in self.flags)  \
		       and self.bcolor=="default"

class Cursor:
	def __init__(self,x,y,fcolor="default",bcolor="default",flags=None):
		self.x=x
		self.y=y
		self.bound()
		self.fcolor=fcolor
		self.bcolor=bcolor
		self.flags=flags
		if flags is None:
			self.flags=set()
		else:
			self.flags=set(flags)

	def bound(self):
		self.x=self.x%term.columns
		self.y=self.y%term.rows

	def nostyle(self):
		self.fcolor="default"
		self.bcolor="default"
		self.flags=set()

	def addCh(self,char,term):
		term.matrix[self.y][self.x]=Char(
			char,
			fcolor=self.fcolor,
			bcolor=self.bcolor,
			flags=self.flags.copy()
		)

	def putCh(self,char,term):
		term.matrix[self.y][self.x]=char

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

class FakeCursor(Cursor):
	def putCh(*_): pass
	def addCh(*_): pass

fakecursor=FakeCursor(0,0)

def sprint(data,cursor,cnv,inc=(1,0)):
	pos=0
	proccessFg=False
	proccessBg=False
	escaped=False
	height=1
	width=[0]
	x=cursor.x
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
			elif data[pos] in s2m:
				cursor.flags^={s2m[data[pos]][0]}
				pos+=1
				continue
			elif data[pos]=="\n":
				cursor.y+=1
				cursor.x=x
				cursor.bound()
				pos+=1
				height+=1
				width.append(0)
				continue
		else:
			escaped=False

		if proccessBg or proccessFg:
			if data[pos]=="[":
				pos+=1
				color=data[pos:].partition("]")[0]
				pos+=len(color)+1
				if color in h256colors:
					color=h256colors[color]
				color=int(color) if color!="default" else color
				assert(color=="default" or color<256) #make sure color in \f[] is valid
				if proccessFg:
					cursor.fcolor=color
				if proccessBg:
					cursor.bcolor=color
				proccessFg=False
				proccessBg=False
				continue

		cursor.addCh(data[pos],cnv)
		width[-1]+=inc[0]
		height+=inc[1]
		if inc[1]: width.append(0)
		cursor+=inc
		pos+=1
	return (height,max(width))

class Canvas:
	def __init__(self,rows,cols,filler=" "):
		self.matrix=[]
		self.filler=filler
		self.cursor=Cursor(0,0)
		self.resize(rows,cols)

	def clear(self):
		for cr in self.matrix:
			for c in cr:
				c.char=self.filler
				c.fcolor,c.bcolor="default","default"
				c.flags.clear()

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

	#x and y are where to render self. sx and sy are top left of rendered internal area
	def render(self,cnv,x,y,ph,pw,sx,sy): #cnv is canvas, ph and pw is the size to render self
		for row in range(ph):
			cnv.matrix[y+row][x:x+pw]=self.matrix[sy+row][sx:sx+pw]

	def print(self,data,inc=(1,0)):
		for char in data:
			self.cursor.addCh(char,self)
			self.cursor+=inc

	def line(self,chr,length,inc=(1,0)):
		for _ in range(length):
			self.cursor.addCh(chr,self)
			self.cursor+=inc

	def fillRect(self,x,y,h,w,c):
		l=[c]*w
		for row in range(y,y+h):
			self.matrix[row][x:x+w]=l

	def sprint(self,data,inc=(1,0)): #aaAAAAAAA Todo: impl a function to compute displayed length
		return sprint(data,self.cursor,self,inc=inc)

def ssize(data,inc=(1,0)):
	return sprint(data,fakecursor,None,inc=inc)

class Terminal(Canvas):
	def __init__(self):
		self.id=uuid()
		term.sizereceivers[self.id]=lambda r,c: self.resize(r,c) or term.clear()
		super().__init__(term.rows,term.columns)

	def __del__(self):
		del term.sizereceivers[self.id]

	def _render(self):
		prev=None
		res=""
		skipped=0
		for row in self.matrix:
			x=0
			for char in row:
				x+=1
				if prev==None:
					res+=str(char)
					prev=char
				else:
					toAdd=(prev-char)+char.char
					if toAdd==" " and char.isNothing():
						skipped+=1
						continue
					res+=self.filler*skipped
					skipped=0
					res+=toAdd
					prev=char
			if skipped!=0:
				res+=term.cleartoeol
			res+="\n"
			skipped=0
		res=res[:-1]+term.homecursor
		return res

	def render(self,*_):
		term.fprint(self._render())

def canvasApp(main):
	term.raw()
	term.noctrlc()
	term.canvas()
	term.clear()
	try:
		main(Terminal())
	except Exception as err:
		term.clear()
		term.uncanvas()
		term.ctrlc()
		term.unraw()
		raise err
	term.clear()
	term.uncanvas()
	term.ctrlc()
	term.unraw()