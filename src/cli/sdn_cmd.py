import cmd


class SDNCommand(cmd.Cmd):
    logbug = None

    def do_exit(self, args):
        return True

    def emptyline(self):
        self.logbug.prompt = self.prompt

    def preloop(self):
        self.logbug.prompt = self.prompt
        self.logbug.is_wait_input = True

    def precmd(self, line):
        self.logbug.prompt = self.prompt
        self.logbug.is_wait_input = False
        return cmd.Cmd.precmd(self, line)

    def postloop(self):
        self.logbug.prompt = self.prompt
