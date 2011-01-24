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
// Force Directed Network Graph
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


function makeGraph(json){
  $("#infovis").empty();
  fd = new $jit.ForceDirected({  
  //id of the visualization container  
  injectInto: 'infovis',  
  //Enable zooming and panning  
  //by scrolling and DnD  
  Navigation: {  
    enable: true,  
    //Enable panning events only if we're dragging the empty  
    //canvas (and not a node).  
    panning: 'avoid nodes',  
    zooming: 10 //zoom speed. higher is more sensible  
  },  
  // Change node and edge styles such as  
  // color and width.  
  // These properties are also set per node  
  // with dollar prefixed data-properties in the  
  // JSON structure.  
  Node: {  
    overridable: true  
  },  
  Edge: {  
    overridable: true,  
    color: '#23A4FF',  
    lineWidth: 0.4  
  },  
  //Native canvas text styling  
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
  // Add node events  
  Events: {  
    enable: true,  
    //Change cursor style when hovering a node  
    onMouseEnter: function() {  
      fd.canvas.getElement().style.cursor = 'move';  
    },  
    onMouseLeave: function() {  
      fd.canvas.getElement().style.cursor = '';  
    },  
    //Update node positions when dragged  
    onDragMove: function(node, eventInfo, e) {  
		var pos = eventInfo.getPos();  
		node.pos.setc(pos.x, pos.y);  
		fd.plot();  
    },  
    //Implement the same handler for touchscreens  
    onTouchMove: function(node, eventInfo, e) {  
      $jit.util.event.stop(e); //stop default touchmove event  
      this.onDragMove(node, eventInfo, e);  
    },  
    //Add also a click handler to nodes  
    onClick: function(node) {  
      if(!node) return;  
      // Build the right column relations list.  
      // This is done by traversing the clicked node connections.  
      //var html = "<h4>" + node.name + " (" + node.data.structure + ") </h4><b> prob. association:</b>" + node.data.prob_association;  
      //append connections information  
      //$jit.id('inner-details').innerHTML = html;  
    }  
  },  
  //Number of iterations for the FD algorithm  
  iterations: 200,  
  //Edge length  
  levelDistance: 375,  
  // Add text to the labels. This method is only triggered  
  // on label creation and only for DOM labels (not native canvas ones).  
  onCreateLabel: function(domElement, node){  
    domElement.innerHTML = node.name;  
    var style = domElement.style;  
    style.fontSize = "1em";  
    style.color = "#333";  
  },  
  // Change node styles when DOM labels are placed  
  // or moved.  
  onPlaceLabel: function(domElement, node){  
    var style = domElement.style;  
    var left = parseInt(style.left);  
    var top = parseInt(style.top);  
    var w = domElement.offsetWidth;  
    style.left = (left - w / 2) + 'px';  
    style.top = (top + 10) + 'px';  
    style.display = '';  
  }  
});  
// load JSON data.  
fd.loadJSON(json);  
// compute positions incrementally and animate.  
fd.computeIncremental({  
  iter: 40,  
  property: 'end',  
  onStep: function(perc){  
    //Log.write(perc + '% loaded...');  
  },  
  onComplete: function(){  
    //Log.write('done');  
    fd.animate({  
      modes: ['linear'],  
      transition: $jit.Trans.Elastic.easeOut,  
      duration: 2500  
    });  
  }  
});
}

function removeCategory(cat)
{
	var stuffToRemove = [];
	
	fd.graph.eachNode(function(node) {  
	  if (node.data.category == cat)
		stuffToRemove.push(node.id);
  	});
  	
  	fd.op.removeNode(stuffToRemove);
  	
  	fd.animate();
}

function init(json)
{
	makeGraph(json);
	
	$("#removeStructures").click(function(){
		removeCategory("structure");
	});  

	$("#removeMethods").click(function(){
		removeCategory("method");
	});  
	
	$("#refresh").click(function(){
		makeGraph(json);
	});  
}
