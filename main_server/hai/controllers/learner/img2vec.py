from torchvision import models, transforms
from torch.autograd import Variable
import torch.nn as nn

class NNFeatures:
    def __init__(self, gpu_num=0):
        self.gpu_num = gpu_num
        model = models.resnet101(pretrained=True).cuda(self.gpu_num)
        self.model = nn.Sequential(*list(model.children())[:-1])

    def img2vec(self, imgs, progress=10):
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
            if progress > 0 and i % progress == 0:
                print("{}/{}".format(i, len(imgs)))

            img_tensor = preprocess(img)
            img_variable = Variable(img_tensor.unsqueeze(0)).cuda(self.gpu_num)
            fc_out = self.model(img_variable).squeeze()
            fcs.append(fc_out.data.cpu().numpy())

        return fcs