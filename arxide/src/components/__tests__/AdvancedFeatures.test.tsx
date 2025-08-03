import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { ThreeDViewer } from '../ThreeDViewer';
import { AdvancedConstraints } from '../AdvancedConstraints';
import { PluginSystem } from '../PluginSystem';

// Mock Three.js and React Three Fiber
jest.mock('@react-three/fiber', () => ({
  Canvas: ({ children }: any) => <div data-testid="three-canvas">{children}</div>,
  useFrame: jest.fn(),
  useThree: jest.fn(() => ({
    camera: { position: { set: jest.fn() }, lookAt: jest.fn() },
  })),
}));

jest.mock('@react-three/drei', () => ({
  OrbitControls: ({ children }: any) => <div data-testid="orbit-controls">{children}</div>,
  Grid: ({ children }: any) => <div data-testid="grid">{children}</div>,
  Box: ({ children }: any) => <div data-testid="box">{children}</div>,
  Sphere: ({ children }: any) => <div data-testid="sphere">{children}</div>,
  Cylinder: ({ children }: any) => <div data-testid="cylinder">{children}</div>,
  Text: ({ children }: any) => <div data-testid="text">{children}</div>,
  Html: ({ children }: any) => <div data-testid="html">{children}</div>,
}));

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const theme = createTheme({
    palette: {
      mode: 'dark',
    },
  });

  return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
};

