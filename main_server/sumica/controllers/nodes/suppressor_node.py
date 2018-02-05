import time

from .node import Node


class SuppressorNode(Node):
    display_name = "Suppressor"
    input_types = ["boolean"]
    output_types = ["boolean"]
    icon = Node.icon_pic("fa fa-sliders-h")

    def __init__(self, man, args):
        super().__init__(args)

        self.wait_sec = args["wait"]
        self.last_fire = time.time()

    def forward(self, values):
        if self.wait_sec < 0:
            return [False]

        if not (False in values) and time.time() - self.last_fire >= self.wait_sec:
            self.last_fire = time.time()
            return [True]

        return [False]