
import pandas as pd
import geopy.distance
from langchain.vectorstores import Qdrant
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

#Loading the data
file_path = 'OECD_Project_Data_Final(6.1) (sector).csv'


all_projects = pd.read_csv(file_path)

all_projects=all_projects[['Year', 'DonorCode', 'DonorName', 'AgencyName', 'CrsID',
       'RecipientName', 'RegionName', 'FlowName', 'USD_Commitment',
       'CurrencyCode', 'ShortDescription', 'ProjectTitle', 'Province',
       'Latitude', 'Longitude', 'PurposeCode', 'PurposeName', 'SectorCode',
       'SectorName', 'ExpectedStartDate', 'CompletionDate', 'LongDescription',
       'Name_of_Donor','BroadSector']].reset_index().rename(columns={'index':'doc_id'})

coords_file= 'Province_Latitude_Longitude.xlsx'
province_coords = pd.read_excel(coords_file)


for prov in province_coords['Province'].unique():
  key_=f"distance_{prov}"
  df_prov=province_coords[province_coords['Province']==prov]
  coords_prov = (df_prov['Latitude'].iloc[0], df_prov['Longitude'].iloc[0])
  all_projects[key_]= all_projects[['Latitude','Longitude']].apply(
      lambda x: geopy.distance.geodesic(coords_prov, (x['Latitude'],x['Longitude'])).km, axis=1)



corpus=('ProjectTitle: '+all_projects['ProjectTitle']+ ' '+'ShortDescription: '+all_projects['ShortDescription']+
        ' '+'LongDescription: '+all_projects['LongDescription']+' Province: '+all_projects['Province'])


# # 1. Initialize the embedding model
embedding_model = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large-instruct")

# # 2. Set up Qdrant client (local path)

collection_name = "Iraq aid projects"

# Local embedded client (on-disk)
client = QdrantClient(
    path="./qdrant_data"  # make sure no other instance is using this path
)

# # 2. Your documents and metadata
texts = corpus.values
metadatas =  all_projects.to_dict(orient='records')

# # 5. Split into chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=10)
docs = []
for text, metadata in zip(texts, metadatas):
    docs.extend(splitter.create_documents([text], metadatas=[metadata]))

# # 6. Create LangChain-compatible Qdrant vectorstore

client.create_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(
        size=embedding_model.embed_query("test").__len__(),
        distance=Distance.COSINE
    )
)

# Upload documents to vector store
vectorstore = Qdrant(
    client=client,
    collection_name=collection_name,
    embeddings=embedding_model,
)
vectorstore.add_documents(documents=docs)
