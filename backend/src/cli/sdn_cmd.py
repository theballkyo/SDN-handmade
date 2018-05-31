import cmd
import logbug


class SDNCommand(cmd.Cmd):
    logbug = logbug.get()

    def __init__(self):
        super(SDNCommand, self).__init__()

    def do_exit(self, args):
        return True

    def emptyline(self):
        self.logbug.prompt = self.prompt

    def preloop(self):
        self.logbug.prompt = self.prompt
        self.logbug.is_wait_input = True

    def postcmd(self, stop, line):
        self.logbug.prompt = self.prompt
        self.logbug.is_wait_input = True
        return cmd.Cmd.postcmd(self, stop, line)

    def precmd(self, line):
        self.logbug.prompt = self.prompt
        self.logbug.is_wait_input = False
        return cmd.Cmd.precmd(self, line)

    def postloop(self):
        self.logbug.prompt = self.prompt
