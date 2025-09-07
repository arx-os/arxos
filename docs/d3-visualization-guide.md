# D3.js Visualization Guide for ArxOS

## Overview

ArxOS data structures are specifically designed to bind directly to D3.js visualizations, enabling real-time, data-driven building representations. Every building object and BILT rating is structured to map seamlessly to D3's selection-based data binding.

## Core Concept: Data-Driven Buildings

Just as D3.js creates Data-Driven Documents, ArxOS creates Data-Driven Buildings:

```javascript
// Traditional approach: Static building data
const building = { floors: 10, rooms: 200 };

// ArxOS approach: Data drives the representation
const buildingData = await arxos.getBuildingHierarchy('empire-state');
d3.select('#building-viz')
  .selectAll('.floor')
  .data(buildingData.children)  // Bind floor data
  .join('g')
  .attr('transform', d => `translate(0, ${d.value * 10})`)  // Position by value
  .style('fill', d => healthColorScale(d.health));  // Color by health
```

## 1. Hierarchical Building Visualization

### Sunburst Diagram - Building Structure

```javascript
// Fetch D3-compatible hierarchy
const buildingHierarchy = await fetch('/api/buildings/empire-state/d3/hierarchy')
  .then(res => res.json());

// Create D3 hierarchy
const root = d3.hierarchy(buildingHierarchy)
  .sum(d => d.value)  // Size by object count
  .sort((a, b) => b.value - a.value);

// Partition layout for sunburst
const partition = d3.partition()
  .size([2 * Math.PI, radius]);

// Apply layout
partition(root);

// Create arc generator
const arc = d3.arc()
  .startAngle(d => d.x0)
  .endAngle(d => d.x1)
  .innerRadius(d => d.y0)
  .outerRadius(d => d.y1);

// Bind data and create sunburst
const svg = d3.select('#sunburst');

svg.selectAll('path')
  .data(root.descendants())
  .join('path')
  .attr('d', arc)
  .style('fill', d => {
    // Color by object type or health
    if (d.data.needs_repair) return '#ff4444';
    return colorScale(d.data.node_type);
  })
  .on('click', clicked);  // Zoom on click

// Real-time updates via SSE
const eventSource = new EventSource('/api/events?type=object.updated');
eventSource.onmessage = (event) => {
  const update = JSON.parse(event.data);
  
  // D3 data binding automatically handles updates
  svg.selectAll('path')
    .data(root.descendants(), d => d.data.id)  // Key function for object constancy
    .join(
      enter => enter.append('path'),
      update => update
        .transition()
        .duration(750)
        .style('fill', d => d.data.id === update.id ? '#00ff00' : null),
      exit => exit.remove()
    );
};
```

### Treemap - Space Utilization

```javascript
// Building space data bound to rectangles
const treemap = d3.treemap()
  .size([width, height])
  .padding(2)
  .round(true);

const root = d3.hierarchy(buildingData)
  .sum(d => d.value)  // Size by square footage or object count
  .sort((a, b) => b.height - a.height || b.value - a.value);

treemap(root);

// Bind data to rectangles
const cell = svg.selectAll('g')
  .data(root.leaves(), d => d.data.id)  // Key function for updates
  .join('g')
  .attr('transform', d => `translate(${d.x0},${d.y0})`);

cell.append('rect')
  .attr('width', d => d.x1 - d.x0)
  .attr('height', d => d.y1 - d.y0)
  .attr('fill', d => {
    // Color represents BILT rating contribution
    return d3.interpolateViridis(d.data.rating_contribution);
  });

// Dynamic updates when contributions change
function updateTreemap(newData) {
  root = d3.hierarchy(newData)
    .sum(d => d.value)
    .sort((a, b) => b.height - a.height || b.value - a.value);
  
  treemap(root);
  
  // D3's data join pattern handles enter/update/exit
  cell.data(root.leaves(), d => d.data.id)
    .join(
      enter => enter.append('g'),
      update => update.transition()
        .duration(750)
        .attr('transform', d => `translate(${d.x0},${d.y0})`),
      exit => exit.transition()
        .duration(750)
        .style('opacity', 0)
        .remove()
    );
}
```

## 2. BILT Rating Visualizations

### Radial Progress - Grade Display

