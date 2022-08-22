import TermCanvas as tc
import Terminal as trm

@tc.canvasApp
def main(term):
	keyIter=trm.keys()
	key=None

	while True:
		term.sprint("\b[blue]*HE*^LLO^ \f[magenta]\b[green]*WO*^RLD^!\b\f[default]\n")
		term.sprint("Effects:\n")
		term.sprint("    - *BOLD*\n")
		term.sprint("    - ^DIM^\n")
		term.sprint("    - *^BOLD+DIM^*\n")
		term.sprint("Colors:\n")
		term.sprint("    - \f[red]re\f[default]\b[red]d\b[default]\n")
		term.sprint("    - \f[green]gr\f[default]\b[green]een\b[default]\n")
		term.sprint("    - \f[yellow]yel\f[default]\b[yellow]low\b[default]\n")
		term.sprint("    - \f[blue]bl\f[default]\b[blue]ue\b[default]\n")
		term.sprint("    - \f[magenta]mage\f[default]\b[magenta]nta\b[default]\n")
		term.sprint("    - \f[cyan]cy\f[default]\b[cyan]an\b[default]\n")
		term.sprint("    - \f[default]defa\f[default]\b[default]ult\b[default]\n")
		if key:
			term.sprint(f"Received keyboard key '{key}'\n")
		term.render()
		term.cursor.goto(0,0)
		term.clear()

		key=next(keyIter)
		if key=="ctrl z":
			break