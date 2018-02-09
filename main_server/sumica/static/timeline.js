console.log("loading timeline");

// DOM element where the Timeline will be attached
var container = document.getElementById('timeline');

// Create a DataSet (allows two way data-binding)
var items = new vis.DataSet([]);

var startdate = new Date();
startdate.setHours(startdate.getHours() - 12);
var enddate = new Date();
enddate.setHours(enddate.getHours() + 1);

var labelBlacklist = [];

var dataset_graph = new vis.DataSet([]);
var options2 = {
    min: startdate,
    max: enddate,
    start: startdate,
    end: enddate,
    height: '100%',
    drawPoints: false,
    interpolation: {enabled: false},
    shaded: {
        orientation: 'bottom'
    },
    dataAxis: {
        left: {
            title: {
                text: "conf."
            }
        }
    }
    //left: {range: {min:0, max:1}}
};
var graph2d = new vis.Graph2d(document.getElementById('confidence'), dataset_graph, options2);

var groups2 = new vis.DataSet();
graph2d.setGroups(groups2);

// Configuration for the Timeline
var options = {
    min: startdate,
    max: enddate,
    height: '100%',
    stack: false,
    tooltip: {
        followMouse: true,
        overflowMethod: 'cap'
    },
    format: {
        majorLabels: {
            millisecond:'HH:mm:ss',
            second:     'HH:mm',
            minute:     '',
            hour:       '',
            weekday:    '',
            day:        '',
            week:       '',
            month:      '',
            year:       ''
        }
    },
    editable: {
        add: true,
        updateTime: false,
        updateGroup: false,
        remove: true
    },
    snap: function (date, scale, step) {
        var second = 1000;
        return Math.round(date / second) * second;
    },
    onAdd: function (item, callback) {
        if (item.group != 0) {
            callback(null);
        } else {
            prettyPrompt('New label', 'Enter name:', function (value) {
                if (value) {
                    item.content = value;
                    item.myType = "label";
                    item.id = createuuid();
                    callback(item); // send back adjusted new item
                    addLabel(item.id, item.content, item.start.getTime() / 1000);
                } else {
                    callback(null); // cancel item creation
                }
            });
        }
    },
    onRemove: function (item, callback) {
        removeLabel(item.id);
        callback(item); // confirm deletion
    }
};

function prettyPrompt(title, text, callback) {
    swal({
        title: title,
        text: text,
        type: 'input',
        showCancelButton: true,
        inputPlaceholder: '読書'
    }, callback);
}

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

var updateTimeline = function () {
    $.ajax({
        type: "POST",
        url: "/timeline",
        data: JSON.stringify({
            start_time: startdate.getTime() / 1000
        }),
        success: function (data, status) {
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

            // dont clear labels
            var nonlabels = items.get({
                filter: function (item) {
                    return (item.myType != "label");
                }
            });
            items.remove(nonlabels);

            dataset_graph.clear();

            if (tldata.length > 0) {
                // video segments
                rows = [];

                for (var i = 0; i < tldata.length; i++) {
                    var seg = tldata[i];
                    var start = new Date(seg["start_time"] * 1000.0);
                    var end = new Date(seg["end_time"] * 1000.0);
                    start.setMilliseconds(0);
                    end.setMilliseconds(0);
                    var count = seg["count"];
                    var tooltip = '<img class="seg-preview" src="' + seg["img"] + '" >';
                    tooltip += "<p>" + count + " images</p>";
                    tooltip += "<p style='position: relative; bottom: 10px;'>" + start.toTimeString().split(' ')[0] +
                        " ~ " + end.toTimeString().split(' ')[0] + "</p>";
                    var col = "gray";
                    if (i % 2 == 0) {
                        col = "lightGray";
                    }

                    var row = {
                        id: createuuid() + "-seg" + i, group: 2, content: '', start: start, end: end, title: tooltip,
                        color: col, myType: "segment", editable: false
                    };
                    rows.push(row);
                }

                // predictions
                var preds = data.predictions;

                for (var i = 0; i < preds.length; i++) {
                    var seg = preds[i];
                    var start = new Date(seg["start_time"] * 1000.0);
                    var end = new Date(seg["end_time"] * 1000.0);
                    var c = seg["class"];
                    var tooltip = data.classes[c];
                    start.setMilliseconds(0);
                    end.setMilliseconds(0);
                    var row = {
                        id: createuuid(), group: 1, content: '', start: start, end: end, title: tooltip,
                        color: "hsl(" + c * 100 + ", 75%, 50%)", myType: "prediction", editable: false
                    };
                    rows.push(row);
                }

                items.add(rows);

                var graph_rows = [];
                groups2.clear();

                for (var i = 0; i < data.confidences.length; i++) {
                    var gid = i;
                    groups2.add({id: gid, content: "", className: "areachart"});

                    for (var k = 0; k < data.confidences[i].length; k++) {
                        var row = {x: new Date(data.conf_times[i][k] * 1000.0), y: data.confidences[i][k], group: gid};
                        graph_rows.push(row);
                    }
                }

                dataset_graph.add(graph_rows);
            } else {
                console.log("no data for timeline.");
            }


            var labels = data.label_data;

            // for labels, add only new labels
            for (var i = 0; i < labels.length; i++) {
                if (items.get(labels[i]["id"]) == null && !labelBlacklist.includes(labels[i]["id"])) {
                    items.add([{
                        id: labels[i]["id"], group: 0, content: labels[i]["label"],
                        start: new Date(labels[i]["time"] * 1000.0),
                        //subgroup: Math.floor(Math.random() * 10000000),
                        myType: "label"
                    }]);
                } else {
                }
            }

            if (!firstUpdate) {
                timeline.removeCustomTime("lastFixed");
            }

            timeline.addCustomTime(new Date(data.segments_last_fixed * 1000.0), "lastFixed");

            firstUpdate = false;

            if (UPDATE_TIMELINE > 0) {
                setTimeout(updateTimeline, UPDATE_TIMELINE * 1000);
            }

        },
        error: function (err) {
            console.log(err);
        }
    });
};

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
timeline.on('select', function(props) {
    var iid = props.items[0];
    var i = iid.indexOf("seg");
    //console.log(iid.substring(i+3, iid.length));

});

graph2d.on('_change', function () {
    visLabelSameWidth();
});

$(window).resize(function () {
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
        $("#timeline .vis-labelset .vis-label").width(w1 + "px");
    }
}

updateTimeline();
visLabelSameWidth();

var addLabel = function (id, name, time) {
    console.log("adding label " + id);
    console.log(time);

    $.ajax({
        type: "POST",
        url: "/label",
        data: JSON.stringify({
            type: 'add',
            username: 'sean',
            time: time,
            id: id,
            label: name
        }),
        success: function(data) {
            //updateFlowchart(true);
        }
    });
    //newLabelNode(0, 0, name, id);
};

var removeLabel = function(id) {
    console.log("removing label " + id);
    labelBlacklist.push(id);

    $.ajax({
        type: "POST",
        url: "/label",
        data: JSON.stringify({
            type: 'remove',
            username: 'sean',
            id: id
        }),
        success: function(data) {
            //setTimeout(function() {updateFlowchart(true)},
        }
    });
};