```javascript
// BILT grade as radial progress
const biltData = await fetch('/api/buildings/empire-state/rating')
  .then(res => res.json());

// Create scales
const gradeScale = d3.scaleOrdinal()
  .domain(['0z', '0y', '0x', /* ... */, '1A'])
  .range(d3.schemeSpectral[11]);

const angleScale = d3.scaleLinear()
  .domain([0, 100])
  .range([0, 2 * Math.PI]);

// Arc generator for progress
const progressArc = d3.arc()
  .innerRadius(80)
  .outerRadius(100)
  .startAngle(0);

// Bind score to arc
const progress = svg.selectAll('.progress')
  .data([biltData.score])
  .join('path')
  .attr('class', 'progress')
  .attr('d', progressArc.endAngle(d => angleScale(d)))
  .style('fill', gradeScale(biltData.grade));

// Animate on rating change
eventSource.addEventListener('bilt.rating.changed', (event) => {
  const newRating = JSON.parse(event.data);
  
  progress
    .data([newRating.score])
    .transition()
    .duration(1000)
    .attrTween('d', function(d) {
      const interpolate = d3.interpolate(
        this._current || 0,
        angleScale(d)
      );
      this._current = angleScale(d);
      return t => progressArc.endAngle(interpolate(t))();
    })
    .style('fill', gradeScale(newRating.grade));
});
```

### Spider Chart - Component Scores

```javascript
// Component scores for radar/spider chart
const components = biltData.components;
const angleSlice = Math.PI * 2 / components.length;

// Scales
const rScale = d3.scaleLinear()
  .domain([0, 100])
  .range([0, radius]);

// Line generator for polygon
const radarLine = d3.lineRadial()
  .radius(d => rScale(d.value))
  .angle((d, i) => i * angleSlice);

// Bind component data
const radarArea = svg.selectAll('.radar-area')
  .data([components])
  .join('path')
  .attr('class', 'radar-area')
  .attr('d', radarLine)
  .style('fill', 'steelblue')
  .style('fill-opacity', 0.5);

// Dots for each component
const dots = svg.selectAll('.radar-dot')
  .data(components, d => d.name)
  .join('circle')
  .attr('class', 'radar-dot')
  .attr('cx', (d, i) => rScale(d.value) * Math.cos(angleSlice * i - Math.PI / 2))
  .attr('cy', (d, i) => rScale(d.value) * Math.sin(angleSlice * i - Math.PI / 2))
  .attr('r', 4);

// Real-time component updates
function updateRadar(newComponents) {
  // D3 handles the data binding and transitions
  radarArea
    .data([newComponents])
    .transition()
    .duration(750)
    .attr('d', radarLine);
  
  dots
    .data(newComponents, d => d.name)
    .transition()
    .duration(750)
    .attr('cx', (d, i) => rScale(d.value) * Math.cos(angleSlice * i - Math.PI / 2))
    .attr('cy', (d, i) => rScale(d.value) * Math.sin(angleSlice * i - Math.PI / 2));
}
```

## 3. Force-Directed Connection Graph

### Building Systems Network

```javascript
// Fetch connection graph data
const graphData = await fetch('/api/buildings/empire-state/d3/connections')
  .then(res => res.json());

// Create force simulation
const simulation = d3.forceSimulation(graphData.nodes)
  .force('link', d3.forceLink(graphData.links)
    .id(d => d.id)
    .strength(d => d.strength))
  .force('charge', d3.forceManyBody()
    .strength(-300))
  .force('center', d3.forceCenter(width / 2, height / 2))
  .force('collision', d3.forceCollide()
    .radius(d => d.radius + 2));

// Bind links
const link = svg.selectAll('.link')
  .data(graphData.links, d => `${d.source.id}-${d.target.id}`)
  .join('line')
  .attr('class', 'link')
  .style('stroke-width', d => Math.sqrt(d.strength));

// Bind nodes
const node = svg.selectAll('.node')
  .data(graphData.nodes, d => d.id)
  .join('circle')
  .attr('class', 'node')
  .attr('r', d => d.radius)
  .style('fill', d => healthColorScale(d.health))
  .call(drag(simulation));

// Update positions on tick
simulation.on('tick', () => {
  link
    .attr('x1', d => d.source.x)
    .attr('y1', d => d.source.y)
    .attr('x2', d => d.target.x)
    .attr('y2', d => d.target.y);
  
  node
    .attr('cx', d => d.x)
    .attr('cy', d => d.y);
});

// Real-time node updates
eventSource.addEventListener('object.state.changed', (event) => {
  const update = JSON.parse(event.data);
  
  // Find and update the specific node
  node
    .filter(d => d.id === update.object_id)
    .transition()
    .duration(300)
    .style('fill', healthColorScale(update.new_health))
    .attr('r', d => d.radius * (update.needs_repair ? 1.5 : 1));
});
```

## 4. Time Series - Rating History

### Line Chart with Real-time Updates

