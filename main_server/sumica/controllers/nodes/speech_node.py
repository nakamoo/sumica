
from .node import Node


class SpeechNode(Node):
    display_name = "Speech Recognition"
    output_types = ["boolean"]
    param_file = "speech-parameters.html"
    icon = Node.icon_pic("fa fa-microphone")

    def __init__(self, id, man, args):
        super().__init__(id, args)

        self.tokens = args["speechText"].split()
        self.state = False

    def forward(self, values):
        state = self.state
        self.state = False
        return [state]

    def on_event(self, event, data):
        if event == "speech" and data["type"] == "speech":
            msg = data["text"]
            print("SPEECH >>>", msg)
            match = True

            for t in self.tokens:
                if t not in msg:
                    match = False
                    break

            if match:
                self.state = True
