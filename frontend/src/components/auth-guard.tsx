import { useEffect } from "react"
import { useLocation, useNavigate } from "react-router-dom"

import { useAuth } from "@/contexts"

interface AuthGuardProps {
  children: React.ReactNode
}

/**
 * AuthGuard component that protects routes by checking authentication status.
 * Redirects unauthenticated users to the login page.
 */
export function AuthGuard({ children }: AuthGuardProps) {
  const navigate = useNavigate()
  const location = useLocation()
  const { isAuthenticated, authStatus, isLoading } = useAuth()

  useEffect(() => {
    // Don't redirect while still loading auth status
    if (isLoading || !authStatus) {
      return
    }

    // If auth is disabled (mode: "none"), allow access
    if (authStatus.mode === "none") {
      return
    }

    // If user is not authenticated and auth is required, redirect to login
    if (!isAuthenticated) {
      // Save the current location so we can redirect back after login
      navigate("/login", {
        replace: true,
        state: { from: location.pathname }
      })
    }
  }, [isAuthenticated, authStatus, isLoading, navigate, location.pathname])

  // Show loading while checking authentication
  if (isLoading || !authStatus) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary" />
      </div>
    )
  }

  // If auth is disabled, render children immediately
  if (authStatus.mode === "none") {
    return children
  }

  // If authenticated, render children
  if (isAuthenticated) {
    return children
  }

  // If not authenticated, don't render anything (will redirect to login)
  return null
}
