import sys
import pandas as pd
import time
import tqdm
import json
import os
import chromadb
sys.path.append('../')
from GigaChat import GigaChat
import dotenv

dotenv.load_dotenv()


chroma_client = chromadb.PersistentClient()
collection = chroma_client.get_or_create_collection(name="okved_collection")

auth_token = os.environ.get('AUTH_TOKEN')

gc = GigaChat(auth_token = auth_token)


df_cl = pd.read_hdf('df_okved_with_embs.h5', key='df')

for n, i in df_cl.iterrows():
    collection.add(documents=[i['text']],
                            ids=[str(n).zfill(3)],
                            embeddings=[i['emb']],
                            metadatas=[{"code": i["code"]}])