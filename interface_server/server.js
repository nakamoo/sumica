var express = require("express");
var fs = require('fs');
var formidable = require('formidable');
var app = express();
var zerorpc = require("zerorpc");
var MongoClient = require('mongodb').MongoClient;
var moment = require('moment');
var bodyParser = require('body-parser')

app.use(bodyParser.urlencoded({ extended: true }));

var vision = new zerorpc.Client();
vision.connect("tcp://127.0.0.1:5001");

var dburl = "mongodb://localhost:27017/hai";
app.use(express.static(__dirname + '/public'));

// webpages

app.get('/', function (req, res) {
  res.sendFile(__dirname + '/views/index.html')
})

app.get('/upload', function(req, res) {
    res.sendFile(__dirname + '/views/upload.html')
})

app.get('/shell', function(req, res) {
    res.sendFile(__dirname + '/views/shell.html')
})

// to-server operations

app.post('/record_act', function (req, res) {
    MongoClient.connect(dburl, function(err, db) {
        if (err) throw err;
        console.log("Database connected; recording command [" + req.body.app + ": " + req.body.cmd + "]");

        var d = moment().toDate();

        var data = {time: d, app: req.body.app, action: req.body.cmd};

        db.collection("actions").insertOne(data, function(err, res) {
            if (err) throw err;
            console.log("Command recorded.");

            vision.invoke("new_act", JSON.stringify(data), function(error, res, more) {});
            db.close();
        });

        db.close();
    });

    res.sendFile(__dirname + '/views/index.html')
})

app.post('/upload', function(req, res) {
	//console.log("image received");

	var form = new formidable.IncomingForm();
	form.parse(req, function (err, fields, files) {
		var oldpath = files.image.path;
		var d = moment().utc().valueOf();
        //console.log(d);
      	var newpath = __dirname + '/../captures/' + d + ".png";

      	fs.readFile(oldpath, function (err, data) {
            if (err) throw err;
            //console.log('File read!');

            // Write the file
            fs.writeFile(newpath, data, function (err) {
                if (err) throw err;
                //console.log('File written!');		

				vision.invoke("newimage", newpath, function(error, res, more) {
					if (error) {
                        fs.unlink(newpath, function (err) {
                            console.log("error; deleting captured image");
                        });
                    }
				});
            });

            // Delete the file
            fs.unlink(oldpath, function (err) {
                if (err) throw err;
            });
        });
    });

	res.send("ok");
});

app.listen(5000, "0.0.0.0");