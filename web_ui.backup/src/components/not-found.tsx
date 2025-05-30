// src/components/not-found.tsx
export default function NotFound() {
  return (
    <div className="flex h-full flex-col items-center justify-center gap-4">
      <h1 className="text-3xl font-bold">404</h1>
      <p className="text-muted-foreground">Page not found</p>
    </div>
  );
}
