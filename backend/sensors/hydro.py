import random

def moisture_sensor():
    rise = random.choices([0,1], weights=[80,20])[0]
    return round(random.uniform(20,30) + rise*random.uniform(20,50),1)

def piezometer():
    rise = random.choices([0,1], weights=[80,20])[0]
    return round(random.uniform(0,10) + rise*random.uniform(20,40),1)
