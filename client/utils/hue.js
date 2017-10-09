var hue = require("node-hue-api");
var HueApi = require("node-hue-api").HueApi;
var fs = require('fs');

cmd = process.argv[2];

//console.log("searching for Hues");
hue.nupnpSearch(function(err, result) {
	if (err) throw err;
	console.log("Hue Bridges Found: " + JSON.stringify(result));
	ip = result[0]["ipaddress"];

	if (fs.existsSync(__dirname + '/hue_user.txt')) {
		if (cmd != "connect") {
	    	connect(ip, fs.readFileSync(__dirname + '/hue_user.txt', 'utf8'));
		}
	    console.log("ok");
	} else {
		register(ip);
	}
});

var register = function(ip) {
	console.log("registering");

	var host = ip, userDescription = "Node API";
	var hue = new HueApi();

	hue.createUser(host, function(err, user) {
		if (err) {
			console.log(err);
		} else {
			console.log("Created user: " + JSON.stringify(user));

			fs.writeFileSync(__dirname + "/hue_user.txt", user); 

	    	//connect(ip, user);
	    	console.log("ok");
		}
	});
}

var connect = function(ip, user) {
	var displayResult = function(result) {
	    if (!result.hasOwnProperty('ipaddress')) {
	    	console.log("not registered");
	    	register(ip);
	    } else {
	    	manage(ip, user);
	    }
	};

	var host = ip,
	    username = user,
	    api;

	api = new HueApi(host, username);

	api.config(function(err, config) {
	    if (err) throw err;
	    displayResult(config);
	});
}

var manage = function(ip, user) {
	var HueApi = require("node-hue-api").HueApi;

	var displayResult = function(result) {
	    console.log(JSON.stringify(result));
	};

	var host = ip,
    username = user,
    api;

	api = new HueApi(host, username);

	if (cmd == "get_state") {
		api.lights()
		    .then(displayResult)
		    .done();
	} else if (cmd == "set_state") {
		console.log("setting state");
		var state = JSON.parse(fs.readFileSync(__dirname + '/hue_state.json', 'utf8'))

		for (var i = 0; i < state.length; i++) { //for now, control all
			api.setLightState(state[i]["id"], state[i]["state"], function(err, lights) {
				console.log(err);
			    if (err) throw err;
			    displayResult(lights);
			});
		}
	}
}
