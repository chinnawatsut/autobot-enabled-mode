import sys

class Console():
    Red = '\033[91m'
    Green = '\033[92m'
    Yellow = '\033[93m'
    Blue = '\033[94m'
    Magenta = '\033[95m'
    Cyan = '\033[96m'
    White = '\033[97m'
    Reset = '\033[0m'
    Bold = '\033[1m'
    Underline = '\033[4m'

    def out(self, text, color):
        sys.stdout.write(color + text + self.Reset)
        sys.stdout.flush()

    def outln(self, text, color):
        self.out(text + "\n", color)
