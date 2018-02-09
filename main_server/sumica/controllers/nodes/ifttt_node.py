from .node import Node
import requests

def data2command(data):
    command = {'platform': 'ifttt', 'data': {'url': data['urlText']}}

    return command

class IFTTTNode(Node):
    askable = True
    testable = True
    param_file = "ifttt-parameters.html"
    display_name = "IFTTT"
    input_types = ["boolean"]
    output_types = ["action"]
    icon = Node.icon_pic("fab fa-app-store")

    @staticmethod
    def test_execute(args):
        print("IFTTT >>> ", args["urlText"])
        requests.post(args["urlText"])
        return []
        #return [data2command(args)]

    def __init__(self, id, man, args):
        super().__init__(id, args)

        self.act = data2command(args)

    def forward(self, values):
        if not (False in values):
            requests.post(self.args["urlText"])
            return [self.act]

        return []