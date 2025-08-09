// Multi-Selection Module

class MultiSelection {
    constructor() {
        this.selectedObjects = new Set();
        this.isMarqueeSelecting = false;
        this.marqueeStart = { x: 0, y: 0 };
        this.marqueeElement = null;
        this.svgContainer = null;
        this.svgElement = null;
        this.init();
    }

    init() {
        this.svgContainer = document.getElementById('svg-container');
        this.svgElement = this.svgContainer ? this.svgContainer.querySelector('svg') : null;
        if (!this.svgContainer || !this.svgElement) return;
        this.createMarqueeElement();
        this.setupEventListeners();
    }

    createMarqueeElement() {
        this.marqueeElement = document.createElement('div');
        this.marqueeElement.className = 'marquee-selection absolute border-2 border-blue-500 bg-blue-100 bg-opacity-20 pointer-events-none z-40 hidden';
        this.svgContainer.appendChild(this.marqueeElement);
    }

    setupEventListeners() {
        // Mouse events for marquee selection
        this.svgContainer.addEventListener('mousedown', this.handleMouseDown.bind(this));
        this.svgContainer.addEventListener('mousemove', this.handleMouseMove.bind(this));
        this.svgContainer.addEventListener('mouseup', this.handleMouseUp.bind(this));

        // Prevent default drag behavior during marquee
        this.svgContainer.addEventListener('dragstart', (e) => {
            if (this.isMarqueeSelecting) e.preventDefault();
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', this.handleKeyDown.bind(this));
    }

    handleMouseDown(event) {
        const target = event.target.closest('.placed-symbol');

        // Start marquee selection if clicking on empty space
        if (!target && event.button === 0) {
            this.startMarqueeSelection(event);
            return;
        }

        // Handle object selection
        if (target) {
            if (event.shiftKey) {
                this.toggleObjectSelection(target);
            } else {
                this.selectObject(target);
            }
        }
    }

    handleMouseMove(event) {
        if (!this.isMarqueeSelecting) return;
        const currentPos = this.getMousePosition(event);
        this.updateMarqueeElement(currentPos);
        this.updateMarqueeSelection(currentPos);
    }

    handleMouseUp(event) {
        if (this.isMarqueeSelecting) {
            this.endMarqueeSelection();
        }
    }

    handleKeyDown(event) {
        switch (event.key) {
            case 'a':
                if (event.ctrlKey || event.metaKey) {
                    event.preventDefault();
                    this.selectAllObjects();
                }
                break;
            case 'd':
                if (event.ctrlKey || event.metaKey) {
                    event.preventDefault();
                    this.clearSelection();
                }
                break;
            case 'Escape':
                this.clearSelection();
                break;
        }
    }

    startMarqueeSelection(event) {
        this.isMarqueeSelecting = true;
        this.marqueeStart = this.getMousePosition(event);

        this.marqueeElement.style.left = this.marqueeStart.x + 'px';
        this.marqueeElement.style.top = this.marqueeStart.y + 'px';
        this.marqueeElement.style.width = '0px';
        this.marqueeElement.style.height = '0px';
        this.marqueeElement.classList.remove('hidden');

        // Clear current selection if not holding shift
        if (!event.shiftKey) {
            this.clearSelection();
        }
    }

    updateMarqueeElement(currentPos) {
        const left = Math.min(this.marqueeStart.x, currentPos.x);
        const top = Math.min(this.marqueeStart.y, currentPos.y);
        const width = Math.abs(currentPos.x - this.marqueeStart.x);
        const height = Math.abs(currentPos.y - this.marqueeStart.y);

        this.marqueeElement.style.left = left + 'px';
        this.marqueeElement.style.top = top + 'px';
        this.marqueeElement.style.width = width + 'px';
        this.marqueeElement.style.height = height + 'px';
    }

    updateMarqueeSelection(currentPos) {
        const marqueeRect = {
            left: Math.min(this.marqueeStart.x, currentPos.x),
            top: Math.min(this.marqueeStart.y, currentPos.y),
            right: Math.max(this.marqueeStart.x, currentPos.x),
            bottom: Math.max(this.marqueeStart.y, currentPos.y)
        };

        const objects = this.svgElement.querySelectorAll('.placed-symbol');
        objects.forEach(obj => {
            const objRect = obj.getBoundingClientRect();
            const containerRect = this.svgContainer.getBoundingClientRect();

            const objLeft = objRect.left - containerRect.left;
            const objTop = objRect.top - containerRect.top;
            const objRight = objLeft + objRect.width;
            const objBottom = objTop + objRect.height;

            if (this.rectsIntersect(marqueeRect, {
                left: objLeft,
                top: objTop,
                right: objRight,
                bottom: objBottom
            })) {
                this.selectedObjects.add(obj);
                obj.classList.add('selected');
            }
        });
    }

    endMarqueeSelection() {
        this.isMarqueeSelecting = false;
        this.marqueeElement.classList.add('hidden');
        this.updateContextPanel();
    }

    getMousePosition(event) {
        const rect = this.svgContainer.getBoundingClientRect();
        return {
            x: event.clientX - rect.left,
            y: event.clientY - rect.top
        };
    }

    rectsIntersect(rect1, rect2) {
        return !(rect1.left > rect2.right ||
                rect1.right < rect2.left ||
                rect1.top > rect2.bottom ||
                rect1.bottom < rect2.top);
    }

    selectObject(obj) {
        this.clearSelection();
        this.selectedObjects.add(obj);
        obj.classList.add('selected');
        this.updateContextPanel();
    }

    toggleObjectSelection(obj) {
        if (this.selectedObjects.has(obj)) {
            this.selectedObjects.delete(obj);
            obj.classList.remove('selected');
        } else {
            this.selectedObjects.add(obj);
            obj.classList.add('selected');
        }
        this.updateContextPanel();
    }

    selectAllObjects() {
        const objects = this.svgElement.querySelectorAll('.placed-symbol');
        objects.forEach(obj => {
            this.selectedObjects.add(obj);
            obj.classList.add('selected');
        });
        this.updateContextPanel();
    }

    clearSelection() {
        this.selectedObjects.forEach(obj => obj.classList.remove('selected'));
        this.selectedObjects.clear();
        this.updateContextPanel();
    }

    getSelectedObjects() {
        return Array.from(this.selectedObjects);
    }

    getSelectedObjectIds() {
        return Array.from(this.selectedObjects).map(obj => obj.getAttribute('data-id'));
    }

    // Batch operations
    moveSelectedObjects(deltaX, deltaY) {
        this.selectedObjects.forEach(obj => {
            const currentX = parseFloat(obj.getAttribute('data-x') || 0);
            const currentY = parseFloat(obj.getAttribute('data-y') || 0);
            const newX = currentX + deltaX;
            const newY = currentY + deltaY;

            obj.setAttribute('data-x', newX);
            obj.setAttribute('data-y', newY);

            const rotation = obj.getAttribute('data-rotation') || 0;
            obj.setAttribute('transform', `translate(${newX},${newY}) rotate(${rotation})`);
        });
    }

    rotateSelectedObjects(angle) {
        this.selectedObjects.forEach(obj => {
            const currentRotation = parseFloat(obj.getAttribute('data-rotation') || 0);
            const newRotation = currentRotation + angle;

            obj.setAttribute('data-rotation', newRotation);

            const x = obj.getAttribute('data-x') || 0;
            const y = obj.getAttribute('data-y') || 0;
            obj.setAttribute('transform', `translate(${x},${y}) rotate(${newRotation})`);
        });
    }

    deleteSelectedObjects() {
        if (this.selectedObjects.size === 0) return;
        if (confirm(`Delete ${this.selectedObjects.size} selected object(s)?`)) {
            this.selectedObjects.forEach(obj => {
                obj.remove();
            });
            this.selectedObjects.clear();
            this.updateContextPanel();
        }
    }

    // Group operations
    groupSelectedObjects() {
        if (this.selectedObjects.size < 2) return;

        const groupId = 'group_' + Date.now();
        const objects = Array.from(this.selectedObjects);

        // Create group element
        const groupElement = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        groupElement.setAttribute('data-group-id', groupId);
        groupElement.classList.add('object-group', 'selected');

        // Move objects to group
        objects.forEach(obj => {
            obj.setAttribute('data-group-id', groupId);
            groupElement.appendChild(obj);
        });

        this.svgElement.appendChild(groupElement);

        // Update selection
        this.clearSelection();
        this.selectedObjects.add(groupElement);
        this.updateContextPanel();
    }

    ungroupSelectedObjects() {
        const groups = Array.from(this.selectedObjects).filter(obj =>
            obj.classList.contains('object-group')
        );

        groups.forEach(group => {
            const groupId = group.getAttribute('data-group-id');
            const objects = group.querySelectorAll('.placed-symbol');

            objects.forEach(obj => {
                obj.removeAttribute('data-group-id');
                this.svgElement.appendChild(obj);
            });

            group.remove();
        });

        this.clearSelection();
    }

    // Selection by criteria
    selectByType(type) {
        const objects = this.svgElement.querySelectorAll(`.placed-symbol[data-type="${type}"]`);
        this.clearSelection();
        objects.forEach(obj => {
            this.selectedObjects.add(obj);
            obj.classList.add('selected');
        });
        this.updateContextPanel();
    }

    selectBySystem(system) {
        const objects = this.svgElement.querySelectorAll(`.placed-symbol[data-system="${system}"]`);
        this.clearSelection();
        objects.forEach(obj => {
            this.selectedObjects.add(obj);
            obj.classList.add('selected');
        });
        this.updateContextPanel();
    }

    selectByStatus(status) {
        const objects = this.svgElement.querySelectorAll(`.placed-symbol[data-status="${status}"]`);
        this.clearSelection();
        objects.forEach(obj => {
            this.selectedObjects.add(obj);
            obj.classList.add('selected');
        });
        this.updateContextPanel();
    }

    // Invert selection
    invertSelection() {
        const allObjects = this.svgElement.querySelectorAll('.placed-symbol');
        allObjects.forEach(obj => {
            if (this.selectedObjects.has(obj)) {
                this.selectedObjects.delete(obj);
                obj.classList.remove('selected');
            } else {
                this.selectedObjects.add(obj);
                obj.classList.add('selected');
            }
        });
        this.updateContextPanel();
    }

    updateContextPanel() {
        if (window.contextPanel) {
            window.contextPanel.updateSelection(this.selectedObjects);
        }

        if (window.svgObjectInteraction) {
            window.svgObjectInteraction.selectedObjects = this.selectedObjects;
        }
    }

    // Export selection data
    exportSelection() {
        const selectionData = Array.from(this.selectedObjects).map(obj => ({
            id: obj.getAttribute('data-id'),
            name: obj.getAttribute('data-name'),
            type: obj.getAttribute('data-type'),
            system: obj.getAttribute('data-system'),
            x: parseFloat(obj.getAttribute('data-x') || 0),
            y: parseFloat(obj.getAttribute('data-y') || 0),
            rotation: parseFloat(obj.getAttribute('data-rotation') || 0),
            status: obj.getAttribute('data-status')
        }));
        return selectionData;
    }

    // Import selection data
    importSelection(selectionData) {
        this.clearSelection();
        selectionData.forEach(data => {
            const obj = this.svgElement.querySelector(`[data-id="${data.id}"]`);
            if (obj) {
                this.selectedObjects.add(obj);
                obj.classList.add('selected');
            }
        });
        this.updateContextPanel();
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.multiSelection = new MultiSelection();
});
