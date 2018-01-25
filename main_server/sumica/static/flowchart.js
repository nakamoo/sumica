var currentScale = 1;
var $container = $("#page");

jsPlumb.ready(function () {
    var minScale = 0.4;
    var maxScale = 2;
    var incScale = 0.1;
    var instance = window.jsp = jsPlumb.getInstance({
        DragOptions: {cursor: 'pointer', zIndex: 2000},

        ConnectionOverlays: [
            ["Arrow", {
                location: 0.5,
                visible: true,
                width: 11,
                length: 11,
                id: "ARROW",
                events: {}
            }]
        ],
        Container: "flowchartcanvas"
    });

    var myDragOptions = {
        start: function(e){
            console.log("sdfsddAA");
          var pz = $container.find(".panzoom");
          currentScale = pz.panzoom("getMatrix")[0];
          $(this).css("cursor","move");
          pz.panzoom("disable");
        },
        drag:function(e){
            var ui = e.el.style;
            var pos = $(e.el).position();
            console.log(pos);
            ui.position = "absolute";
            ui.top = pos.top/currentScale + "px";
            ui.left = pos.left/currentScale + "px";
            console.log(ui.top);
          //if($(this).hasClass("jsplumb-connected"))
          //{
            instance.repaint(e.el);
          //}
        },
        stop: function(e){
          var nodeId = $(this).attr('id');
          //if($(this).hasClass("jsplumb-connected"))
          //{
            instance.repaint(e.el);
          //}
          $(this).css("cursor","");
          $container.find(".panzoom").panzoom("enable");
        }, grid: [20, 20], containment: true
    };

    $panzoom = $container.find('.panzoom').panzoom({
        minScale: minScale,//0.4
        maxScale: maxScale,//2
        increment: incScale,//0.1
        cursor: "",
        ignoreChildrensEvents:true
    }).on("panzoomstart", function (e, pz, ev) {
        $panzoom.css("cursor", "move");//set "move" cursor on start only
    })
    .on("panzoomend", function (e, pz) {
        $panzoom.css("cursor", "");//restore cursor
    });
    $panzoom.parent()
        .on('mousewheel.focal', function (e) {
            //if Control pressed then zoom
            if (e.ctrlKey || e.originalEvent.ctrlKey) {
                e.preventDefault();
                var delta = e.delta || e.originalEvent.wheelDelta;
                var zoomOut = delta ? delta < 0 : e.originalEvent.deltaY > 0;
                $panzoom.panzoom('zoom', zoomOut, {
                    animate: true,
                    exponential: false,
                });
            } else {//else pan (touchpad and Shift key works)
                e.preventDefault();
                var deltaY = e.deltaY || e.originalEvent.wheelDeltaY || (-e.originalEvent.deltaY);
                var deltaX = e.deltaX || e.originalEvent.wheelDeltaX || (-e.originalEvent.deltaX);
                $panzoom.panzoom("pan", deltaX / 2, deltaY / 2, {
                    animate: true,
                    relative: true,
                });
            }
        })
        //on start store initial offsets and mouse coord
        .on("mousedown touchstart", function (ev) {

            var matrix = $container.find(".panzoom").panzoom("getMatrix");
            var offsetX = matrix[4];
            var offsetY = matrix[5];
            var dragstart = {x: ev.pageX, y: ev.pageY, dx: offsetX, dy: offsetY};
            $(ev.target).css("cursor", "move");
            $(this).data('dragstart', dragstart);
        })
        //calculate mouse offset from starting pos and apply it to panzoom matrix
        .on("mousemove touchmove", function (ev) {
            var dragstart = $(this).data('dragstart');

            if (dragstart) {
                var deltaX = dragstart.x - ev.pageX;
                var deltaY = dragstart.y - ev.pageY;
                var matrix = $container.find(".panzoom").panzoom("getMatrix");
                matrix[4] = parseInt(dragstart.dx) - deltaX;
                matrix[5] = parseInt(dragstart.dy) - deltaY;
                $container.find(".panzoom").panzoom("setMatrix", matrix);
            }
        })
        .on("mouseup touchend touchcancel", function (ev) {
            console.log('mouseup touchend touchcancel');
            $(this).data('dragstart', null);
            $(ev.target).css("cursor", "");
        });

    console.log('done');



    var connectorPaintStyle = {
            strokeWidth: 2,
            stroke: "orange",
            joinstyle: "round"
        },

        connectorHoverStyle = {
            strokeWidth: 3,
            stroke: "white"
        },
        endpointHoverStyle = {
            fill: "white"
        },
        imageSourceEndpoint = {
            endpoint: "Dot",
            paintStyle: {
                fill: "dodgerblue",
                radius: 7
            },
            isSource: true,
            connector: ["Bezier", {stub: [40, 60], gap: 10, cornerRadius: 5, alwaysRespectStubs: true}],
            connectorStyle: connectorPaintStyle,
            hoverPaintStyle: endpointHoverStyle,
            connectorHoverStyle: connectorHoverStyle,
            dragOptions: {},
            maxConnections: -1
        },
        labelTargetEndpoint = {
            endpoint: "Dot",
            paintStyle: {fill: "orange", radius: 7},
            hoverPaintStyle: endpointHoverStyle,
            maxConnections: -1,
            dropOptions: {hoverClass: "hover", activeClass: "active"},
            isTarget: true
        };

    var initLabelNode = function (el) {
        instance.addEndpoint(el, labelTargetEndpoint, {anchor: ["LeftMiddle"], uuid: el.id});
    };

    var newLabelNode = function (x, y, label) {
        var d = document.createElement("div");
        var id = jsPlumbUtil.uuid();

        instance.draggable(d, myDragOptions);
        d.className = "item";
        d.id = id;
        d.innerHTML = label;
        d.style.left = x + "px";
        d.style.top = y + "px";
        instance.getContainer().appendChild(d);
        initLabelNode(d);

        return d;
    };

    var initImageNode = function (el) {
        instance.addEndpoint(el, imageSourceEndpoint, {anchor: ["RightMiddle"], uuid: el.id});
    };

    var newImageNode = function (x, y, imdata) {
        var d = document.createElement("div");
        var id = jsPlumbUtil.uuid();

        instance.draggable(d, myDragOptions);
        d.className = "item";
        d.id = id;
        d.innerHTML = '<img class="itemimage" src=' + 'data:image/jpeg;base64,' + imdata + '>';
        d.style.left = x + "px";
        d.style.top = y + "px";
        instance.getContainer().appendChild(d);
        initImageNode(d);

        return d;
    };

    instance.batch(function () {
        /*
        instance.addEndpoint("label1", imageSourceEndpoint, {
            anchor: ["RightMiddle"], uuid: "label1right"});

        instance.addEndpoint("label2", labelTargetEndpoint, {
            anchor: ["LeftMiddle"], uuid: "label2left"});

        instance.addEndpoint("image1", labelTargetEndpoint, {
            anchor: ["RightMiddle"], uuid: "image1right"});

        instance.draggable(jsPlumb.getSelector(".item"), { grid: [20, 20] , containment:true});

        instance.connect({uuids: ["label1right", "label2left"], editable: true});
        */

        instance.bind("click", function (conn, originalEvent) {
            instance.deleteConnection(conn);
        });

        instance.bind("connectionDrag", function (connection) {
            console.log("connection " + connection.id + " is being dragged. suspendedElement is ", connection.suspendedElement, " of type ", connection.suspendedElementType);
        });

        instance.bind("connectionDragStop", function (connection) {
            console.log("connection " + connection.id + " was dragged");
        });

        instance.bind("connectionMoved", function (params) {
            console.log("connection " + params.connection.id + " was moved");
        });
    });

    var updateFlowchart = function () {
        $.ajax({
            type: "POST",
            url: "https://homeai.ml:5000/knowledge",
            success: function (data, status) {
                //instance.deleteEveryEndpoint();
                //instance.detachEveryConnection();
                //instance.empty(instance.getContainer());
                //instance.reset();
                var labels = data["classes"];

                var labelIds = [];

                for (var i in labels) {
                    var x = 600 + Math.floor(i / 4) * 100;
                    var y = 50 + (i % 4) * 100;

                    labelIds.push(newLabelNode(x, y, labels[i]).id);
                }

                var images = data["icons"];
                var mapping = data["mapping"];

                for (var i in images) {
                    var x = 100 + Math.floor(i / 4) * 100;
                    var y = 50 + (i % 4) * 100;

                    var el = newImageNode(x, y, images[i]);
                    var labelId = labelIds[mapping[i]];

                    instance.connect({uuids: [el.id, labelId], editable: true});
                }

                //setTimeout(updateFlowchart, 5000);
            },
            error: function (data, status) {

            }
        });
    };

    updateFlowchart();
});
