from .node import Node


class SpeechNode(Node):
    display_name = "Speech Recognition"
    output_types = ["boolean"]

    def __init__(self, man, args):
        super().__init__(args)

    def forward(self, values):
        return []