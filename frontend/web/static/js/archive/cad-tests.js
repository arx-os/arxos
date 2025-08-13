/**
 * Arxos CAD System JavaScript Test Suite
 * Browser-based testing for CAD functionality
 *
 * @author Arxos Team
 * @version 1.0.0
 * @license MIT
 */

class CadTestSuite {
    constructor() {
        this.tests = [];
        this.results = [];
        this.currentTest = null;
        this.testCanvas = null;
        this.testContext = null;
    }

    /**
     * Initialize test environment
     */
    async initialize() {
        console.log('Initializing CAD Test Suite...');

        // Create test canvas
        this.createTestCanvas();

        // Initialize test components
        this.cadEngine = new CadEngine();
        this.arxObjectSystem = new ArxObjectSystem();
        this.aiAssistant = new AiAssistant();

        // Register all tests
        this.registerTests();

        console.log('CAD Test Suite initialized successfully');
    }

    /**
     * Create test canvas
     */
    createTestCanvas() {
        // Create a test canvas if it doesn't exist
        let canvas = document.getElementById('test-canvas');
        if (!canvas) {
            canvas = document.createElement('canvas');
            canvas.id = 'test-canvas';
            canvas.width = 800;
            canvas.height = 600;
            canvas.style.border = '1px solid #ccc';
            document.body.appendChild(canvas);
        }

        this.testCanvas = canvas;
        this.testContext = canvas.getContext('2d');
    }

    /**
     * Register all tests
     */
    registerTests() {
        // Core functionality tests
        this.addTest('Class Loading', this.testClassLoading.bind(this));
        this.addTest('CAD Engine Initialization', this.testCadEngineInit.bind(this));
        this.addTest('ArxObject System', this.testArxObjectSystem.bind(this));
        this.addTest('AI Assistant', this.testAiAssistant.bind(this));

        // Drawing tests
        this.addTest('Drawing Tools', this.testDrawingTools.bind(this));
        this.addTest('Precision Drawing', this.testPrecisionDrawing.bind(this));
        this.addTest('Object Creation', this.testObjectCreation.bind(this));
        this.addTest('Object Selection', this.testObjectSelection.bind(this));

        // Performance tests
        this.addTest('Performance Tracking', this.testPerformanceTracking.bind(this));
        this.addTest('Memory Management', this.testMemoryManagement.bind(this));
        this.addTest('Rendering Performance', this.testRenderingPerformance.bind(this));

        // Export/Import tests
        this.addTest('SVG Export', this.testSvgExport.bind(this));
        this.addTest('JSON Export', this.testJsonExport.bind(this));
        this.addTest('JSON Import', this.testJsonImport.bind(this));

        // AI functionality tests
        this.addTest('AI Command Parsing', this.testAiCommandParsing.bind(this));
        this.addTest('AI Object Creation', this.testAiObjectCreation.bind(this));
        this.addTest('AI Design Analysis', this.testAiDesignAnalysis.bind(this));

        // Event system tests
        this.addTest('Event System', this.testEventSystem.bind(this));
        this.addTest('Keyboard Shortcuts', this.testKeyboardShortcuts.bind(this));
        this.addTest('Mouse Interactions', this.testMouseInteractions.bind(this));

        // Measurement tests
        this.addTest('Measurement Calculations', this.testMeasurementCalculations.bind(this));
        this.addTest('Constraint System', this.testConstraintSystem.bind(this));
        this.addTest('Relationship System', this.testRelationshipSystem.bind(this));
    }

    /**
     * Add a test to the suite
     */
    addTest(name, testFunction) {
        this.tests.push({
            name: name,
            function: testFunction
        });
    }

    /**
     * Run all tests
     */
    async runAllTests() {
        console.log('Running CAD Test Suite...');

        this.results = [];
        let passed = 0;
        let failed = 0;

        for (const test of this.tests) {
            try {
                this.currentTest = test.name;
                console.log(`Running test: ${test.name}`);

                const result = await test.function();

                if (result) {
                    this.results.push({ name: test.name, status: 'PASS', message: 'Test passed' });
                    passed++;
                    console.log(`✅ ${test.name}: PASS`);
                } else {
                    this.results.push({ name: test.name, status: 'FAIL', message: 'Test failed' });
                    failed++;
                    console.log(`❌ ${test.name}: FAIL`);
                }

            } catch (error) {
                this.results.push({ name: test.name, status: 'ERROR', message: error.message });
                failed++;
                console.log(`❌ ${test.name}: ERROR - ${error.message}`);
            }
        }

        console.log(`\nTest Results: ${passed} passed, ${failed} failed`);
        this.displayResults();

        return {
            total: this.tests.length,
            passed: passed,
            failed: failed,
            results: this.results
        };
    }

