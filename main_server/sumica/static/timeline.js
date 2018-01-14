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
      timeline: { showRowLabels: false }
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
                rows.push(['timeline', ""+i, new Date(seg[0]*1000.0), new Date(seg[1]*1000.0)]);
            }

            drawChart();

            setTimeout(updateTimeline, 100);
        },
        error: function(data, status) {

        }
    });
};

updateTimeline();