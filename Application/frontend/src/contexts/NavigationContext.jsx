import React, { createContext, useContext, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useUserPreferences } from "../utils/userPreferences";
import {
  optimizedNavigate,
  observeCoreWebVitals,
  preloadResource,
} from "../utils/performance";

const NavigationContext = createContext();

export const useOptimizedNavigation = () => {
  const context = useContext(NavigationContext);
  if (!context) {
    throw new Error(
      "useOptimizedNavigation must be used within NavigationProvider",
    );
  }
  return context;
};

export const NavigationProvider = ({ children }) => {
  const { preferences } = useUserPreferences();
  const navigate = useNavigate();

  // Set up performance monitoring if enabled
  useEffect(() => {
    if (preferences.performanceMonitoring) {
      const cleanup = observeCoreWebVitals((metric) => {
        // Log performance metrics (could send to analytics)
        console.log(`Performance metric: ${metric.name}`, metric);
      });
      return cleanup;
    }
  }, [preferences.performanceMonitoring]);

  // Enhanced navigation function that respects user preferences
  const navigateWithPreferences = (to, options = {}) => {
    if (preferences.prefetchData && options.prefetch !== false) {
      // Preload the destination if user prefers prefetching
      optimizedNavigate(navigate, to);
    } else {
      navigate(to, options);
    }
  };

  // Preload resources based on user preferences
  const preloadForRoute = (route, resources = []) => {
    if (preferences.prefetchData && !preferences.lowDataMode) {
      resources.forEach((resource) => {
        preloadResource(resource.url, resource.type);
      });
    }
  };

  const contextValue = {
    navigate: navigateWithPreferences,
    preloadForRoute,
    preferences,
  };

  return (
    <NavigationContext.Provider value={contextValue}>
      {children}
    </NavigationContext.Provider>
  );
};
