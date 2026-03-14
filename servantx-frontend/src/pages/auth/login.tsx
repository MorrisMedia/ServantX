import { useEffect } from "react";
import { useLocation } from "wouter";
import { LoginForm } from "@/components/auth/LoginForm";
import { Logo } from "@/components/servantx/Header";
import { useAuth } from "@/lib/hooks/useAuth";

export default function LoginPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const [, setLocation] = useLocation();

  // Don't auto-redirect - let user stay on login page even if authenticated
  // They can manually navigate to dashboard if needed

  // Show loading while checking auth status
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  // Show message if already authenticated, but still show login form
  const showAuthenticatedMessage = isAuthenticated;

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-md space-y-8">
        <div className="flex justify-center">
          <Logo />
        </div>
        {showAuthenticatedMessage && (
          <div className="rounded-md bg-green-50 dark:bg-green-950 p-4 text-sm text-green-700 dark:text-green-300 border border-green-200 dark:border-green-800">
            <p className="font-medium">You are already logged in.</p>
            <p className="mt-1">
              <a href="/dashboard" className="underline">Go to Dashboard</a> or continue below.
            </p>
          </div>
        )}
        <LoginForm />
      </div>
    </div>
  );
}

