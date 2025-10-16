from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
import numpy as np
from ml.demand_model import DemandModel

router = APIRouter()

# Load or train your demand forecasting model
model = DemandModel.load_or_train()

# Request schema
class DemandRequest(BaseModel):
    history: List[float]
    days_ahead: int = 7

# POST endpoint for demand prediction
@router.post("/demand")
def predict_demand(req: DemandRequest):
    hist = np.array(req.history, dtype=float)
    
    # Check minimum history length
    if len(hist) < 14:
        return {"error": "Please provide at least 14 days of historical data (daily)."}
    
    # Predict next 'days_ahead' values
    preds = model.predict_next(hist, req.days_ahead)
    
    # Return with key "prediction" to match frontend expectation
    return {"prediction": preds.tolist(), "days_ahead": req.days_ahead}

