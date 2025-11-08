ffrom fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 👇 Replace this URL with your actual frontend Cloud Run URL once it's deployed
origins = [
    "https://rnrltradehub-frontend-nonprod-<projectid>.us-central1.run.app",
    "https://rnrltradehub-nonprod-502095789065.us-central1.run.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "RNRL TradeHub NonProd API is running!"}

