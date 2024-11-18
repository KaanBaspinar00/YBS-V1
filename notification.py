from pushbullet import Pushbullet

API_KEY = "o.22D73CVRXZ0pQQhDKNdfIaK7qVID5940"

file = "notific.txt"

with open(file, mode= 'r') as f:
   text = f.read()

pb = Pushbullet(API_KEY)
push = pb.push_note("Mesaj Geldi: ", text)