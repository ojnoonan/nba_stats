// Enhanced API service with comprehensive error handling and correlation ID support
const API_BASE_URL = "/api";

const RETRY_COUNT = 3;
const RETRY_DELAY = 1000;
const REQUEST_TIMEOUT = 15000;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

// Enhanced API Error class with correlation ID support
export class ApiError extends Error {
  constructor(message, status, correlationId, response) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.correlationId = correlationId;
    this.response = response;
    this.timestamp = new Date().toISOString();
  }

  static async fromResponse(response) {
    const correlationId =
      response.headers.get("x-correlation-id") ||
      response.headers.get("correlation-id");

    let errorData;
    try {
      errorData = await response.json();
    } catch {
      errorData = { detail: `HTTP ${response.status}: ${response.statusText}` };
    }

    const message =
      errorData.detail ||
      errorData.message ||
      `Request failed with status ${response.status}`;

    return new ApiError(message, response.status, correlationId, errorData);
  }

  toJSON() {
    return {
      name: this.name,
      message: this.message,
      status: this.status,
      correlationId: this.correlationId,
      timestamp: this.timestamp,
      response: this.response,
    };
  }
}

// Request interceptor for adding correlation IDs and headers
const enhanceRequest = (options = {}) => {
  const correlationId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

  return {
    ...options,
    headers: {
      "Content-Type": "application/json",
      "X-Correlation-ID": correlationId,
      "X-Client-Version": process.env.REACT_APP_VERSION || "unknown",
      "X-Client-Type": "web",
      ...options.headers,
    },
  };
};

// Enhanced fetch with retry logic and comprehensive error handling
const fetchWithRetry = async (url, options = {}) => {
  let lastError;
  const enhancedOptions = enhanceRequest(options);

  for (let attempt = 1; attempt <= RETRY_COUNT; attempt++) {
    try {
      const cleanUrl = url.replace(/\/+$/, "");
      const controller = new AbortController();

      // Use provided signal or create timeout
      const signal = options.signal || controller.signal;
      let timeoutId;

      if (!options.signal) {
        timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT);
      }

      const response = await fetch(cleanUrl, {
        ...enhancedOptions,
        signal,
      });

      if (timeoutId) {
        clearTimeout(timeoutId);
      }

      if (!response.ok) {
        const apiError = await ApiError.fromResponse(response);

        // Log error for monitoring
        console.error(`API Error [Attempt ${attempt}]:`, {
          url: cleanUrl,
          status: response.status,
          correlationId: apiError.correlationId,
          error: apiError.toJSON(),
        });

        throw apiError;
      }

      const correlationId = response.headers.get("x-correlation-id");
      let data;

      try {
        data = await response.json();
      } catch {
        data = null; // Handle non-JSON responses
      }

      // Log successful request
      console.debug(`API Success:`, {
        url: cleanUrl,
        correlationId,
        attempt,
      });

      return data;
    } catch (error) {
      lastError = error;

      // Don't retry on client errors (4xx) except 408, 429
      if (error instanceof ApiError) {
        const shouldRetry =
          error.status === 408 || // Request Timeout
          error.status === 429 || // Too Many Requests
          error.status >= 500; // Server Errors

        if (!shouldRetry) {
          throw error;
        }
      }

      // Don't retry on abort errors
      if (error.name === "AbortError") {
        throw error;
      }

      // If this was the last attempt, throw the error
      if (attempt === RETRY_COUNT) {
        break;
      }

      // Wait before retrying with exponential backoff
      const delay = RETRY_DELAY * Math.pow(2, attempt - 1);
      console.warn(`API retry ${attempt}/${RETRY_COUNT} after ${delay}ms:`, {
        url,
        error: error.message,
        attempt,
      });

      await sleep(delay);
    }
  }

  throw lastError;
};

// Health check endpoint
export const checkHealth = async () => {
  try {
    return await fetchWithRetry(`${API_BASE_URL}/health`);
  } catch (error) {
    console.error("Health check failed:", error);
    throw new Error("Health check failed");
  }
};

// Teams API
export const fetchTeams = async () => {
  try {
    return await fetchWithRetry(`${API_BASE_URL}/teams`);
  } catch (error) {
    console.error("Failed to fetch teams:", error);
    throw error;
  }
};

export const fetchTeam = async (teamId) => {
  try {
    return await fetchWithRetry(`${API_BASE_URL}/teams/${teamId}`);
  } catch (error) {
    console.error(`Failed to fetch team ${teamId}:`, error);
    throw error;
  }
};

// Players API
export const fetchPlayers = async (
  teamId = null,
  activeOnly = true,
  options = {},
) => {
  try {
    const params = new URLSearchParams();
    if (teamId) params.append("team_id", teamId);
    if (activeOnly) params.append("active_only", activeOnly);

    const url = `${API_BASE_URL}/players${params.toString() ? `?${params}` : ""}`;
    return await fetchWithRetry(url, options);
  } catch (error) {
    console.error("Failed to fetch players:", error);
    throw error;
  }
};

