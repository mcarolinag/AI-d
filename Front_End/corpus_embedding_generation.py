import torch
from sentence_transformers import SentenceTransformer
import pandas as pd

file_path = 'OECD_Project_Data_Final(6.1).xlsx'
all_projects = pd.read_excel(file_path)


corpus=('ProjectTitle: '+all_projects['ProjectTitle']+ ' '+'ShortDescription: '+all_projects['ShortDescription']+
        ' '+'LongDescription: '+all_projects['LongDescription']+' Province: '+all_projects['Province'])

embedder = SentenceTransformer("intfloat/multilingual-e5-large-instruct")

corpus_embeddings = embedder.encode(corpus.values, convert_to_tensor=True)

torch.save(corpus_embeddings , "corpus_embeddings.pt")