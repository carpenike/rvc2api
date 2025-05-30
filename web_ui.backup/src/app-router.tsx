// src/app-router.tsx
import { router } from "@/lib/router";
import {
  RouterProvider,
} from "react-router-dom";

export function AppRouter() {
  return <RouterProvider router={router} />;
}
