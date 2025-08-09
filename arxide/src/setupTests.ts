// Jest setup file for DOM testing
import '@testing-library/jest-dom';

// Mock global objects that are used in components
Object.defineProperty(window, 'CadEngine', {
  value: jest.fn(() => ({
    initialize: jest.fn(),
    render: jest.fn(),
    update: jest.fn(),
    destroy: jest.fn(),
  })),
  writable: true,
});

Object.defineProperty(window, 'ConstraintSolver', {
  value: jest.fn(() => ({
    solve: jest.fn(),
    validate: jest.fn(),
    optimize: jest.fn(),
  })),
  writable: true,
});

// Mock Tauri API
Object.defineProperty(window, '__TAURI__', {
  value: {
    invoke: jest.fn(),
    event: {
      listen: jest.fn(),
      emit: jest.fn(),
    },
  },
  writable: true,
});

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock IntersectionObserver
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});
