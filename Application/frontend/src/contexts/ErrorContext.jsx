import React, { createContext, useContext, useReducer, useEffect } from "react";
import { reportError } from "../services/enhancedApi";

// Error context
const ErrorContext = createContext();

// Error types
export const ERROR_TYPES = {
  API_ERROR: "API_ERROR",
  NETWORK_ERROR: "NETWORK_ERROR",
  VALIDATION_ERROR: "VALIDATION_ERROR",
  AUTH_ERROR: "AUTH_ERROR",
  UNKNOWN_ERROR: "UNKNOWN_ERROR",
};

// Error severities
export const ERROR_SEVERITIES = {
  LOW: "LOW",
  MEDIUM: "MEDIUM",
  HIGH: "HIGH",
  CRITICAL: "CRITICAL",
};

// Initial state
const initialState = {
  errors: [],
  globalError: null,
  isOnline: navigator.onLine,
  errorHistory: [],
  retryQueue: [],
};

// Error reducer
const errorReducer = (state, action) => {
  switch (action.type) {
    case "ADD_ERROR":
      const newError = {
        id: Date.now() + Math.random(),
        timestamp: new Date().toISOString(),
        ...action.payload,
      };

      return {
        ...state,
        errors: [...state.errors, newError],
        errorHistory: [...state.errorHistory, newError].slice(-100), // Keep last 100 errors
        globalError:
          action.payload.severity === ERROR_SEVERITIES.CRITICAL
            ? newError
            : state.globalError,
      };

    case "REMOVE_ERROR":
      return {
        ...state,
        errors: state.errors.filter((error) => error.id !== action.payload.id),
        globalError:
          state.globalError?.id === action.payload.id
            ? null
            : state.globalError,
      };

    case "CLEAR_ERRORS":
      return {
        ...state,
        errors: [],
        globalError: null,
      };

    case "SET_ONLINE_STATUS":
      return {
        ...state,
        isOnline: action.payload,
      };

    case "ADD_RETRY_ITEM":
      return {
        ...state,
        retryQueue: [...state.retryQueue, action.payload],
      };

    case "REMOVE_RETRY_ITEM":
      return {
        ...state,
        retryQueue: state.retryQueue.filter(
          (item) => item.id !== action.payload.id,
        ),
      };

    case "CLEAR_RETRY_QUEUE":
      return {
        ...state,
        retryQueue: [],
      };

    default:
      return state;
  }
};

