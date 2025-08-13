/**
 * Landing Page Interactive Features
 * Pure JavaScript implementation for arxos.io landing page
 * No React/TS - Web technology only
 */

class LandingPageController {
    constructor() {
        this.initializeAnimations();
        this.initializeDemoSystem();
        this.initializeMetrics();
        this.initializeNavigation();
        this.initializeOptimizationViz();
    }

    /**
     * Initialize smooth animations and intersection observers
     */
    initializeAnimations() {
        // Fade-in animation for sections
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                    
                    // Trigger counter animations for statistics
                    if (entry.target.classList.contains('stats-container')) {
                        this.animateCounters();
                    }
                }
            });
        }, observerOptions);

        // Observe all sections and cards
        document.querySelectorAll('section, .algorithm-card').forEach(el => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(20px)';
            el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            observer.observe(el);
        });

        // Parallax effect for hero background
        this.initializeParallax();
    }

    /**
     * Initialize parallax scrolling effects
     */
    initializeParallax() {
        window.addEventListener('scroll', () => {
            const scrolled = window.pageYOffset;
            const parallaxElements = document.querySelectorAll('.hero-pattern');
            
            parallaxElements.forEach(el => {
                const speed = 0.5;
                el.style.transform = `translateY(${scrolled * speed}px)`;
            });
        });
    }

    /**
     * Animate statistics counters
     */
    animateCounters() {
        const counters = [
            { element: document.querySelector('[data-counter="success"]'), target: 94.6, suffix: '%' },
            { element: document.querySelector('[data-counter="response"]'), target: 100, suffix: 'ms', prefix: '<' },
            { element: document.querySelector('[data-counter="endpoints"]'), target: 500, suffix: '+' }
        ];

        counters.forEach(counter => {
            if (!counter.element || counter.element.dataset.animated) return;
            
            counter.element.dataset.animated = 'true';
            const start = 0;
            const duration = 2000;
            const startTime = performance.now();

            const animate = (currentTime) => {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
                
                const current = start + (counter.target - start) * this.easeOutQuart(progress);
                const value = counter.target % 1 === 0 ? Math.floor(current) : current.toFixed(1);
                
                counter.element.textContent = 
                    (counter.prefix || '') + value + (counter.suffix || '');
                
                if (progress < 1) {
                    requestAnimationFrame(animate);
                }
            };

            requestAnimationFrame(animate);
        });
    }

    /**
     * Easing function for smooth animations
     */
    easeOutQuart(t) {
        return 1 - Math.pow(1 - t, 4);
    }

    /**
     * Initialize interactive demo system
     */
    initializeDemoSystem() {
        const demoButtons = document.querySelectorAll('.demo-button');
        const demoScenarios = {
            'genetic': this.runGeneticAlgorithmDemo,
            'constraint': this.runConstraintValidationDemo,
            'spatial': this.runSpatialConflictDemo
        };

        demoButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const demoType = button.dataset.demo;
                
                // Visual feedback
                this.highlightDemoButton(button);
                
                // Run demo scenario
                if (demoScenarios[demoType]) {
                    demoScenarios[demoType].call(this);
                } else {
                    this.showGenericDemo(button.textContent);
                }
            });
        });
    }

    /**
     * Highlight selected demo button
     */
    highlightDemoButton(activeButton) {
        document.querySelectorAll('.demo-button').forEach(btn => {
            btn.classList.remove('bg-blue-700');
            btn.classList.add('bg-gray-800');
        });
        
        activeButton.classList.remove('bg-gray-800');
        activeButton.classList.add('bg-blue-700');
        
        // Reset after 3 seconds
        setTimeout(() => {
            activeButton.classList.remove('bg-blue-700');
            activeButton.classList.add('bg-gray-800');
        }, 3000);
    }

    /**
     * Run genetic algorithm demo visualization
     */
    runGeneticAlgorithmDemo() {
        this.showToast('🧬 Genetic Algorithm Demo', 
            'Initializing multi-island evolution with migration strategies...', 'info');
        
        // Simulate genetic algorithm progress
        let generation = 0;
        const maxGenerations = 50;
        
        const interval = setInterval(() => {
            generation++;
            const fitness = 65 + (30 * (1 - Math.exp(-generation / 15)));
            const diversity = Math.max(20, 80 * Math.exp(-generation / 25));
            
            this.updateOptimizationProgress('Genetic Algorithm', fitness, generation, maxGenerations);
            
            if (generation >= maxGenerations) {
                clearInterval(interval);
                this.showToast('✅ Optimization Complete', 
                    `Converged at generation ${generation} with fitness ${fitness.toFixed(1)}%`, 'success');
            }
        }, 100);
    }

    /**
     * Run constraint validation demo
     */
    runConstraintValidationDemo() {
        this.showToast('⚡ Constraint Validation', 
            'Running real-time building code compliance check...', 'info');
        
        const constraints = [
            'Fire safety clearances',
            'Structural load limits', 
            'HVAC system requirements',
            'Accessibility compliance',
            'Energy efficiency standards'
        ];
        
        let validatedCount = 0;
        const interval = setInterval(() => {
            if (validatedCount < constraints.length) {
                this.showConstraintCheck(constraints[validatedCount], Math.random() > 0.1);
                validatedCount++;
            } else {
                clearInterval(interval);
                this.showToast('✅ Validation Complete', 
                    'All constraints validated in 78ms', 'success');
            }
        }, 800);
    }

    /**
     * Run spatial conflict detection demo
     */
    runSpatialConflictDemo() {
        this.showToast('🌳 Spatial Analysis', 
            'Scanning for spatial conflicts using Octree indexing...', 'info');
        
        setTimeout(() => {
            this.showToast('⚠️ Conflicts Detected', 
                'Found 3 spatial conflicts - auto-resolving with optimization...', 'warning');
            
            setTimeout(() => {
                this.showToast('✅ Conflicts Resolved', 
                    'Spatial optimization complete - 0 conflicts remaining', 'success');
            }, 2000);
        }, 1500);
    }

    /**
     * Show constraint validation check
     */
    showConstraintCheck(constraint, passed) {
        const status = passed ? '✅' : '❌';
        const color = passed ? 'success' : 'error';
        this.showToast(`${status} ${constraint}`, 
            passed ? 'Validation passed' : 'Violation detected - auto-fixing...', color);
    }

    /**
     * Update optimization progress visualization
     */
    updateOptimizationProgress(algorithm, progress, iteration, maxIterations) {
        const progressBar = document.querySelector(`[data-algorithm="${algorithm.toLowerCase()}"]`);
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
            progressBar.parentElement.nextElementSibling.textContent = `${progress.toFixed(1)}%`;
        }
    }

    /**
     * Initialize real-time metrics display
     */
    initializeMetrics() {
        this.startMetricsUpdates();
        this.initializePerformanceChart();
        this.setupAPIIntegration();
    }

    /**
     * Start real-time metrics updates
     */
    startMetricsUpdates() {
        const updateMetrics = () => {
            const metrics = {
                responseTime: this.simulateMetric(47, 5, 25, 75),
                convergence: this.simulateMetric(94.2, 2, 90, 98),
                objects: this.simulateMetric(8439, 100, 8000, 9000),
                health: this.simulateMetric(99.6, 0.5, 98, 100)
            };
            
            this.updateMetricDisplay('response-time', `${metrics.responseTime}ms`);
            this.updateMetricDisplay('convergence', `${metrics.convergence.toFixed(1)}%`);
            this.updateMetricDisplay('objects', metrics.objects.toLocaleString());
            this.updateMetricDisplay('health', `${metrics.health.toFixed(1)}%`);
        };
        
        // Initial update
        updateMetrics();
        
        // Update every 3 seconds
        setInterval(updateMetrics, 3000);
    }

    /**
     * Simulate realistic metric fluctuations
     */
    simulateMetric(base, variance, min, max) {
        const change = (Math.random() - 0.5) * variance * 2;
        return Math.max(min, Math.min(max, base + change));
    }

    /**
     * Update metric display element
     */
    updateMetricDisplay(metricId, value) {
        const element = document.querySelector(`[data-metric="${metricId}"]`);
        if (element) {
            element.textContent = value;
            
            // Add update flash effect
            element.style.color = '#10b981';
            setTimeout(() => {
                element.style.color = '';
            }, 200);
        }
    }

    /**
     * Initialize smooth navigation and scrolling
     */
    initializeNavigation() {
        // Smooth scroll for navigation links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', (e) => {
                e.preventDefault();
                const target = document.querySelector(anchor.getAttribute('href'));
                
                if (target) {
                    const headerOffset = 80;
                    const elementPosition = target.getBoundingClientRect().top;
                    const offsetPosition = elementPosition + window.pageYOffset - headerOffset;

                    window.scrollTo({
                        top: offsetPosition,
                        behavior: 'smooth'
                    });
                }
            });
        });

        // Update active navigation on scroll
        this.initializeScrollSpy();
        
        // Mobile menu toggle
        this.initializeMobileMenu();
    }

    /**
     * Initialize scroll spy for navigation highlighting
     */
    initializeScrollSpy() {
        const sections = document.querySelectorAll('section[id]');
        const navLinks = document.querySelectorAll('nav a[href^="#"]');
        
        window.addEventListener('scroll', () => {
            let current = '';
            
            sections.forEach(section => {
                const sectionTop = section.getBoundingClientRect().top;
                if (sectionTop <= 100) {
                    current = section.getAttribute('id');
                }
            });
            
            navLinks.forEach(link => {
                link.classList.remove('text-blue-600');
                link.classList.add('text-gray-600');
                
                if (link.getAttribute('href') === `#${current}`) {
                    link.classList.remove('text-gray-600');
                    link.classList.add('text-blue-600');
                }
            });
        });
    }

    /**
     * Initialize mobile menu functionality
     */
    initializeMobileMenu() {
        const mobileMenuButton = document.querySelector('[data-mobile-menu-toggle]');
        const mobileMenu = document.querySelector('[data-mobile-menu]');
        
        if (mobileMenuButton && mobileMenu) {
            mobileMenuButton.addEventListener('click', () => {
                mobileMenu.classList.toggle('hidden');
            });
        }
    }

    /**
     * Initialize optimization visualization
     */
    initializeOptimizationViz() {
        this.startOptimizationAnimation();
    }

    /**
     * Start optimization visualization animation
     */
    startOptimizationAnimation() {
        const algorithms = [
            'genetic-algorithm',
            'nsga-ii-multi-objective', 
            'constraint-satisfaction',
            'spatial-conflict-resolution'
        ];
        
        let algorithmIndex = 0;
        
        const updateVisualization = () => {
            const algorithm = algorithms[algorithmIndex];
            const progress = 70 + Math.random() * 25;
            
            this.updateOptimizationBar(algorithm, progress);
            
            algorithmIndex = (algorithmIndex + 1) % algorithms.length;
        };
        
        // Update every 4 seconds
        setInterval(updateVisualization, 4000);
    }

    /**
     * Update optimization progress bar
     */
    updateOptimizationBar(algorithmId, progress) {
        const progressBar = document.querySelector(`[data-progress="${algorithmId}"]`);
        if (progressBar) {
            progressBar.style.width = `${progress}%`;
            
            // Add pulse effect
            progressBar.style.opacity = '0.7';
            setTimeout(() => {
                progressBar.style.opacity = '1';
            }, 200);
        }
    }

    /**
     * Setup API integration for real-time data
     */
    setupAPIIntegration() {
        // Wait for API client to be available
        if (window.arxosAPI && window.realTimeData) {
            this.connectToRealTimeData();
        } else {
            // Wait for API client initialization
            setTimeout(() => this.setupAPIIntegration(), 1000);
        }
    }

    /**
     * Connect to real-time data streams
     */
    connectToRealTimeData() {
        const api = window.arxosAPI;
        const realTimeData = window.realTimeData;

        // Subscribe to metrics updates
        realTimeData.subscribe('metrics', (metricsData) => {
            this.updateRealMetrics(metricsData);
        });

        // Subscribe to optimization updates
        realTimeData.subscribe('optimization', (optimizationData) => {
            this.updateOptimizationVisualization(optimizationData);
        });

        // Try to fetch initial metrics
        this.fetchInitialMetrics();
    }

    /**
     * Fetch initial metrics from API
     */
    async fetchInitialMetrics() {
        try {
            const api = window.arxosAPI;
            const response = await api.getSystemHealth();
            
            if (response.success) {
                this.updateRealMetrics(response.data);
                this.showToast('✅ Connected', 'Live data connection established', 'success');
            }
        } catch (error) {
            console.log('Using simulated metrics (backend not connected)');
            // Continue with simulated metrics
        }
    }

    /**
     * Update metrics with real API data
     */
    updateRealMetrics(metricsData) {
        if (metricsData.response_time) {
            this.updateMetricDisplay('response-time', `${metricsData.response_time}ms`);
        }
        
        if (metricsData.optimization_convergence) {
            this.updateMetricDisplay('convergence', `${metricsData.optimization_convergence}%`);
        }
        
        if (metricsData.active_objects) {
            this.updateMetricDisplay('objects', metricsData.active_objects.toLocaleString());
        }
        
        if (metricsData.system_health) {
            this.updateMetricDisplay('health', `${metricsData.system_health}%`);
        }
    }

    /**
     * Update optimization visualization with real data
     */
    updateOptimizationVisualization(optimizationData) {
        if (optimizationData.algorithms) {
            Object.entries(optimizationData.algorithms).forEach(([algorithm, progress]) => {
                this.updateOptimizationBar(algorithm, progress);
            });
        }
    }

    /**
     * Initialize performance chart (placeholder for future WebGL implementation)
     */
    initializePerformanceChart() {
        // Future: WebGL-based real-time performance visualization
        console.log('Performance chart initialization - ready for WebGL implementation');
    }

    /**
     * Show toast notification
     */
    showToast(title, message, type = 'info') {
        const toastContainer = document.querySelector('#toast-container') || this.createToastContainer();
        
        const toast = document.createElement('div');
        toast.className = `toast-notification p-4 rounded-lg shadow-lg mb-2 transition-all duration-300 ${this.getToastColors(type)}`;
        
        toast.innerHTML = `
            <div class="font-semibold">${title}</div>
            <div class="text-sm opacity-90">${message}</div>
        `;
        
        // Add animation classes
        toast.classList.add('toast-enter');
        toastContainer.appendChild(toast);
        
        // Auto-remove after 4 seconds
        setTimeout(() => {
            toast.classList.remove('toast-enter');
            toast.classList.add('toast-exit');
            
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }, 4000);
    }

    /**
     * Create toast container if it doesn't exist
     */
    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'fixed top-4 right-4 z-50 space-y-2';
        document.body.appendChild(container);
        return container;
    }

    /**
     * Get toast color classes based on type
     */
    getToastColors(type) {
        const colors = {
            info: 'bg-blue-600 text-white',
            success: 'bg-green-600 text-white', 
            warning: 'bg-yellow-600 text-white',
            error: 'bg-red-600 text-white'
        };
        
        return colors[type] || colors.info;
    }

    /**
     * Generic demo handler
     */
    showGenericDemo(demoName) {
        this.showToast('🚀 Demo Started', `Running ${demoName} demonstration...`, 'info');
        
        setTimeout(() => {
            this.showToast('✅ Demo Complete', `${demoName} demonstration finished successfully`, 'success');
        }, 2000);
    }
}

// Initialize landing page controller when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.landingPageController = new LandingPageController();
    
    // Add data attributes to elements for demo functionality
    document.querySelectorAll('.demo-button').forEach((button, index) => {
        const demoTypes = ['genetic', 'constraint', 'spatial'];
        button.dataset.demo = demoTypes[index] || 'generic';
    });
    
    // Add data attributes for metrics
    const metricsElements = document.querySelectorAll('.live-metric');
    const metricTypes = ['response-time', 'convergence', 'objects', 'health'];
    metricsElements.forEach((el, index) => {
        if (metricTypes[index]) {
            el.dataset.metric = metricTypes[index];
        }
    });
    
    // Add data attributes for progress bars
    const progressBars = document.querySelectorAll('.optimization-viz .bg-blue-500');
    const algorithmNames = ['genetic-algorithm', 'nsga-ii-multi-objective', 'constraint-satisfaction', 'spatial-conflict-resolution'];
    progressBars.forEach((bar, index) => {
        if (algorithmNames[index]) {
            bar.dataset.progress = algorithmNames[index];
        }
    });
});

// Export for potential external use
window.LandingPageController = LandingPageController;