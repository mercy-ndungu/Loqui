interface LoadingSpinnerProps {
  className?: string;
  size?: "sm" | "md" | "lg";
}

const sizes = { sm: "h-4 w-4 border-2", md: "h-6 w-6 border-2", lg: "h-10 w-10 border-[3px]" };

export default function LoadingSpinner({ className = "", size = "md" }: LoadingSpinnerProps) {
  return (
    <div
      className={`inline-block animate-spin rounded-full border-primary border-t-transparent ${sizes[size]} ${className}`}
      role="status"
      aria-label="Loading"
    />
  );
}
