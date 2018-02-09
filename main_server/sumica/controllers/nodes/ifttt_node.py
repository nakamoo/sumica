from .node import Node
import requests

def data2command(data):
    command = {'platform': 'ifttt', 'data': {'url': data['urlText']}}

    return command

def request(args):
    try:
        requests.post(args["urlText"], params={'value1': args['urlParam1'],
                                           'value2': args['urlParam2'],
                                           'value3': args['urlParam3']})
    except:
        pass

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
        request(args)
        return []

    def __init__(self, id, man, args):
        super().__init__(id, args)

        self.act = data2command(args)

    def forward(self, values):
        if not (False in values):
            request(self.args)
            return [self.act]

        return []