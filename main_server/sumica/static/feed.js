
var ctx = document.getElementById("predCanvas").getContext('2d');
ctx.height = 500;
var myChart = new Chart(ctx, {
    type: 'horizontalBar',
    data: {
        labels: [],
        datasets: [{}]
    },
    options: {
        legend: { display: false },
        scales: {
            xAxes: [{
                display: true,
                ticks: {
                    min: 0,
                    max: 1
                }
            }],
            yAxes: [{
                ticks: {
                    fontSize: 14
                }
            }]
        },
        title: {
            display: true,
            text: 'predictions',
            fontSize: 14
        },
        responsive: true,
        maintainAspectRatio: false
    }
});
Chart.defaults.global.defaultFontColor = "#fff";

function hslToRgb(h, s, l){
    var r, g, b;

    if(s == 0){
        r = g = b = l; // achromatic
    }else{
        var hue2rgb = function hue2rgb(p, q, t){
            if(t < 0) t += 1;
            if(t > 1) t -= 1;
            if(t < 1/6) return p + (q - p) * 6 * t;
            if(t < 1/2) return q;
            if(t < 2/3) return p + (q - p) * (2/3 - t) * 6;
            return p;
        }

        var q = l < 0.5 ? l * (1 + s) : l + s - l * s;
        var p = 2 * l - q;
        r = hue2rgb(p, q, h + 1/3);
        g = hue2rgb(p, q, h);
        b = hue2rgb(p, q, h - 1/3);
    }

    return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)];
}

var feed = document.getElementById("feed");
var counter = 0;

var updateFeed = function() {
    var get_images = false;

    if (UPDATE_CAMFEED > 0) {
        get_images = counter % UPDATE_CAMFEED == 0
    }

    $.ajax({
        type: "POST",
        url: "/feed",
        data: JSON.stringify({
            get_images: get_images
        }),
        success: function(data, status) {
            if (data.images && data.images.length > 0) {
                var imgs = "";

                for (var i = 0; i < data.images.length; i++) {
                    card = "";
                    card += "<div class='card text-white bg-dark text-center'>" +
                        "<div class='card-block'>" +
                        "<p class='card-text'>" + data.images[i]["name"] + "</p>" +
                        "</div>";
                    card += '<img class="card-img-bottom feedImage" src=' + 'data:image/jpeg;base64,' + data.images[i]["img"] + '>';
                    card += "</div>";
                    imgs += card;
                }

                feed.innerHTML = imgs;
            } else if (UPDATE_CAMFEED < 0) {
                feed.innerHTML =
                    "<div class='card text-white bg-dark text-center'>" +
                    "<div class='card-block'>" +
                    "<p class='card-text'>NO FEED</p>" +
                    "</div>" +
                    "</div>";
            }

            if (data.classes.length > 0) {
                // is js retarded?
                if (myChart.data.labels.join(',') == data.classes.join(',')) {
                    // only update values if labels are the same
                    myChart.data.datasets[0].data = data.predictions;

                    myChart.update();
                } else if (data.predictions) {
                    // update everything if different
                    myChart.config.data = {
                        labels: data.classes,
                        datasets: [{
                            data: data.predictions,
                            borderWidth: 1
                        }]
                    };

                    var bgColors = [];
                    var bColors = [];

                    for (var i = 0; i < data.predictions.length; i++) {
                        var rgb = hslToRgb(i * 100 / 360.0 % 1.0, 0.75, 0.5);
                        var str = 'rgba(' + rgb[0] + ', ' + rgb[1] + ', ' + rgb[2];
                        bgColors.push(str + ', 0.5)');
                        bColors.push(str + ', 1.0)');
                    }

                    myChart.data.datasets[0].borderColor = bColors;
                    myChart.data.datasets[0].backgroundColor = bgColors;

                    myChart.update();
                }
            }

            counter += 1;
            //setTimeout(updateFeed, 1000);
        },
        error: function(data, status) {
            setTimeout(updateFeed, 1000);
        },
        timeout: 3000
    });
};

updateFeed();
