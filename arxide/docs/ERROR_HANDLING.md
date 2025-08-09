# ArxIDE Error Handling Guide

This document provides comprehensive guidance on error handling in ArxIDE, including common error patterns, best practices, and troubleshooting steps.

## Error Categories

### 1. Tauri Command Errors

These occur when the frontend tries to invoke Tauri commands that fail.

**Common Causes:**
- Missing Tauri commands in the backend
- Invalid parameters passed to commands
- File system permission issues
- Network connectivity problems

**Error Pattern:**
```typescript
try {
  const result = await invoke('command_name', { param: value });
} catch (error) {
  console.error('Tauri command failed:', error);
  setError(error instanceof Error ? error.message : 'Unknown error');
}
```

**Solutions:**
1. Ensure the command exists in `src-tauri/src/main.rs`
2. Validate parameters before sending
3. Check file permissions and paths
4. Implement proper error recovery

### 2. TypeScript/React Errors

**Common Causes:**
- Type mismatches
- Undefined/null values
- Missing dependencies
- Incorrect import paths

**Error Pattern:**
```typescript
// Type error
const [data, setData] = useState<string | null>(null);
data.toUpperCase(); // Error: Object is possibly null

// Fix
data?.toUpperCase() || '';
```

**Solutions:**
1. Use proper TypeScript types
2. Implement null checks
3. Use optional chaining (`?.`)
4. Add proper error boundaries

### 3. Build/Compilation Errors

**Common Causes:**
- Missing dependencies
- Version conflicts
- Configuration issues
- Syntax errors

**Solutions:**
1. Run `npm install` to install missing dependencies
2. Check `package.json` for version conflicts
3. Verify TypeScript configuration
4. Use the development script: `./scripts/dev.sh lint`

## Error Handling Best Practices

### 1. Frontend Error Handling

```typescript
// Good: Comprehensive error handling
const handleProjectOperation = async (operation: () => Promise<any>) => {
  try {
    setIsLoading(true);
    setError(null);

    const result = await operation();

    // Handle success
    showNotification('Operation completed successfully', 'success');
    return result;
  } catch (error) {
    // Handle different error types
    if (error instanceof Error) {
      if (error.message.includes('permission')) {
        setError('Permission denied. Please check file permissions.');
      } else if (error.message.includes('not found')) {
        setError('File not found. Please check the file path.');
      } else {
        setError(`Operation failed: ${error.message}`);
      }
    } else {
      setError('An unexpected error occurred.');
    }

    console.error('Operation failed:', error);
    showNotification('Operation failed', 'error');
  } finally {
    setIsLoading(false);
  }
};
```

### 2. Error Boundaries

```typescript
// Error boundary component
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <h2>Something went wrong</h2>
          <p>{this.state.error?.message}</p>
          <button onClick={() => window.location.reload()}>
            Reload Application
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
```

### 3. Async Error Handling

```typescript
// Good: Proper async error handling
const loadProject = async (filePath: string) => {
  try {
    const projectData = await invoke('open_project', { path: filePath });
    setCurrentProject(projectData);
    showNotification('Project loaded successfully', 'success');
  } catch (error) {
    handleProjectError(error, 'Failed to load project');
  }
};

const handleProjectError = (error: unknown, context: string) => {
  let errorMessage = context;

  if (error instanceof Error) {
    errorMessage += `: ${error.message}`;
  }

  setError(errorMessage);
  showNotification(errorMessage, 'error');
  console.error(`${context}:`, error);
};
```

## Common Error Scenarios

### 1. Missing Tauri Commands

**Symptoms:**
- Console errors: "Command not found"
- Frontend fails to initialize
- File operations don't work

**Solution:**
1. Check `src-tauri/src/main.rs` for missing commands
2. Ensure commands are registered in the invoke handler
3. Rebuild the backend: `cargo build`

### 2. File Permission Errors

**Symptoms:**
- "Permission denied" errors
- Cannot save or open files
- File watcher fails

**Solution:**
1. Check file permissions
2. Ensure proper file paths
3. Run with appropriate permissions
4. Use proper error handling in the backend

