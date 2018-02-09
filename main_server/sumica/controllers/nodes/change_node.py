from .node import Node

class ChangeNode(Node):
    display_name = "Change Detection"
    input_types = ["boolean"]
    output_types = ["boolean"]
    icon = Node.icon_pic("fa fa-exclamation")
    param_file = "change-parameters.html"

    def __init__(self, id, man, args):
        super().__init__(id, args)

        self.on2off = args["mode"] == "ON to OFF"
        self.current_state = None

    def forward(self, values):
        re = False

        if self.current_state is not None:
            if self.on2off and self.current_state is True and values[0] is False:
                re = True
            elif not self.on2off and self.current_state is False and values[0] is True:
                re = True

        self.current_state = values[0]

        return [re]