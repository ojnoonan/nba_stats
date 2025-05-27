import React from "react";
import { Link } from "react-router-dom";
import { ExternalLinkIcon } from "lucide-react";

/**
 * Link component for opening content in dedicated pages
 */
const PageLink = ({
  to,
  children,
  className = "",
  showIcon = true,
  variant = "button", // "button" | "text" | "icon"
}) => {
  const baseClasses = "inline-flex items-center transition-colors";

  const variants = {
    button:
      "px-3 py-1.5 rounded-md border border-border hover:bg-muted/50 text-sm",
    text: "text-primary hover:text-primary/80 underline-offset-4 hover:underline",
    icon: "p-1.5 rounded-md hover:bg-muted/50 text-muted-foreground hover:text-primary",
  };

  return (
    <Link
      to={to}
      className={`${baseClasses} ${variants[variant]} ${className}`}
    >
      {variant !== "icon" && children}
      {showIcon && (
        <ExternalLinkIcon
          className={`h-4 w-4 ${variant !== "icon" ? "ml-1.5" : ""}`}
        />
      )}
    </Link>
  );
};

export default PageLink;
