var express = require("express");
var fs = require('fs');
var formidable = require('formidable');
var app = express();
var zerorpc = require("zerorpc");

var vision = new zerorpc.Client();
vision.connect("tcp://127.0.0.1:5001");

app.post('/upload', function(req, res) {
	//console.log("image received");

	var form = new formidable.IncomingForm();
	form.parse(req, function (err, fields, files) {
		var oldpath = files.image.path;
		var d = new Date();
      	var newpath = __dirname + '/images/' + d.getTime() + ".png";

      	fs.readFile(oldpath, function (err, data) {
            if (err) throw err;
            //console.log('File read!');

            // Write the file
            fs.writeFile(newpath, data, function (err) {
                if (err) throw err;
                //console.log('File written!');		

				vision.invoke("newimage", newpath, function(error, res, more) {
					//console.log(res.toString('utf8'))
				});
            });

            // Delete the file
            fs.unlink(oldpath, function (err) {
                if (err) throw err;
                //console.log('File deleted!');
            });
        });
    });

	res.send("ok");
});

app.listen(5000, function(){
  console.log("Live at port 5000");
});
