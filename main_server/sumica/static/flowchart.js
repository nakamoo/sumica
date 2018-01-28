var currentScale = 1;
var $container = $("#page");
var instance = null;
var platforms = null;

var myDragOptions = {
    //grid: [20, 20], containment: true
};

// init connector and endpoint types
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
        scope: "image",
        maxConnections: -1
    },
    labelTargetEndpoint = {
        endpoint: "Dot",
        paintStyle: {fill: "orange", radius: 7},
        hoverPaintStyle: endpointHoverStyle,
        maxConnections: -1,
        dropOptions: {hoverClass: "hover", activeClass: "active"},
        scope: "image",
        isTarget: true
    },
    labelSourceEndpoint = {
        endpoint: "Dot",
        paintStyle: {fill: "orange", radius: 7},
        hoverPaintStyle: endpointHoverStyle,
        maxConnections: -1,
        scope: "action",
        isSource: true,
        connector: ["Bezier", {stub: [40, 60], gap: 10, cornerRadius: 5, alwaysRespectStubs: true}],
        connectorStyle: connectorPaintStyle,
        connectorHoverStyle: connectorHoverStyle
    },
    actionTargetEndpoint = {
        endpoint: "Dot",
        paintStyle: {fill: "tomato", radius: 7},
        hoverPaintStyle: endpointHoverStyle,
        maxConnections: -1,
        scope: "action",
        isTarget: true
    };

var initGeneralNode = function(x, y) {
    var node = document.createElement("div");
    var id = jsPlumbUtil.uuid();

    var body = document.createElement("div");
    body.className = "itembody";
    $(node).append($(body));

    node.className = "item";
    node.id = id;
    node.style.left = x + "px";
    node.style.top = y + "px";
    instance.setDraggable(node, true);

    var $node = $(node);
    var delButton = $('<button type="button" class="btn btn-circle btn-sm deleteButton">' +
        '<span class="fa fa-times" aria-hidden="true"></span>' +
        '</button>');
    $node.append(delButton);
    delButton.css("display", "none");
    delButton.click(
        function() {
            instance.remove(node);
        }
    );

    $node.mouseover(function() {
        delButton.css("display", "inline");
    }).mouseout(function() {
        delButton.css("display", "none");
    });

    return {body: body, main: node};
};

//node creation

var newLabelNode = function (x, y, label) {
    var n = initGeneralNode(x, y);

    var text = $('<p style="margin: 0;">' + label + '</p>');
    $(n.body).append(text);

    instance.getContainer().appendChild(n.main);

    instance.addEndpoint(n.main, labelTargetEndpoint, {anchor: ["LeftMiddle"], uuid: n.main.id});
    instance.addEndpoint(n.main, labelSourceEndpoint, {anchor: ["RightMiddle"], uuid: n.main.id + "source"});

    return n.main;
};

var newImageNode = function (x, y, imdata) {
    var n = initGeneralNode(x, y);

    var img = $('<img class="itemimage" src="' + imdata + '" >');
    $(n.body).append(img);

    instance.getContainer().appendChild(n.main);
    instance.addEndpoint(n.main, imageSourceEndpoint, {anchor: ["RightMiddle"], uuid: n.main.id});

    return n.main;
};

// organize layout of graph with dagre
var dagreLayout = function () {
    var g = new dagre.graphlib.Graph();
    g.setGraph({rankdir: 'LR', ranksep: 500});
    g.setDefaultEdgeLabel(function () {
        return {};
    });

    $('.item').each(
        function (idx, node) {
            var n = $(node);
            g.setNode(n.attr('id'), {
                width: Math.round(n.width()),
                height: Math.round(n.height())
            });
        }
    );

    instance.getAllConnections().forEach(
        function (edge) {
            g.setEdge(
                edge.source.id,
                edge.target.id
            );
        });


    dagre.layout(g);

    // Applying the calculated layout
    g.nodes().forEach(
        function (n) {
            $('#' + n).css('left', g.node(n).x + 'px');
            $('#' + n).css('top', g.node(n).y + 'px');
        });

    instance.repaintEverything();
};

var addDraggables = function(el) {

    el.draggable({
        start: function (e) {
            var pz = $container.find(".panzoom");
            currentScale = pz.panzoom("getMatrix")[0];
            $(this).css("cursor", "move");
            //pz.panzoom("disable");
            $(this).addClass('noclick');
        },
        drag: function (e, ui) {
            //ui.position.left = Math.round(ui.position.left / currentScale / 20.0) * 20.0;
            //ui.position.top = Math.round(ui.position.top / currentScale / 20.0) * 20.0;
            ui.position.left = ui.position.left / currentScale;
            ui.position.top = ui.position.top / currentScale;

            if ($(this).hasClass("ui-draggable")) {
                instance.repaint($(this).attr('id'), ui.position);
            }
        },
        stop: function (e, ui) {
            var nodeId = $(this).attr('id');
            if ($(this).hasClass("ui-draggable")) {
                instance.repaint(nodeId, ui.position);
            }
            $(this).css("cursor", "");
            $container.find(".panzoom").panzoom("enable");

            //hacky
            setTimeout(function() {
                console.log($(this));
                $(this).removeClass('noclick');
            }, 100);

        }//, grid: [20, 20], containment: true
    });
};