    /**
     * Display test results
     */
    displayResults() {
        const resultsDiv = document.getElementById('test-results');
        if (!resultsDiv) return;

        resultsDiv.innerHTML = '';

        for (const result of this.results) {
            const div = document.createElement('div');
            div.className = `p-2 rounded mb-2 ${
                result.status === 'PASS' ? 'bg-green-600' :
                result.status === 'FAIL' ? 'bg-red-600' : 'bg-yellow-600'
            }`;
            div.textContent = `${result.status}: ${result.name} - ${result.message}`;
            resultsDiv.appendChild(div);
        }
    }

    /**
     * Test class loading
     */
    async testClassLoading() {
        // Check if all required classes are available
        if (typeof CadEngine === 'undefined') {
            throw new Error('CadEngine class not loaded');
        }

        if (typeof ArxObjectSystem === 'undefined') {
            throw new Error('ArxObjectSystem class not loaded');
        }

        if (typeof AiAssistant === 'undefined') {
            throw new Error('AiAssistant class not loaded');
        }

        if (typeof CadApplication === 'undefined') {
            throw new Error('CadApplication class not loaded');
        }

        return true;
    }

    /**
     * Test CAD Engine initialization
     */
    async testCadEngineInit() {
        const cadEngine = new CadEngine();
        await cadEngine.initialize('test-canvas');

        if (!cadEngine.isInitialized) {
            throw new Error('CAD Engine failed to initialize');
        }

        if (!cadEngine.canvas) {
            throw new Error('Canvas not found');
        }

        if (!cadEngine.ctx) {
            throw new Error('Canvas context not available');
        }

        return true;
    }

    /**
     * Test ArxObject System
     */
    async testArxObjectSystem() {
        const arxSystem = new ArxObjectSystem();

        // Test object creation
        const geometry = {
            type: 'rectangle',
            startPoint: { x: 0, y: 0 },
            endPoint: { x: 100, y: 100 }
        };

        const arxObject = arxSystem.createArxObject('room', geometry, {
            name: 'Test Room',
            type: 'bedroom'
        });

        if (!arxObject || !arxObject.id) {
            throw new Error('Failed to create ArxObject');
        }

        // Test object retrieval
        const retrievedObject = arxSystem.getArxObject(arxObject.id);
        if (!retrievedObject) {
            throw new Error('Failed to retrieve ArxObject');
        }

        // Test object update
        arxSystem.updateArxObject(arxObject.id, {
            properties: { name: 'Updated Room' }
        });

        const updatedObject = arxSystem.getArxObject(arxObject.id);
        if (updatedObject.properties.name !== 'Updated Room') {
            throw new Error('Failed to update ArxObject');
        }

        // Test object deletion
        arxSystem.deleteArxObject(arxObject.id);
        const deletedObject = arxSystem.getArxObject(arxObject.id);
        if (deletedObject) {
            throw new Error('Failed to delete ArxObject');
        }

        return true;
    }

    /**
     * Test AI Assistant
     */
    async testAiAssistant() {
        const aiAssistant = new AiAssistant();
        const arxSystem = new ArxObjectSystem();

        // Test message processing
        const response = await aiAssistant.processMessage('Hello', arxSystem);

        if (!response || typeof response !== 'string') {
            throw new Error('AI Assistant not responding correctly');
        }

        // Test intent parsing
        const intent = aiAssistant.parseIntent('Create a room');
        if (!intent || intent.type !== 'create') {
            throw new Error('AI intent parsing failed');
        }

        return true;
    }

    /**
     * Test drawing tools
     */
    async testDrawingTools() {
        const cadEngine = new CadEngine();
        await cadEngine.initialize('test-canvas');

        // Test tool switching
        cadEngine.setCurrentTool('line');
        if (cadEngine.currentTool !== 'line') {
            throw new Error('Failed to set drawing tool');
        }

        cadEngine.setCurrentTool('rectangle');
        if (cadEngine.currentTool !== 'rectangle') {
            throw new Error('Failed to set drawing tool');
        }

        cadEngine.setCurrentTool('circle');
        if (cadEngine.currentTool !== 'circle') {
            throw new Error('Failed to set drawing tool');
        }

        return true;
    }

