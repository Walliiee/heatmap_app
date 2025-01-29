from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import heatmap  # adjust if your file name or path is different

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
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

# Include the heatmap router
app.include_router(heatmap.router)
