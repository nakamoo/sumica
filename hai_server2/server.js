var express = require("express");
var fs = require('fs');
var bodyParser = require('body-parser')
var app = express();
var path = __dirname + '/views/';

/*app.get("/", function(req, res){
  res.sendFile(path + "index.html");
});*/

app.post('/upload', function(req, res) {
	console.log("image received");
});

app.listen(5000, function(){
  console.log("Live at port 5000");
});
