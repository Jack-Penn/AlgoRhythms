from typing import Union
from fastapi import FastAPI # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from gemini_api import generate_weights

# fastapi dev server.py

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
        return {"status": "success"}

@app.get("/generate-weights")
async def spotify_login(mood: Union[str, None] = None, activity: Union[str, None] = None):
    if(mood is not None and activity is not None):
        weights = await generate_weights(mood, activity)
        return weights
    else:
        return {"error": "Activity or Mood is undefined"}


# @app.get("/items/{item_id}")
# async def read_item(item_id: int, q: Union[str, None] = None):
#     return {"item_id": item_id, "q": q}