export const fetchPlayer = async (playerId, options = {}) => {
  try {
    console.log(`Fetching player with ID: ${playerId}`);
    const url = `${API_BASE_URL}/players/${playerId}`;
    const data = await fetchWithRetry(url, options);
    console.log("Player data received:", data);
    return data;
  } catch (error) {
    console.error(`Failed to fetch player ${playerId}:`, error);
    throw error;
  }
};

export const searchPlayers = async (query, options = {}) => {
  try {
    const params = new URLSearchParams({ q: query });
    const url = `${API_BASE_URL}/players/search?${params}`;
    return await fetchWithRetry(url, options);
  } catch (error) {
    console.error("Failed to search players:", error);
    throw error;
  }
};

// Games API
export const fetchGames = async (date = null, teamId = null, options = {}) => {
  try {
    const params = new URLSearchParams();
    if (date) params.append("date", date);
    if (teamId) params.append("team_id", teamId);

    const url = `${API_BASE_URL}/games${params.toString() ? `?${params}` : ""}`;
    return await fetchWithRetry(url, options);
  } catch (error) {
    console.error("Failed to fetch games:", error);
    throw error;
  }
};

export const fetchGame = async (gameId, options = {}) => {
  try {
    return await fetchWithRetry(`${API_BASE_URL}/games/${gameId}`, options);
  } catch (error) {
    console.error(`Failed to fetch game ${gameId}:`, error);
    throw error;
  }
};

export const fetchUpcomingGames = async (days = 7, options = {}) => {
  try {
    const params = new URLSearchParams({ days: days.toString() });
    const url = `${API_BASE_URL}/games/upcoming?${params}`;
    return await fetchWithRetry(url, options);
  } catch (error) {
    console.error("Failed to fetch upcoming games:", error);
    throw error;
  }
};

// Stats API
export const fetchPlayerStats = async (
  playerId,
  season = null,
  options = {},
) => {
  try {
    const params = new URLSearchParams();
    if (season) params.append("season", season);

    const url = `${API_BASE_URL}/players/${playerId}/stats${params.toString() ? `?${params}` : ""}`;
    return await fetchWithRetry(url, options);
  } catch (error) {
    console.error(`Failed to fetch player stats for ${playerId}:`, error);
    throw error;
  }
};

export const fetchTeamStats = async (teamId, season = null, options = {}) => {
  try {
    const params = new URLSearchParams();
    if (season) params.append("season", season);

    const url = `${API_BASE_URL}/teams/${teamId}/stats${params.toString() ? `?${params}` : ""}`;
    return await fetchWithRetry(url, options);
  } catch (error) {
    console.error(`Failed to fetch team stats for ${teamId}:`, error);
    throw error;
  }
};

// Admin API
export const updateData = async (options = {}) => {
  try {
    return await fetchWithRetry(`${API_BASE_URL}/admin/update-data`, {
      method: "POST",
      ...options,
    });
  } catch (error) {
    console.error("Failed to update data:", error);
    throw error;
  }
};

export const getDataStatus = async (options = {}) => {
  try {
    return await fetchWithRetry(`${API_BASE_URL}/admin/data-status`, options);
  } catch (error) {
    console.error("Failed to fetch data status:", error);
    throw error;
  }
};

// Batch API calls utility
export const batchApiCalls = async (calls, options = {}) => {
  const { maxConcurrency = 5, failFast = false } = options;
  const results = {};
  const errors = {};

  // Execute calls in batches to avoid overwhelming the server
  const batches = [];
  for (let i = 0; i < calls.length; i += maxConcurrency) {
    batches.push(calls.slice(i, i + maxConcurrency));
  }

  for (const batch of batches) {
    const promises = batch.map(async ({ key, apiCall, args = [] }) => {
      try {
        results[key] = await apiCall(...args);
      } catch (error) {
        errors[key] = error;
        if (failFast) {
          throw error;
        }
      }
    });

    if (failFast) {
      await Promise.all(promises);
    } else {
      await Promise.allSettled(promises);
    }
  }

  return { results, errors };
};

// Error reporting utility
export const reportError = async (error, context = {}) => {
  try {
    const errorReport = {
      error:
        error instanceof ApiError
          ? error.toJSON()
          : {
              name: error.name,
              message: error.message,
              stack: error.stack,
            },
      context: {
        url: window.location.href,
        userAgent: navigator.userAgent,
        timestamp: new Date().toISOString(),
        ...context,
      },
    };

    // Send to error reporting service
    await fetchWithRetry(`${API_BASE_URL}/admin/error-report`, {
      method: "POST",
      body: JSON.stringify(errorReport),
    });

    console.log("Error reported successfully:", errorReport);
  } catch (reportingError) {
    console.error("Failed to report error:", reportingError);
  }
};
