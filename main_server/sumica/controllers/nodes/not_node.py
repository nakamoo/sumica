from .node import Node

class NotNode(Node):
    display_name = "NOT gate"
    input_types = ["boolean"]
    output_types = ["boolean"]
    icon = Node.icon_text("NOT", "2em")

    def __init__(self, id, man, args):
        super().__init__(id, args)

    def forward(self, values):


        return [not values[0]]