import { memo } from "react";

const LoadingSpinner = memo(function LoadingSpinner({ label }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-full p-8">
      <svg
        className="animate-spin h-8 w-8 text-blue-500 mb-2"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        role="img"
        aria-label="Loading spinner"
      >
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
      </svg>
      {label && <span className="text-sm text-gray-600">{label}</span>}
    </div>
  );
});

export default LoadingSpinner;
