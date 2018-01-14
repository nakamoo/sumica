jsPlumb.ready(function () {
    var endpoint1 = {
        endpoint: ["Dot", {radius: 10}],
        paintStyle: {fill: "dodgerblue"},
        hoverPaintStyle: {fill: "white"},
        connectorOverlays: [["PlainArrow", {width: 15, length: 15, location: 0.5}]],
        isSource: true,
        //scope: "green",
        connectorStyle: {stroke: "lightgray", strokeWidth: 6},
        connectorHoverStyle: {stroke: "white", strokeWidth: 6},
        connector: ["Bezier"],
        maxConnections: 1,
        isTarget: false,
        anchors: ["Right"],
        scope: "image"
        //dropOptions: exampleDropOptions
    };

    var endpoint2 = {
        endpoint: ["Dot", {radius: 10}],
        paintStyle: {fill: "orange"},
        hoverPaintStyle: {fill: "white"},
        connectorOverlays: [["PlainArrow", {width: 15, length: 15, location: 0.5}]],
        isSource: false,
        //scope: "green",
        connectorStyle: {stroke: "lightgray", strokeWidth: 6},
        connectorHoverStyle: {stroke: "white", strokeWidth: 6},
        connector: ["Bezier"],
        maxConnections: -1,
        isTarget: true,
        anchors: ["Left"],
        scope: "image"
        //dropOptions: exampleDropOptions
    };

    var endpoint3 = {
        endpoint: ["Dot", {radius: 10}],
        paintStyle: {fill: "orange"},
        hoverPaintStyle: {fill: "white"},
        connectorOverlays: [["PlainArrow", {width: 15, length: 15, location: 0.5}]],
        isSource: true,
        //scope: "green",
        connectorStyle: {stroke: "lightgray", strokeWidth: 6},
        connectorHoverStyle: {stroke: "white", strokeWidth: 6},
        connector: ["Bezier"],
        maxConnections: -1,
        isTarget: false,
        anchors: ["Right"],
        scope: "action"
        //dropOptions: exampleDropOptions
    };

    var endpoint4 = {
        endpoint: ["Dot", {radius: 10}],
        paintStyle: {fill: "tomato"},
        hoverPaintStyle: {fill: "white"},
        connectorOverlays: [["PlainArrow", {width: 15, length: 15, location: 0.5}]],
        isSource: false,
        //scope: "green",
        connectorStyle: {stroke: "lightgray", strokeWidth: 6},
        connectorHoverStyle: {stroke: "white", strokeWidth: 6},
        connector: ["Bezier"],
        maxConnections: -1,
        isTarget: true,
        anchors: ["Left"],
        scope: "action"
        //dropOptions: exampleDropOptions
    };

    dragcommon = {containment: true, grid: [20, 20]}

    /*jsPlumb.draggable("img1", dragcommon);
    jsPlumb.draggable("img2", dragcommon);
    jsPlumb.draggable("img3", dragcommon);
    jsPlumb.draggable("label1", dragcommon);
    jsPlumb.draggable("label2", dragcommon);
    jsPlumb.draggable("action1", dragcommon);

    jsPlumb.addEndpoint("img1", endpoint1);
    jsPlumb.addEndpoint("img2", endpoint1);
    jsPlumb.addEndpoint("img3", endpoint1);
    jsPlumb.addEndpoint("label1", endpoint2);
    jsPlumb.addEndpoint("label2", endpoint2);

    jsPlumb.addEndpoint("label1", endpoint3);
    jsPlumb.addEndpoint("label2", endpoint3);
    jsPlumb.addEndpoint("action1", endpoint4);

    jsPlumb.makeSource("img1", endpoint1);
    jsPlumb.makeSource("img2", endpoint1);
    jsPlumb.makeSource("img3", endpoint1);
    jsPlumb.makeTarget("label1", endpoint2);
    jsPlumb.makeTarget("label2", endpoint2);

    jsPlumb.makeSource("label1", endpoint3);
    jsPlumb.makeSource("label2", endpoint3);
    jsPlumb.makeSource("action1", endpoint4);

    jsPlumb.connect({
        source: "img2",
        target: "label1",
        overlays: [["PlainArrow", {width: 15, length: 15, location: 0.5}]],
        //detachable:false
    });*/

    var newNode = function (x, y) {
        var d = document.createElement("div");
        var id = jsPlumbUtil.uuid();
        d.className = "labelitem";
        d.id = id;
        d.innerHTML = "<p>LABEL</p>";
        //d.style.left = x + "px";
        //d.style.top = y + "px";
        jsPlumb.getContainer().appendChild(d);
        //initNode(d);
        jsPlumb.draggable(d.id);

        jsPlumb.addEndpoint(d.id, endpoint2);
        jsPlumb.makeTarget(d.id, endpoint2);

        return d;
    };

    var canvas = document.getElementById("flowchart");

    jsPlumb.on(canvas, "dblclick", function (e) {
        newNode(e.offsetX, e.offsetY);
    });

    jsPlumb.bind("click", function (c) {
        jsPlumb.deleteConnection(c);
    });

    jsPlumb.bind("connection", function (info, originalEvent) {
        if (originalEvent) {
            //alert("connection created");
        }
    });

    jsPlumb.bind("connectionDetached", function (info, originalEvent) {
        if (originalEvent) {
            //alert("connection detached");
        }
    });

    jsPlumb.bind("beforeDrop", function (connection) {
        console.log(connection);
        return connection.sourceId !== connection.targetId;
    });
});