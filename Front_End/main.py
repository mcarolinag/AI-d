# Import necessary modules
from fastapi import FastAPI                 # For building the web API
from fastapi.middleware.cors import CORSMiddleware  # To allow communication between frontend and backend
from pydantic import BaseModel               # To define the expected format of incoming JSON data
from get_project import get_projects  


#imports for closest_projects
import torch
from sentence_transformers import SentenceTransformer
import pandas as pd
import geopy.distance

#Connect to Front End
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# Create a FastAPI instance
app = FastAPI()

# Mount the 'static' directory for serving static files like CSS/JS/HTML
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def serve_html():
    with open("static/Ai_d_main.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return html_content

@app.get("/Ai_d_main.html", response_class=HTMLResponse)
async def serve_html():
    with open("static/Ai_d_main.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return html_content

@app.get("/Second_Boot.html", response_class=HTMLResponse)
async def serve_html():
    with open("static/Second_Boot.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return html_content

@app.get("/result.html", response_class=HTMLResponse)
async def serve_html():
    with open("static/result.html", "r", encoding="utf-8") as file:
        html_content = file.read()
    return html_content

# Add CORS middleware to allow the frontend (HTML/JS) to make requests to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # Allow requests from any origin 
    allow_methods=["*"],     # Allow all HTTP methods
    allow_headers=["*"],     # Allow all headers 
)

# Define the format of the data we expect to receive 
# The frontend should send JSON like: { "description": "your input here" }
# In FastAPI the default input object for the input from the frontend is input.xxxx
class DescriptionInput(BaseModel):
    title: str
    province: str
    description: str
    radius: int
    disable_radius: bool
    num_projects: int

def closest_projects(input: DescriptionInput):
    query_corpus = ('Project Title: ' + input.title + ' ' + 'Description: ' + input.description
                    + ' Province: ' + input.province)
    embedder = SentenceTransformer("intfloat/multilingual-e5-large-instruct")
    corpus_embeddings = torch.load('corpus_embeddings.pt').cpu()
    top_k = min(input.num_projects, len(corpus_embeddings))
    query_embedding = embedder.encode(query_corpus, convert_to_tensor=True).cpu()
    
    max_distance = input.radius

    file_path = 'OECD_Project_Data_Final(6.1).xlsx'
    all_projects = pd.read_excel(file_path)

    if input.disable_radius:

        # Find the closest 5 sentences of the corpus for each query sentence based on cosine similarity
        # We use cosine-similarity and torch.topk to find the highest 5 scores
        similarity_scores = embedder.similarity(query_embedding, corpus_embeddings)[0]
        scores, indices = torch.topk(similarity_scores, k=top_k)
        results = pd.DataFrame(list(zip(indices.tolist(), scores.tolist())), columns=['index', 'score'])
        results_info = pd.merge(results, all_projects.reset_index(), on=['index'])

    else:
        coords_file = 'Province_Latitude_Longitude.xlsx'
        province_coords = pd.read_excel(coords_file)
        coords_query_ = province_coords[province_coords['Province'] == input.province]
        coords_query = (coords_query_['Latitude'].values[0], coords_query_['Longitude'].values[0])
        all_projects['distances'] = all_projects[['Latitude', 'Longitude']].apply(
            lambda x: geopy.distance.geodesic(coords_query, (x['Latitude'], x['Longitude'])).km, axis=1)

        max_dist_projects = all_projects[all_projects['distances'] <= max_distance].reset_index()

        # We use cosine-similarity and torch.topk to find the highest 5 scores
        similarity_scores = \
            embedder.similarity(query_embedding, corpus_embeddings[max_dist_projects['index'].values, :])[0]
        scores, indices = torch.topk(similarity_scores, k=top_k)
        results = pd.DataFrame(list(zip(max_dist_projects.iloc[indices.tolist()]['index'].values, scores.tolist())),
                               columns=['index', 'score'])
        results_info = pd.merge(results, max_dist_projects, on=['index'])

    return results_info

# Define a POST route (API endpoint) called /wordcount
# Here the input is the class defined above, (which is the input coming from the frontend)
# input.description is the description object inside the DescriptionInput class
# and we stored the result of the count_words function in word_count value
# And return it in a dictionary because JSON requires a dictionary format to use in the frontend. 
# Later we may call the query function here and store the result in dictionary and return to our frontend. 

# Define a normal function to process the input

# Define a POST route (API endpoint) called /input_check
# This async function calls the input_check() function and returns its result

@app.post("/get_projects")
async def fetch_projects(input: DescriptionInput):
    try:
        df = closest_projects(input)
        return get_projects(df)
    except Exception as e:
        return {"error": str(e)}