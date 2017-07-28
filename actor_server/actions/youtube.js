var YouTube = require('youtube-node');
var sys = require('util')
var exec = require('child_process').exec;

var youTube = new YouTube();

youTube.setKey('AIzaSyB1OOSpTREs85WUMvIgJvLTZKye4BVsoFU');

console.log("starting yt");

youTube.search(process.argv.slice(2).join(" "), 1, function(error, result) {
  if (error) {
    console.log(error);
  }
  else {
    console.log(result)
    var id = result["items"][0]["id"]["videoId"];
    console.log(id);

    exec("google-chrome https://www.youtube.com/watch?v=" + id, function(err, stdout, stderr) {
	  console.log(stdout);
	});
  }
});