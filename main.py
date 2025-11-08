from fastapi import FastAPI
import os
import uvicorn

app = FastAPI(title="RNRL TradeHub NonProd API")

@app.get("/")
def read_root():
    return {"message": "RNRL TradeHub NonProd API is running!"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