```javascript
// Rating history data
const history = biltData.history;

// Scales
const xScale = d3.scaleTime()
  .domain(d3.extent(history, d => new Date(d.timestamp * 1000)))
  .range([0, width]);

const yScale = d3.scaleLinear()
  .domain([0, 100])
  .range([height, 0]);

// Line generator
const line = d3.line()
  .x(d => xScale(new Date(d.timestamp * 1000)))
  .y(d => yScale(d.score))
  .curve(d3.curveMonotoneX);

// Bind historical data
const path = svg.selectAll('.line')
  .data([history])
  .join('path')
  .attr('class', 'line')
  .attr('d', line)
  .style('fill', 'none')
  .style('stroke', 'steelblue');

// Real-time streaming updates
let dataBuffer = [...history];
const maxPoints = 100;

eventSource.addEventListener('bilt.rating.calculated', (event) => {
  const newPoint = JSON.parse(event.data);
  
  // Add new data point
  dataBuffer.push({
    timestamp: Date.now() / 1000,
    score: newPoint.score,
    grade: newPoint.grade
  });
  
  // Keep only recent points
  if (dataBuffer.length > maxPoints) {
    dataBuffer.shift();
  }
  
  // Update scales
  xScale.domain(d3.extent(dataBuffer, d => new Date(d.timestamp * 1000)));
  
  // Smooth transition
  path
    .data([dataBuffer])
    .transition()
    .duration(500)
    .ease(d3.easeLinear)
    .attr('d', line);
});
```

## 5. Contribution Heatmap

### Activity Patterns

```javascript
// Heatmap data
const heatmapData = await fetch('/api/buildings/empire-state/d3/heatmap')
  .then(res => res.json());

// Scales
const xScale = d3.scaleBand()
  .domain(d3.range(24))  // Hours
  .range([0, width]);

const yScale = d3.scaleBand()
  .domain(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
  .range([0, height]);

const colorScale = d3.scaleSequential(d3.interpolateYlOrRd)
  .domain([0, d3.max(heatmapData.grid, d => d.value)]);

// Bind heatmap cells
const cells = svg.selectAll('.cell')
  .data(heatmapData.grid, d => `${d.x}-${d.y}`)
  .join('rect')
  .attr('class', 'cell')
  .attr('x', d => xScale(d.x))
  .attr('y', d => yScale(d.y))
  .attr('width', xScale.bandwidth())
  .attr('height', yScale.bandwidth())
  .style('fill', d => colorScale(d.value));

// Live contribution updates
eventSource.addEventListener('contribution.recorded', (event) => {
  const contribution = JSON.parse(event.data);
  const hour = new Date(contribution.timestamp).getHours();
  const day = new Date(contribution.timestamp).getDay();
  
  // Update specific cell
  cells
    .filter(d => d.x === hour && d.y === day)
    .transition()
    .duration(300)
    .style('fill', function(d) {
      d.value += 1;  // Increment contribution count
      return colorScale(d.value);
    })
    .transition()
    .duration(300)
    .style('fill', d => colorScale(d.value));
});
```

## 6. Sankey Diagram - Token Flow

### Value Flow Visualization

```javascript
// Token flow data
const sankeyData = await fetch('/api/buildings/empire-state/d3/sankey')
  .then(res => res.json());

// Sankey generator
const sankey = d3.sankey()
  .nodeWidth(15)
  .nodePadding(10)
  .extent([[1, 1], [width - 1, height - 6]]);

// Process data
const {nodes, links} = sankey(sankeyData);

// Bind links (flows)
const link = svg.selectAll('.sankey-link')
  .data(links, d => `${d.source.id}-${d.target.id}`)
  .join('path')
  .attr('class', 'sankey-link')
  .attr('d', d3.sankeyLinkHorizontal())
  .style('stroke-width', d => Math.max(1, d.width))
  .style('stroke', d => flowColorScale(d.flow_type))
  .style('fill', 'none')
  .style('opacity', 0.5);

// Bind nodes
const node = svg.selectAll('.sankey-node')
  .data(nodes, d => d.id)
  .join('rect')
  .attr('class', 'sankey-node')
  .attr('x', d => d.x0)
  .attr('y', d => d.y0)
  .attr('height', d => d.y1 - d.y0)
  .attr('width', d => d.x1 - d.x0)
  .style('fill', d => nodeColorScale(d.category));

// Real-time token flow updates
eventSource.addEventListener('token.transferred', (event) => {
  const transfer = JSON.parse(event.data);
  
  // Highlight the flow path
  link
    .filter(d => 
      d.source.id === transfer.from && 
      d.target.id === transfer.to
    )
    .transition()
    .duration(500)
    .style('opacity', 1)
    .style('stroke-width', d => Math.max(1, d.width * 1.5))
    .transition()
    .delay(500)
    .duration(500)
    .style('opacity', 0.5)
    .style('stroke-width', d => Math.max(1, d.width));
});
```

## 7. Performance Optimizations

### Virtual DOM with Large Datasets

