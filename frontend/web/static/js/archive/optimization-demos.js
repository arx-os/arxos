/**
 * Interactive Optimization Demos
 * WebGL-based visualizations for Arxos optimization algorithms
 * Pure web technology implementation
 */

class OptimizationDemos {
    constructor() {
        this.canvas = null;
        this.gl = null;
        this.shaderProgram = null;
        this.animationId = null;
        this.isInitialized = false;
        
        this.initializeWebGL();
        this.setupEventListeners();
    }

    /**
     * Initialize WebGL context and shaders
     */
    initializeWebGL() {
        try {
            this.createCanvas();
            this.setupWebGLContext();
            this.compileShaders();
            this.isInitialized = true;
            
            console.log('WebGL optimization demos initialized successfully');
        } catch (error) {
            console.error('WebGL initialization failed:', error);
            this.fallbackToCanvas2D();
        }
    }

    /**
     * Create canvas element for WebGL rendering
     */
    createCanvas() {
        this.canvas = document.createElement('canvas');
        this.canvas.width = 800;
        this.canvas.height = 600;
        this.canvas.className = 'demo-canvas';
        this.canvas.style.cssText = `
            width: 100%;
            height: auto;
            max-width: 800px;
            border-radius: 12px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        `;
    }

    /**
     * Setup WebGL rendering context
     */
    setupWebGLContext() {
        this.gl = this.canvas.getContext('webgl') || this.canvas.getContext('experimental-webgl');
        
        if (!this.gl) {
            throw new Error('WebGL not supported');
        }

        // Set viewport and clear color
        this.gl.viewport(0, 0, this.canvas.width, this.canvas.height);
        this.gl.clearColor(0.95, 0.96, 0.97, 1.0);
        this.gl.enable(this.gl.DEPTH_TEST);
        this.gl.enable(this.gl.BLEND);
        this.gl.blendFunc(this.gl.SRC_ALPHA, this.gl.ONE_MINUS_SRC_ALPHA);
    }

    /**
     * Compile and setup shaders
     */
    compileShaders() {
        const vertexShaderSource = `
            attribute vec3 a_position;
            attribute vec4 a_color;
            uniform mat4 u_modelViewMatrix;
            uniform mat4 u_projectionMatrix;
            varying vec4 v_color;
            
            void main() {
                gl_Position = u_projectionMatrix * u_modelViewMatrix * vec4(a_position, 1.0);
                v_color = a_color;
            }
        `;

        const fragmentShaderSource = `
            precision mediump float;
            varying vec4 v_color;
            uniform float u_time;
            
            void main() {
                float pulse = 0.8 + 0.2 * sin(u_time * 3.0);
                gl_FragColor = v_color * pulse;
            }
        `;

        const vertexShader = this.compileShader(vertexShaderSource, this.gl.VERTEX_SHADER);
        const fragmentShader = this.compileShader(fragmentShaderSource, this.gl.FRAGMENT_SHADER);

        this.shaderProgram = this.gl.createProgram();
        this.gl.attachShader(this.shaderProgram, vertexShader);
        this.gl.attachShader(this.shaderProgram, fragmentShader);
        this.gl.linkProgram(this.shaderProgram);

        if (!this.gl.getProgramParameter(this.shaderProgram, this.gl.LINK_STATUS)) {
            throw new Error('Shader program failed to link: ' + this.gl.getProgramInfoLog(this.shaderProgram));
        }
    }

    /**
     * Compile individual shader
     */
    compileShader(source, type) {
        const shader = this.gl.createShader(type);
        this.gl.shaderSource(shader, source);
        this.gl.compileShader(shader);

        if (!this.gl.getShaderParameter(shader, this.gl.COMPILE_STATUS)) {
            throw new Error('Shader compilation error: ' + this.gl.getShaderInfoLog(shader));
        }

        return shader;
    }

