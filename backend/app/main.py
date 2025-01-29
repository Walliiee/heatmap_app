from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import heatmap

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://172.20.0.1:3000",  # Added this line
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI!"}

app.include_router(heatmap.router)
