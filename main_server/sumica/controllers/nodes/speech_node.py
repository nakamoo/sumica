from .node import Node


class SpeechNode(Node):
    display_name = "Speech Recognition"
    output_types = ["boolean"]
    param_file = "speech-parameters.html"
    icon = Node.icon_pic("fa fa-microphone")

    def __init__(self, man, args):
        super().__init__(args)

    def forward(self, values):
        return []