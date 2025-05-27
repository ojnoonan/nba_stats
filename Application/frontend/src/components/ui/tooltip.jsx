import * as React from "react";
import * as TooltipPrimitive from "@radix-ui/react-tooltip";

const TooltipProvider = TooltipPrimitive.Provider;
const TooltipRoot = TooltipPrimitive.Root;
const TooltipTrigger = TooltipPrimitive.Trigger;
const TooltipPortal = TooltipPrimitive.Portal;

const TooltipContent = React.forwardRef(
  ({ className, sideOffset = 4, ...props }, ref) => (
    <TooltipPrimitive.Content
      ref={ref}
      sideOffset={sideOffset}
      className="z-50 overflow-hidden rounded-md border border-border/50 bg-popover px-3 py-1.5 text-xs text-popover-foreground shadow-lg animate-fade-in"
      {...props}
    />
  ),
);
TooltipContent.displayName = "TooltipContent";

export function Tooltip({ children, content }) {
  return (
    <TooltipRoot>
      <TooltipTrigger asChild>{children}</TooltipTrigger>
      <TooltipPortal>
        <TooltipContent>{content}</TooltipContent>
      </TooltipPortal>
    </TooltipRoot>
  );
}

export function TooltipWrapper({ children }) {
  return <TooltipProvider>{children}</TooltipProvider>;
}
