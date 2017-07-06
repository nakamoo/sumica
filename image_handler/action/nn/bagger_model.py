import torch
import torch.nn as nn
import random
from torch.autograd import Variable

encoding_size = 128

class Bagger(nn.Module):
	def __init__(self, action_size):
		super(Bagger, self).__init__()

		self.encoder = nn.Sequential(
			nn.Linear(80+4, 128),
			nn.Linear(128, encoding_size)
		)

		self.decoder = nn.Sequential(
			nn.Linear(128, 128),
			nn.Linear(128, action_size)
		)

	def forward(self, X):
		bundles = []

		for x in X:
			encoded = self.encoder(x)
			encoded = encoded.view(-1, encoding_size)
			encoded = torch.sum(encoded, 0)
			bundles.append(encoded)
		
		bundles = torch.cat(bundles)

		outputs = self.decoder(bundles)

		return outputs

if __name__ == "__main__":
	X = [Variable(torch.rand([random.randint(1, 10), 84])) for i in range(8)]
	model = Bagger(4)
	preds = model(X)
	print(preds.size())