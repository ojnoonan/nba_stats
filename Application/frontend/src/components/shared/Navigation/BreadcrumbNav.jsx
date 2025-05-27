import React from "react";
import { Link, useLocation } from "react-router-dom";
import { ChevronRightIcon, HomeIcon } from "lucide-react";

/**
 * Breadcrumb navigation component
 */
const BreadcrumbNav = ({ items = [], className = "", showHome = true }) => {
  const location = useLocation();

  const breadcrumbItems = showHome
    ? [{ label: "Home", href: "/" }, ...items]
    : items;

  if (breadcrumbItems.length <= 1) {
    return null;
  }

  return (
    <nav
      className={`flex items-center space-x-1 text-sm text-muted-foreground ${className}`}
    >
      {breadcrumbItems.map((item, index) => {
        const isLast = index === breadcrumbItems.length - 1;
        const isCurrent = item.href === location.pathname;

        return (
          <React.Fragment key={item.href || index}>
            {index > 0 && <ChevronRightIcon className="h-4 w-4 mx-1" />}
            {isLast || isCurrent ? (
              <span className="font-medium text-foreground">
                {index === 0 && showHome ? (
                  <HomeIcon className="h-4 w-4" />
                ) : (
                  item.label
                )}
              </span>
            ) : (
              <Link
                to={item.href}
                className="hover:text-primary transition-colors"
              >
                {index === 0 && showHome ? (
                  <HomeIcon className="h-4 w-4" />
                ) : (
                  item.label
                )}
              </Link>
            )}
          </React.Fragment>
        );
      })}
    </nav>
  );
};

export default BreadcrumbNav;
