
#imports for closest_projects
import torch
from sentence_transformers import SentenceTransformer
import pandas as pd
import geopy.distance

class DescriptionInput:
    def __init__(self, title,province,description,radius,disable_radius,num_projects):
        self.title = title
        self.province = province
        self.description = description
        self.radius = radius
        self.disable_radius= disable_radius
        self.num_projects =num_projects
    def check(self):
        print(self.title)

file_path = 'OECD_Project_Data_test_15_projects.xlsx'
query = pd.read_excel(file_path)
query.head()

test1 = DescriptionInput(query['ProjectTitle'][0], province=query['Province'][0],
                         description=query['LongDescription'][0], radius=200, disable_radius=False, num_projects=5)


test2 = DescriptionInput(query['ProjectTitle'][0], province=query['Province'][0],
                         description=query['LongDescription'][0], radius=200, disable_radius=True, num_projects=5)

def closest_projects(input: DescriptionInput):
    query_corpus = ('Project Title: ' + input.title + ' ' + 'Description: ' +input.description
                    + ' Province: ' + input.province)
    embedder = SentenceTransformer("intfloat/multilingual-e5-large-instruct")
    corpus_embeddings = torch.load('../Front_End/corpus_embeddings.pt')
    top_k = min(input.num_projects, len(corpus_embeddings))
    query_embedding = embedder.encode(query_corpus, convert_to_tensor=True)
    max_distance = input.radius

    file_path = '../Front_End/OECD_Project_Data_Final(6.1).xlsx'
    all_projects = pd.read_excel(file_path)

    if input.disable_radius:

        # Find the closest 5 sentences of the corpus for each query sentence based on cosine similarity
        # We use cosine-similarity and torch.topk to find the highest 5 scores
        similarity_scores = embedder.similarity(query_embedding, corpus_embeddings)[0]
        scores, indices = torch.topk(similarity_scores, k=top_k)
        results=pd.DataFrame(list(zip(indices.tolist(), scores.tolist())), columns=['index','score'])
        results_info=pd.merge(results,all_projects.reset_index(), on=['index'])

    else:
        coords_file= '../Front_End/Province_Latitude_Longitude.xlsx'
        province_coords = pd.read_excel(coords_file)
        coords_query_=province_coords[province_coords['Province']==input.province]
        coords_query = (coords_query_['Latitude'].values[0], coords_query_['Longitude'].values[0])
        all_projects ['distances'] = all_projects [['Latitude', 'Longitude']].apply(
            lambda x: geopy.distance.geodesic(coords_query, (x['Latitude'], x['Longitude'])).km, axis=1)

        max_dist_projects = all_projects [all_projects ['distances'] <= max_distance].reset_index()

        # We use cosine-similarity and torch.topk to find the highest 5 scores
        similarity_scores = \
        embedder.similarity(query_embedding, corpus_embeddings[max_dist_projects['index'].values, :])[0]
        scores, indices = torch.topk(similarity_scores, k=top_k)
        results=pd.DataFrame(list(zip(max_dist_projects.iloc[indices.tolist()]['index'].values, scores.tolist())), columns=['index','score'])
        results_info=pd.merge(results,max_dist_projects, on=['index'])

    return results_info          

results1=closest_projects(test1)


results2=closest_projects(test2)