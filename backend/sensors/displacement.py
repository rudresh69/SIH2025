import random

def crack_sensor():
    spike = random.choices([0,1], weights=[80,20])[0]
    return round(random.uniform(0,0.1) + spike*random.uniform(3,5),2)

def inclinometer():
    drift = random.uniform(0,0.5)
    jump = random.choices([0,1], weights=[90,10])[0]
    return round(drift + jump*random.uniform(1,2),2)

def extensometer():
    drift = random.uniform(0,0.2)
    jump = random.choices([0,1], weights=[85,15])[0]
    return round(drift + jump*random.uniform(1,2),2)
