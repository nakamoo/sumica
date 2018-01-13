var feed = document.getElementById("feed");

var updateFeed = function() {
    $.ajax({
        type: "POST",
        url: "https://homeai.ml:5000/feed",
        success: function(data, status) {
            var imgs = "";

            if (data.length > 0) {
                for (var i in data) {
                    img = new Image();
                    img.src = "data:image/jpeg;base64," + data[i]["img"];
                    img.className  = "feedimg";
                    imgs += img.outerHTML;
                }

                feed.innerHTML = imgs;
            } else {
                feed.innerHTML =
                    "<div class='card text-white bg-dark text-center h-25'>" +
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
}

updateFeed();