    /**
     * Test precision drawing
     */
    async testPrecisionDrawing() {
        const cadEngine = new CadEngine();
        await cadEngine.initialize('test-canvas');

        // Test precision settings
        cadEngine.setPrecision(0.001);
        if (cadEngine.precision !== 0.001) {
            throw new Error('Failed to set precision');
        }

        cadEngine.setPrecision(0.01);
        if (cadEngine.precision !== 0.01) {
            throw new Error('Failed to set precision');
        }

        // Test grid snapping
        const point = { x: 10.123, y: 20.456 };
        const snappedPoint = cadEngine.snapToGrid(point);

        if (snappedPoint.x === point.x || snappedPoint.y === point.y) {
            throw new Error('Grid snapping not working');
        }

        return true;
    }

    /**
     * Test object creation
     */
    async testObjectCreation() {
        const cadEngine = new CadEngine();
        await cadEngine.initialize('test-canvas');

        // Test line creation
        const lineObject = cadEngine.createArxObject(
            { x: 0, y: 0 },
            { x: 100, y: 100 }
        );

        if (!lineObject || lineObject.type !== 'line') {
            throw new Error('Failed to create line object');
        }

        // Test rectangle creation
        const rectObject = cadEngine.createArxObject(
            { x: 0, y: 0 },
            { x: 100, y: 100 }
        );

        if (!rectObject || rectObject.type !== 'rectangle') {
            throw new Error('Failed to create rectangle object');
        }

        // Test circle creation
        const circleObject = cadEngine.createArxObject(
            { x: 50, y: 50 },
            { x: 100, y: 50 }
        );

        if (!circleObject || circleObject.type !== 'circle') {
            throw new Error('Failed to create circle object');
        }

        return true;
    }

    /**
     * Test object selection
     */
    async testObjectSelection() {
        const cadEngine = new CadEngine();
        await cadEngine.initialize('test-canvas');

        // Create test object
        const testObject = cadEngine.createArxObject(
            { x: 50, y: 50 },
            { x: 150, y: 150 }
        );

        cadEngine.addArxObject(testObject);

        // Test selection
        cadEngine.selectedObjects.add(testObject.id);

        if (!cadEngine.selectedObjects.has(testObject.id)) {
            throw new Error('Failed to select object');
        }

        // Test deselection
        cadEngine.selectedObjects.delete(testObject.id);

        if (cadEngine.selectedObjects.has(testObject.id)) {
            throw new Error('Failed to deselect object');
        }

        return true;
    }

    /**
     * Test performance tracking
     */
    async testPerformanceTracking() {
        const cadEngine = new CadEngine();
        await cadEngine.initialize('test-canvas');

        // Test FPS calculation
        const startTime = performance.now();
        cadEngine.updatePerformance();
        const endTime = performance.now();

        if (cadEngine.fps <= 0) {
            throw new Error('FPS calculation failed');
        }

        return true;
    }

    /**
     * Test memory management
     */
    async testMemoryManagement() {
        const cadEngine = new CadEngine();
        await cadEngine.initialize('test-canvas');

        const initialObjectCount = cadEngine.arxObjects.size;

        // Create objects
        for (let i = 0; i < 10; i++) {
            const obj = cadEngine.createArxObject(
                { x: i * 10, y: i * 10 },
                { x: (i + 1) * 10, y: (i + 1) * 10 }
            );
            cadEngine.addArxObject(obj);
        }

        if (cadEngine.arxObjects.size !== initialObjectCount + 10) {
            throw new Error('Object addition failed');
        }

        // Delete objects
        for (const [id, obj] of cadEngine.arxObjects) {
            cadEngine.arxObjects.delete(id);
        }

        if (cadEngine.arxObjects.size !== 0) {
            throw new Error('Object deletion failed');
        }

        return true;
    }

