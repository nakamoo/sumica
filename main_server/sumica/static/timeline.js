// DOM element where the Timeline will be attached
var container = document.getElementById('timeline');

// Create a DataSet (allows two way data-binding)
var items = new vis.DataSet([]);

var startdate = new Date();
startdate.setHours(startdate.getHours() - 6);
var enddate = new Date();
startdate.setHours(startdate.getHours() + 1);

// Configuration for the Timeline
var options = {
    min: startdate,
    max: enddate,
    height: 100%
};

// Create a Timeline
var timeline = new vis.Timeline(container, items, options);

var updateTimeline = function() {
    $.ajax({
        type: "POST",
        url: "https://homeai.ml:5000/timeline",
        success: function(data, status) {
            var tldata = data.timeline;

            if (tldata.length > 0) {
                rows = [];

                for (var i in tldata) {
                    var seg = tldata[i];
                    var start = new Date(seg["start_time"]*1000.0);
                    var end = new Date(seg["end_time"]*1000.0);
                    start.setMilliseconds(0);
                    end.setMilliseconds(0);
                    var count = seg["count"];
                    var row = {id: i, content: '', start: start, end: end};
                    rows.push(row);
                }

                console.log(rows);

                items.clear();
                items.add(rows);
                //timeline.redraw();
            } else {
                alert("no data for timeline.");
            }

            //setTimeout(updateTimeline, 1000);
        },
        error: function(data, status) {

        }
    });
};

updateTimeline();