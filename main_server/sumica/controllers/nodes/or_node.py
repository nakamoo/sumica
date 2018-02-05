from .node import Node

class OrNode(Node):
    display_name = "OR gate"
    input_types = ["boolean", "boolean"]
    output_types = ["boolean"]
    icon = Node.icon_text("OR", "2em")

    def __init__(self, man, args):
        super().__init__(args)

    def forward(self, values):
        return [True in values]