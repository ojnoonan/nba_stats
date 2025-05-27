# Error Handling System Documentation

## Overview

The NBA Stats application features a comprehensive error handling system designed to provide excellent user experience, detailed error tracking, and robust error recovery mechanisms. The system includes error boundaries, API error handling, global error state management, and user-friendly error notifications.

## Architecture

### 1. Error Boundaries

Error boundaries catch JavaScript errors anywhere in the component tree and display fallback UI instead of crashing the entire application.

#### ErrorBoundary Component
```jsx
import { ErrorBoundary } from './components/error';

// Basic usage
<ErrorBoundary name="ComponentName">
  <YourComponent />
</ErrorBoundary>

// Page-level error boundary
<ErrorBoundary name="HomePage" level="page">
  <HomePage />
</ErrorBoundary>

// Component-level error boundary
<ErrorBoundary name="PlayerCard" level="component">
  <PlayerCard player={player} />
</ErrorBoundary>
```

#### ApiErrorBoundary Component
Specialized for handling API-related errors with network status awareness:

```jsx
import { ApiErrorBoundary } from './components/error';

<ApiErrorBoundary
  onRetry={handleRetry}
  fallback={CustomErrorComponent}
>
  <DataComponent />
</ApiErrorBoundary>
```

### 2. Global Error Context

The ErrorProvider manages global error state and provides hooks for error handling.

#### Setup
```jsx
import { ErrorProvider } from './contexts/ErrorContext';

function App() {
  return (
    <ErrorProvider>
      <YourApp />
    </ErrorProvider>
  );
}
```

#### Using Error Context
```jsx
import { useError } from './contexts/ErrorContext';

function Component() {
  const { addError, removeError, errors, ERROR_TYPES, ERROR_SEVERITIES } = useError();

  const handleError = (error) => {
    addError(error, {
      type: ERROR_TYPES.API_ERROR,
      severity: ERROR_SEVERITIES.HIGH,
      title: 'Failed to Load Data',
      message: 'Please try again later.',
      context: { component: 'DataLoader' },
      actions: [
        {
          label: 'Retry',
          handler: retryFunction,
          dismissOnClick: true
        }
      ]
    });
  };
}
```

### 3. API Error Handling

Enhanced API service with correlation ID tracking and retry logic.

#### Enhanced API Usage
```jsx
import { fetchPlayers, ApiError } from './services/enhancedApi';

// API calls automatically include correlation IDs and retry logic
try {
  const players = await fetchPlayers();
} catch (error) {
  if (error instanceof ApiError) {
    console.log('Correlation ID:', error.correlationId);
    console.log('Status:', error.status);
    console.log('Response:', error.response);
  }
}
```

#### API Error Hooks
```jsx
import { useApiCall, useBatchApiCalls } from './hooks/useApiError';

// Single API call with error handling
const {
  data,
  loading,
  error,
  execute,
  retry,
  attemptCount
} = useApiCall(fetchPlayers, {
  immediate: true,
  retryCount: 3,
  onError: (error) => console.error(error),
  onSuccess: (data) => console.log(data)
});

// Batch API calls
const {
  results,
  loading,
  errors,
  executeAll,
  executeOne,
  hasErrors
} = useBatchApiCalls({
  players: fetchPlayers,
  teams: fetchTeams
}, {
  onAnyError: (key, error) => handleError(key, error),
  onAllSuccess: (results) => handleSuccess(results)
});
```

### 4. Error Notifications

User-friendly error notifications with different severity levels.

#### Error Notification Container
```jsx
import { ErrorNotificationContainer } from './components/error';

// Add to your app root
<ErrorNotificationContainer
  position="top-right"
  maxErrors={3}
/>
```

## Error Types and Severities

### Error Types
- `API_ERROR` - Server/API related errors
- `NETWORK_ERROR` - Network connectivity issues
- `VALIDATION_ERROR` - Form validation errors
- `AUTH_ERROR` - Authentication/authorization errors
- `UNKNOWN_ERROR` - Unclassified errors

### Error Severities
- `LOW` - Minor issues, informational
- `MEDIUM` - Standard errors, user attention needed
- `HIGH` - Serious errors, immediate attention
- `CRITICAL` - System-breaking errors, urgent attention

## Error Recovery Features

