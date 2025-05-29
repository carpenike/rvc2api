import React from "react";

export const ThemeTest: React.FC = () => {
  return (
    <div className="p-4 space-y-4 border rounded-lg">
      <h2 className="text-xl font-bold">Theme Test Component</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-background text-foreground p-4 border rounded">
          <p>Background/Foreground</p>
          <p className="text-sm text-muted-foreground">Muted text</p>
        </div>
        <div className="bg-card text-card-foreground p-4 border rounded">
          <p>Card Background/Foreground</p>
        </div>
        <div className="bg-primary text-primary-foreground p-4 rounded">
          <p>Primary Background/Foreground</p>
        </div>
      </div>
      <div className="mt-4">
        <p>CSS Variables Test:</p>
        <div
          style={{
            backgroundColor: "hsl(var(--background))",
            color: "hsl(var(--foreground))",
            padding: "1rem",
            border: "1px solid hsl(var(--border))"
          }}
        >
          Direct CSS variables
        </div>
      </div>
    </div>
  );
};
