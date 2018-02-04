from .node import Node


class TimetrackerNode(Node):
    def __init__(self, args):
        super().__init__(args)

        self.min_time = float(args["minTime"])
        self.max_time = float(args["maxTime"])
        self.repeat = 60

    def forward(self, values):

        return []