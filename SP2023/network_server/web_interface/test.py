import random, requests, time

url_ = "http://localhost:7777/sensor"
door_status = ['open', 'closed']


while True:
    smoke = random.randint(0, 100)
    mono = random.randint(0, 50)
    door = random.choice(door_status)
    resp = requests.post(url_, data={"smoke": f"{mono} {smoke} {door}"})
    time.sleep(3)