// Error provider component
export const ErrorProvider = ({ children }) => {
  const [state, dispatch] = useReducer(errorReducer, initialState);

  // Handle online/offline status
  useEffect(() => {
    const handleOnline = () =>
      dispatch({ type: "SET_ONLINE_STATUS", payload: true });
    const handleOffline = () =>
      dispatch({ type: "SET_ONLINE_STATUS", payload: false });

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  // Auto-remove errors after timeout
  useEffect(() => {
    const timeouts = state.errors
      .map((error) => {
        if (error.autoRemove !== false) {
          const timeout =
            error.timeout ||
            (error.severity === ERROR_SEVERITIES.CRITICAL ? 10000 : 5000);
          return setTimeout(() => {
            dispatch({ type: "REMOVE_ERROR", payload: { id: error.id } });
          }, timeout);
        }
        return null;
      })
      .filter(Boolean);

    return () => timeouts.forEach(clearTimeout);
  }, [state.errors]);

  // Process retry queue when coming back online
  useEffect(() => {
    if (state.isOnline && state.retryQueue.length > 0) {
      state.retryQueue.forEach(async (item) => {
        try {
          await item.retryFunction();
          dispatch({ type: "REMOVE_RETRY_ITEM", payload: { id: item.id } });
        } catch (error) {
          // Retry failed, keep in queue or remove based on max attempts
          if (item.attempts >= (item.maxAttempts || 3)) {
            dispatch({ type: "REMOVE_RETRY_ITEM", payload: { id: item.id } });
          }
        }
      });
    }
  }, [state.isOnline, state.retryQueue]);

  const addError = (error, options = {}) => {
    const {
      type = ERROR_TYPES.UNKNOWN_ERROR,
      severity = ERROR_SEVERITIES.MEDIUM,
      title,
      message,
      correlationId,
      context = {},
      autoRemove = true,
      timeout,
      actions = [],
    } = options;

    // Determine error type and severity from error object
    let errorType = type;
    let errorSeverity = severity;
    let errorMessage = message || error?.message || "An unknown error occurred";
    let errorTitle = title;

    if (error && typeof error === "object") {
      // Handle API errors
      if (error.status) {
        errorType = ERROR_TYPES.API_ERROR;
        if (error.status >= 500) {
          errorSeverity = ERROR_SEVERITIES.HIGH;
        } else if (error.status === 401 || error.status === 403) {
          errorType = ERROR_TYPES.AUTH_ERROR;
          errorSeverity = ERROR_SEVERITIES.HIGH;
        }
      }

      // Handle network errors
      if (error.name === "TypeError" && error.message.includes("fetch")) {
        errorType = ERROR_TYPES.NETWORK_ERROR;
        errorSeverity = ERROR_SEVERITIES.HIGH;
      }

      // Handle validation errors
      if (error.name === "ValidationError") {
        errorType = ERROR_TYPES.VALIDATION_ERROR;
        errorSeverity = ERROR_SEVERITIES.LOW;
      }
    }

    // Generate title if not provided
    if (!errorTitle) {
      switch (errorType) {
        case ERROR_TYPES.API_ERROR:
          errorTitle = "API Error";
          break;
        case ERROR_TYPES.NETWORK_ERROR:
          errorTitle = "Network Error";
          break;
        case ERROR_TYPES.VALIDATION_ERROR:
          errorTitle = "Validation Error";
          break;
        case ERROR_TYPES.AUTH_ERROR:
          errorTitle = "Authentication Error";
          break;
        default:
          errorTitle = "Error";
      }
    }

    const errorPayload = {
      type: errorType,
      severity: errorSeverity,
      title: errorTitle,
      message: errorMessage,
      correlationId: error?.correlationId || correlationId,
      originalError: error,
      context,
      autoRemove,
      timeout,
      actions,
    };

    dispatch({ type: "ADD_ERROR", payload: errorPayload });

    // Report critical errors
    if (errorSeverity === ERROR_SEVERITIES.CRITICAL) {
      reportError(error, { ...context, severity: errorSeverity });
    }

    return errorPayload.id;
  };

  const removeError = (id) => {
    dispatch({ type: "REMOVE_ERROR", payload: { id } });
  };

  const clearErrors = () => {
    dispatch({ type: "CLEAR_ERRORS" });
  };

  const addRetryItem = (retryFunction, options = {}) => {
    const retryItem = {
      id: Date.now() + Math.random(),
      retryFunction,
      attempts: 0,
      maxAttempts: options.maxAttempts || 3,
      context: options.context || {},
    };

    dispatch({ type: "ADD_RETRY_ITEM", payload: retryItem });
    return retryItem.id;
  };

  const removeRetryItem = (id) => {
    dispatch({ type: "REMOVE_RETRY_ITEM", payload: { id } });
  };

  const clearRetryQueue = () => {
    dispatch({ type: "CLEAR_RETRY_QUEUE" });
  };

  const getErrorsByType = (type) => {
    return state.errors.filter((error) => error.type === type);
  };

  const getErrorsBySeverity = (severity) => {
    return state.errors.filter((error) => error.severity === severity);
  };

  const hasErrors = () => {
    return state.errors.length > 0;
  };

  const hasCriticalErrors = () => {
    return state.errors.some(
      (error) => error.severity === ERROR_SEVERITIES.CRITICAL,
    );
  };

  const contextValue = {
    // State
    errors: state.errors,
    globalError: state.globalError,
    isOnline: state.isOnline,
    errorHistory: state.errorHistory,
    retryQueue: state.retryQueue,

    // Actions
    addError,
    removeError,
    clearErrors,
    addRetryItem,
    removeRetryItem,
    clearRetryQueue,

    // Utilities
    getErrorsByType,
    getErrorsBySeverity,
    hasErrors,
    hasCriticalErrors,

    // Constants
    ERROR_TYPES,
    ERROR_SEVERITIES,
  };

  return (
    <ErrorContext.Provider value={contextValue}>
      {children}
    </ErrorContext.Provider>
  );
};

// Hook to use error context
export const useError = () => {
  const context = useContext(ErrorContext);
  if (!context) {
    throw new Error("useError must be used within an ErrorProvider");
  }
  return context;
};

// Hook for handling specific error types
export const useApiError = () => {
  const { addError, getErrorsByType, ERROR_TYPES } = useError();

  const handleApiError = (error, context = {}) => {
    return addError(error, {
      type: ERROR_TYPES.API_ERROR,
      context,
    });
  };

  const apiErrors = getErrorsByType(ERROR_TYPES.API_ERROR);

  return { handleApiError, apiErrors };
};

// Hook for handling network errors
export const useNetworkError = () => {
  const { addError, getErrorsByType, isOnline, ERROR_TYPES } = useError();

  const handleNetworkError = (error, context = {}) => {
    return addError(error, {
      type: ERROR_TYPES.NETWORK_ERROR,
      context,
    });
  };

  const networkErrors = getErrorsByType(ERROR_TYPES.NETWORK_ERROR);

  return { handleNetworkError, networkErrors, isOnline };
};
