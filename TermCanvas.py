import Terminal as term
from uuid import uuid4 as uuid

bold="1"
dim="2"
resetweight="22"

#for different text fonts
flags=[ #{flag character; enable escape number; disable escape number; flag symbol}
	"b12*", #bold
	"d22`", #dim
	"i33_", #italic
	"u44|", #underline
	"f55^", #flashing
	"r77%", #inverse
	"h88",  #hidden
	"s99~"  #strikethrough
]

h256colors={ #ANSI256 colour aliases (used in \f[colour], \b[colour] and others)
	"black":"0",
	"red":"1",
	"green":"2",
	"yellow":"3",
	"blue":"4",
	"magenta":"5",
	"cyan":"6",
	"white":"7"
}

f2m={} #character to information
for item in flags:
	f2m[item[0]]=item[1:]
s2m={} #symbol to information
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
			self.flags=set() #set of characters
		else:
			self.flags=set(flags)

	def copy(self):
		return Char(self.char,self.fcolor,self.bcolor,self.flags.copy())

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
		for flag in other.flags-self.flags:
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
		return self.char==" " and self.bcolor=="default" and (not self.flags)

class Cursor:
	# wrapping=False #ignore going out of bounds and wrap around
	wrapping=True
	def __init__(self,x,y,fcolor="default",bcolor="default",flags=None):
		self.x=x
		self.y=y
		self.fcolor=fcolor
		self.bcolor=bcolor
		self.flags=flags
		if flags is None:
			self.flags=set()
		else:
			self.flags=set(flags)

	def nostyle(self):
		self.fcolor="default"
		self.bcolor="default"
		self.flags=set()

	def wrap(self,cnv):
		width=len(cnv.matrix[0])
		height=len(cnv.matrix)
		if self.x>=width or self.y>=height:
			if self.wrapping:
				return (self.x%width, self.y%height)
			else:
				raise ValueError(
					f"Out of bounds (at {self.x,self.y} where size is {height,width})"
				)
		else:
			return (self.x,self.y)

	def addCh(self,char,cnv): # add character with cursor formatting
		x,y=self.wrap(cnv)

		cnv.matrix[y][x]=Char(
			char,
			fcolor=self.fcolor,
			bcolor=self.bcolor,
			flags=self.flags.copy()
		)

	def putCh(self,char,cnv): # add own character
		cnv.matrix[self.y][self.x]=char.copy()

	def __add__(self,offset):
		self.x+=offset[0]
		self.y+=offset[1]
		return self

	def __sub__(self,offset):
		self.x-=offset[0]
		self.y-=offset[1]
		return self

	def goto(self,x,y):
		self.x=x
		self.y=y

	def goX(self,x):
		self.x=x
	
	def goY(self,y):
		self.y=y

class FakeCursor(Cursor):
	def putCh(*_): pass
	def addCh(*_): pass

fakecursor=FakeCursor(0,0)
fakecursor.wrapping=True

def procColor(color):
	if color in h256colors:
		color=h256colors[color]
	elif color.startswith("#"):
		color=term.toTermCol(*term.hexToRgb(color[1:]))
	elif color==".":
		color="default"
	color=int(color) if color!="default" else color
	assert(color=="default" or color<256) 
	return color

