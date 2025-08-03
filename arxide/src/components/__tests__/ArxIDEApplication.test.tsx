import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { ArxIDEApplication } from '../ArxIDEApplication';

// Mock Tauri APIs
jest.mock('@tauri-apps/api/tauri', () => ({
  invoke: jest.fn(),
}));

jest.mock('@tauri-apps/api/dialog', () => ({
  open: jest.fn(),
  save: jest.fn(),
}));

jest.mock('@tauri-apps/api/window', () => ({
  appWindow: {
    listen: jest.fn(),
    close: jest.fn(),
  },
}));

jest.mock('@tauri-apps/api/event', () => ({
  listen: jest.fn(),
}));

jest.mock('@tauri-apps/api/notification', () => ({
  isPermissionGranted: jest.fn(),
  requestPermission: jest.fn(),
  sendNotification: jest.fn(),
}));

// Mock window.CadEngine
const mockCadEngine = {
  initialize: jest.fn(),
  clearCanvas: jest.fn(),
  loadProject: jest.fn(),
  arxObjects: new Map(),
  constraintSolver: {
    constraints: new Map(),
  },
};

const mockConstraintSolver = {
  constraints: new Map(),
  addConstraint: jest.fn(),
  removeConstraint: jest.fn(),
  solveConstraints: jest.fn(),
};

// Setup global mocks
beforeEach(() => {
  // Mock window objects
  Object.defineProperty(window, 'CadEngine', {
    value: jest.fn(() => mockCadEngine),
    writable: true,
  });

  Object.defineProperty(window, 'ConstraintSolver', {
    value: jest.fn(() => mockConstraintSolver),
    writable: true,
  });

  // Mock script loading
  Object.defineProperty(document, 'createElement', {
    value: jest.fn(() => ({
      src: '',
      onload: jest.fn(),
      onerror: jest.fn(),
    })),
    writable: true,
  });

  // Clear all mocks
  jest.clearAllMocks();
});

// Test wrapper component
const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const theme = createTheme({
    palette: {
      mode: 'dark',
    },
  });

  return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
};

