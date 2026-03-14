/**
 * Authentication Flow Utility Functions
 * 
 * Complete flow:
 * 1. User registers -> automatically logged in -> redirected to dashboard
 * 2. User logs in -> redirected to dashboard
 * 3. If already authenticated, login/register pages redirect to dashboard
 */

import { register, login, getCurrentUser } from "../api/auth";
import type { RegisterData, LoginCredentials, User } from "../types/auth";

/**
 * Complete registration flow
 * - Registers the user
 * - Automatically logs them in
 * - Returns user data for context update
 */
export async function registerAndLogin(data: RegisterData): Promise<User> {
  try {
    // Step 1: Register the user
    const registerResponse = await register(data);
    
    // Step 2: User is automatically logged in after registration
    // The backend should set the JWT cookie
    const user = registerResponse.user;
    
    // Step 3: Verify user is authenticated
    const currentUser = await getCurrentUser();
    if (!currentUser) {
      throw new Error("Registration successful but authentication failed");
    }
    
    return currentUser;
  } catch (error) {
    console.error("Registration error:", error);
    throw error;
  }
}

/**
 * Complete login flow
 * - Authenticates the user
 * - Returns user data for context update
 */
export async function loginUser(credentials: LoginCredentials): Promise<User> {
  try {
    // Step 1: Login the user (backend sets JWT cookie)
    const loginResponse = await login(credentials);
    
    // Step 2: Verify user is authenticated
    const currentUser = await getCurrentUser();
    if (!currentUser) {
      throw new Error("Login successful but authentication verification failed");
    }
    
    return currentUser;
  } catch (error) {
    console.error("Login error:", error);
    throw error;
  }
}

/**
 * Check if user is authenticated
 * Useful for route protection
 */
export async function checkAuth(): Promise<User | null> {
  try {
    return await getCurrentUser();
  } catch (error) {
    console.error("Auth check error:", error);
    return null;
  }
}



