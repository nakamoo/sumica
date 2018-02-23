import sys

i3d_root = '../kinetics_i3d_pytorch'
sys.path.insert(0, i3d_root)

import numpy as np
import torch
from src.i3dpt import I3D

rgb_weights_path = i3d_root + '/model/model_rgb.pth'
classes_path = i3d_root + '/data/kinetic-samples/label_map.txt'

class I3DModel:
    def __init__(self):
        self.kinetics_classes = [x.strip() for x in open(classes_path)]
        
        i3d_rgb = I3D(num_classes=400, modality='rgb')
        i3d_rgb.eval()
        i3d_rgb.load_state_dict(torch.load(rgb_weights_path))
        i3d_rgb.cuda(2)

        self.i3d = i3d_rgb
        
    def predict(self, sample):
        sample_var = torch.autograd.Variable(torch.from_numpy(sample).float().cuda(2))
        out_var, out_logit = self.i3d(sample_var)
        out_tensor = out_var.data.cpu()

        top_val, top_idx = torch.sort(out_tensor, 1, descending=True)
        
        return top_val[:, 0].numpy(), top_idx[:, 0].numpy()