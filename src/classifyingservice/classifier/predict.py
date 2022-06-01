from PIL import Image
from torchvision import models, transforms
from io import BytesIO

import torch
import torch.nn as nn
import requests

class_names = [
    'Backpacks', 
    'Belts', 
    'Bra', 
    'Briefs', 
    'Caps', 
    'Casual Shoes', 
    'Clutches', 
    'Deodorant', 
    'Dresses', 
    'Earrings', 
    'Flats', 
    'Flip Flops', 
    'Formal Shoes', 
    'Handbags', 
    'Heels', 
    'Jackets', 
    'Jeans', 
    'Kurtas', 
    'Lipstick', 
    'Nail Polish', 
    'Perfume and Body Mist', 
    'Sandals', 
    'Sarees', 
    'Shirts', 
    'Shorts', 
    'Socks', 
    'Sports Shoes', 
    'Sunglasses', 
    'Sweaters', 
    'Sweatshirts', 
    'Ties', 
    'Tops', 
    'Track Pants', 
    'Trousers', 
    'Tshirts', 
    'Wallets', 
    'Watches'
    ]

# Data augmentation and normalization for training
# Just normalization for validation
data_transforms = {
    'val': transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ]),
}

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
model_ft = models.resnet18(pretrained=True)
num_ftrs = model_ft.fc.in_features

#Changing the number of outputs in the last layer to the number of different item types
model_ft.fc = nn.Linear(num_ftrs, len(class_names))

model_ft = model_ft.to(device)
model = model_ft
model.load_state_dict(torch.load('model_fine_tuned.pt', device))
model.eval()

torch.no_grad()

class Classifier():
    def Predict(self, host, pictureName):
        response = requests.get("http://" + host + pictureName)
        img = Image.open(BytesIO(response.content))
        img_t = data_transforms['val'](img).unsqueeze(0)
        img_t = img_t.to(device)
        outputs = model(img_t)
        _, preds = torch.max(outputs, 1)

        return class_names[int(preds.cpu().numpy())]

