import random

def rain_sensor():
    event = random.choices([0,1], weights=[80,20])[0]
    return round(random.uniform(0,10) + event*random.uniform(50,100),1)
