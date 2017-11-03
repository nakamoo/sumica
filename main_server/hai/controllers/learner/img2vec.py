from torchvision import models, transforms
from torch.autograd import Variable
import torch.nn as nn

class NNFeatures:
    def __init__(self):
        model = models.resnet34(pretrained=True).cuda()
        self.model = nn.Sequential(*list(model.children())[:-1])

    def img2vec(self, imgs):
        fcs = []

        # imgs = (NxWxHxC)

        normalize = transforms.Normalize(
           mean=[0.485, 0.456, 0.406],
           std=[0.229, 0.224, 0.225]
        )
        preprocess = transforms.Compose([
           transforms.Scale(224),
           transforms.ToTensor(),
           normalize
        ])

        for i, img in enumerate(imgs):
            print("{}/{}".format(i, len(imgs)))
            
            img_tensor = preprocess(img)
            img_variable = Variable(img_tensor.unsqueeze(0)).cuda()
            fc_out = self.model(img_variable).squeeze()
            fcs.append(fc_out.data.cpu().numpy())

        return fcs