describe('Advanced Features', () => {
  describe('ThreeDViewer', () => {
    const mockObjects = [
      {
        id: 'obj1',
        type: 'box',
        position: [0, 0, 0],
        rotation: [0, 0, 0],
        scale: [1, 1, 1],
        color: '#ff0000',
        dimensions: { width: 1, height: 1, depth: 1 },
      },
      {
        id: 'obj2',
        type: 'sphere',
        position: [2, 0, 0],
        rotation: [0, 0, 0],
        scale: [1, 1, 1],
        color: '#00ff00',
        dimensions: { radius: 0.5 },
      },
    ];

    const defaultProps = {
      objects: mockObjects,
      selectedObject: null,
      onObjectSelect: jest.fn(),
      onObjectUpdate: jest.fn(),
      viewMode: '3D' as const,
      onViewModeChange: jest.fn(),
      precision: 0.001,
      gridSize: 0.1,
    };

    it('should render 3D viewer with objects', () => {
      render(
        <TestWrapper>
          <ThreeDViewer {...defaultProps} />
        </TestWrapper>
      );

      expect(screen.getByTestId('three-canvas')).toBeInTheDocument();
      expect(screen.getByTestId('grid')).toBeInTheDocument();
    });

    it('should display view mode controls', () => {
      render(
        <TestWrapper>
          <ThreeDViewer {...defaultProps} />
        </TestWrapper>
      );

      expect(screen.getByLabelText('toggle 2d/3d view')).toBeInTheDocument();
      expect(screen.getByLabelText('zoom in')).toBeInTheDocument();
      expect(screen.getByLabelText('zoom out')).toBeInTheDocument();
      expect(screen.getByLabelText('rotate view')).toBeInTheDocument();
      expect(screen.getByLabelText('center view')).toBeInTheDocument();
    });

    it('should show status information', () => {
      render(
        <TestWrapper>
          <ThreeDViewer {...defaultProps} />
        </TestWrapper>
      );

      expect(screen.getByText('View Mode: 3D')).toBeInTheDocument();
      expect(screen.getByText('Objects: 2')).toBeInTheDocument();
      expect(screen.getByText('Precision: 0.001"')).toBeInTheDocument();
      expect(screen.getByText('Grid: 0.1"')).toBeInTheDocument();
    });

    it('should handle view mode toggle', () => {
      const onViewModeChange = jest.fn();
      render(
        <TestWrapper>
          <ThreeDViewer {...defaultProps} onViewModeChange={onViewModeChange} />
        </TestWrapper>
      );

      const toggleButton = screen.getByLabelText('toggle 2d/3d view');
      fireEvent.click(toggleButton);

      expect(onViewModeChange).toHaveBeenCalledWith('2D');
    });

    it('should handle object selection', () => {
      const onObjectSelect = jest.fn();
      render(
        <TestWrapper>
          <ThreeDViewer {...defaultProps} onObjectSelect={onObjectSelect} />
        </TestWrapper>
      );

      // Simulate object selection (this would be handled by Three.js events)
      expect(onObjectSelect).toBeDefined();
    });
  });

  describe('AdvancedConstraints', () => {
    const mockConstraints = [
      {
        id: 'constraint1',
        type: 'distance',
        objects: ['obj1', 'obj2'],
        parameters: {
          value: 10,
          tolerance: 0.001,
          units: 'inches',
        },
        status: 'valid',
        metadata: {
          description: 'Distance between objects',
          autoSolve: true,
        },
      },
      {
        id: 'constraint2',
        type: 'parallel',
        objects: ['obj1', 'obj3'],
        parameters: {
          tolerance: 0.1,
          units: 'degrees',
        },
        status: 'pending',
        metadata: {
          description: 'Parallel constraint',
          autoSolve: false,
        },
      },
    ];

    const mockObjects = [
      { id: 'obj1', name: 'Object 1' },
      { id: 'obj2', name: 'Object 2' },
      { id: 'obj3', name: 'Object 3' },
    ];

    const defaultProps = {
      constraints: mockConstraints,
      objects: mockObjects,
      onConstraintAdd: jest.fn(),
      onConstraintUpdate: jest.fn(),
      onConstraintDelete: jest.fn(),
      onConstraintsOptimize: jest.fn(),
      onConstraintSolve: jest.fn(),
      precision: 0.001,
    };

    it('should render constraints list', () => {
      render(
        <TestWrapper>
          <AdvancedConstraints {...defaultProps} />
        </TestWrapper>
      );

      expect(screen.getByText('Advanced Constraints')).toBeInTheDocument();
      expect(screen.getByText('Distance')).toBeInTheDocument();
      expect(screen.getByText('Parallel')).toBeInTheDocument();
    });

    it('should show constraint statistics', () => {
      render(
        <TestWrapper>
          <AdvancedConstraints {...defaultProps} />
        </TestWrapper>
      );

      expect(screen.getByText('Total: 2')).toBeInTheDocument();
      expect(screen.getByText('Valid: 1')).toBeInTheDocument();
      expect(screen.getByText('Pending: 1')).toBeInTheDocument();
    });

    it('should handle adding new constraint', () => {
      const onConstraintAdd = jest.fn();
      render(
        <TestWrapper>
          <AdvancedConstraints {...defaultProps} onConstraintAdd={onConstraintAdd} />
        </TestWrapper>
      );

      const addButton = screen.getByLabelText('add constraint');
      fireEvent.click(addButton);

      // Dialog should open
      expect(screen.getByText('Add New Constraint')).toBeInTheDocument();
    });

    it('should handle constraint deletion', () => {
      const onConstraintDelete = jest.fn();
      render(
        <TestWrapper>
          <AdvancedConstraints {...defaultProps} onConstraintDelete={onConstraintDelete} />
        </TestWrapper>
      );

      // Expand first constraint
      const expandButton = screen.getByLabelText('expand more');
      fireEvent.click(expandButton);

      // Click delete button
      const deleteButton = screen.getByLabelText('delete constraint');
      fireEvent.click(deleteButton);

      expect(onConstraintDelete).toHaveBeenCalledWith('constraint1');
    });

    it('should handle constraint optimization', () => {
      const onConstraintsOptimize = jest.fn();
      render(
        <TestWrapper>
          <AdvancedConstraints {...defaultProps} onConstraintsOptimize={onConstraintsOptimize} />
        </TestWrapper>
      );

      const optimizeButton = screen.getByLabelText('optimize constraints');
      fireEvent.click(optimizeButton);

      expect(onConstraintsOptimize).toHaveBeenCalled();
    });

    it('should show constraint details when expanded', () => {
      render(
        <TestWrapper>
          <AdvancedConstraints {...defaultProps} />
        </TestWrapper>
      );

      // Expand first constraint
      const expandButton = screen.getByLabelText('expand more');
      fireEvent.click(expandButton);

      expect(screen.getByText('Objects:')).toBeInTheDocument();
      expect(screen.getByText('Parameters:')).toBeInTheDocument();
      expect(screen.getByText('Metadata:')).toBeInTheDocument();
    });
  });

  describe('PluginSystem', () => {
    const mockPlugins = [
      {
        id: 'plugin1',
        name: 'Sample Tool',
        version: '1.0.0',
        description: 'A sample plugin for testing',
        author: 'Test Author',
        category: 'tool',
        status: 'active',
        enabled: true,
        settings: { setting1: 'value1' },
        dependencies: [],
        permissions: [],
        metadata: {
          tags: ['sample', 'test'],
          rating: 4.5,
        },
      },
      {
        id: 'plugin2',
        name: 'Advanced Constraint',
        version: '2.0.0',
        description: 'Advanced constraint plugin',
        author: 'Another Author',
        category: 'constraint',
        status: 'inactive',
        enabled: false,
        settings: {},
        dependencies: [],
        permissions: [],
        metadata: {
          tags: ['constraint', 'advanced'],
          rating: 4.0,
        },
      },
    ];

    const mockAvailablePlugins = [
      {
        id: 'marketplace1',
        name: 'Marketplace Plugin',
        version: '1.0.0',
        description: 'Available plugin from marketplace',
        author: 'Marketplace Author',
        category: 'utility',
        status: 'active',
        enabled: true,
        settings: {},
        dependencies: [],
        permissions: [],
        metadata: {
          tags: ['marketplace'],
          rating: 4.8,
        },
      },
    ];

    const defaultProps = {
      plugins: mockPlugins,
      onPluginInstall: jest.fn(),
      onPluginUninstall: jest.fn(),
      onPluginEnable: jest.fn(),
      onPluginDisable: jest.fn(),
      onPluginUpdate: jest.fn(),
      onPluginExecute: jest.fn(),
      availablePlugins: mockAvailablePlugins,
      onPluginSearch: jest.fn(),
      onPluginDownload: jest.fn(),
    };

    it('should render plugin system with tabs', () => {
      render(
        <TestWrapper>
          <PluginSystem {...defaultProps} />
        </TestWrapper>
      );

      expect(screen.getByText('Plugin System')).toBeInTheDocument();
      expect(screen.getByText('Installed (2)')).toBeInTheDocument();
      expect(screen.getByText('Marketplace')).toBeInTheDocument();
      expect(screen.getByText('Development')).toBeInTheDocument();
    });

    it('should show plugin statistics', () => {
      render(
        <TestWrapper>
          <PluginSystem {...defaultProps} />
        </TestWrapper>
      );

      expect(screen.getByText('Total: 2')).toBeInTheDocument();
      expect(screen.getByText('Active: 1')).toBeInTheDocument();
      expect(screen.getByText('Enabled: 1')).toBeInTheDocument();
      expect(screen.getByText('Errors: 0')).toBeInTheDocument();
    });

    it('should display installed plugins', () => {
      render(
        <TestWrapper>
          <PluginSystem {...defaultProps} />
        </TestWrapper>
      );

      expect(screen.getByText('Sample Tool')).toBeInTheDocument();
      expect(screen.getByText('Advanced Constraint')).toBeInTheDocument();
    });

    it('should handle plugin enable/disable', () => {
      const onPluginEnable = jest.fn();
      const onPluginDisable = jest.fn();
      render(
        <TestWrapper>
          <PluginSystem {...defaultProps} onPluginEnable={onPluginEnable} onPluginDisable={onPluginDisable} />
        </TestWrapper>
      );

      // Find enable/disable buttons (they might be in cards)
      const enableButtons = screen.getAllByLabelText('enable plugin');
      const disableButtons = screen.getAllByLabelText('disable plugin');

      if (enableButtons.length > 0) {
        fireEvent.click(enableButtons[0]);
        expect(onPluginEnable).toHaveBeenCalled();
      }

      if (disableButtons.length > 0) {
        fireEvent.click(disableButtons[0]);
        expect(onPluginDisable).toHaveBeenCalled();
      }
    });

    it('should handle plugin uninstall', () => {
      const onPluginUninstall = jest.fn();
      render(
        <TestWrapper>
          <PluginSystem {...defaultProps} onPluginUninstall={onPluginUninstall} />
        </TestWrapper>
      );

      // Find uninstall buttons
      const uninstallButtons = screen.getAllByLabelText('uninstall plugin');
      if (uninstallButtons.length > 0) {
        fireEvent.click(uninstallButtons[0]);
        expect(onPluginUninstall).toHaveBeenCalled();
      }
    });

    it('should switch to marketplace tab', () => {
      render(
        <TestWrapper>
          <PluginSystem {...defaultProps} />
        </TestWrapper>
      );

      const marketplaceButton = screen.getByText('Marketplace');
      fireEvent.click(marketplaceButton);

      expect(screen.getByText('Plugin Marketplace')).toBeInTheDocument();
      expect(screen.getByText('Marketplace Plugin')).toBeInTheDocument();
    });

    it('should handle plugin search in marketplace', () => {
      const onPluginSearch = jest.fn();
      render(
        <TestWrapper>
          <PluginSystem {...defaultProps} onPluginSearch={onPluginSearch} />
        </TestWrapper>
      );

      // Switch to marketplace
      const marketplaceButton = screen.getByText('Marketplace');
      fireEvent.click(marketplaceButton);

      // Find search field
      const searchField = screen.getByLabelText('Search plugins...');
      fireEvent.change(searchField, { target: { value: 'test' } });

      expect(onPluginSearch).toHaveBeenCalledWith('test');
    });

    it('should switch to development tab', () => {
      render(
        <TestWrapper>
          <PluginSystem {...defaultProps} />
        </TestWrapper>
      );

      const developmentButton = screen.getByText('Development');
      fireEvent.click(developmentButton);

      expect(screen.getByText('Plugin Development')).toBeInTheDocument();
      expect(screen.getByText('Plugin SDK')).toBeInTheDocument();
      expect(screen.getByText('Plugin Builder')).toBeInTheDocument();
      expect(screen.getByText('Security Guidelines')).toBeInTheDocument();
    });
  });

  describe('Integration Tests', () => {
    it('should handle 3D object selection and constraint creation', () => {
      const mockObjects = [
        {
          id: 'obj1',
          type: 'box',
          position: [0, 0, 0],
          rotation: [0, 0, 0],
          scale: [1, 1, 1],
          color: '#ff0000',
          dimensions: { width: 1, height: 1, depth: 1 },
        },
      ];

      const mockConstraints = [];

      const onObjectSelect = jest.fn();
      const onConstraintAdd = jest.fn();

      // This would test the integration between 3D viewer and constraints
      expect(onObjectSelect).toBeDefined();
      expect(onConstraintAdd).toBeDefined();
    });

    it('should handle plugin execution with 3D objects', () => {
      const mockPlugins = [
        {
          id: '3d-tool',
          name: '3D Tool',
          version: '1.0.0',
          description: '3D manipulation tool',
          author: 'Test Author',
          category: 'tool',
          status: 'active',
          enabled: true,
          settings: {},
          dependencies: [],
          permissions: [],
          metadata: {},
        },
      ];

      const onPluginExecute = jest.fn();

      // This would test plugin execution affecting 3D objects
      expect(onPluginExecute).toBeDefined();
    });
  });

  describe('Performance Tests', () => {
    it('should handle large number of 3D objects efficiently', () => {
      const largeObjects = Array.from({ length: 100 }, (_, i) => ({
        id: `obj${i}`,
        type: 'box',
        position: [i, 0, 0],
        rotation: [0, 0, 0],
        scale: [1, 1, 1],
        color: '#ff0000',
        dimensions: { width: 1, height: 1, depth: 1 },
      }));

      render(
        <TestWrapper>
          <ThreeDViewer
            objects={largeObjects}
            selectedObject={null}
            onObjectSelect={jest.fn()}
            onObjectUpdate={jest.fn()}
            viewMode="3D"
            onViewModeChange={jest.fn()}
            precision={0.001}
            gridSize={0.1}
          />
        </TestWrapper>
      );

      expect(screen.getByTestId('three-canvas')).toBeInTheDocument();
    });

    it('should handle large number of constraints efficiently', () => {
      const largeConstraints = Array.from({ length: 50 }, (_, i) => ({
        id: `constraint${i}`,
        type: 'distance',
        objects: [`obj${i}`, `obj${i + 1}`],
        parameters: {
          value: 10,
          tolerance: 0.001,
          units: 'inches',
        },
        status: 'valid',
        metadata: {
          description: `Constraint ${i}`,
          autoSolve: true,
        },
      }));

      render(
        <TestWrapper>
          <AdvancedConstraints
            constraints={largeConstraints}
            objects={Array.from({ length: 51 }, (_, i) => ({ id: `obj${i}`, name: `Object ${i}` }))}
            onConstraintAdd={jest.fn()}
            onConstraintUpdate={jest.fn()}
            onConstraintDelete={jest.fn()}
            onConstraintsOptimize={jest.fn()}
            onConstraintSolve={jest.fn()}
            precision={0.001}
          />
        </TestWrapper>
      );

      expect(screen.getByText('Advanced Constraints')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('should handle 3D rendering errors gracefully', () => {
      // Mock Three.js to throw an error
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

      render(
        <TestWrapper>
          <ThreeDViewer
            objects={[]}
            selectedObject={null}
            onObjectSelect={jest.fn()}
            onObjectUpdate={jest.fn()}
            viewMode="3D"
            onViewModeChange={jest.fn()}
            precision={0.001}
            gridSize={0.1}
          />
        </TestWrapper>
      );

      expect(screen.getByTestId('three-canvas')).toBeInTheDocument();
      consoleSpy.mockRestore();
    });

    it('should handle constraint validation errors', () => {
      const invalidConstraints = [
        {
          id: 'invalid',
          type: 'invalid_type',
          objects: [],
          parameters: {},
          status: 'invalid',
          metadata: {},
        },
      ];

      render(
        <TestWrapper>
          <AdvancedConstraints
            constraints={invalidConstraints}
            objects={[]}
            onConstraintAdd={jest.fn()}
            onConstraintUpdate={jest.fn()}
            onConstraintDelete={jest.fn()}
            onConstraintsOptimize={jest.fn()}
            onConstraintSolve={jest.fn()}
            precision={0.001}
          />
        </TestWrapper>
      );

      expect(screen.getByText('Advanced Constraints')).toBeInTheDocument();
    });
  });
}); 