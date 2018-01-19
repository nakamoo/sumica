// DOM element where the Timeline will be attached
var container = document.getElementById('timeline');

// Create a DataSet (allows two way data-binding)
var items = new vis.DataSet([]);

var startdate = new Date();
startdate.setHours(startdate.getHours() - 6);
var enddate = new Date();
enddate.setHours(enddate.getHours() + 1);

var dataset_graph = new vis.DataSet([]);
var options2 = {
    min: startdate,
    max: enddate,
    start: startdate,
    end: enddate,
    height: '100%',
    drawPoints: false//,
    //interpolation: {enabled:false}
};
var graph2d = new vis.Graph2d(document.getElementById('confidence'), dataset_graph, options2);

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
    {id: 1, content: 'predictions'},
    {id: 2, content: 'camera'}
]);

// Create a Timeline
var timeline = new vis.Timeline(container);
timeline.setOptions(options);
timeline.setItems(items);
timeline.setGroups(groups);

var firstUpdate = true;

var rng = function() {  return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15); };

var updateTimeline = function() {
    $.ajax({
        type: "POST",
        url: "https://homeai.ml:5000/timeline",
        success: function(data, status) {
            var tldata = data.timeline;

            if (firstUpdate) {
                // override rendering code
                var RangeItem = vis.timeline.components.items.RangeItem;
                RangeItem.prototype.origRedraw = RangeItem.prototype.redraw;
                RangeItem.prototype.redraw = function (returnQueue) {
                    // first invoke the original redraw
                    var re = this.origRedraw(returnQueue);

                    if (this.dom != null) {
                        this.dom.box.style.backgroundColor = this.data.color;
                        this.dom.box.style.borderColor = "transparent";
                    }

                    return re;
                };
            }

            items.clear();
            dataset_graph.clear();

            if (tldata.length > 0) {
                // video segments
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
                    var row = {id: rng(), group: 2, content: '', start: start, end: end, title: tooltip, color: "hsl(" + i*100 + ", 75%, 50%)"};
                    rows.push(row);
                }

                // predictions
                for (var i = 0; i < data.predictions.length; i) {
                    var seg = data.predictions[i];
                    var start = new Date(seg["start_time"]*1000.0);
                    var end = new Date(seg["end_time"]*1000.0);
                    var c = seg["class"];
                    var tooltip = data.classes[c];
                    start.setMilliseconds(0);
                    end.setMilliseconds(0);
                    var row = {id: rng(), group: 1, content: '', start: start, end: end, title: tooltip, color: "hsl(" + c*100 + ", 75%, 50%)"};
                    rows.push(row);
                }

                items.add(rows);

                var graph_rows = [];
                for (var i = 0; i < data.confidences.length; i++) {
                    var row = {x: new Date(data.times[i]*1000.0), y: data.confidences[i]};
                    graph_rows.push(row);
                }

                dataset_graph.add(graph_rows);
            } else {
                alert("no data for timeline.");
            }

            var labels = data.label_data;

            for (var i = 0; i < labels.length; i++) {
                items.add([{id: rng(), group: 0, content: labels[i]["label"],
                    start: new Date(labels[i]["time"]*1000.0)
                    //subgroup: Math.floor(Math.random() * 10000000)
                }]);
            }

            if (!firstUpdate) {
                timeline.removeCustomTime("lastFixed");
            }

            timeline.addCustomTime(new Date(data.segments_last_fixed * 1000.0), "lastFixed");

            firstUpdate = false;
            //setTimeout(updateTimeline, 5000);
        },
        error: function(data, status) {

        }
    });
};

updateTimeline();

//$(window).resize(function(){
//    timeline.redraw();
//});

// stacking charts
function onChangeGraph(range) {
    if (!range.byUser) {
      return;
    }

    timeline.setOptions({
      start: range.start,
      end: range.end,
      height: '100%'
  });
}

function onChangeTimeline(range) {
    if (!range.byUser) {
      return;
    }

    graph2d.setOptions({
      start: range.start,
      end: range.end,
      height: '100%'
  });
}

graph2d.on('rangechange', onChangeGraph);
timeline.on('rangechange', onChangeTimeline);


graph2d.on('_change', function() {
  visLabelSameWidth();
});

$(window).resize(function(){
  visLabelSameWidth();
});

// Vis same width label.
function visLabelSameWidth() {
    var ylabel_width = $("#timeline .vis-labelset .vis-label").width() + "px";
    //$("#confidence")[0].childNodes[0].childNodes[2].style.left = ylabel_width;
    //$("#confidence .vis-content")[1].style.width = ylabel_width;
    //$("#confidence .vis-content.vis-data-axis").style.width = ylabel_width;

    var w1 = $("#confidence .vis-content .vis-data-axis").width();
    var w2 = $("#timeline .vis-labelset .vis-label").width();

    $("#confidence")[0].childNodes[0].childNodes[2].style.display = 'none';

    if (w2 > w1) {
        $("#confidence .vis-content")[1].style.width = ylabel_width;
    }
    else {
        $("#timeline .vis-labelset .vis-label").width(w1+"px");
    }
}

visLabelSameWidth();