## setup
* install node+npm (```brew install node```)
* install mongodb
* ```npm install```

## complete launch
* (in hai_server) ```node server.js```
* (in image_handler) ```python imagereceiver.py```
* (in nn_server) ```python detect_server.py```
* (in client) ```python client.py http://127.0.0.1:5000/upload```

## schematic
![](images/diagram.png)

## ports
* 5000: website <-> server
* 5001: server.js <-> imagereceiver.py
* 5002: object detection server
* 27017: mongodb