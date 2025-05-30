import { Button } from "@/components/ui/button"; // shadcn
import { useState } from "react";
import reactLogo from "./assets/react.svg";
import viteLogo from "/vite.svg";

export default function App() {
  const [count, setCount] = useState(0);

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-8 bg-background text-foreground">
      {/* logos */}
      <div className="flex gap-8">
        <a href="https://vite.dev" target="_blank">
          <img src={viteLogo} className="h-24 w-24 transition-all hover:drop-shadow-[0_0_2rem_var(--primary)]" />
        </a>
        <a href="https://react.dev" target="_blank">
          <img src={reactLogo} className="h-24 w-24 animate-spin-slow" />
        </a>
      </div>

      {/* heading */}
      <h1 className="text-4xl font-bold">Vite + React + Tailwind v4</h1>

      {/* counter */}
      <div className="rounded-xl border p-8 shadow">
        <Button onClick={() => setCount((c) => c + 1)} size="lg">
          Count is&nbsp;{count}
        </Button>
        <p className="mt-4 text-sm">
          Edit <code className="font-mono">src/App.tsx</code> and save to test&nbsp;HMR
        </p>
      </div>

      <p className="text-sm opacity-70">
        Click the logos to learn more
      </p>
    </main>
  );
}
