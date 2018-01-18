// DOM element where the Timeline will be attached
var container = document.getElementById('timeline');

// Create a DataSet (allows two way data-binding)
var items = new vis.DataSet([]);

var startdate = new Date();
startdate.setHours(startdate.getHours() - 6);
var enddate = new Date();
enddate.setHours(enddate.getHours() + 1);

// Configuration for the Timeline
var options = {
    min: startdate,
    max: enddate,
    height: '100%',
    stack: false,
    tooltip: {
      followMouse: true,
      overflowMethod: 'cap'
    }
};

var groups = new vis.DataSet([
    {id: 0, content: 'events'},
    {id: 1, content: 'camera'}
]);

// Create a Timeline
var timeline = new vis.Timeline(container);
timeline.setOptions(options);
timeline.setItems(items);
timeline.setGroups(groups);

var updateTimeline = function() {
    $.ajax({
        type: "POST",
        url: "https://homeai.ml:5000/timeline",
        success: function(data, status) {
            var tldata = data.timeline;

            if (tldata.length > 0) {
                items.clear();
                rows = [];

                for (var i = 0; i < tldata.length; i++) {
                    var seg = tldata[i];
                    var start = new Date(seg["start_time"]*1000.0);
                    var end = new Date(seg["end_time"]*1000.0);
                    start.setMilliseconds(0);
                    end.setMilliseconds(0);
                    var count = seg["count"];
                    var tooltip = '<img src="' + seg["img"] + '" >';
                    tooltip += "<p>" + count + " images</p>";
                    var row = {id: i, group: 1, content: '', start: start, end: end, title: tooltip};
                    rows.push(row);
                }

                items.add(rows);
                //timeline.redraw();

                var bars = $(".vis-group").children().filter(".vis-item");

                for (var i = 0; i < bars.length; i++) {
                    var bar = bars[i];
                    //console.log(bar);
                    bar.style.backgroundColor = "hsl(" + i*100 + ", 50%, 50%)";
                }
            } else {
                alert("no data for timeline.");
            }

            var labels = data.label_data;

            for (var i = 0; i < labels.length; i++) {
                items.add([{id: tldata.length+i, group: 0, content: labels[i]["label"], start: new Date(labels[i]["time"]*1000.0)}]);
            }

            setTimeout(updateTimeline, 1000);
        },
        error: function(data, status) {

        }
    });
};

updateTimeline();

//$(window).resize(function(){
//    timeline.redraw();
//});