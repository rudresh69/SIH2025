from fastapi import FastAPI
import time

# Import sensor functions
from sensors.sesmic import accelerometer, geophone, seismometer
from sensors.displacement import crack_sensor, inclinometer, extensometer
from sensors.hydro import moisture_sensor, piezometer
from sensors.environmental import rain_sensor

app = FastAPI()

@app.get("/sensor/sesmic")
def get_vibration():
    return {
        "accelerometer": accelerometer(),
        "geophone": geophone(),
        "seismometer": seismometer(),
        "timestamp": time.time()
    }

@app.get("/sensor/displacement")
def get_displacement():
    return {
        "crack": crack_sensor(),
        "inclinometer": inclinometer(),
        "extensometer": extensometer(),
        "timestamp": time.time()
    }

@app.get("/sensor/hydro")
def get_hydro():
    return {
        "moisture": moisture_sensor(),
        "piezometer": piezometer(),
        "timestamp": time.time()
    }

@app.get("/sensor/environment")
def get_environment():
    return {
        "rain": rain_sensor(),
        "timestamp": time.time()
    }

@app.get("/risk-level")
def get_risk():
    acc = accelerometer()
    geo = geophone()
    seis = seismometer()
    crack = crack_sensor()
    moisture = moisture_sensor()
    rain = rain_sensor()

    vibration_score = max(acc, geo, seis)
    if (vibration_score>1.5 or crack>3) and rain>50:
        risk = "HIGH"
    elif vibration_score>0.5 or crack>1:
        risk = "MEDIUM"
    else:
        risk = "LOW"

    return {
        "risk_level": risk,
        "accelerometer": acc,
        "geophone": geo,
        "seismometer": seis,
        "crack": crack,
        "moisture": moisture,
        "rain": rain,
        "timestamp": time.time()
    }
