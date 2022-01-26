from enum import Enum
import numpy as np
import torch
import torch.nn.functional as F
import torchvision.transforms as tt
from PIL import Image
import tempfile
from nst_tg_bot.model.trunc_vgg19 import TruncVGG19
from nst_tg_bot.model.inv_net import InverseNet


class Model():

	def __init__(self):
		self.__vgg19 = TruncVGG19(11)
		self.__inv_net = InverseNet()
		self.__inv_net.load_state_dict(torch.load('./nst_tg_bot/model/invnet_params.pt',
		                                          map_location=torch.device('cpu')))

		self.__img_std  = torch.tensor([0.485, 0.456, 0.406]).reshape(-1, 1, 1)
		self.__img_mean = torch.tensor([0.229, 0.224, 0.225]).reshape(-1, 1, 1)
		self.__transforms = tt.Compose([
		    tt.ToTensor(),
		    tt.Normalize(mean=[0.485, 0.456, 0.406],
		                 std=[0.229, 0.224, 0.225])
		])
		self.__MIN_IMG_SIZE = 228
		self.__MAX_IMG_SIZE = 512

	def transfer_style(self, content_path, style_path):
		with Image.open(content_path) as content_img, \
			Image.open(style_path) as style_img:
			content_resized = self.__resize_if_small(content_img)
			style_resized   = self.__resize_if_small(style_img)
			content_resized = self.__resize_if_large(content_resized)
			style_resized   = self.__resize_if_large(style_resized)

			content = self.__transforms(np.array(content_resized)).repeat(1, 1, 1, 1)
			style   = self.__transforms(np.array(style_resized)).repeat(1, 1, 1, 1)

			with torch.no_grad():
				features_c = self.__vgg19(content)
				features_s = self.__vgg19(style)
				features_n = self.__style_swap(features_c, features_s[0])

				result_t = self.__denorm(self.__inv_net(features_n)[0])

			result_np = np.rollaxis(result_t.numpy(), 0, 3)
			result_np = self.__correct_gamma(result_np, np.array(style_img) / 255)
			result_np = np.clip(result_np, 0, 1)
			result = Image.fromarray(np.uint8(result_np * 255))

			Wc, Hc = content_img.size
			if Hc < self.__MIN_IMG_SIZE or Wc < self.__MIN_IMG_SIZE:
				result = result.resize((Wc, Hc))

			return self.__save_image(result)


	def __resize_if_small(self, img):
		W, H = img.size
		if H < self.__MIN_IMG_SIZE:
			scale = self.__MIN_IMG_SIZE / H
			img = img.resize((int(W * scale), int(H * scale)))

		W, H = img.size
		if W < self.__MIN_IMG_SIZE:
			scale = self.__MIN_IMG_SIZE / W
			img = img.resize((int(W * scale), int(H * scale)))

		return img

	def __resize_if_large(self, img):
		W, H = img.size
		if H > self.__MAX_IMG_SIZE:
			scale = self.__MAX_IMG_SIZE / H
			img = img.resize((int(W * scale), int(H * scale)))

		W, H = img.size
		if W > self.__MAX_IMG_SIZE:
			scale = self.__MAX_IMG_SIZE / W
			img = img.resize((int(W * scale), int(H * scale)))

		return img

	def __style_swap(self, features_c, features_s, patch_size=3):
		"""
		Executes style swapping algorithm.
		:param features_c: content images features with shape (B, C, H, W)
		:param features_s: style image features with shape (C, Hs, Ws)
		:param patch_size: size of patches (default 3)
		:returns: calculated features of the content images with a new style
		"""

		assert features_s.shape[0] == features_c.shape[1]
		B, C, H, W = features_c.shape
		C, Hs, Ws  = features_s.shape
		s = patch_size

		patches_s = torch.tensor(np.array([[
	        	layer[a:a+s, b:b+s] for a in range(Hs-s+1) for b in range(Ws-s+1)
	    	] for layer in features_s.detach().numpy()
		])).moveaxis(1, 0)

		patches_s_norm = F.normalize(patches_s, dim=0)
		correlations = F.conv2d(features_c, patches_s_norm)

		phi = torch.argmax(correlations, dim=1)
		matches = torch.moveaxis(F.one_hot(phi, num_classes=len(patches_s)), 3, 1).type(torch.float)

		result = F.conv_transpose2d(matches, patches_s, stride=1)

		conv = torch.tensor([
		    [1., 1., 1.],
		    [1., 1., 1.],
		    [1., 1., 1.]
		]).repeat(C, 1, 1, 1)
		overlap = F.conv2d(torch.ones(B, 1, H - 2, W - 2), conv, padding=2)

		return result / overlap

	def __denorm(self, x):
		return torch.clamp(x * self.__img_std + self.__img_mean, 0, 1)

	def __correct_gamma(self, img, target):
		std_t  =  np.std(target)
		mean_t = np.mean(target)

		std_i  =  np.std(img)
		mean_i = np.mean(img)

		return (img - mean_i) / std_i * std_t + mean_t

	def __save_image(self, img):
		file = tempfile.NamedTemporaryFile(suffix='.png')
		img.save(file.name)

		return file