# Import necessary modules
from fastapi import FastAPI                  # For building the web API
from fastapi.middleware.cors import CORSMiddleware  # To allow communication between frontend and backend
from pydantic import BaseModel               # To define the expected format of incoming JSON data

# Create a FastAPI instance
app = FastAPI()

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

def input_check(input: DescriptionInput):
    result = {
        "Title": input.title,
        "Province": input.province,
        "Description": input.description,
        "DisableRadius": input.disable_radius,
        "NumProjects": input.num_projects
    }

    # Only include Radius if DisableRadius is False
    if not input.disable_radius:
        result["Radius"] = input.radius

    return result
# Define a POST route (API endpoint) called /wordcount
# Here the input is the class defined above, (which is the input coming from the frontend)
# input.description is the description object inside the DescriptionInput class
# and we stored the result of the count_words function in word_count value
# And return it in a dictionary because JSON requires a dictionary format to use in the frontend. 
# Later we may call the query function here and store the result in dictionary and return to our frontend. 

# Define a normal function to process the input

# Define a POST route (API endpoint) called /input_check
# This async function calls the input_check() function and returns its result
@app.post("/input_check")
async def check_output(input: DescriptionInput):
    return input_check(input)