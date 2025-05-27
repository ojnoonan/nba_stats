// Performance utilities for NBA Stats app

/**
 * Debounce function to limit the frequency of function calls
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @param {boolean} immediate - Execute immediately on first call
 * @returns {Function} Debounced function
 */
export const debounce = (func, wait, immediate = false) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      timeout = null;
      if (!immediate) func.apply(this, args);
    };
    const callNow = immediate && !timeout;
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
    if (callNow) func.apply(this, args);
  };
};

/**
 * Throttle function to limit the frequency of function calls
 * @param {Function} func - Function to throttle
 * @param {number} limit - Time limit in milliseconds
 * @returns {Function} Throttled function
 */
export const throttle = (func, limit) => {
  let inThrottle;
  return function (...args) {
    if (!inThrottle) {
      func.apply(this, args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
};

/**
 * Optimized navigation helper that works with React Router
 * @param {Function} navigate - React Router navigate function
 * @param {string} url - URL to navigate to
 * @param {object} options - Navigation options
 */
export const optimizedNavigate = (navigate, url, options = {}) => {
  // Use View Transitions API if available for smooth navigation
  if (document.startViewTransition && !options.replace) {
    document.startViewTransition(() => {
      navigate(url, options);
    });
  } else {
    navigate(url, options);
  }
};

/**
 * Preload critical resources
 * @param {string} url - URL to preload
 * @param {string} as - Resource type
 */
export const preloadResource = (url, as = "fetch") => {
  const link = document.createElement("link");
  link.rel = "preload";
  link.href = url;
  link.as = as;
  if (as === "fetch") {
    link.crossOrigin = "anonymous";
  }
  document.head.appendChild(link);
};

/**
 * Lazy load images with intersection observer
 * @param {HTMLImageElement} img - Image element
 * @param {string} src - Image source
 */
export const lazyLoadImage = (img, src) => {
  if ("IntersectionObserver" in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const image = entry.target;
          image.src = src;
          image.classList.remove("lazy");
          observer.unobserve(image);
        }
      });
    });
    observer.observe(img);
  } else {
    // Fallback for browsers without IntersectionObserver
    img.src = src;
  }
};

/**
 * Format numbers for better performance display
 * @param {number} num - Number to format
 * @param {number} decimals - Number of decimal places
 * @returns {string} Formatted number
 */
export const formatNumber = (num, decimals = 1) => {
  if (typeof num !== "number" || isNaN(num)) return "0";
  return Number(num).toFixed(decimals);
};

/**
 * Calculate cache hit rate for query performance monitoring
 */
export const calculateCacheStats = (queryClient) => {
  const cache = queryClient.getQueryCache();
  const queries = cache.getAll();

  const stats = {
    total: queries.length,
    fresh: 0,
    stale: 0,
    inactive: 0,
    error: 0,
  };

  queries.forEach((query) => {
    if (query.isStale()) {
      stats.stale++;
    } else {
      stats.fresh++;
    }

    if (query.isInactive()) {
      stats.inactive++;
    }

    if (query.state.status === "error") {
      stats.error++;
    }
  });

  return {
    ...stats,
    hitRate:
      stats.total > 0 ? ((stats.fresh / stats.total) * 100).toFixed(1) : "0.0",
  };
};

/**
 * Memory usage monitoring (development only)
 */
export const getMemoryUsage = () => {
  if (performance.memory) {
    return {
      used: Math.round(performance.memory.usedJSHeapSize / 1048576), // MB
      total: Math.round(performance.memory.totalJSHeapSize / 1048576), // MB
      limit: Math.round(performance.memory.jsHeapSizeLimit / 1048576), // MB
    };
  }
  return null;
};

/**
 * Performance observer for Core Web Vitals
 */
export const observePerformance = (callback) => {
  if ("PerformanceObserver" in window) {
    try {
      const observer = new PerformanceObserver((list) => {
        list.getEntries().forEach(callback);
      });

      observer.observe({ entryTypes: ["measure", "navigation"] });

      // Observe Core Web Vitals
      observer.observe({ type: "largest-contentful-paint", buffered: true });
      observer.observe({ type: "first-input", buffered: true });
      observer.observe({ type: "layout-shift", buffered: true });

      return observer;
    } catch (e) {
      console.warn("Performance Observer not fully supported", e);
    }
  }
  return null;
};

/**
 * Specific Core Web Vitals observer
 * @param {Function} callback - Callback function to handle metrics
 * @returns {Function} Cleanup function
 */
export const observeCoreWebVitals = (callback) => {
  if ("PerformanceObserver" in window) {
    const observers = [];

    try {
      // Largest Contentful Paint (LCP)
      const lcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1];
        callback({
          name: "LCP",
          value: lastEntry.startTime,
          delta: lastEntry.startTime,
          id: `v3-${Date.now()}-${Math.floor(Math.random() * (9e12 - 1)) + 1e12}`,
        });
      });
      lcpObserver.observe({ type: "largest-contentful-paint", buffered: true });
      observers.push(lcpObserver);

      // First Input Delay (FID)
      const fidObserver = new PerformanceObserver((list) => {
        list.getEntries().forEach((entry) => {
          callback({
            name: "FID",
            value: entry.processingStart - entry.startTime,
            delta: entry.processingStart - entry.startTime,
            id: `v3-${Date.now()}-${Math.floor(Math.random() * (9e12 - 1)) + 1e12}`,
          });
        });
      });
      fidObserver.observe({ type: "first-input", buffered: true });
      observers.push(fidObserver);

      // Cumulative Layout Shift (CLS)
      let clsValue = 0;
      const clsObserver = new PerformanceObserver((list) => {
        list.getEntries().forEach((entry) => {
          if (!entry.hadRecentInput) {
            clsValue += entry.value;
            callback({
              name: "CLS",
              value: clsValue,
              delta: entry.value,
              id: `v3-${Date.now()}-${Math.floor(Math.random() * (9e12 - 1)) + 1e12}`,
            });
          }
        });
      });
      clsObserver.observe({ type: "layout-shift", buffered: true });
      observers.push(clsObserver);

      // Return cleanup function
      return () => {
        observers.forEach((observer) => observer.disconnect());
      };
    } catch (e) {
      console.warn("Core Web Vitals observer not fully supported", e);
      return () => {};
    }
  }
  return () => {};
};
