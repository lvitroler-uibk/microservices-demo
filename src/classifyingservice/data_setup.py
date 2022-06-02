from PIL import Image
import numpy as np 
import pandas as pd 
import os


#If you run this cell in  as a Kaggle's notebook:
DATASET_PATH = "products/"

# Reading the rows and dropping the ones with errors
df = pd.read_csv(DATASET_PATH + "styles.csv", nrows=44416, error_bad_lines=False)
df['image'] = df.apply(lambda row: str(row['id']) + ".jpg", axis=1)
df = df.reset_index(drop=True)

N_Pictures = 250
N_Classes = np.sum(df.articleType.value_counts().to_numpy() > N_Pictures)

#Inspecting the item classes that made it to our new dataset
temp = df.articleType.value_counts().sort_values(ascending=False)[:N_Classes]
items_count = temp.values
items_label = temp.index.tolist()

#Creating new dataframes for training/validation
df_train = pd.DataFrame(columns=['articleType','image'])
df_val   = pd.DataFrame(columns=['articleType','image'])

for ii in range(0,N_Classes):
    temp = df[df.articleType==items_label[ii]].sample(N_Pictures)

    df_train = pd.concat([df_train, temp[ :int(N_Pictures*0.6) ][['articleType','image']] ]            , sort=False)
    df_val   = pd.concat([df_val,   temp[  int(N_Pictures*0.6): N_Pictures ][['articleType','image']] ], sort=False)

df_train.reset_index(drop=True)
df_val.reset_index(drop=True)

#Create folders for new dataset
os.mkdir('data')
os.mkdir('data/train')
os.mkdir('data/val')

data = {'train': df_train, 'val': df_val}

# and save each individual image to the new directory
for x in ['train','val']:
    for label, file in data[x].values:
        
        try:
            img = Image.open(DATASET_PATH+'images/'+file)
        except FileNotFoundError:
            # If file does not exist continue
            continue
            
        #Else save file to new directory  
        try:
            img.save('data/'+x+'/'+label+'/'+file) 
        except FileNotFoundError:
            #If folder does not exist, create one and save the image
            os.mkdir('data/'+x+'/'+label)
            img.save('data/'+x+'/'+label+'/'+file)