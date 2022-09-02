hidecursor="\033[?25l"
showcursor="\033[?25h"

homecursor="\033[H"

savecursor="\033[s"
loadcursor="\033[u"

normalscreen="\033[?47l"
canvasscreen="\033[?47h"

cleartoeos="\033[0J"
cleartoeol="\033[0K"

movecursor="\033[{row};{column}H"

#foreground
fred="\033[31m"
fgreen="\033[32m"
fyellow="\033[33m"
fblue="\033[34m"
fmagenta="\033[35m"
fcyan="\033[36m"
fwhite="\033[37m"
fdefault="\033[39m" #reset text color

#background
bred="\033[41m"
bgreen="\033[42m"
byellow="\033[43m"
bblue="\033[44m"
bmagenta="\033[45m"
bcyan="\033[46m"
bwhite="\033[47m"
bdefault="\033[49m" #reset text color

black256=0
red256=1
green256=2
yellow256=3
blue256=4
magenta256=5
cyan256=6
white256=7

f256=lambda ID: f"\033[38;5;{ID}m" #foreground in 256col mode
b256=lambda ID: f"\033[48;5;{ID}m" #background in 256col mode

reset="\033[0m"

bold="\033[1m"
dim="\033[2m"
italic="\033[3m"
underline="\033[4m"

resetweight="\033[22m"

from sys import stdin,stdout
from os import get_terminal_size as termsize
from threading import Thread as thread
from threading import Lock as lock
from time import sleep as wait
from random import randint as random
from random import choice 
import termios, sys
import select
fd=stdin.fileno()

def sfprint(*stuff):
	if len(stuff)>1:
		stdout.write(" ".join(stuff))
	else:
		stdout.write(stuff[0])

def fprint(*stuff):
	if len(stuff)>1:
		stdout.write(" ".join(stuff))
	else:
		stdout.write(stuff[0])
	stdout.flush()

size=termsize()
rows=size.lines
columns=size.columns
maxx=columns-1
maxy=rows-1
sizereceivers={}

import signal

def updateSize(*a):
	global size,rows,columns,maxx,maxy,sizereceivers
	size=termsize()
	rows=size.lines
	columns=size.columns
	maxx=columns-1
	maxy=rows-1
	for receiver in sizereceivers:
		sizereceivers[receiver](rows,cols)

signal.signal(signal.SIGWINCH, updateSize)

read=stdin.read

def raw():
	raw=termios.tcgetattr(fd)
	raw[3]=raw[3] & ~(termios.ECHO | termios.ICANON)
	termios.tcsetattr(fd,termios.TCSADRAIN,raw)

def unraw():
	unraw=termios.tcgetattr(fd)
	unraw[3]=unraw[3] | (termios.ECHO | termios.ICANON)
	termios.tcsetattr(fd,termios.TCSADRAIN,unraw)

def noctrlc():
	noctrlc=termios.tcgetattr(fd)
	noctrlc[3]=noctrlc[3] & ~termios.ISIG
	termios.tcsetattr(fd,termios.TCSADRAIN,noctrlc)

def ctrlc():
	ctrlc=termios.tcgetattr(fd)
	ctrlc[3]=ctrlc[3] | termios.ISIG
	termios.tcsetattr(fd,termios.TCSADRAIN,ctrlc)

def canvas():
	fprint(savecursor+hidecursor+canvasscreen)

def clear():
	fprint(homecursor+cleartoeos)

def uncanvas():
	fprint(normalscreen+loadcursor+showcursor) #restore terminal

mappings={
	0:"ctrl 1",
	27:"ctrl 2",
	28:"ctrl 3",
	29:"ctrl 4",
	30:"ctrl 5",
	31:"ctrl 6",
	127:"ctrl 7",
	23:"ctrl w",
	5:"ctrl e",
	18:"ctrl r",
	20:"ctrl t",
	25:"ctrl y",
	21:"ctrl u",
	9:"ctrl i",
	16:"ctrl p",
	1:"ctrl a",
	4:"ctrl d",
	6:"ctrl f",
	7:"ctrl g",
	8:"ctrl h",
	11:"ctrl k",
	12:"ctrl l",
	26:"ctrl z",
	24:"ctrl x",
	3:"ctrl c",
	2:"ctrl b",
	14:"ctrl n",
	ord("\033"):"escape"
}
def proccessTermChar(char):
	if ord(char) in mappings:
		return mappings[ord(char)]
	else: 
		return char

def stdinempty():
	return select.select([sys.stdin,],[],[],0.0)[0]==[]

def readall(blocking=True): #if its one big write (eg. arrow key), it will onnly get first char :(
	data=stdin.read(1) if blocking else ""
	while not stdinempty():
		data+=stdin.read(1)
	return data

arrowChars={"A":"up","B":"down","C":"right","D":"left"}
arrowModifyers={"2":"shift","3":"option","4":"shift option"}
def keys():
	while True:
		data=readall()
		while data!="":
			if data[0]=='\033' and len(data)>1 and data[1]=='[': #arrow key?
				data=data[2:]
				if data.startswith("1"):
					data+=sys.stdin.read(3)
					data=data[2:]
					if data[0] in arrowModifyers:
						modifyer=arrowModifyers[data[0]]
						data=data[1:]
						if data[0] in arrowChars:
							yield modifyer+" "+arrowChars[data[0]]
							data=data[1:]
				elif data[0] in arrowChars:
					yield arrowChars[data[0]]
					data=data[1:]
			elif data[0]=='\033' and len(data)==1:
				data+=sys.stdin.read(2)
			else:
				yield proccessTermChar(data[0])
				data=data[1:]

class Action:
	def __init__(self,func,*args,**kwargs):
		self.func=func
		self.args=args
		self.kwargs=kwargs
	def run(self):
		return self.func(*self.args,**self.kwargs)

class KeyHandler:
		def __init__(self,actions):
			self.actions=actions
			self.thread=None
			self.tasks=[]
			self.delay=0.01

		def _handle(self):
			for key in keys():
				try:
					action=self.actions[key]
				except KeyError:
					try:
						action=self.actions["default"]
						action=Action(action.func,key,*action.args,**action.kwargs)
					except KeyError:
						continue
				self.tasks+=[[key,thread(target=action.run)]]
				self.tasks[-1][1].start()
				for task in reversed(range(len(self.tasks))):
					if not self.tasks[task][1].is_alive():
						self.tasks.pop(task)
				wait(self.delay) #timeframe where key handler can be killed (sketch 1000)
				if self.thread==None:
					break

		def handle(self):
			if self.thread==None:
				self.thread=thread(target=self._handle)
				self.thread.start()

		def stop(self):
			self.thread=None
			self.tasks=[]

from time import perf_counter as timecounter

class Stopwatch:
	def __init__(self):
		self.reset()

	def start(self):
		self.started=timecounter()

	def stop(self):
		if self.started!=-1:
			self.totalElapsed+=timecounter()-self.started
			self.started=-1
		return self.time()
	end=stop

	def reset(self):
		self.started=-1
		self.totalElapsed=0

	def time(self):
		if self.started!=-1:
			return self.totalElapsed+(timecounter()-self.started)
		else:
			return self.totalElapsed