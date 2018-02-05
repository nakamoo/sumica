from .node import Node

class AndNode(Node):
    display_name = "AND gate"
    input_types = ["boolean", "boolean"]
    output_types = ["boolean"]

    def __init__(self, args):
        super().__init__(args)

    def forward(self, values):
        return [not (False in [v[0] for v in values])]