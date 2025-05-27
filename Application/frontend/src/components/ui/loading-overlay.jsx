import { LoadingSpinner } from "./loading-spinner";

export function LoadingOverlay({ progress, isLoading, children }) {
  return (
    <div className="relative">
      {children}
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-background/60 backdrop-blur-sm rounded-full">
          <div className="flex flex-col items-center space-y-2">
            <LoadingSpinner size="default" className="text-primary" />
            {progress != null && (
              <span className="text-lg font-bold text-primary tracking-wider">
                {Math.round(progress)}%
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
