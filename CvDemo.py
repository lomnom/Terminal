import TermCanvas as tc
import Terminal as trm

@tc.canvasApp #wrapper that initialises terminal and gives you canvas
def main(term):
	keyIter=trm.keys()
	key=None
 
	while True:
		# \b[background] \f[foreground]
		term.sprint("\b[blue]*HE*|LLO| \f[magenta]\b[green]*WO*|RLD|!\f\b[default]\n")
		term.sprint("Effects:\n")
		term.sprint("    - *BOLD*\n")
		term.sprint("    - |uline|\n") # markdown supported somewhat, | is underline, * is bold... eg
		term.sprint("    - *|BOLD+uline|*\n")
		term.sprint("Colors:\n")
		term.sprint("    - \f[red]re\f[default]\b[red]d\b[default]\n")
		term.sprint("    - \f[green]gr\f[default]\b[green]een\b[default]\n")
		term.sprint("    - \f[yellow]yel\f[default]\b[yellow]low\b[default]\n")
		term.sprint("    - \f[blue]bl\f[default]\b[blue]ue\b[default]\n")
		term.sprint("    - \f[magenta]mage\f[default]\b[magenta]nta\b[default]\n")
		term.sprint("    - \f[cyan]cy\f[default]\b[cyan]an\b[default]\n")
		term.sprint("    - \f[default]defa\f[default]\b[default]ult\b[default]\n")
		if key:
			term.print(f"Received keyboard key '{key}'\n")
		term.render() # push buffer
		term.cursor.goto(0,0)
		term.clear()
 
		key=next(keyIter)
		if key=="ctrl z":
			break