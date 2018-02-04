from .node import Node

class HueNode(Node):
    def __init__(self, args):
        super().__init__(args)

    def forward(self, values):
        return True in values