from .node import Node

class DelayNode(Node):
    display_name = "Delay"
    input_types = ["boolean"]
    output_types = ["boolean"]
    icon = Node.icon_text("NOT", "2em")

    def __init__(self, id, man, args):
        super().__init__(id, args)
        self.delay = float(args["delay"])

    def forward(self, values):


        return [not values[0]]