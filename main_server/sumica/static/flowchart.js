jsPlumb.ready(function () {
    var instance = window.jsp = jsPlumb.getInstance({
        DragOptions: { cursor: 'pointer', zIndex: 2000 },

        ConnectionOverlays: [
            [ "Arrow", {
                location: 0.5,
                visible:true,
                width:11,
                length:11,
                id:"ARROW",
                events:{
                }
            } ]
        ],
        Container: "flowchartcontainer"
    });

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
            connector: [ "Bezier", { stub: [40, 60], gap: 10, cornerRadius: 5, alwaysRespectStubs: true } ],
            connectorStyle: connectorPaintStyle,
            hoverPaintStyle: endpointHoverStyle,
            connectorHoverStyle: connectorHoverStyle,
            dragOptions: {},
            maxConnections: -1
        },
        labelTargetEndpoint = {
            endpoint: "Dot",
            paintStyle: { fill: "orange", radius: 7 },
            hoverPaintStyle: endpointHoverStyle,
            maxConnections: -1,
            dropOptions: { hoverClass: "hover", activeClass: "active" },
            isTarget: true
        };

    var initLabelNode = function(el) {
        instance.addEndpoint(el, labelTargetEndpoint, {anchor: ["LeftMiddle"], uuid: el.id});
    };

    var newLabelNode = function(x, y, label) {
        var d = document.createElement("div");
        var id = jsPlumbUtil.uuid();

        instance.draggable(d, { grid: [20, 20] , containment:true});
        d.className = "item";
        d.id = id;
        d.innerHTML = label;
        d.style.left = x + "px";
        d.style.top = y + "px";
        instance.getContainer().appendChild(d);
        initLabelNode(d);

        return d;
    };

    var initImageNode = function(el) {
        instance.addEndpoint(el, imageSourceEndpoint, {anchor: ["RightMiddle"], uuid: el.id});
    };

    var newImageNode = function(x, y, imdata) {
        var d = document.createElement("div");
        var id = jsPlumbUtil.uuid();

        instance.draggable(d, { grid: [20, 20] , containment:true});
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

    var updateFlowchart = function() {
        $.ajax({
            type: "POST",
            url: "https://homeai.ml:5000/knowledge",
            success: function(data, status) {
                //instance.deleteEveryEndpoint();
                //instance.detachEveryConnection();
                //instance.empty(instance.getContainer());
                //instance.reset();
                var labels = data["classes"];

                var labelIds  = [];

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
            error: function(data, status) {

            }
        });
    };

    updateFlowchart();
});