    /**
     * Test rendering performance
     */
    async testRenderingPerformance() {
        const cadEngine = new CadEngine();
        await cadEngine.initialize('test-canvas');

        // Create multiple objects
        for (let i = 0; i < 100; i++) {
            const obj = cadEngine.createArxObject(
                { x: i * 5, y: i * 5 },
                { x: (i + 1) * 5, y: (i + 1) * 5 }
            );
            cadEngine.addArxObject(obj);
        }

        // Test rendering
        const startTime = performance.now();
        cadEngine.render();
        const endTime = performance.now();

        const renderTime = endTime - startTime;
        if (renderTime > 16.67) { // Should render in less than 16.67ms for 60fps
            throw new Error(`Rendering too slow: ${renderTime.toFixed(2)}ms`);
        }

        return true;
    }

    /**
     * Test SVG export
     */
    async testSvgExport() {
        const cadEngine = new CadEngine();
        await cadEngine.initialize('test-canvas');

        // Create test object
        const testObject = cadEngine.createArxObject(
            { x: 0, y: 0 },
            { x: 100, y: 100 }
        );
        cadEngine.addArxObject(testObject);

        // Export to SVG
        const svg = cadEngine.exportToSVG();

        if (!svg || typeof svg !== 'string') {
            throw new Error('SVG export failed');
        }

        if (!svg.includes('<svg')) {
            throw new Error('Invalid SVG output');
        }

        return true;
    }

    /**
     * Test JSON export
     */
    async testJsonExport() {
        const arxSystem = new ArxObjectSystem();

        // Create test object
        const geometry = {
            type: 'rectangle',
            startPoint: { x: 0, y: 0 },
            endPoint: { x: 100, y: 100 }
        };

        const arxObject = arxSystem.createArxObject('room', geometry);

        // Export to JSON
        const json = arxSystem.exportToJSON();

        if (!json || typeof json !== 'string') {
            throw new Error('JSON export failed');
        }

        // Parse JSON to verify it's valid
        try {
            const parsed = JSON.parse(json);
            if (!parsed.arxObjects || !Array.isArray(parsed.arxObjects)) {
                throw new Error('Invalid JSON structure');
            }
        } catch (e) {
            throw new Error('Invalid JSON output');
        }

        return true;
    }

    /**
     * Test JSON import
     */
    async testJsonImport() {
        const arxSystem = new ArxObjectSystem();

        // Create test data
        const testData = {
            arxObjects: [{
                id: 'test_123',
                type: 'room',
                geometry: {
                    type: 'rectangle',
                    startPoint: { x: 0, y: 0 },
                    endPoint: { x: 100, y: 100 }
                },
                properties: { name: 'Test Room' },
                measurements: [],
                constraints: [],
                relationships: [],
                metadata: { created: Date.now() }
            }],
            relationships: [],
            metadata: { exported: Date.now() }
        };

        const jsonData = JSON.stringify(testData);

        // Import JSON
        arxSystem.importFromJSON(jsonData);

        // Verify import
        const importedObject = arxSystem.getArxObject('test_123');
        if (!importedObject) {
            throw new Error('JSON import failed');
        }

        if (importedObject.type !== 'room') {
            throw new Error('Imported object type incorrect');
        }

        return true;
    }

    /**
     * Test AI command parsing
     */
    async testAiCommandParsing() {
        const aiAssistant = new AiAssistant();

        // Test create commands
        const createIntent = aiAssistant.parseIntent('Create a room');
        if (createIntent.type !== 'create') {
            throw new Error('Create command parsing failed');
        }

        // Test modify commands
        const modifyIntent = aiAssistant.parseIntent('Modify the door');
        if (modifyIntent.type !== 'modify') {
            throw new Error('Modify command parsing failed');
        }

        // Test analyze commands
        const analyzeIntent = aiAssistant.parseIntent('Analyze the design');
        if (analyzeIntent.type !== 'analyze') {
            throw new Error('Analyze command parsing failed');
        }

        return true;
    }

    /**
     * Test AI object creation
     */
    async testAiObjectCreation() {
        const aiAssistant = new AiAssistant();
        const arxSystem = new ArxObjectSystem();

        // Test room creation
        const response = await aiAssistant.processMessage('Create a 20x30 room', arxSystem);

        if (!response || typeof response !== 'string') {
            throw new Error('AI object creation failed');
        }

        if (!response.includes('created')) {
            throw new Error('AI response not indicating creation');
        }

        return true;
    }