    /**
     * Setup event listeners for demo interactions
     */
    setupEventListeners() {
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('demo-button')) {
                const demoType = e.target.dataset.demo;
                this.runDemo(demoType);
            }
        });
    }

    /**
     * Run specific optimization demo
     */
    runDemo(demoType) {
        if (!this.isInitialized) {
            this.showFallbackDemo(demoType);
            return;
        }

        switch (demoType) {
            case 'genetic':
                this.runGeneticAlgorithmDemo();
                break;
            case 'constraint':
                this.runConstraintSolvingDemo();
                break;
            case 'spatial':
                this.runSpatialOptimizationDemo();
                break;
            case 'nsga':
                this.runNSGAIIDemo();
                break;
            default:
                this.runGenericOptimizationDemo();
        }
    }

    /**
     * Genetic Algorithm Visualization Demo
     */
    runGeneticAlgorithmDemo() {
        const demoContainer = this.createDemoContainer('Genetic Algorithm Optimization');
        demoContainer.appendChild(this.canvas);
        
        this.showDemoModal(demoContainer);
        
        // Initialize genetic algorithm parameters
        const population = this.generatePopulation(50);
        let generation = 0;
        const maxGenerations = 100;
        
        const animate = (time) => {
            this.gl.clear(this.gl.COLOR_BUFFER_BIT | this.gl.DEPTH_BUFFER_BIT);
            
            // Render population
            this.renderPopulation(population, generation / maxGenerations);
            
            // Evolve population
            if (generation < maxGenerations) {
                this.evolvePopulation(population);
                generation++;
            }
            
            // Update generation counter
            this.updateGenerationCounter(generation, maxGenerations);
            
            if (generation < maxGenerations) {
                this.animationId = requestAnimationFrame(animate);
            } else {
                this.showOptimizationComplete(population);
            }
        };
        
        this.animationId = requestAnimationFrame(animate);
    }

    /**
     * NSGA-II Multi-objective Optimization Demo
     */
    runNSGAIIDemo() {
        const demoContainer = this.createDemoContainer('NSGA-II Multi-objective Optimization');
        demoContainer.appendChild(this.canvas);
        
        this.showDemoModal(demoContainer);
        
        // Initialize multi-objective population
        const population = this.generateMultiObjectivePopulation(100);
        let generation = 0;
        
        const animate = (time) => {
            this.gl.clear(this.gl.COLOR_BUFFER_BIT | this.gl.DEPTH_BUFFER_BIT);
            
            // Render Pareto frontier
            this.renderParetoFrontier(population);
            
            // Perform NSGA-II selection
            this.performNSGAIISelection(population);
            
            generation++;
            this.updateGenerationCounter(generation, 150);
            
            if (generation < 150) {
                this.animationId = requestAnimationFrame(animate);
            }
        };
        
        this.animationId = requestAnimationFrame(animate);
    }

    /**
     * Constraint Solving Demo
     */
    runConstraintSolvingDemo() {
        const demoContainer = this.createDemoContainer('Constraint Satisfaction Problem Solving');
        demoContainer.appendChild(this.canvas);
        
        this.showDemoModal(demoContainer);
        
        // Initialize constraint network
        const constraints = this.generateConstraintNetwork();
        let iteration = 0;
        
        const animate = (time) => {
            this.gl.clear(this.gl.COLOR_BUFFER_BIT | this.gl.DEPTH_BUFFER_BIT);
            
            // Render constraint network
            this.renderConstraintNetwork(constraints, iteration);
            
            // Apply constraint propagation
            this.propagateConstraints(constraints);
            
            iteration++;
            
            if (iteration < 200 && !this.isConstraintNetworkSolved(constraints)) {
                this.animationId = requestAnimationFrame(animate);
            } else {
                this.showConstraintSolutionFound(constraints);
            }
        };
        
        this.animationId = requestAnimationFrame(animate);
    }

    /**
     * Spatial Optimization Demo
     */
    runSpatialOptimizationDemo() {
        const demoContainer = this.createDemoContainer('Spatial Optimization with Octree Indexing');
        demoContainer.appendChild(this.canvas);
        
        this.showDemoModal(demoContainer);
        
        // Initialize spatial objects
        const spatialObjects = this.generateSpatialObjects(200);
        const octree = this.buildOctree(spatialObjects);
        let optimizationStep = 0;
        
        const animate = (time) => {
            this.gl.clear(this.gl.COLOR_BUFFER_BIT | this.gl.DEPTH_BUFFER_BIT);
            
            // Render octree structure
            this.renderOctree(octree);
            
            // Render spatial objects
            this.renderSpatialObjects(spatialObjects);
            
            // Perform spatial optimization
            this.optimizeSpatialLayout(spatialObjects, octree);
            
            optimizationStep++;
            
            if (optimizationStep < 300) {
                this.animationId = requestAnimationFrame(animate);
            }
        };
        
        this.animationId = requestAnimationFrame(animate);
    }

    /**
     * Generate population for genetic algorithm
     */
    generatePopulation(size) {
        const population = [];
        for (let i = 0; i < size; i++) {
            population.push({
                genes: Array.from({length: 10}, () => Math.random()),
                fitness: Math.random(),
                x: (Math.random() - 0.5) * 2,
                y: (Math.random() - 0.5) * 2,
                color: [Math.random(), Math.random(), Math.random(), 0.8]
            });
        }
        return population;
    }

    /**
     * Generate multi-objective population
     */
    generateMultiObjectivePopulation(size) {
        const population = [];
        for (let i = 0; i < size; i++) {
            const individual = {
                genes: Array.from({length: 5}, () => Math.random()),
                objectives: [Math.random(), Math.random()],
                rank: 0,
                crowdingDistance: 0,
                x: Math.random() * 2 - 1,
                y: Math.random() * 2 - 1,
                color: [0.2, 0.6, 1.0, 0.7]
            };
            population.push(individual);
        }
        return population;
    }

    /**
     * Evolve population using genetic operators
     */
    evolvePopulation(population) {
        // Selection
        population.sort((a, b) => b.fitness - a.fitness);
        
        // Crossover and mutation
        for (let i = population.length / 2; i < population.length; i++) {
            const parent1 = population[Math.floor(Math.random() * population.length / 2)];
            const parent2 = population[Math.floor(Math.random() * population.length / 2)];
            
            // Simple crossover
            population[i].genes = parent1.genes.map((gene, idx) => 
                Math.random() < 0.5 ? gene : parent2.genes[idx]
            );
            
            // Mutation
            population[i].genes = population[i].genes.map(gene => 
                Math.random() < 0.1 ? Math.random() : gene
            );
            
            // Update fitness and position
            population[i].fitness = this.evaluateFitness(population[i].genes);
            population[i].x = (population[i].fitness - 0.5) * 2;
            population[i].y = (Math.random() - 0.5) * 2;
        }
    }

    /**
     * Evaluate fitness function
     */
    evaluateFitness(genes) {
        // Simple fitness function for demonstration
        return genes.reduce((sum, gene) => sum + Math.sin(gene * Math.PI * 2), 0) / genes.length + 0.5;
    }

    /**
     * Render population as colored points
     */
    renderPopulation(population, progress) {
        this.gl.useProgram(this.shaderProgram);
        
        // Create vertex data
        const vertices = [];
        const colors = [];
        
        population.forEach(individual => {
            vertices.push(individual.x, individual.y, 0);
            const intensity = individual.fitness;
            colors.push(intensity, 1 - intensity, 0.5, 0.8);
        });
        
        this.renderPoints(vertices, colors);
    }

    /**
     * Render Pareto frontier
     */
    renderParetoFrontier(population) {
        this.gl.useProgram(this.shaderProgram);
        
        // Calculate Pareto frontier
        const paretoFront = this.calculateParetoFront(population);
        
        const vertices = [];
        const colors = [];
        
        paretoFront.forEach(individual => {
            vertices.push(
                individual.objectives[0] * 2 - 1,
                individual.objectives[1] * 2 - 1,
                0
            );
            colors.push(1.0, 0.3, 0.3, 0.9);
        });
        
        // Render non-dominated solutions in red
        this.renderPoints(vertices, colors);
        
        // Render rest of population in blue
        const otherVertices = [];
        const otherColors = [];
        
        population.filter(ind => !paretoFront.includes(ind)).forEach(individual => {
            otherVertices.push(
                individual.objectives[0] * 2 - 1,
                individual.objectives[1] * 2 - 1,
                0
            );
            otherColors.push(0.3, 0.3, 1.0, 0.5);
        });
        
        this.renderPoints(otherVertices, otherColors);
    }

    /**
     * Calculate Pareto frontier
     */
    calculateParetoFront(population) {
        const paretoFront = [];
        
        for (let i = 0; i < population.length; i++) {
            let isDominated = false;
            
            for (let j = 0; j < population.length; j++) {
                if (i !== j && this.dominates(population[j], population[i])) {
                    isDominated = true;
                    break;
                }
            }
            
            if (!isDominated) {
                paretoFront.push(population[i]);
            }
        }
        
        return paretoFront;
    }

    /**
     * Check if individual a dominates individual b
     */
    dominates(a, b) {
        let betterInOne = false;
        
        for (let i = 0; i < a.objectives.length; i++) {
            if (a.objectives[i] < b.objectives[i]) {
                return false;
            }
            if (a.objectives[i] > b.objectives[i]) {
                betterInOne = true;
            }
        }
        
        return betterInOne;
    }

    /**
     * Render points using WebGL
     */
    renderPoints(vertices, colors) {
        if (vertices.length === 0) return;
        
        // Create and bind vertex buffer
        const vertexBuffer = this.gl.createBuffer();
        this.gl.bindBuffer(this.gl.ARRAY_BUFFER, vertexBuffer);
        this.gl.bufferData(this.gl.ARRAY_BUFFER, new Float32Array(vertices), this.gl.STATIC_DRAW);
        
        // Create and bind color buffer
        const colorBuffer = this.gl.createBuffer();
        this.gl.bindBuffer(this.gl.ARRAY_BUFFER, colorBuffer);
        this.gl.bufferData(this.gl.ARRAY_BUFFER, new Float32Array(colors), this.gl.STATIC_DRAW);
        
        // Set up vertex attributes
        const positionAttributeLocation = this.gl.getAttribLocation(this.shaderProgram, 'a_position');
        const colorAttributeLocation = this.gl.getAttribLocation(this.shaderProgram, 'a_color');
        
        this.gl.bindBuffer(this.gl.ARRAY_BUFFER, vertexBuffer);
        this.gl.enableVertexAttribArray(positionAttributeLocation);
        this.gl.vertexAttribPointer(positionAttributeLocation, 3, this.gl.FLOAT, false, 0, 0);
        
        this.gl.bindBuffer(this.gl.ARRAY_BUFFER, colorBuffer);
        this.gl.enableVertexAttribArray(colorAttributeLocation);
        this.gl.vertexAttribPointer(colorAttributeLocation, 4, this.gl.FLOAT, false, 0, 0);
        
        // Set uniforms
        const modelViewMatrixLocation = this.gl.getUniformLocation(this.shaderProgram, 'u_modelViewMatrix');
        const projectionMatrixLocation = this.gl.getUniformLocation(this.shaderProgram, 'u_projectionMatrix');
        const timeLocation = this.gl.getUniformLocation(this.shaderProgram, 'u_time');
        
        const identity = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1];
        this.gl.uniformMatrix4fv(modelViewMatrixLocation, false, identity);
        this.gl.uniformMatrix4fv(projectionMatrixLocation, false, identity);
        this.gl.uniform1f(timeLocation, performance.now() / 1000);
        
        // Draw points
        this.gl.drawArrays(this.gl.POINTS, 0, vertices.length / 3);
    }

    /**
     * Create demo container modal
     */
    createDemoContainer(title) {
        const container = document.createElement('div');
        container.className = 'demo-container';
        container.innerHTML = `
            <div class="demo-header">
                <h3 class="text-xl font-bold">${title}</h3>
                <button class="demo-close btn btn-outline btn-sm">Close</button>
            </div>
            <div class="demo-content"></div>
            <div class="demo-controls">
                <div class="demo-stats">
                    <span id="generation-counter">Generation: 0</span>
                    <span id="fitness-display">Best Fitness: 0.0</span>
                </div>
            </div>
        `;
        
        return container;
    }

    /**
     * Show demo modal
     */
    showDemoModal(container) {
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center';
        modal.appendChild(container);
        
        // Close modal functionality
        const closeButton = container.querySelector('.demo-close');
        closeButton.addEventListener('click', () => {
            this.stopAnimation();
            document.body.removeChild(modal);
        });
        
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.stopAnimation();
                document.body.removeChild(modal);
            }
        });
        
        document.body.appendChild(modal);
    }

    /**
     * Update generation counter
     */
    updateGenerationCounter(generation, maxGenerations) {
        const counter = document.getElementById('generation-counter');
        if (counter) {
            counter.textContent = `Generation: ${generation}/${maxGenerations}`;
        }
    }

    /**
     * Stop animation
     */
    stopAnimation() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
    }

    /**
     * Fallback to Canvas 2D if WebGL is not available
     */
    fallbackToCanvas2D() {
        console.log('Falling back to Canvas 2D rendering');
        this.canvas = document.createElement('canvas');
        this.canvas.width = 800;
        this.canvas.height = 600;
        this.ctx = this.canvas.getContext('2d');
        this.isInitialized = true;
    }

    /**
     * Show fallback demo using Canvas 2D
     */
    showFallbackDemo(demoType) {
        const demoContainer = this.createDemoContainer(`${demoType} Optimization (Canvas 2D)`);
        demoContainer.appendChild(this.canvas);
        
        this.showDemoModal(demoContainer);
        
        // Simple 2D animation
        let frame = 0;
        const animate = () => {
            this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
            
            // Draw simple optimization visualization
            this.drawSimpleOptimization(frame);
            frame++;
            
            if (frame < 300) {
                this.animationId = requestAnimationFrame(animate);
            }
        };
        
        this.animationId = requestAnimationFrame(animate);
    }

    /**
     * Draw simple optimization using Canvas 2D
     */
    drawSimpleOptimization(frame) {
        const centerX = this.canvas.width / 2;
        const centerY = this.canvas.height / 2;
        
        // Draw optimization progress
        for (let i = 0; i < 50; i++) {
            const angle = (i / 50) * Math.PI * 2 + frame * 0.01;
            const radius = 100 + Math.sin(frame * 0.02 + i) * 50;
            const x = centerX + Math.cos(angle) * radius;
            const y = centerY + Math.sin(angle) * radius;
            
            this.ctx.beginPath();
            this.ctx.arc(x, y, 3, 0, Math.PI * 2);
            this.ctx.fillStyle = `hsl(${(frame + i * 10) % 360}, 70%, 60%)`;
            this.ctx.fill();
        }
        
        // Draw convergence indicator
        this.ctx.font = '16px Arial';
        this.ctx.fillStyle = '#333';
        this.ctx.fillText(`Optimization Progress: ${Math.min(100, Math.floor(frame / 3))}%`, 10, 30);
    }

    // Placeholder methods for spatial optimization
    generateConstraintNetwork() { return []; }
    generateSpatialObjects() { return []; }
    buildOctree() { return {}; }
    renderConstraintNetwork() {}
    renderOctree() {}
    renderSpatialObjects() {}
    propagateConstraints() {}
    isConstraintNetworkSolved() { return false; }
    optimizeSpatialLayout() {}
    performNSGAIISelection() {}
    showOptimizationComplete() {}
    showConstraintSolutionFound() {}
}

// Initialize optimization demos
document.addEventListener('DOMContentLoaded', () => {
    window.optimizationDemos = new OptimizationDemos();
    
    // Add demo buttons to landing page demo section
    const demoButtons = document.querySelectorAll('.demo-button');
    demoButtons.forEach((button, index) => {
        const demoTypes = ['genetic', 'constraint', 'spatial', 'nsga'];
        if (!button.dataset.demo && demoTypes[index]) {
            button.dataset.demo = demoTypes[index];
        }
    });
});

// Export for external use
window.OptimizationDemos = OptimizationDemos;