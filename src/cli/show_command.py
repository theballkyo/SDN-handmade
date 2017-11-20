class ShowCommand:
    def __init__(self, topology):
        self.topology = topology

    def handle_command(self, commands):
        """ Handle commands
        """
        if commands[0] in ('device', 'devices'):
            if len(commands) < 2:
                print()
                return True

            if commands[1].isdigit():
                device_index = int(commands[1])
                if len(commands) < 3:
                    self.__show_device_details(device_index)
                    return True
                action = commands[2]
            else:
                # Todo
                return False


    def __show_device_details(self, device_index):
        """ Display device detail"""
        pass
