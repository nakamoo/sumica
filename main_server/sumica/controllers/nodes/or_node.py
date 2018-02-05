from .node import Node

class OrNode(Node):
    display_name = "OR gate"
    input_types = ["boolean", "boolean"]
    output_types = ["boolean"]

    def __init__(self, args):
        super().__init__(args)

    def forward(self, values):
        return [True in [v[0] for v in values]]