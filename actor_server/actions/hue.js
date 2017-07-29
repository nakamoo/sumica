var hue = require("node-hue-api");
var HueApi = require("node-hue-api").HueApi;
var fs = require('fs');

var displayBridges = function(bridge) {
	//console.log("Hue Bridges Found: " + JSON.stringify(bridge));
};

hue.nupnpSearch(function(err, result) {
	if (err) throw err;
	displayBridges(result);
	connect(result[0]["ipaddress"], "ybh9yzkJXCwzmGVjbaWcFU28i5V0WVcz0IdJ9WtO");
});

var register = function(ip) {
	console.log("registering");

	var host = ip,
	    userDescription = "Node API";

	var displayUserResult = function(result) {
	    console.log("Created user: " + JSON.stringify(result));
	    // save name
	    connect(ip, result);
	};

	var displayError = function(err) {
	    console.log(err);
	};

	var hue = new HueApi();

	// --------------------------
	// Using a callback (with default description and auto generated username)
	hue.createUser(host, function(err, user) {
		if (err) console.log(err);
		displayUserResult(user);
	});
}

var connect = function(ip, user) {
	var HueApi = require("node-hue-api").HueApi;

	var displayResult = function(result) {
	    //console.log(JSON.stringify(result, null, 2));

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

	// --------------------------
	// Using a callback
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

	cmd = process.argv[2];

	if (cmd == "get_state") {
		api.lights()
		    .then(displayResult)
		    .done();
	} else if (cmd == "set_state") {
		console.log("setting state");
		var state = JSON.parse(fs.readFileSync('actions/hue_state.json', 'utf8'))

		api.setLightState(3, state, function(err, lights) {
		    if (err) throw err;
		    displayResult(lights);
		});
	}
}