def sprint(data,cursor,cnv,inc=(1,0),newline=(0,1)):
	processFg=False #take colour expression next "[colour]"
	processBg=False 
	escaped=False #ignore next special character 
	pos=0 #position in string
	line=0 #line number (starts from 0!)
	beginY=cursor.y #initial cursor position
	beginX=cursor.x
	maxCoords=[beginX,beginY] # used to calculate size
	minCoords=[beginX,beginY]

	while not pos>=len(data): #iterate through entire string
		if processBg or processFg: #brought out to reduce repeat code
			if data[pos]=="[":
				pos+=1
				color=data[pos:].partition("]")[0]
				pos+=len(color)+1
				color=procColor(color)
				if processFg:
					cursor.fcolor=color
				if processBg:
					cursor.bcolor=color
				processFg=False
				processBg=False
				continue
			else:
				data=data.replace("\f",'\\f').replace("\b",'\\b')
				raise SyntaxError(
					f"\\f or \\b not continued with [colour] in string `{data}` at position {pos}"
				)

		if not escaped: #special characters (should not directly add characters)
			#find colour modifiers
			if data[pos]=="\\": #evaluate escaping front slash character
				escaped=True
				pos+=1
				continue
			elif data[pos:pos+2]=="\f\b" or data[pos:pos+2]=="\b\f": 
				pos+=2
				processFg=True
				processBg=True
				continue
			elif data[pos]=="\f":
				pos+=1
				processFg=True
				continue
			elif data[pos]=="\b":
				pos+=1
				processBg=True
				continue
			elif data[pos] in s2m:
				cursor.flags^={s2m[data[pos]][0]}
				pos+=1
				continue
			elif data[pos]=="\n":
				line+=1 #destination line
				cursor.x=beginX+(newline[0]*line)
				cursor.y=beginY+(newline[1]*line)
				pos+=1
				continue
		else:
			escaped=False

		# normal characters (should be the only thing displayed)
		cursor.addCh(data[pos],cnv)
		cursor+=inc
		pos+=1

		if cursor.x>maxCoords[0]:
			maxCoords[0]=cursor.x
		if cursor.y>maxCoords[1]:
			maxCoords[1]=cursor.y
		if cursor.x<minCoords[0]:
			minCoords[0]=cursor.x
		if cursor.y<minCoords[1]:
			minCoords[1]=cursor.y

	return (maxCoords[1]-minCoords[1]+1,maxCoords[0]-minCoords[0]) # height, width

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
			for col in range(pw):
				cnv.matrix[y+row][x+col]=self.matrix[sy+row][sx+col].copy()

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

	def sprint(self,data,inc=(1,0)):
		return sprint(data,self.cursor,self,inc=inc)

def ssize(data,inc=(1,0)):
	return sprint(data,fakecursor,None,inc=inc)

class Terminal(Canvas):
	def __init__(self):
		self.id=uuid()
		term.sizereceivers[self.id]=lambda r,c: self.resize(r,c) or term.clear()
		super().__init__(term.rows,term.columns)
		self.project=super().render

	def _render(self):
		prev=None
		prevNothing=None
		res=""
		skipped=0
		for row in self.matrix:
			x=0
			for char in row:
				x+=1
				if prev==None:
					res+=str(char)
					prev=char
					prevNothing=char.isNothing()
				else:
					isNothing=char.isNothing()
					if isNothing and prevNothing:
						skipped+=1
						prev=char
						prevNothing=isNothing
						continue
					toAdd=(prev-char)+char.char
					if prevNothing:
						res+=self.filler*skipped
					skipped=0
					res+=toAdd
					prev=char
					prevNothing=isNothing
			if skipped!=0:
				res+=term.cleartoeol
			res+="\n"
			skipped=0
		res=res[:-1]+term.homecursor
		return res

	def render(self,*_):
		term.fprint(self._render())

# https://stackoverflow.com/questions/1643327/sys-excepthook-and-threading
import sys
import threading

def setup_thread_excepthook():
    """
    Workaround for `sys.excepthook` thread bug from:
    http://bugs.python.org/issue1230540

    Call once from the main thread before creating any threads.
    """

    init_original = threading.Thread.__init__

    def init(self, *args, **kwargs):

        init_original(self, *args, **kwargs)
        run_original = self.run

        def run_with_except_hook(*args2, **kwargs2):
            try:
                run_original(*args2, **kwargs2)
            except Exception:
                sys.excepthook(*sys.exc_info())

        self.run = run_with_except_hook

    threading.Thread.__init__ = init
setup_thread_excepthook()
# ========================================================================

import sys, os
from time import sleep
DIED=False #if the program died
def canvasApp(main): #TODO: make it into global exception bracket
	global DIED
	term.raw()
	term.noctrlc()
	term.canvas()
	term.clear()
	term.nbStdin()

	def exceptHook(exception,value,traceback):
		global DIED
		term.clear()
		term.uncanvas()
		term.ctrlc()
		term.unraw()
		term.bStdin()
		DIED=True
		sleep(0.1)
		sys.__excepthook__(exception, value, traceback)
		os._exit(-1)
	sys.excepthook=exceptHook

	trm=Terminal()
	main(trm)

	DIED=True #if the program died
	sleep(0.1) 
	term.bStdin()
	term.clear()
	term.uncanvas()
	term.ctrlc()
	term.unraw()