import random

def accelerometer():
    spike = random.choices([0,1], weights=[85,15])[0]
    return round(random.uniform(0,0.2) + spike*random.uniform(1,2),2)

def geophone():
    spike = random.choices([0,1], weights=[85,15])[0]
    return round(random.uniform(0,0.5) + spike*random.uniform(1,3),2)

def seismometer():
    spike = random.choices([0,1], weights=[90,10])[0]
    return round(random.uniform(0,0.05) + spike*random.uniform(0.5,1.5),2)
