import sys
from collections import OrderedDict

i3d_root = '../../kinetics_i3d_pytorch'
sys.path.insert(0, i3d_root)

import numpy as np
import torch
from src.i3dpt import I3D

rgb_weights_path = i3d_root + '/model/model_rgb.pth'
classes_path = i3d_root + '/data/kinetic-samples/label_map.txt'
gpu = 1
kinetics = False

class I3DModel:
    def __init__(self):
        if kinetics:
            self.kinetics_classes = [x.strip() for x in open(classes_path)]
            i3d_rgb = I3D(num_classes=400, modality='rgb')

            i3d_rgb.eval()
            save = torch.load(rgb_weights_path)
            i3d_rgb.load_state_dict(save)
            i3d_rgb.cuda(gpu)
        else:
            lines = [line.rstrip() for line in open("Charades_v1_classes.txt", "r").readlines()]
            self.kinetics_classes = [" ".join(line.split()[1:]) for line in lines]


            i3d_rgb = I3D(num_classes=157, modality='rgb')

            i3d_rgb.eval()
            path = "/home/sean/charades-algorithms/pytorch/cache/model02/model_best.pth.tar"
            print("Action model: " + path)
            save = torch.load(path)

            new_state_dict = OrderedDict()
            for k, v in save['state_dict'].items():
                name = k[7:]  # remove `module.`
                new_state_dict[name] = v

            i3d_rgb.load_state_dict(new_state_dict)
            i3d_rgb.cuda(gpu)

        self.i3d = i3d_rgb
        
    def predict(self, sample):
        sample_var = torch.autograd.Variable(torch.from_numpy(sample).float().cuda(gpu))
        out_var, out_logit = self.i3d(sample_var)

        out_tensor = out_var.data.cpu()

        top_val, top_idx = torch.sort(out_tensor, 1, descending=True)

        return top_val[:, 0].numpy(), top_idx[:, 0].numpy()
