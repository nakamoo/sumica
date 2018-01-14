google.charts.load('current', {'packages':['timeline']});
google.charts.setOnLoadCallback(drawChart);

var rows = [['null', Date.now(), Date.now()]]

function drawChart() {
    var container = document.getElementById('timeline');
    var chart = new google.visualization.Timeline(container);
    var dataTable = new google.visualization.DataTable();

    dataTable.addColumn({type: 'string', id: 'timeline'});
    dataTable.addColumn({type: 'string', id: 'segment'});
    dataTable.addColumn({type: 'date', id: 'Start'});
    dataTable.addColumn({type: 'date', id: 'End'});
    dataTable.addRows(rows);

    var options = {
        //timeline: { showRowLabels: false },
        width: 2000
        //backgroundColor: '#000',
        //hAxis: {
        //    textStyle:{color: '#F00'}
        //}
    };

    chart.draw(dataTable, options);
}

$(window).resize(function(){
    drawChart();
});

var updateTimeline = function() {
    $.ajax({
        type: "POST",
        url: "https://homeai.ml:5000/timeline",
        success: function(data, status) {
            var tldata = data["timeline"];
            rows = [];

            for (var i in tldata) {
                var seg = tldata[i];
                var start = new Date(seg["start_time"]*1000.0);
                var end = new Date(seg["end_time"]*1000.0);
                start.setMilliseconds(0);
                end.setMilliseconds(0);
                var count = seg["count"];
                rows.push(['clips', count + " images", start, end]);
            }

            drawChart();

            setTimeout(updateTimeline, 1000);
        },
        error: function(data, status) {

        }
    });
};

updateTimeline();