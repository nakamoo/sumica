var feed = document.getElementById("feed");

var updateFeed = function() {
    $.ajax({
        type: "POST",
        url: "https://homeai.ml:5000/feed",
        success: function(data, status) {
            if (data.length > 0) {
                var imgs = "";

                for (var i in data) {
                    card = "";
                    card += "<div class='card text-white bg-dark text-center'>" +
                        "<div class='card-block'>" +
                        "<p class='card-text'>" + data[i]["name"] + "</p>" +
                        "</div>";
                    card += '<img class="card-img-bottom" src=' + 'data:image/jpeg;base64,' + data[i]["img"] + '>';
                    card += "</div>";
                    imgs += card;
                }

                feed.innerHTML = imgs;
            } else {
                feed.innerHTML =
                    "<div class='card text-white bg-dark text-center'>" +
                    "<div class='card-block'>" +
                    "<p class='card-text'>NO FEED</p>" +
                    "</div>" +
                    "</div>";
            }

            setTimeout(updateFeed, 100);
        },
        error: function(data, status) {

        }
    });
};

updateFeed();