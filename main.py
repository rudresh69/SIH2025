from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variable to store current mode
ALERT_MODE = {"mode": "emergency", "location": "NMIET HOSTEL"}

@app.get("/alert")
def get_alert():
    return ALERT_MODE

@app.post("/alert/{mode}")
def set_alert(mode: str):
    global ALERT_MODE
    if mode not in ["safe", "warning", "emergency"]:
        return {"error": "Invalid mode"}
    ALERT_MODE["mode"] = mode
    return ALERT_MODE
