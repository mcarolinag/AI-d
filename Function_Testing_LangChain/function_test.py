
#imports for closest_projects


import pandas as pd
#from langchain.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient

from qdrant_client.http.models import Distance, VectorParams
#from langchain_community.vectorstores import Qdrant
from langchain_qdrant import Qdrant
from langchain.schema import Document
from qdrant_client.http import models
from qdrant_client.http.models import Filter, FieldCondition, Range


class DescriptionInput:
    def __init__(self, title,province,description,radius,disable_radius,num_projects,broad_sector):
        self.title = title
        self.province = province
        self.description = description
        self.radius = radius
        self.disable_radius= disable_radius
        self.num_projects =num_projects
        self.broad_sector=broad_sector
    def check(self):
        print(self.title)

#file_path = 'OECD_Project_Data_test_15_projects.xlsx'
file_path = 'OECD_Project_Data_Final(6.1) (sector).csv'
query = pd.read_csv(file_path)
query.head()

test1 = DescriptionInput(query['ProjectTitle'][0], province=query['Province'][0],
                        description=query['LongDescription'][0], radius=200, disable_radius=False, num_projects=5,broad_sector=query['BroadSector'][0] )

#
# test2 = DescriptionInput(query['ProjectTitle'][0], province=query['Province'][0],
#                          description=query['LongDescription'][0], radius=200, disable_radius=True, num_projects=5, broad_sector=query['BroadSector'][0] )

def closest_projects(input: DescriptionInput):
    query_corpus = ('Project Title: ' + input.title + ' ' + 'Description: ' +input.description
                    + ' Province: ' + input.province)


    embedding_model = HuggingFaceEmbeddings(model_name="intfloat/multilingual-e5-large-instruct")

    collection_name = "Iraq aid projects"

    # Local embedded client (on-disk)
    client = QdrantClient(
        path="./qdrant_data"  # make sure no other instance is using this path
    )
    vectorstore = Qdrant(
        client=client,
        collection_name=collection_name,
        embeddings=embedding_model,
    )

    max_distance = input.radius

    if input.disable_radius:

        # Find the closest 5 sentences of the corpus for each query sentence based on cosine similarity
        # We use cosine-similarity and torch.topk to find the highest 5 scores

        similar_docs = vectorstore.similarity_search_with_score(
            query=query_corpus,
            k=input.num_projects,
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.BroadSector",  # Metadata field to filter on
                        match=models.MatchValue(value=input.broad_sector)  # Value to match
                    )
                ]
            )
        )
    else:
        max_distance = input.radius
        key_ = f"distance_{input.province}"
        similar_docs = vectorstore.similarity_search_with_score(
            k=5,
            query=query_corpus,
            filter=models.Filter(must=[models.FieldCondition(
                key=f"metadata.{key_}",
                range=models.Range(lte=max_distance)),
                models.FieldCondition(
                    key="metadata.BroadSector",
                    match=models.MatchValue(value=input.broad_sector))
            ]
            )
        )

    df_test = pd.DataFrame(similar_docs)
    df_test.columns = ['doc', 'score']
    df_test['metadata'] = df_test.apply(lambda x: x['doc'].metadata, axis=1)
    df_results = pd.DataFrame(df_test['metadata'].to_list())
    df_results['score'] = df_test['score']

    return df_results

results1=closest_projects(test1)
print('results1', results1 )

# results2=closest_projects(test2)
# print('results2', results2 )