```javascript
// Use D3 with canvas for thousands of objects
const canvas = d3.select('#canvas-viz')
  .append('canvas')
  .attr('width', width)
  .attr('height', height);

const context = canvas.node().getContext('2d');

// Quadtree for efficient spatial queries
const quadtree = d3.quadtree()
  .x(d => d.x)
  .y(d => d.y)
  .addAll(buildingObjects);

// Render only visible objects
function render() {
  context.clearRect(0, 0, width, height);
  
  // Get objects in viewport
  const visibleObjects = [];
  quadtree.visit((node, x0, y0, x1, y1) => {
    if (!node.length) {
      const d = node.data;
      if (d.x >= viewport.x0 && d.x <= viewport.x1 &&
          d.y >= viewport.y0 && d.y <= viewport.y1) {
        visibleObjects.push(d);
      }
    }
    return x0 > viewport.x1 || x1 < viewport.x0 ||
           y0 > viewport.y1 || y1 < viewport.y0;
  });
  
  // Draw visible objects
  visibleObjects.forEach(d => {
    context.beginPath();
    context.arc(d.x, d.y, d.radius, 0, 2 * Math.PI);
    context.fillStyle = healthColorScale(d.health);
    context.fill();
  });
}

// Debounced updates for real-time data
const debouncedRender = d3.debounce(render, 16);  // 60 FPS

eventSource.onmessage = (event) => {
  const update = JSON.parse(event.data);
  // Update data structure
  updateObjectData(update);
  // Request render
  debouncedRender();
};
```

## 8. Integration with ArxOS API

### Complete Example: Live Building Dashboard

```html
<!DOCTYPE html>
<html>
<head>
  <script src="https://d3js.org/d3.v7.min.js"></script>
  <style>
    .update-flash { fill: #00ff00 !important; }
    .needs-repair { stroke: #ff0000; stroke-width: 3px; }
  </style>
</head>
<body>
  <div id="dashboard"></div>
  
  <script>
    class ArxOSDashboard {
      constructor(buildingId) {
        this.buildingId = buildingId;
        this.eventSource = new EventSource(`/api/events?building_id=${buildingId}`);
        this.setupVisualizations();
        this.bindEvents();
      }
      
      async setupVisualizations() {
        // Fetch initial data
        const [hierarchy, rating, connections] = await Promise.all([
          fetch(`/api/buildings/${this.buildingId}/d3/hierarchy`).then(r => r.json()),
          fetch(`/api/buildings/${this.buildingId}/rating`).then(r => r.json()),
          fetch(`/api/buildings/${this.buildingId}/d3/connections`).then(r => r.json())
        ]);
        
        // Create visualizations
        this.sunburst = this.createSunburst(hierarchy);
        this.ratingGauge = this.createRatingGauge(rating);
        this.forceGraph = this.createForceGraph(connections);
      }
      
      bindEvents() {
        // Object updates
        this.eventSource.addEventListener('object.updated', (e) => {
          const data = JSON.parse(e.data);
          this.updateObject(data);
        });
        
        // Rating changes
        this.eventSource.addEventListener('bilt.rating.changed', (e) => {
          const data = JSON.parse(e.data);
          this.updateRating(data);
        });
        
        // Contributions
        this.eventSource.addEventListener('contribution.recorded', (e) => {
          const data = JSON.parse(e.data);
          this.flashContribution(data);
        });
      }
      
      updateObject(data) {
        // D3's data binding handles the update
        d3.select(`#object-${data.id}`)
          .datum(data)
          .classed('needs-repair', d => d.needs_repair)
          .transition()
          .duration(750)
          .style('fill', d => this.healthColorScale(d.health));
      }
      
      updateRating(data) {
        // Smooth transition for rating changes
        this.ratingGauge
          .datum(data)
          .transition()
          .duration(1000)
          .call(this.animateGauge);
      }
      
      flashContribution(data) {
        // Visual feedback for contributions
        d3.select(`#object-${data.object_id}`)
          .classed('update-flash', true)
          .transition()
          .duration(300)
          .attr('r', d => d.radius * 1.5)
          .transition()
          .duration(300)
          .attr('r', d => d.radius)
          .on('end', function() {
            d3.select(this).classed('update-flash', false);
          });
      }
    }
    
    // Initialize dashboard
    const dashboard = new ArxOSDashboard('empire-state');
  </script>
</body>
</html>
```

## Key Principles

1. **Data Binding is Core**: Every ArxOS object has a unique ID for D3's key function
2. **Real-time Updates**: SSE events trigger D3 transitions automatically
3. **Hierarchical Structure**: Building paths map directly to D3 hierarchies
4. **Scales for Everything**: BILT grades, health scores, all map to D3 scales
5. **Enter/Update/Exit**: ArxOS events align with D3's data join pattern

## Conclusion

ArxOS and D3.js are perfectly aligned - both are fundamentally about making data drive the representation. Every building object, BILT rating, and contribution event is structured to bind directly to visual elements, enabling true data-driven building visualizations that update in real-time as the physical world changes.