#! /bin/sh

mkdir -p ~/.kaggle
cp kaggle.json ~/.kaggle/kaggle.json
chmod 600 ~/.kaggle/kaggle.json
kaggle datasets download -d paramaggarwal/fashion-product-images-small
unzip fashion-product-images-small.zip -d products 
python classifyingservice/data_setup.py
python classifyingservice/train.py
python classifyingservice/classifying_server.py
