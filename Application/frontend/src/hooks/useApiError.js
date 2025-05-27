import { useState, useCallback, useRef, useEffect } from "react";

/**
 * Enhanced hook for handling API calls with comprehensive error management
 * @param {Function} apiFunction - The API function to call
 * @param {Object} options - Configuration options
 * @returns {Object} - State and methods for API interaction
 */
export const useApiCall = (apiFunction, options = {}) => {
  const {
    immediate = false,
    retryCount = 3,
    retryDelay = 1000,
    onSuccess,
    onError,
    dependencies = [],
  } = options;

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(immediate);
  const [error, setError] = useState(null);
  const [isRetrying, setIsRetrying] = useState(false);
  const [attemptCount, setAttemptCount] = useState(0);

  const abortControllerRef = useRef(null);
  const retryTimeoutRef = useRef(null);

  const execute = useCallback(
    async (...args) => {
      // Cancel any pending requests
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      // Clear retry timeout
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }

      abortControllerRef.current = new AbortController();

      setLoading(true);
      setError(null);
      setAttemptCount((prev) => prev + 1);

      try {
        const result = await apiFunction(...args, {
          signal: abortControllerRef.current.signal,
        });

        setData(result);
        setLoading(false);

        if (onSuccess) {
          onSuccess(result);
        }

        return result;
      } catch (err) {
        if (err.name === "AbortError") {
          return; // Request was cancelled, don't update state
        }

        setError(err);
        setLoading(false);

        if (onError) {
          onError(err);
        }

        throw err;
      }
    },
    [apiFunction, onSuccess, onError],
  );

  const retry = useCallback(
    async (...args) => {
      setIsRetrying(true);

      for (let attempt = 1; attempt <= retryCount; attempt++) {
        try {
          const result = await execute(...args);
          setIsRetrying(false);
          return result;
        } catch (err) {
          if (attempt === retryCount) {
            setIsRetrying(false);
            throw err;
          }

          // Wait before next retry
          await new Promise((resolve) => {
            retryTimeoutRef.current = setTimeout(resolve, retryDelay * attempt);
          });
        }
      }
    },
    [execute, retryCount, retryDelay],
  );

  const reset = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current);
    }

    setData(null);
    setLoading(false);
    setError(null);
    setIsRetrying(false);
    setAttemptCount(0);
  }, []);

  // Execute immediately if requested
  useEffect(() => {
    if (immediate) {
      execute();
    }

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current);
      }
    };
  }, [immediate, execute, ...dependencies]);

  return {
    data,
    loading,
    error,
    isRetrying,
    attemptCount,
    execute,
    retry,
    reset,
  };
};

/**
 * Hook for handling multiple API calls with batch error management
 * @param {Object} apiCalls - Object containing named API functions
 * @param {Object} options - Configuration options
 * @returns {Object} - State and methods for batch API interaction
 */
export const useBatchApiCalls = (apiCalls, options = {}) => {
  const { onAllSuccess, onAnyError } = options;

  const [results, setResults] = useState({});
  const [loading, setLoading] = useState({});
  const [errors, setErrors] = useState({});
  const [isExecuting, setIsExecuting] = useState(false);

  const executeAll = useCallback(
    async (args = {}) => {
      setIsExecuting(true);
      const newResults = {};
      const newErrors = {};
      const newLoading = {};

      // Initialize loading states
      Object.keys(apiCalls).forEach((key) => {
        newLoading[key] = true;
      });
      setLoading(newLoading);

      const promises = Object.entries(apiCalls).map(
        async ([key, apiFunction]) => {
          try {
            const result = await apiFunction(args[key] || {});
            newResults[key] = result;
            newLoading[key] = false;
            setLoading((prev) => ({ ...prev, [key]: false }));
          } catch (error) {
            newErrors[key] = error;
            newLoading[key] = false;
            setLoading((prev) => ({ ...prev, [key]: false }));

            if (onAnyError) {
              onAnyError(key, error);
            }
          }
        },
      );

      await Promise.allSettled(promises);

      setResults(newResults);
      setErrors(newErrors);
      setIsExecuting(false);

      const hasErrors = Object.keys(newErrors).length > 0;
      if (!hasErrors && onAllSuccess) {
        onAllSuccess(newResults);
      }

      return { results: newResults, errors: newErrors };
    },
    [apiCalls, onAllSuccess, onAnyError],
  );

  const executeOne = useCallback(
    async (key, args = {}) => {
      if (!apiCalls[key]) {
        throw new Error(`API function '${key}' not found`);
      }

      setLoading((prev) => ({ ...prev, [key]: true }));
      setErrors((prev) => ({ ...prev, [key]: null }));

      try {
        const result = await apiCalls[key](args);
        setResults((prev) => ({ ...prev, [key]: result }));
        setLoading((prev) => ({ ...prev, [key]: false }));
        return result;
      } catch (error) {
        setErrors((prev) => ({ ...prev, [key]: error }));
        setLoading((prev) => ({ ...prev, [key]: false }));

        if (onAnyError) {
          onAnyError(key, error);
        }

        throw error;
      }
    },
    [apiCalls, onAnyError],
  );

  const reset = useCallback(() => {
    setResults({});
    setLoading({});
    setErrors({});
    setIsExecuting(false);
  }, []);

  return {
    results,
    loading,
    errors,
    isExecuting,
    executeAll,
    executeOne,
    reset,
    hasErrors: Object.keys(errors).length > 0,
    isAllLoading: Object.values(loading).some(Boolean),
  };
};

/**
 * Hook for handling form submission with API calls and error management
 * @param {Function} submitFunction - The function to call on form submission
 * @param {Object} options - Configuration options
 * @returns {Object} - State and methods for form submission
 */
export const useFormSubmission = (submitFunction, options = {}) => {
  const { onSuccess, onError, resetOnSuccess = true } = options;

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  const submit = useCallback(
    async (formData) => {
      setIsSubmitting(true);
      setSubmitError(null);
      setSubmitSuccess(false);

      try {
        const result = await submitFunction(formData);
        setSubmitSuccess(true);

        if (onSuccess) {
          onSuccess(result);
        }

        if (resetOnSuccess) {
          setTimeout(() => setSubmitSuccess(false), 3000);
        }

        return result;
      } catch (error) {
        setSubmitError(error);

        if (onError) {
          onError(error);
        }

        throw error;
      } finally {
        setIsSubmitting(false);
      }
    },
    [submitFunction, onSuccess, onError, resetOnSuccess],
  );

  const reset = useCallback(() => {
    setIsSubmitting(false);
    setSubmitError(null);
    setSubmitSuccess(false);
  }, []);

  return {
    submit,
    isSubmitting,
    submitError,
    submitSuccess,
    reset,
  };
};
