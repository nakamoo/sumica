from .node import Node

class OrNode(Node):
    def __init__(self, args):
        super().__init__(args)

    def forward(self, values):
        return [True in [v[0] for v in values]]