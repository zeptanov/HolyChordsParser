import sys
from app.cli import run_cli
from app.gui import run_gui


def main():
    if len(sys.argv) < 2:
        run_gui()
    else:
        run_cli()

if __name__ == "__main__":
    main()
