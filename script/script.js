//
// Useful functions
// Jessica Voytek 2011
//

log = function (log_data) {
	if (window.console != undefined) {
		console.log(log_data);
	}
}


//
// Modified from code provided by Nicolas Garcia Belmonte, http://www.thejit.org
// copyright ©2008-2011 Nicolas Garcia Belmonte
//
// Modifications by Jessica Voytek, 2011
//

var labelType, useGradients, nativeTextSupport, animate;


//
// Space Tree
//

(function() {
	var ua = navigator.userAgent,
		iStuff = ua.match(/iPhone/i) || ua.match(/iPad/i),
		typeOfCanvas = typeof HTMLCanvasElement,
		nativeCanvasSupport = (typeOfCanvas == 'object' || typeOfCanvas == 'function'),
		textSupport = nativeCanvasSupport 
		&& (typeof document.createElement('canvas').getContext('2d').fillText == 'function');
		//I'm setting this based on the fact that ExCanvas provides text support for IE
		//and that as of today iPhone/iPad current text support is lame
		labelType = (!nativeCanvasSupport || (textSupport && !iStuff))? 'Native' : 'HTML';
		nativeTextSupport = labelType == 'Native';
		useGradients = nativeCanvasSupport;
		animate = !(iStuff || !nativeCanvasSupport);
})();

var barChart;

