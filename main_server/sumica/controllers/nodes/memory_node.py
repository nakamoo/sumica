import time

from .node import Node

class MemoryNode(Node):
    display_name = "Memory"
    input_types = ["boolean"]
    output_types = ["boolean"]
    icon = Node.icon_pic("fas fa-pencil-alt")
    param_file = "memory-parameters.html"

    def __init__(self, id, man, args):
        super().__init__(id, args)

        self.state = False
        self.reset_every = float(args["resetTime"])
        self.last_reset = 0

    def forward(self, values):
        if time.time() - self.last_reset > self.reset_every:
            self.state = False
            self.last_reset = time.time()

        if values[0]:
            self.state = True

        return [self.state]