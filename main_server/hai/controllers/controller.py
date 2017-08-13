from server_actors import actor

class Controller(object):
    def __init__(self):
        pass

    def on_event(self, event, data):
        pass

    def execute(self):
        pass


class Sample(Controller):
    def __init__(self, gpu=-1):
        self.gpu = gpu

    def execute(self):
        # colect data from DB or api

        # logic

        actor.sample()

        response = []
        response.append({"app": "TV", "cmd": "turn on", "controller": "Sample"})
        response.append({"app": "music", "cmd": "pray", "controller": "Sample"})
        return response