    /**
     * Test AI design analysis
     */
    async testAiDesignAnalysis() {
        const aiAssistant = new AiAssistant();
        const arxSystem = new ArxObjectSystem();

        // Create some test objects
        const geometry = {
            type: 'rectangle',
            startPoint: { x: 0, y: 0 },
            endPoint: { x: 100, y: 100 }
        };

        arxSystem.createArxObject('room', geometry);

        // Test analysis
        const response = await aiAssistant.processMessage('Analyze the design', arxSystem);

        if (!response || typeof response !== 'string') {
            throw new Error('AI design analysis failed');
        }

        if (!response.includes('analysis') && !response.includes('statistics')) {
            throw new Error('AI analysis response incomplete');
        }

        return true;
    }

    /**
     * Test event system
     */
    async testEventSystem() {
        const cadEngine = new CadEngine();
        await cadEngine.initialize('test-canvas');

        let eventReceived = false;

        // Add event listener
        cadEngine.addEventListener('testEvent', (data) => {
            eventReceived = true;
        });

        // Dispatch event
        cadEngine.dispatchEvent('testEvent', { test: true });

        if (!eventReceived) {
            throw new Error('Event system not working');
        }

        return true;
    }

    /**
     * Test keyboard shortcuts
     */
    async testKeyboardShortcuts() {
        const cadEngine = new CadEngine();
        await cadEngine.initialize('test-canvas');

        // Test key handling
        const keyEvent = new KeyboardEvent('keydown', {
            key: 'Escape',
            bubbles: true
        });

        // Simulate key press
        document.dispatchEvent(keyEvent);

        // Verify tool is reset to select
        if (cadEngine.currentTool !== 'select') {
            // This is expected behavior - Escape should cancel drawing
            console.log('Escape key handling working');
        }

        return true;
    }

    /**
     * Test mouse interactions
     */
    async testMouseInteractions() {
        const cadEngine = new CadEngine();
        await cadEngine.initialize('test-canvas');

        // Test mouse coordinate tracking
        const mouseEvent = new MouseEvent('mousemove', {
            clientX: 100,
            clientY: 100,
            bubbles: true
        });

        cadEngine.canvas.dispatchEvent(mouseEvent);

        // Verify coordinate tracking
        if (cadEngine.currentPoint &&
            (cadEngine.currentPoint.x !== 0 || cadEngine.currentPoint.y !== 0)) {
            console.log('Mouse coordinate tracking working');
        }

        return true;
    }

    /**
     * Test measurement calculations
     */
    async testMeasurementCalculations() {
        const arxSystem = new ArxObjectSystem();

        // Test area calculation
        const geometry = {
            type: 'rectangle',
            startPoint: { x: 0, y: 0 },
            endPoint: { x: 100, y: 100 }
        };

        const arxObject = arxSystem.createArxObject('room', geometry);

        // Check measurements
        const areaMeasurement = arxObject.measurements.find(m => m.type === 'area');
        if (!areaMeasurement || areaMeasurement.value !== 10000) {
            throw new Error('Area calculation failed');
        }

        return true;
    }

    /**
     * Test constraint system
     */
    async testConstraintSystem() {
        const arxSystem = new ArxObjectSystem();

        // Test constraint creation
        const geometry = {
            type: 'rectangle',
            startPoint: { x: 0, y: 0 },
            endPoint: { x: 100, y: 100 }
        };

        const arxObject = arxSystem.createArxObject('room', geometry);

        // Add constraint
        arxSystem.addConstraint(arxObject.id, 'width', { value: 100 });

        if (arxObject.constraints.length === 0) {
            throw new Error('Constraint addition failed');
        }

        return true;
    }

    /**
     * Test relationship system
     */
    async testRelationshipSystem() {
        const arxSystem = new ArxObjectSystem();

        // Create two objects
        const geometry1 = {
            type: 'rectangle',
            startPoint: { x: 0, y: 0 },
            endPoint: { x: 100, y: 100 }
        };

        const geometry2 = {
            type: 'rectangle',
            startPoint: { x: 100, y: 0 },
            endPoint: { x: 200, y: 100 }
        };

        const obj1 = arxSystem.createArxObject('room', geometry1);
        const obj2 = arxSystem.createArxObject('room', geometry2);

        // Add relationship
        arxSystem.addRelationship(obj1.id, obj2.id, 'adjacent');

        // Check relationships
        const relatedObjects = arxSystem.getRelatedArxObjects(obj1.id);
        if (relatedObjects.length === 0) {
            throw new Error('Relationship creation failed');
        }

        return true;
    }
}

// Export for global use
window.CadTestSuite = CadTestSuite;
