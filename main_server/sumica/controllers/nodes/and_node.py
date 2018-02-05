from .node import Node

class AndNode(Node):
    display_name = "AND gate"
    input_types = ["boolean", "boolean"]
    output_types = ["boolean"]
    icon = Node.icon_text("AND", "2em")

    def __init__(self, man, args):
        super().__init__(args)

    def forward(self, values):
        return [not (False in values)]