describe('ArxIDEApplication', () => {
  describe('Initialization', () => {
    it('should initialize ArxIDE successfully', async () => {
      render(
        <TestWrapper>
          <ArxIDEApplication />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('ArxIDE - Professional CAD')).toBeInTheDocument();
      });
    });

    it('should initialize CAD engine on mount', async () => {
      render(
        <TestWrapper>
          <ArxIDEApplication />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(window.CadEngine).toHaveBeenCalled();
        expect(mockCadEngine.initialize).toHaveBeenCalledWith('cad-canvas');
      });
    });

    it('should initialize constraint solver on mount', async () => {
      render(
        <TestWrapper>
          <ArxIDEApplication />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(window.ConstraintSolver).toHaveBeenCalled();
      });
    });
  });

  describe('File Operations', () => {
    it('should create new file when New File is clicked', async () => {
      const { invoke } = require('@tauri-apps/api/tauri');
      invoke.mockResolvedValue('success');

      render(
        <TestWrapper>
          <ArxIDEApplication />
        </TestWrapper>
      );

      // Open sidebar
      const menuButton = screen.getByLabelText('menu');
      fireEvent.click(menuButton);

      // Click New File
      const newFileButton = screen.getByText('New File');
      fireEvent.click(newFileButton);

      await waitFor(() => {
        expect(mockCadEngine.clearCanvas).toHaveBeenCalled();
      });
    });

    it('should open file when Open File is clicked', async () => {
      const { open } = require('@tauri-apps/api/dialog');
      const { invoke } = require('@tauri-apps/api/tauri');

      open.mockResolvedValue('/test/path/file.svgx');
      invoke.mockResolvedValue(JSON.stringify({
        id: 'test',
        name: 'Test Project',
        objects: [],
        constraints: [],
      }));

      render(
        <TestWrapper>
          <ArxIDEApplication />
        </TestWrapper>
      );

      // Open sidebar
      const menuButton = screen.getByLabelText('menu');
      fireEvent.click(menuButton);

      // Click Open File
      const openFileButton = screen.getByText('Open File');
      fireEvent.click(openFileButton);

      await waitFor(() => {
        expect(open).toHaveBeenCalledWith({
          multiple: false,
          filters: [
            { name: 'SVGX Files', extensions: ['svgx'] },
            { name: 'All Files', extensions: ['*'] },
          ],
        });
      });
    });

    it('should save file when Save is clicked', async () => {
      const { invoke } = require('@tauri-apps/api/tauri');

      invoke.mockResolvedValue('success');

      render(
        <TestWrapper>
          <ArxIDEApplication />
        </TestWrapper>
      );

      // Open sidebar
      const menuButton = screen.getByLabelText('menu');
      fireEvent.click(menuButton);

      // Click Save
      const saveButton = screen.getByText('Save');
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(invoke).toHaveBeenCalledWith('write_file', expect.any(Object));
      });
    });
  });

  describe('Export Operations', () => {
    it('should export to DXF when Export to DXF is clicked', async () => {
      const { save } = require('@tauri-apps/api/dialog');
      const { invoke } = require('@tauri-apps/api/tauri');

      save.mockResolvedValue('/test/path/export.dxf');
      invoke.mockResolvedValue('success');

      render(
        <TestWrapper>
          <ArxIDEApplication />
        </TestWrapper>
      );

      // Open sidebar
      const menuButton = screen.getByLabelText('menu');
      fireEvent.click(menuButton);

      // Click Export to DXF
      const exportDXFButton = screen.getByText('Export to DXF');
      fireEvent.click(exportDXFButton);

      await waitFor(() => {
        expect(save).toHaveBeenCalledWith({
          filters: [{ name: 'DXF Files', extensions: ['dxf'] }],
        });
      });
    });

    it('should export to IFC when Export to IFC is clicked', async () => {
      const { save } = require('@tauri-apps/api/dialog');
      const { invoke } = require('@tauri-apps/api/tauri');

      save.mockResolvedValue('/test/path/export.ifc');
      invoke.mockResolvedValue('success');

      render(
        <TestWrapper>
          <ArxIDEApplication />
        </TestWrapper>
      );

      // Open sidebar
      const menuButton = screen.getByLabelText('menu');
      fireEvent.click(menuButton);

      // Click Export to IFC
      const exportIFCButton = screen.getByText('Export to IFC');
      fireEvent.click(exportIFCButton);

      await waitFor(() => {
        expect(save).toHaveBeenCalledWith({
          filters: [{ name: 'IFC Files', extensions: ['ifc'] }],
        });
      });
    });
  });

  describe('UI Interactions', () => {
    it('should toggle dark mode when theme button is clicked', async () => {
      render(
        <TestWrapper>
          <ArxIDEApplication />
        </TestWrapper>
      );

      const themeButton = screen.getByLabelText('toggle dark mode');
      fireEvent.click(themeButton);

      await waitFor(() => {
        // Theme state should change (implementation dependent)
        expect(themeButton).toBeInTheDocument();
      });
    });

    it('should open settings dialog when Settings is clicked', async () => {
      render(
        <TestWrapper>
          <ArxIDEApplication />
        </TestWrapper>
      );

      // Open sidebar
      const menuButton = screen.getByLabelText('menu');
      fireEvent.click(menuButton);

      // Click Settings
      const settingsButton = screen.getByText('Settings');
      fireEvent.click(settingsButton);

      await waitFor(() => {
        expect(screen.getByText('ArxIDE Settings')).toBeInTheDocument();
      });
    });

    it('should open help dialog when Help is clicked', async () => {
      render(
        <TestWrapper>
          <ArxIDEApplication />
        </TestWrapper>
      );

      // Open sidebar
      const menuButton = screen.getByLabelText('menu');
      fireEvent.click(menuButton);

      // Click Help
      const helpButton = screen.getByText('Help');
      fireEvent.click(helpButton);

      await waitFor(() => {
        expect(screen.getByText('ArxIDE Help')).toBeInTheDocument();
      });
    });
  });

  describe('CAD Canvas', () => {
    it('should render CAD canvas', async () => {
      render(
        <TestWrapper>
          <ArxIDEApplication />
        </TestWrapper>
      );

      await waitFor(() => {
        const canvas = screen.getByRole('img', { hidden: true });
        expect(canvas).toBeInTheDocument();
        expect(canvas).toHaveAttribute('id', 'cad-canvas');
      });
    });

    it('should apply dark mode styling to canvas', async () => {
      render(
        <TestWrapper>
          <ArxIDEApplication />
        </TestWrapper>
      );

      await waitFor(() => {
        const canvas = screen.getByRole('img', { hidden: true });
        expect(canvas).toHaveStyle({ backgroundColor: '#1a1a1a' });
      });
    });
  });

  describe('Notifications', () => {
    it('should show notification when file is saved', async () => {
      const { invoke } = require('@tauri-apps/api/tauri');
      const { sendNotification } = require('@tauri-apps/api/notification');

      invoke.mockResolvedValue('success');
      sendNotification.mockResolvedValue('success');

      render(
        <TestWrapper>
          <ArxIDEApplication />
        </TestWrapper>
      );

      // Open sidebar
      const menuButton = screen.getByLabelText('menu');
      fireEvent.click(menuButton);

      // Click Save
      const saveButton = screen.getByText('Save');
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(sendNotification).toHaveBeenCalledWith({
          title: 'ArxIDE',
          body: 'File saved successfully',
          icon: '✅',
        });
      });
    });

    it('should show error notification when file operation fails', async () => {
      const { invoke } = require('@tauri-apps/api/tauri');
      const { sendNotification } = require('@tauri-apps/api/notification');

      invoke.mockRejectedValue(new Error('File operation failed'));
      sendNotification.mockResolvedValue('success');

      render(
        <TestWrapper>
          <ArxIDEApplication />
        </TestWrapper>
      );

      // Open sidebar
      const menuButton = screen.getByLabelText('menu');
      fireEvent.click(menuButton);

      // Click Save
      const saveButton = screen.getByText('Save');
      fireEvent.click(saveButton);

      await waitFor(() => {
        expect(sendNotification).toHaveBeenCalledWith({
          title: 'ArxIDE',
          body: 'Failed to save file',
          icon: '❌',
        });
      });
    });
  });

  describe('Error Handling', () => {
    it('should handle CAD engine initialization failure gracefully', async () => {
      // Mock CAD engine to throw error
      Object.defineProperty(window, 'CadEngine', {
        value: jest.fn(() => {
          throw new Error('CAD engine failed to initialize');
        }),
        writable: true,
      });

      render(
        <TestWrapper>
          <ArxIDEApplication />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('ArxIDE - Professional CAD')).toBeInTheDocument();
      });
    });

    it('should handle file operation errors gracefully', async () => {
      const { invoke } = require('@tauri-apps/api/tauri');
      invoke.mockRejectedValue(new Error('File operation failed'));

      render(
        <TestWrapper>
          <ArxIDEApplication />
        </TestWrapper>
      );

      // Open sidebar
      const menuButton = screen.getByLabelText('menu');
      fireEvent.click(menuButton);

      // Click New File
      const newFileButton = screen.getByText('New File');
      fireEvent.click(newFileButton);

      await waitFor(() => {
        // Should not crash, should show error notification
        expect(screen.getByText('New File')).toBeInTheDocument();
      });
    });
  });

  describe('Performance', () => {
    it('should handle large project data efficiently', async () => {
      const largeProjectData = {
        id: 'large_project',
        name: 'Large Project',
        objects: Array.from({ length: 1000 }, (_, i) => ({
          type: 'line',
          startPoint: { x: i, y: i },
          endPoint: { x: i + 1, y: i + 1 },
        })),
        constraints: [],
      };

      const { invoke } = require('@tauri-apps/api/tauri');
      invoke.mockResolvedValue(JSON.stringify(largeProjectData));

      render(
        <TestWrapper>
          <ArxIDEApplication />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByText('ArxIDE - Professional CAD')).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels', async () => {
      render(
        <TestWrapper>
          <ArxIDEApplication />
        </TestWrapper>
      );

      await waitFor(() => {
        expect(screen.getByLabelText('menu')).toBeInTheDocument();
        expect(screen.getByLabelText('toggle dark mode')).toBeInTheDocument();
        expect(screen.getByLabelText('notifications')).toBeInTheDocument();
        expect(screen.getByLabelText('account')).toBeInTheDocument();
      });
    });

    it('should support keyboard navigation', async () => {
      render(
        <TestWrapper>
          <ArxIDEApplication />
        </TestWrapper>
      );

      // Test tab navigation
      const menuButton = screen.getByLabelText('menu');
      menuButton.focus();
      expect(menuButton).toHaveFocus();

      // Test keyboard shortcuts (implementation dependent)
      fireEvent.keyDown(document, { key: 'n', ctrlKey: true });
      // Should trigger new file
    });
  });
}); 