import torch
import torch.nn as nn
import random
from torch.autograd import Variable
import torch.optim as optim
import numpy as np
import torch.nn.functional as F

encoding_size = 32
others = encoding_size

class Bagger(nn.Module):
	def __init__(self, action_size):
		super(Bagger, self).__init__()

		self.encoder = nn.Sequential(
			nn.Linear(80+4, others),
			torch.nn.ELU(),
			torch.nn.Dropout(),
			#nn.BatchNorm1d(others),
			nn.Linear(others, encoding_size),
			torch.nn.ELU(),
			torch.nn.Dropout(),
			#nn.BatchNorm1d(encoding_size)
		)

		self.decoder = nn.Sequential(
			nn.Linear(encoding_size, others),
			torch.nn.ELU(),
			torch.nn.Dropout(),
			#nn.BatchNorm1d(others),
			nn.Linear(others, action_size)
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

	def loss(self, out, target):
 		return F.cross_entropy(out, target)

class BaggerModel():
	def __init__(self, data):
		self.nn = Bagger(len(data.class_names))

		self.train(data)

	def train(self, data):
		self.nn.train()
		optimizer = optim.SGD(self.nn.parameters(), lr=1e-3, momentum=0.9)
		min_loss = 1000000
		patience = 0
		iters = 0

		X = []
		Y = []

		for x, y in zip(data.X, data.Y):
			inputs = Variable(torch.from_numpy(x))
			X.append(inputs)
			Y.append(y)

		Y = Variable(torch.from_numpy(np.array(Y)))

		while True:
			
			optimizer.zero_grad()
			output = self.nn(X)
			loss = self.nn.loss(output, Y)
			accuracy = output.data.max(1)[1].eq(Y.data).sum() / len(Y)

			if iters % 10 == 0:
				print(iters, "loss", loss.data[0])
				print(iters, "accuracy", accuracy)

			loss.backward()
			optimizer.step()

			patience += 1
			iters += 1

			if loss.data[0] <= 0:
				break

			if loss.data[0] / min_loss < 0.5:
				min_loss = loss.data[0]
				patience = 0
				print("RESET")

			if patience > 100:
				break

	def predict(self, state):
		self.nn.eval()
		state = Variable(torch.from_numpy(np.array(state)))
		logits = self.nn(state)
		probs = F.softmax(logits)
		out = np.argmax(probs.data.numpy(), axis=1)
		return out, probs.data.numpy()

if __name__ == "__main__":
	X = [Variable(torch.rand([random.randint(1, 10), 84])) for i in range(8)]
	model = Bagger(4)
	preds = model(X)
	print(preds.size())