function bar(json) {
    barChart = new $jit.BarChart({
      //id of the visualization container
      injectInto: 'bar-chart',
      //whether to add animations
      animate: true,
      //horizontal or vertical barcharts
      orientation: 'vertical',
      //bars separation
      barsOffset: 1,
      hoveredColor: '#333',
      //visualization offset
      Margin: {
        top:0,
        left: 15,
        right: 15,
        bottom:0
      },
      //labels offset position
      labelOffset: 5,
      //bars style
      //type: useGradients? 'stacked:gradient' : 'stacked',
      //whether to show the aggregation of the values
      showAggregates:false,
      //whether to show the labels for the bars
      showLabels:false,
      //labels style
      Label: {
        type: 'HTML', //Native or HTML
        size: 13,
        family: 'Arial',
        color: 'white'
      },
      //add tooltips
      Tips: {
        enable: true,
        onShow: function(tip, elem) {
          //tip.innerHTML = "<b>" + elem.label + "</b>: " + elem.value;
          tip.innerHTML = "<div class=\"tip-text\"><b>Term:</b> " + elem.label + "<br /><b>Category:</b> " + elem.category + "<br /><b>Prob. association with search term:</b> " + elem.value + "</div>"
        }
      }
    });
    //load JSON data.
    barChart.loadJSON(json);
    
    prefix = barChart.canvas.viz.root.replace('$root', '');
    
    $.each(json.values, function(index, bar) {
    	div = $('#' + prefix + bar.label.replace(/'/g, '_').replace(/ /g, '_').replace(/&#39;/g, '_'))
    	$(div).css('background-color', bar.color[0]);
    	$(div).hover(
    		function(){
    			category = getCategoryData(bar.category);
    			$(this).css('background-color', '#' + category.color_highlight);
				ht.graph.getByName(bar.label).data.$color = '#' + category.color_highlight;
				ht.plot();
    		}, 
    		
    		function(){
    			category = getCategoryData(bar.category);
    			$(this).css('background-color', '#' + category.color);
				ht.graph.getByName(bar.label).data.$color = '#' + category.color;
				ht.plot();
    		}
    	);
    		

    });

}

function tree(json){
	//end
	//init Spacetree
	//Create a new space tree (ST) instance
	var st = new $jit.ST({
		//id of viz container element
		injectInto: 'tree',
		//set duration for the animation
		duration: 800,
		//set animation transition type
		transition: $jit.Trans.Quart.easeInOut,
		//set distance between node and its children
		levelDistance: 40,
		
		//enable panning
		Navigation: {
		enable:true,
		panning:true,
		  zooming: 10 //zoom speed. higher is more sensible  
		},
		
		//set node and edge styles
		//set overridable=true for styling individual
		//nodes or edges
		Node: {
			autoHeight: true,
			width: 160,
			type: 'rectangle',
			color: '#aaa',
			overridable: true
		},
		
		//Add Tips  
		Tips: {  
	    	enable: true,  
	    	onShow: function(tip, node) {  
				//count connections  
				var count = 0;  
				node.eachAdjacency(function() { count++; });  
				//display node info in tooltip  
				tip.innerHTML = "<div class=\"tip-text\"><b>Category:</b> " + node.data.category + "<br /><b>Prob. association w/parent:</b> " + node.data.prob_association + "</div>";  
			}
		},  
		
		Edge: {
			type: 'bezier',
			overridable: true
		},
				
		//This method is called on DOM label creation.
		//Use this method to add event handlers and styles to
		//your node.
		onCreateLabel: function(label, node){
			label.id = node.id;
			label.innerHTML = node.name;
			label.onclick = function(){
				st.onClick(node.id);
  			};
			//set label styles
			var style = label.style;
			style.width = 160 + 'px';
			style.cursor = 'pointer';
			style.color = '#333';
			style.textAlign= 'center';
			style.paddingTop = '3px';
		},
		
		//This method is called right before plotting
		//a node. It's useful for changing an individual node
		//style properties before plotting it.
		//The data properties prefixed with a dollar
		//sign will override the global node style properties.
		onBeforePlotNode: function(node){
  		
	  		//add some color to the nodes in the path between the
	  		//root node and the selected node.
	  		if (node.selected) {
				node.data.$color = "#ff7";
	  		} else {
				//delete node.data.$color;
				//if the node belongs to the last plotted level
				if(!node.anySubnode("exist")) {
					//count children number
					var count = 0;
					node.eachSubnode(function(n) { count++; });
				}
	  		}
		},
		
		//This method is called right before plotting
		//an edge. It's useful for changing an individual edge
		//style properties before plotting it.
		//Edge data proprties prefixed with a dollar sign will
		//override the Edge global style properties.
		onBeforePlotLine: function(adj){
	  		if (adj.nodeFrom.selected && adj.nodeTo.selected) {
				adj.data.$color = "#eed";
				adj.data.$lineWidth = 3;
	  		}
	  		else {
				delete adj.data.$color;
				delete adj.data.$lineWidth;
	  		}
		}
    });
    
    
	//load json data
	st.loadJSON(json);
	//compute node positions and layout
	st.compute();
	//optional: make a translation of the tree
	st.geom.translate(new $jit.Complex(-200, 0), "current");
	//emulate a click on the root node.
	st.onClick(st.root);
	//Add event handlers to switch spacetree orientation.
	var top = $jit.id('r-top'), 
		left = $jit.id('r-left'), 
		bottom = $jit.id('r-bottom'), 
		right = $jit.id('r-right');


	function changeHandler() {
		if(this.checked) {
			top.disabled = bottom.disabled = right.disabled = left.disabled = true;
			st.switchPosition(this.value, "animate", {
				onComplete: function(){
  					top.disabled = bottom.disabled = right.disabled = left.disabled = false;
				}
  			});
		}
    };
    
    top.onchange = left.onchange = bottom.onchange = right.onchange = changeHandler;
    //end

}

//
// Hyper Tree Network Graph
//

(function() {
	var ua = navigator.userAgent,
		iStuff = ua.match(/iPhone/i) || ua.match(/iPad/i),
		typeOfCanvas = typeof HTMLCanvasElement,
		nativeCanvasSupport = (typeOfCanvas == 'object' || typeOfCanvas == 'function'),
		textSupport = nativeCanvasSupport 
			&& (typeof document.createElement('canvas').getContext('2d').fillText == 'function');
	//I'm setting this based on the fact that ExCanvas provides text support for IE
	//and that as of today iPhone/iPad current text support is lame
	//labelType = (!nativeCanvasSupport || (textSupport && !iStuff))? 'Native' : 'HTML';
	labelType = 'HTML';
	nativeTextSupport = labelType == 'Native';
	useGradients = nativeCanvasSupport;
	animate = !(iStuff || !nativeCanvasSupport);
})();

var ht;

function makeGraph(json){
    $("#infovis").empty();
	ht = new $jit.Hypertree({  
    //id of the visualization container  
    injectInto: 'infovis',  
    //canvas width and height  
    width: 974,  
    height: 500,  
    Navigation: {  
        enable: true,  
        //Enable panning events only if we're dragging the empty  
        //canvas (and not a node).  
        panning: 'avoid nodes',  
        zooming: 25 //zoom speed. higher is more sensible  
    },  
    //Change Node and Edge styles and colors.  
    Node: {  
        overridable: true,
        transform: false
    },  
    Edge: {  
        overridable: true,  
        color: '#23A4FF',  
        lineWidth: 0.4  
    },  
    Label: {  
        type: labelType, //Native or HTML  
        size: 16,  
        style: 'normal',
        color: '#000'
    },  
    //Add Tips  
    Tips: {  
        enable: true,  
        onShow: function(tip, node) {  
            //count connections  
            var count = 0;  
            node.eachAdjacency(function() { count++; });  
            //display node info in tooltip  
            tip.innerHTML = "<div class=\"tip-text\"><b>Category:</b> " + node.data.category + "<br /><b>Prob. association with search term:</b> " + node.data.prob_association + "</div>";  
        }  
    },     
    //Add the node's name to its corresponding label.  
    //This method is only called on label creation.  
    onCreateLabel: function(domElement, node){  
        domElement.innerHTML = node.name;  
    },  
	Events: {  
		enable: true,  
		type: 'Native',  
		//Change cursor style when hovering a node  
		onMouseEnter: function(node, eventInfo, e) {  
			ht.canvas.getElement().style.cursor = 'move'; 
			category = getCategoryData(node.data.category);
			node.data.$color = "#" + category.color_highlight;
			barChartPrefix = barChart.canvas.viz.root.replace('$root', '');
			$('#' + barChartPrefix + node.name.replace(/'/g, '_').replace(/ /g, '_').replace(/&#39;/g, '_')).css('background-color', '#' + category.color_highlight);

			node.eachAdjacency(function(adj) { 
				if (adj.nodeTo.data.$type == 'star' || node.data.$type == 'star') {
					adj.data.$color = '#004a7d'; 			
				} else {
					adj.data.$color = '#999999'; 			
				}

			});
			ht.plot();
		},  
		onMouseLeave: function(node, eventInfo, e) {  
			ht.canvas.getElement().style.cursor = '';  
			category = getCategoryData(node.data.category);
			node.data.$color = "#" + category.color;
			barChartPrefix = barChart.canvas.viz.root.replace('$root', '');
			$('#' + barChartPrefix + node.name.replace(/'/g, '_').replace(/ /g, '_').replace(/&#39;/g, '_')).css('background-color', '#' + category.color);
			node.eachAdjacency(function(adj) { 
				if (adj.nodeTo.data.$type == 'star' || node.data.$type == 'star') {
					adj.data.$color = '#23A4FF'; 			
				} else {
					adj.data.$color = '#cccccc'; 			
				}
			});
			ht.plot();
		},  
		//Update node positions when dragged  
		onDragMove: function(node, eventInfo, e) {  
			var pos = eventInfo.getPos();  
			node.pos.setc(pos.x/300, pos.y/300);  
			ht.plot();
		},  
		//Implement the same handler for touchscreens  
		onTouchMove: function(node, eventInfo, e) {  
			$jit.util.event.stop(e); //stop default touchmove event  
			this.onDragMove(node, eventInfo, e);  
		},
		onDoubleClick: function(node, eventInfo, e) {
        	window.location = 'Search?term_a=' + node.name;		
		}  
	},  
    //Ths method is called when moving/placing a label.  
    //Add label styles based on their position.  
    onPlaceLabel: function(domElement, node){  
        log(node);
        $(domElement).dblclick(function(){
        	log('doublecliked!');
        	window.location = 'Search?term_a=' + node.name;
        });
        var style = domElement.style;  
        style.display = '';  
        if (node._depth <= 1) {  
            style.fontSize = "1em";  
            style.color = "#333";  
  
        } else if(node._depth == 2){  
            style.fontSize = "0.8em";  
            style.color = "#555";  
  
        } else {  
            style.display = 'none';  
        }  
  
        var left = parseInt(style.left);  
        var w = domElement.offsetWidth;  
        style.left = (left - w / 2) + 'px';  
    }

});  



//load JSON data.  
ht.loadJSON(json);  
 
//Compute positions and plot.  
ht.refresh(); 

}

function morph(json) {
  	
	ht.op.morph(json, {  
        type: 'fade:con',  
        duration: 1000,  
        fps: 30,  
        hideLabels:false  
    });
	ht.graph.computeLevels(ht.root);
}

function init(json) {
	makeGraph(json);
		
	$("#refresh").click(function(){
		makeGraph(json);
	});  
}
