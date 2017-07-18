(cd hai_server; node server.js) &
(cd nn_server; python detect_server.py) &
(cd image_handler; python imagereceiver.py) &
(cd client; python client.py http://localhost:5000/upload)