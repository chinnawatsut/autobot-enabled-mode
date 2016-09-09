from lib.jenkins import Jenkins
from lib.console import Console
import json

class Autobot():
    def __init__(self):
        self.con = Console()
        self.jenkins = Jenkins('http://10.89.104.33')

    def run(self, view_name):
        view_name = self.alias(view_name)
        if self.jenkins.enable(view_name):
            self.jenkins.build(view_name)

    def alias(self, view_name):
        with open('alias.json') as data_file:
            data = json.load(data_file)

        if data.has_key(view_name):
            view_name = data[view_name]
            self.con.out("Alias name found: ", self.con.White)
            self.con.outln(view_name, self.con.Yellow)
        return view_name
