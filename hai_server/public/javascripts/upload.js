$(function() {
    //videoタグを取得
    var video = document.getElementById('camera');
    //カメラが起動できたかのフラグ
    var localMediaStream = null;
    //カメラ使えるかチェック
    var hasGetUserMedia = function() {
        return (navigator.getUserMedia || navigator.webkitGetUserMedia || navigator.mozGetUserMedia || navigator.msGetUserMedia);
    };

    //エラー
    var onFailSoHard = function(e) {
        console.log('エラー!', e);
    };

    if(!hasGetUserMedia()) {
        alert("未対応ブラウザです。");
    } else {
        window.URL = window.URL || window.webkitURL;
        navigator.getUserMedia  = navigator.getUserMedia || navigator.webkitGetUserMedia || navigator.mozGetUserMedia || navigator.msGetUserMedia;
        navigator.getUserMedia({video: true}, function(stream) {
            video.src = window.URL.createObjectURL(stream);
            localMediaStream = stream;
        }, onFailSoHard);
    }

    var sendImage = function() {
        if (localMediaStream) {
            var canvas = document.getElementById('canvas');
            //canvasの描画モードを2sに
            var ctx = canvas.getContext('2d');
            var img = document.getElementById('img');

            //videoの縦幅横幅を取得
            var w = video.offsetWidth;
            var h = video.offsetHeight;

            //同じサイズをcanvasに指定
            canvas.setAttribute("width", w);
            canvas.setAttribute("height", h);

            //canvasにコピー
            ctx.drawImage(video, 0, 0, w, h);

            //ここから画像のバイナリ化
            var can = canvas.toDataURL();
            // Data URLからBase64のデータ部分のみを取得
            var base64Data = can.split(',')[1];
            // base64形式の文字列をデコード
            var data = window.atob(base64Data); 
            var buff = new ArrayBuffer(data.length);
            var arr = new Uint8Array(buff);

            // blobの生成
            for(var i = 0, dataLen = data.length; i < dataLen; i++){
                arr[i] = data.charCodeAt(i);
            }
            var blob = new Blob([arr], {type: 'image/png'});

            //ここから画像データ送信
            //urlを設定
            var url = 'upload';

            //データをセット
            var formData = new FormData();
            formData.append('image', blob);

            //非同期通信開始
            $.ajax({
                url: url,
                type: 'POST',
                data: formData,
                contentType: false,
                processData: false,
                success: function(data, dataType) {
                },
                error: function(XMLHttpRequest, textStatus, errorThrown) {
                           console.log('Error : ' + errorThrown);
                       }
            });
        }
    };

    // 3000ミリ秒ごとに写真をpost
    var startSendImage = function() {
      setInterval(sendImage, 3000);
    }

    $("#start").click(startSendImage);
});
