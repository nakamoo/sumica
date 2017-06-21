var express = require("express");
var fs = require('fs');
var app = express();
var path = __dirname + '/views/';

/*app.get("/", function(req, res){
  res.sendFile(path + "index.html");
});*/

app.get('/detect', function(req, res) {
	console.log("image received");
});

app.listen(5000, function(){
  console.log("Live at port 5000");
});