jsPlumb.ready(function () {
    var minScale = 0.4;
    var maxScale = 3;
    var incScale = 0.1;
    instance = window.jsp = jsPlumb.getInstance({
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

    function updateBG(matrix) {
        var followX = -matrix[4] / matrix[0];
        var followY = -matrix[5] / matrix[0];
        var screenW = $('#flowchartabscontainer').width() / minScale;
        var width = screenW * 2.0;

        var interval = 100;
        $('#flowchartbg').css({left: Math.round(followX / interval) * interval - screenW / 2.0,
            top: Math.round(followY / interval) * interval - screenW / 2.0, width: width, height: width});

    };

    $panzoom = $container.find('.panzoom').panzoom({
        minScale: minScale,//0.4
        maxScale: maxScale,//2
        increment: incScale,//0.1
        cursor: "",
        ignoreChildrensEvents: true
    }).on("panzoomstart", function (e, pz, ev) {
        $panzoom.css("cursor", "move");//set "move" cursor on start only
    })
        .on("panzoomend", function (e, pz) {
            $panzoom.css("cursor", "");//restore cursor
        });
    $panzoom.parent()
        .on('mousewheel.focal', function (e) {
            //if Control pressed then zoom
            e.preventDefault();
            var delta = e.delta || e.originalEvent.wheelDelta;
            var zoomOut = delta ? delta < 0 : e.originalEvent.deltaY > 0;
            $panzoom.panzoom('zoom', zoomOut, {
                animate: true,
                exponential: false,
                focal: e
            });

            var matrix = $container.find(".panzoom").panzoom("getMatrix");
            instance.setZoom(matrix[0]);

            updateBG(matrix);
        })
        //on start store initial offsets and mouse coord
        .on("mousedown touchstart", function (ev) {
            if (ev.target.id == 'flowchartabscontainer' || ev.target.id == 'flowchartbg') {
                var matrix = $container.find(".panzoom").panzoom("getMatrix");
                var offsetX = matrix[4];
                var offsetY = matrix[5];
                var dragstart = {x: ev.pageX, y: ev.pageY, dx: offsetX, dy: offsetY};
                $(ev.target).css("cursor", "move");
                $(this).data('dragstart', dragstart);
            }
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

                updateBG(matrix);
                $container.find(".panzoom").panzoom("setMatrix", matrix);
            }
        })
        .on("mouseup touchend touchcancel", function (ev) {
            $(this).data('dragstart', null);
            $(ev.target).css("cursor", "");
        });

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
                    var x = 800;
                    var y = 50 + i * 100;

                    labelIds.push(newLabelNode(x, y, labels[i]).id);
                }

                var images = data["icons"];
                var mapping = data["mapping"];

                for (var i in images) {
                    var x = 300;
                    var y = 50 + i * 100;

                    var el = newImageNode(x, y, images[i]);
                    var labelId = labelIds[mapping[i]];

                    instance.connect({uuids: [el.id, labelId], editable: true});
                }

                //setTimeout(updateFlowchart, 5000);

                addDraggables($container.find(".item"));
                dagreLayout();
            },
            error: function (data, status) {

            }
        });
    };

    updateFlowchart();
});


var newNode = function () {
    var d = document.createElement("div");
    d.className = "item";
    d.innerHTML = "";

    var body = document.createElement("div");
    body.className = "itembody";

    var $d = $(d);

    $d.append($(body));
    return d;
};

var $addLabel = $('#addLabel');

$addLabel.draggable({
    cursorAt: {top: 0, left: 0},
    start: function (event, ui) {
    },
    stop: function (event, ui) {
        var matrix = $container.find(".panzoom").panzoom("getMatrix");
        var x = (ui.offset.left - matrix[4]) / matrix[0];
        var y = (ui.offset.top - matrix[5]) / matrix[0];

        /*swal({
            title: "New label",
            text: "Enter name:",
            type: 'input',
            showCancelButton: true,
            inputPlaceholder: '読書'
        }, function(value) {
            if (value) {
                newLabelNode(x, y, value);
            }
        });*/
        $("#addLabelModal").modal();

        $('#addLabelOk').unbind().click(function (e) {
            e.preventDefault();
            newLabelNode(x, y, $('#addLabelName').val());
            $("#addLabelModal").modal('hide');
            $('#newLabelForm').trigger('reset');
        });
    },
    helper: newNode,
    cancel: false
});