### 3. TypeScript Compilation Errors

**Symptoms:**
- Build fails with type errors
- IDE shows red squiggles
- Type mismatches

**Solution:**
1. Fix type annotations
2. Add proper interfaces
3. Use type guards
4. Run `npm run type-check`

### 4. React State Errors

**Symptoms:**
- Component crashes
- Undefined state access
- Infinite re-renders

**Solution:**
1. Use proper state initialization
2. Implement null checks
3. Use React.memo for performance
4. Add error boundaries

## Debugging Tools

### 1. Development Tools

```bash
# Run with debugging
RUST_LOG=debug npm run dev

# Check for TypeScript errors
npm run type-check

# Lint code
npm run lint

# Run tests
npm test
```

### 2. Browser Developer Tools

- **Console**: Check for JavaScript errors
- **Network**: Monitor API calls
- **Sources**: Debug TypeScript code
- **Application**: Check storage and cache

### 3. Tauri DevTools

```bash
# Enable Tauri devtools
npm run tauri dev -- --devtools
```

## Error Recovery Strategies

### 1. Graceful Degradation

```typescript
const loadFeature = async () => {
  try {
    return await invoke('advanced_feature');
  } catch (error) {
    console.warn('Advanced feature not available, using fallback');
    return fallbackFeature();
  }
};
```

### 2. Retry Logic

```typescript
const retryOperation = async (
  operation: () => Promise<any>,
  maxRetries: number = 3
) => {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await operation();
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
};
```

### 3. User Feedback

```typescript
const showUserFriendlyError = (error: unknown) => {
  let message = 'An unexpected error occurred';

  if (error instanceof Error) {
    switch (error.message) {
      case 'File not found':
        message = 'The file could not be found. Please check the path.';
        break;
      case 'Permission denied':
        message = 'Access denied. Please check file permissions.';
        break;
      default:
        message = error.message;
    }
  }

  setError(message);
  showNotification(message, 'error');
};
```

## Testing Error Scenarios

### 1. Unit Tests

```typescript
describe('Error Handling', () => {
  it('should handle Tauri command errors', async () => {
    const mockInvoke = jest.fn().mockRejectedValue(new Error('Command failed'));

    await expect(loadProject('test.json')).rejects.toThrow('Command failed');
  });

  it('should handle network errors', async () => {
    // Test network error scenarios
  });
});
```

### 2. Integration Tests

```typescript
describe('Error Recovery', () => {
  it('should recover from file permission errors', async () => {
    // Test permission error recovery
  });

  it('should handle missing dependencies', async () => {
    // Test dependency error handling
  });
});
```

## Monitoring and Logging

### 1. Error Logging

```typescript
const logError = (error: unknown, context: string) => {
  const errorInfo = {
    message: error instanceof Error ? error.message : String(error),
    stack: error instanceof Error ? error.stack : undefined,
    context,
    timestamp: new Date().toISOString(),
    userAgent: navigator.userAgent,
  };

  console.error('Application Error:', errorInfo);

  // Send to error tracking service
  if (process.env.NODE_ENV === 'production') {
    // sendToErrorService(errorInfo);
  }
};
```

### 2. Performance Monitoring

```typescript
const measureOperation = async <T>(
  operation: () => Promise<T>,
  name: string
): Promise<T> => {
  const start = performance.now();

  try {
    const result = await operation();
    const duration = performance.now() - start;

    console.log(`${name} completed in ${duration}ms`);
    return result;
  } catch (error) {
    const duration = performance.now() - start;
    console.error(`${name} failed after ${duration}ms:`, error);
    throw error;
  }
};
```

## Conclusion

Proper error handling is crucial for a robust application. By following these guidelines and implementing comprehensive error handling strategies, ArxIDE can provide a better user experience and easier debugging for developers.

Remember to:
1. Always validate inputs
2. Provide meaningful error messages
3. Implement proper error recovery
4. Test error scenarios
5. Monitor and log errors appropriately
6. Use error boundaries for React components
7. Handle async operations properly
