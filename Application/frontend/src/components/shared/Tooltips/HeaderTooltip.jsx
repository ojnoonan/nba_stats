import React from "react";
import { Tooltip } from "../../ui/tooltip";

/**
 * Consistent header tooltip component for table headers
 */
const HeaderTooltip = ({ children, content, side = "top", className = "" }) => {
  if (!content) {
    return <span className={className}>{children}</span>;
  }

  return (
    <Tooltip content={content}>
      <span
        className={`cursor-help underline decoration-dotted decoration-muted-foreground/50 ${className}`}
      >
        {children}
      </span>
    </Tooltip>
  );
};

export default HeaderTooltip;
