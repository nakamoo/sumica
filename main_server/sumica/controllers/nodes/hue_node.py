from .node import Node

import controllermanager as cm


class HueNode(Node):
    def __init__(self, man, args):
        super().__init__(args)

        self.act = cm.platforms['hue'].data2command(args)

    def forward(self, values):
        if not (False in [v[0] for v in values]):
            return [self.act]

        return []