# Import necessary modules
from fastapi import FastAPI                 # For building the web API
from fastapi.middleware.cors import CORSMiddleware  # To allow communication between frontend and backend
from pydantic import BaseModel               # To define the expected format of incoming JSON data
from get_project import get_projects  


#imports for closest_projects
import pandas as pd
#from langchain.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient

from qdrant_client.http.models import Distance, VectorParams
from langchain.vectorstores import Qdrant
#from langchain_qdrant import Qdrant
from langchain.schema import Document
from qdrant_client.http import models
from qdrant_client.http.models import Filter, FieldCondition, Range



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



    if input.disable_radius:

        # Find the closest 5 sentences of the corpus for each query sentence based on cosine similarity
        # We use cosine-similarity and torch.topk to find the highest 5 scores

        similar_docs = vectorstore.similarity_search_with_score(
            query=query_corpus,
            k=input.num_projects
        )


    else:
        max_distance = input.radius
        key_ = f"distance_{input.province}"
        similar_docs = vectorstore.similarity_search_with_score(
            k=input.num_projects,
            query=query_corpus,
            filter=models.Filter(must=[models.FieldCondition(key=f"metadata.{key_}",
                                                             range=models.Range(lte=max_distance))])
        )

    df_test = pd.DataFrame(similar_docs)
    df_test.columns = ['doc', 'score']
    df_test['metadata'] = df_test.apply(lambda x: x['doc'].metadata, axis=1)
    df_results = pd.DataFrame(df_test['metadata'].to_list())
    df_results['score'] = df_test['score']

    return df_results
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