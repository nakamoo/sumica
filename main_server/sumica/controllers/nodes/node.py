
class Node:
    param_file = ""
    testable = False
    input_types = []
    output_types = []
    display_name = None

    def __init__(self, args):
        self.args = args
        self.inputs = []
        self.outputs = []

    def forward(self, values):
        return []