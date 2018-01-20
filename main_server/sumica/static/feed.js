
var ctx = document.getElementById("predCanvas").getContext('2d');
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
            }]
        },
        title: {
            display: true,
            text: 'predictions'
        }
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

var updateFeed = function() {
    $.ajax({
        type: "POST",
        url: "https://homeai.ml:5000/feed",
        success: function(data, status) {
            if (data.images.length > 0) {
                var imgs = "";

                for (var i = 0; i < data.images.length; i++) {
                    card = "";
                    card += "<div class='card text-white bg-dark text-center'>" +
                        "<div class='card-block'>" +
                        "<p class='card-text'>" + data.images[i]["name"] + "</p>" +
                        "</div>";
                    card += '<img class="card-img-bottom" src=' + 'data:image/jpeg;base64,' + data.images[i]["img"] + '>';
                    card += "</div>";
                    imgs += card;
                }

                feed.innerHTML = imgs;

                // is js retarded?
                if (myChart.data.labels.join(',') == data.classes.join(',')) {
                    // only update values if labels are the same
                    myChart.data.datasets[0].data = data.predictions;

                    myChart.update();
                } else {
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
                        var rgb = hslToRgb(i*100 / 360.0 % 1.0, 0.75, 0.5);
                        var str = 'rgba(' + rgb[0] + ', ' + rgb[1] + ', ' + rgb[2];
                        bgColors.push(str + ', 0.5)');
                        bColors.push(str + ', 1.0)');
                    }

                    myChart.data.datasets[0].borderColor = bColors;
                    myChart.data.datasets[0].backgroundColor = bgColors;

                    myChart.update();
                }

                setTimeout(updateFeed, 500);
            } else {
                feed.innerHTML =
                    "<div class='card text-white bg-dark text-center'>" +
                    "<div class='card-block'>" +
                    "<p class='card-text'>NO FEED</p>" +
                    "</div>" +
                    "</div>";
                setTimeout(updateFeed, 1000);
            }
        },
        error: function(data, status) {
            setTimeout(updateFeed, 1000);
        }
    });
};

updateFeed();