from .node import Node


class VoiceNode(Node):
    testable = True
    param_file = "voice-parameters.html"
    display_name = "Voice"
    input_types = ["boolean"]
    output_types = ["action"]
    icon = Node.icon_pic("fa fa-volume-up")

    @staticmethod
    def test_execute(args):
        return [{"platform": "tts", "data": args["voiceText"]}]

    def __init__(self, id, man, args):
        super().__init__(id, args)

        self.text = args["voiceText"]
        self.done = False

    def forward(self, values):
        if not (False in values):
            #if not self.done:
            #self.done = True
            return [{"platform": "tts", "data": self.text}]
        else:
            pass
            #self.done = False

        return []