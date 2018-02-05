from .node import Node


class VoiceNode(Node):
    param_file = "voice-parameters.html"
    display_name = "Voice"
    input_types = ["boolean"]
    output_types = ["action"]

    def __init__(self, man, args):
        super().__init__(args)

        self.text = args["voiceText"]
        self.done = False

    def forward(self, values):
        if not (False in [v[0] for v in values]):
            if not self.done:
                self.done = True
                return [{"platform": "tts", "data": self.text}]
        else:
            self.done = False

        return []