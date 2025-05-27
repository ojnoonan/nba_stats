import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import { useState } from "react";
import { fetchStatus } from "../../services/api";
import { LoadingSpinner } from "../ui/loading-spinner";
import { SearchBar } from "../ui/search-bar";

export default function NavigationBar() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const { data: status } = useQuery({
    queryKey: ["status"],
    queryFn: fetchStatus,
  });

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen);
  };

  const closeMobileMenu = () => {
    setIsMobileMenuOpen(false);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "N/A";
    const date = new Date(dateStr);
    const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    return `${format(date, "MMM d, yyyy, h:mm a")}`;
  };

  const renderStatusMessage = () => {
    if (!status) return null;

    if (status.is_updating) {
      const phase = status.current_phase || "data";
      return (
        <div className="flex items-center space-x-2 text-primary text-sm">
          <LoadingSpinner size="small" />
          <span>Updating {phase}...</span>
        </div>
      );
    }

    if (status.last_error) {
      return <div className="text-sm text-destructive">Update failed</div>;
    }

    return (
      <div className="text-sm text-muted-foreground">
        Updated{" "}
        {formatDate(status.last_successful_update || status.last_update)}
      </div>
    );
  };

  return (
    <nav
      className="sticky top-0 z-50 backdrop-blur-lg border-b border-border/40 bg-background/95"
      role="navigation"
      aria-label="Main navigation"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-8">
            <Link
              to="/"
              className="text-xl font-bold text-primary focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 rounded"
              aria-label="NBA Stats - Home"
            >
              NBA Stats
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden md:flex space-x-4" role="menubar">
              <Link
                to="/teams"
                className="nav-link"
                role="menuitem"
                onClick={closeMobileMenu}
              >
                Teams
              </Link>
              <Link
                to="/players"
                className="nav-link"
                role="menuitem"
                onClick={closeMobileMenu}
              >
                Players
              </Link>
              <Link
                to="/games"
                className="nav-link"
                role="menuitem"
                onClick={closeMobileMenu}
              >
                Games
              </Link>
              <Link
                to="/upcoming-games"
                className="nav-link"
                role="menuitem"
                onClick={closeMobileMenu}
              >
                Upcoming Games
              </Link>
            </div>
          </div>

          <div className="hidden md:flex items-center space-x-4">
            <SearchBar />
            <Link
              to="/settings"
              className="text-muted-foreground hover:text-primary transition-colors"
              title="Settings"
            >
              <svg
                width="20"
                height="20"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <circle cx="12" cy="12" r="3" />
                <path d="M12 1v6m0 6v6m11-7h-6m-6 0H1" />
              </svg>
            </Link>
            <div className="text-right" role="status" aria-live="polite">
              {renderStatusMessage()}
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={toggleMobileMenu}
              className="inline-flex items-center justify-center p-2 rounded-md text-foreground hover:text-primary hover:bg-muted focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
              aria-expanded={isMobileMenuOpen}
              aria-controls="mobile-menu"
              aria-label="Toggle navigation menu"
            >
              <span className="sr-only">Open main menu</span>
              <svg
                className="h-6 w-6"
                stroke="currentColor"
                fill="none"
                viewBox="0 0 24 24"
              >
                <path
                  className={isMobileMenuOpen ? "hidden" : "inline-flex"}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
                <path
                  className={isMobileMenuOpen ? "inline-flex" : "hidden"}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile Navigation Menu */}
        <div
          className={`md:hidden transition-all duration-200 ease-in-out ${
            isMobileMenuOpen
              ? "max-h-96 opacity-100"
              : "max-h-0 opacity-0 overflow-hidden"
          }`}
          id="mobile-menu"
          role="menu"
          aria-label="Mobile navigation menu"
        >
          <div className="px-2 pt-2 pb-3 space-y-1 border-t border-border/40 bg-background/98">
            <Link
              to="/teams"
              className="nav-link block px-3 py-2 text-base"
              role="menuitem"
              onClick={closeMobileMenu}
            >
              Teams
            </Link>
            <Link
              to="/players"
              className="nav-link block px-3 py-2 text-base"
              role="menuitem"
              onClick={closeMobileMenu}
            >
              Players
            </Link>
            <Link
              to="/games"
              className="nav-link block px-3 py-2 text-base"
              role="menuitem"
              onClick={closeMobileMenu}
            >
              Games
            </Link>
            <Link
              to="/upcoming-games"
              className="nav-link block px-3 py-2 text-base"
              role="menuitem"
              onClick={closeMobileMenu}
            >
              Upcoming Games
            </Link>
            <Link
              to="/settings"
              className="nav-link block px-3 py-2 text-base"
              role="menuitem"
              onClick={closeMobileMenu}
            >
              Settings
            </Link>

            {/* Mobile Search and Status */}
            <div className="px-3 py-2 border-t border-border/40 mt-2">
              <SearchBar />
              <div className="mt-2 text-sm" role="status" aria-live="polite">
                {renderStatusMessage()}
              </div>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}
