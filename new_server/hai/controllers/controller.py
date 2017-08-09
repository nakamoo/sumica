class Controller(object):
    def __init__(self):
        pass

    def execute(self):
        pass


class SampleController(Controller):
    def __init__(self, gpu=-1):
        self.gpu = gpu

    def execute(self):
        return "turn off"

