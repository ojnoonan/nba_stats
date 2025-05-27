import React, { createContext, useContext } from "react";
import { TooltipProvider } from "@radix-ui/react-tooltip";

/**
 * Context for managing tooltip state across the application
 */
const TooltipContext = createContext({});

export const useTooltipContext = () => useContext(TooltipContext);

export const TooltipProviderWrapper = ({
  children,
  delayDuration = 300,
  skipDelayDuration = 100,
}) => {
  return (
    <TooltipProvider
      delayDuration={delayDuration}
      skipDelayDuration={skipDelayDuration}
    >
      <TooltipContext.Provider value={{ delayDuration, skipDelayDuration }}>
        {children}
      </TooltipContext.Provider>
    </TooltipProvider>
  );
};
