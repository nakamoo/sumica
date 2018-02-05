from .node import Node

def data2command(data):
    command = {'platform': 'ifttt', 'data': {'url': data['urlText']}, 'stateful': False}

    return command

class IFTTTNode(Node):
    param_file = "ifttt-parameters.html"
    display_name = "IFTTT"
    input_types = ["boolean"]
    output_types = ["action"]
    icon = Node.icon_pic("fab fa-app-store")

    def __init__(self, man, args):
        super().__init__(args)

        self.act = data2command(args)

    def forward(self, values):
        if not (False in values):
            return [self.act]

        return []