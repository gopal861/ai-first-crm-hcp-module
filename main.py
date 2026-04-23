from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agent.graph import graph

app = FastAPI()

# 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat")
def chat(data: dict):
    return graph.invoke({"input": data["input"]})
