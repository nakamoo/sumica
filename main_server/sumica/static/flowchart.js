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

    instance.batch(function () {
        instance.addEndpoint("label1", imageSourceEndpoint, {
            anchor: ["RightMiddle"], uuid: "label1right"});

        instance.addEndpoint("label2", labelTargetEndpoint, {
            anchor: ["LeftMiddle"], uuid: "label2left"});

        instance.addEndpoint("image1", labelTargetEndpoint, {
            anchor: ["RightMiddle"], uuid: "image1right"});

        instance.draggable(jsPlumb.getSelector(".item"), { grid: [20, 20] , containment:true});

        instance.connect({uuids: ["label1right", "label2left"], editable: true});

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
});