$.get({
    url: "https://homeai.ml:5000/platforms",
    success:function(data) {
        platforms = data;
        var dropdown = $('#selectPlatform, #editPlatform');

        for (var i = 0; i < data.length; i++) {
            dropdown.append($('<option>', {
                value: '' + i,
                text: data[i]
            }));
        }
        },
    async:false
});

$(window).on('load', function () {
    $('body').append('<div id="hiddenStuff" style="display: none;"></div>');

    for (var i = 0; i < platforms.length; i++) {
        $('<div id="platform-' + platforms[i] + '"></div>').load("parameters/" + platforms[i]).appendTo('#hiddenStuff');
    }
});

var checkActionValid = function () {
    var selectedVal = $('#selectPlatform').val();

    if ((selectedVal != '-1' && selectedVal != null) && $('#addActionName').val() != '') {
        $('#addActionOk').prop('disabled', false);
    } else {
        $('#addActionOk').prop('disabled', true);
    }
};

$('#addActionName').keyup(function () {
    checkActionValid();
});

$('#selectPlatform').change(function () {
    checkActionValid();

    if ($(this).val() != '-1') {
        var pName = platforms[parseInt($(this).val())];
        $('#paramsCard').css('display', 'flex');
        $('#actionParams').html($('#platform-' + pName + ' > .setParameters').html());
        window[pName + 'InitSetParameters']();
    }
});

$('#editPlatform').change(function () {
    var params = $("#editActionModal").data('params');

    var pName = platforms[parseInt($(this).val())];
    $('#editActionParams').html($('#platform-' + pName + ' > .setParameters').html());
    window[pName + 'InitSetParameters']();

    if (params.platform == $(this).val()) {
        window[pName + 'InitFromObject'](params);
    }
});

var initActionNode = function (el, body) {
    instance.addEndpoint(el, actionTargetEndpoint, {anchor: ["LeftMiddle"], uuid: el.id});

   $(body)
        .click(function () {
            console.log('uwot', $(el));

            if ($(el).hasClass('noclick')) {
                $(el).removeClass('noclick');
                return;
            }

            var params = $(el).data('params');

            $('#editActionName').val(params.actionName);
            $('#editPlatform').val(params.platform);
            var pName = platforms[parseInt(params.platform)];
            $('#editActionParams').html($('#platform-' + pName + ' > .setParameters').html());
            window[pName + 'InitSetParameters']();
            window[pName + 'InitFromObject'](params);
            $("#editActionModal").data('params', params);
            $("#editActionModal").modal();
        });
};

var newActionNode = function (x, y, params) {
    var n = initGeneralNode(x, y);

    instance.getContainer().appendChild(n.main);
    var $d = $(n.main);
    $d.data('params', params);

    var text = $('<p style="margin: 0;">' + params.actionName + '</p>');
    $(n.body).append(text);

    initActionNode(n.main, n.body);

    return n.main;
};

var $addAction = $('#addAction');

$('#addActionModal').on('hidden.bs.modal', function () {
    $('#addActionName').val('');
    $('#selectPlatform').val('-1');
    $('#paramsCard').css('display', 'none');
    $('#actionParams').empty();
    $('#addActionOk').prop('disabled', true);
});

$addAction.draggable({
    cursorAt: {top: 0, left: 0},
    start: function (event, ui) {
    },
    stop: function (event, ui) {
        var matrix = $container.find(".panzoom").panzoom("getMatrix");
        var x = (ui.offset.left - matrix[4]) / matrix[0];
        var y = (ui.offset.top - matrix[5]) / matrix[0];

        $("#addActionModal").modal({backdrop: 'static'});

        $('#addActionOk').unbind().click(function (e) {
            var pName = platforms[parseInt($('#selectPlatform').val())];
            var params = window[pName + "ToObject"]();
            params.actionName = $('#addActionName').val();
            params.platform = $('#selectPlatform').val();//$('#selectPlatform option:selected').text();
            params.username = 'sean';

            e.preventDefault();

            var node = newActionNode(x, y, params);
            addDraggables($(node));
            $("#addActionModal").modal('hide');
        });

        $('#testAction').unbind().click(function (e) {
            var pName = platforms[parseInt($('#selectPlatform').val())];
            var params = window[pName + "ToObject"]();
            params.username = 'sean';

            $.ajax({
                type: "POST",
                url: "https://homeai.ml:5000/test/" + pName,
                data: JSON.stringify(params)
            });
        });
    },
    helper: newNode,
    cancel: false
});
