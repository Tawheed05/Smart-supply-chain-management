from fastapi import FastAPI
from routers import predict, optimize
import uvicorn

app = FastAPI(title="Hacktrix Logistics API")

app.include_router(predict.router, prefix="/predict", tags=["predict"])
app.include_router(optimize.router, prefix="/optimize", tags=["optimize"])

@app.get("/health")
def health():
    return {"status":"ok", "service":"Hacktrix Logistics API"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