### 1. Automatic Retry
- Exponential backoff for API calls
- Configurable retry counts
- Smart retry logic (don't retry 4xx errors except 408, 429)

### 2. Offline Support
- Detect online/offline status
- Queue retry actions for when connection returns
- Visual indicators for offline state

### 3. Correlation ID Tracking
- Every request gets a unique correlation ID
- Track errors across frontend and backend
- Easier debugging and support

### 4. User Actions
- Retry buttons for failed operations
- Report bug functionality for critical errors
- Navigate home or refresh page options

## Implementation Examples

### 1. Page with Comprehensive Error Handling
```jsx
import { ErrorBoundary, ApiErrorBoundary } from './components/error';
import { useApiCall } from './hooks/useApiError';
import { useError } from './contexts/ErrorContext';

const MyPage = () => {
  const { addError, ERROR_TYPES, ERROR_SEVERITIES } = useError();

  const {
    data,
    loading,
    error,
    retry
  } = useApiCall(fetchData, {
    immediate: true,
    onError: (error) => {
      addError(error, {
        type: ERROR_TYPES.API_ERROR,
        severity: ERROR_SEVERITIES.HIGH,
        title: 'Failed to Load Data',
        actions: [{ label: 'Retry', handler: retry }]
      });
    }
  });

  if (error) {
    return (
      <ApiErrorBoundary onRetry={retry}>
        <div>Error loading data</div>
      </ApiErrorBoundary>
    );
  }

  return (
    <ErrorBoundary name="MyPageContent">
      {loading ? <LoadingSpinner /> : <DataDisplay data={data} />}
    </ErrorBoundary>
  );
};
```

### 2. Form with Error Handling
```jsx
import { useFormSubmission } from './hooks/useApiError';
import { useError } from './contexts/ErrorContext';

const MyForm = () => {
  const { addError, ERROR_TYPES } = useError();

  const {
    submit,
    isSubmitting,
    submitError,
    submitSuccess
  } = useFormSubmission(submitData, {
    onError: (error) => {
      addError(error, {
        type: ERROR_TYPES.VALIDATION_ERROR,
        title: 'Form Submission Failed',
        message: 'Please check your input and try again.'
      });
    },
    onSuccess: () => {
      addError(null, {
        type: ERROR_TYPES.API_ERROR,
        severity: ERROR_SEVERITIES.LOW,
        title: 'Success',
        message: 'Data saved successfully!',
        timeout: 3000
      });
    }
  });

  return (
    <form onSubmit={(e) => {
      e.preventDefault();
      submit(formData);
    }}>
      {/* Form fields */}
      <button
        type="submit"
        disabled={isSubmitting}
        className={isSubmitting ? 'opacity-50' : ''}
      >
        {isSubmitting ? 'Saving...' : 'Save'}
      </button>
    </form>
  );
};
```

## Best Practices

### 1. Error Boundary Placement
- Wrap each page with a page-level error boundary
- Wrap complex components with component-level boundaries
- Use descriptive names for error boundaries for better debugging

### 2. Error Context Usage
- Use appropriate error types and severities
- Provide meaningful titles and messages
- Include relevant context for debugging
- Add user actions when possible

### 3. API Error Handling
- Always handle errors in API calls
- Use correlation IDs for tracking
- Implement appropriate retry logic
- Provide user feedback for long-running operations

### 4. User Experience
- Show loading states during operations
- Provide clear error messages
- Offer recovery options (retry, refresh, navigate)
- Auto-dismiss non-critical notifications

### 5. Development vs Production
- Show detailed error information in development
- Log errors for monitoring in production
- Use correlation IDs for support requests
- Implement error reporting to external services

## Monitoring and Debugging

### 1. Error Logging
All errors include:
- Correlation ID for tracking
- Timestamp
- Error type and severity
- Component context
- User agent and URL
- Stack trace (development)

### 2. Error Reporting
- Automatic reporting for critical errors
- Manual bug reporting for user-initiated reports
- Integration with external monitoring services

### 3. Development Tools
- Console logging with structured error data
- Debug information display in development mode
- Error history tracking
- Retry queue monitoring

## Configuration

### Environment Variables
```bash
# API Configuration
REACT_APP_API_BASE_URL=/api
REACT_APP_REQUEST_TIMEOUT=15000
REACT_APP_RETRY_COUNT=3
REACT_APP_RETRY_DELAY=1000

# Error Reporting
REACT_APP_ERROR_REPORTING_URL=https://api.sentry.io/...
REACT_APP_ENABLE_ERROR_REPORTING=true

# Development
REACT_APP_SHOW_DEBUG_INFO=true
REACT_APP_LOG_LEVEL=debug
```

### Error Notification Settings
```jsx
<ErrorNotificationContainer
  position="top-right"        // Position on screen
  maxErrors={3}              // Maximum visible errors
  autoRemoveTimeout={5000}   // Auto-dismiss timeout
  enableSounds={false}       // Error notification sounds
/>
```

## Integration with Backend

The frontend error handling system is designed to work with the backend error middleware:

### 1. Correlation ID Tracking
- Frontend sends `X-Correlation-ID` header
- Backend includes correlation ID in error responses
- Full request tracing across system boundaries

### 2. Structured Error Responses
- Consistent error format from backend
- Error codes and categories
- Recovery suggestions from server

### 3. Health Monitoring
- Frontend checks backend health
- Circuit breaker pattern for failed services
- Graceful degradation when services unavailable

This comprehensive error handling system ensures robust error management, excellent user experience, and effective debugging capabilities throughout the NBA Stats application.
