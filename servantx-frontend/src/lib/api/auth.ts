import { API_BASE_URL } from "../api";
import type { LoginCredentials, RegisterData, AuthResponse, User, ForgotPasswordData, ResetPasswordData, ChangePasswordData } from "../types/auth";
import { getAccessToken, setAccessToken, removeAccessToken, setRefreshToken, getRefreshToken, removeRefreshToken, removeAllTokens } from "./token";
import { mapAuthResponse } from "../types/auth";

/**
 * Get authorization header with Bearer token
 */
function getAuthHeaders(): HeadersInit {
  const token = getAccessToken();
  return {
    "Content-Type": "application/json",
    ...(token && { Authorization: `Bearer ${token}` }),
  };
}

/**
 * Login with email and password
 */
export async function login(credentials: LoginCredentials): Promise<AuthResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(credentials),
  });

  if (!response.ok) {
    let errorMessage = `Login failed: ${response.status}`;
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch {
      const errorText = await response.text();
      errorMessage = errorText || errorMessage;
    }
    throw new Error(errorMessage);
  }

  const responseData = await response.json();
  const mapped = mapAuthResponse(responseData);
  
  // Store tokens
  if (mapped.accessToken) {
    setAccessToken(mapped.accessToken);
  }
  if (mapped.refreshToken) {
    setRefreshToken(mapped.refreshToken);
  }
  
  return {
    user: mapped.user,
    accessToken: mapped.accessToken,
    refreshToken: mapped.refreshToken,
  };
}

/**
 * Register with email and password
 */
export async function register(data: RegisterData): Promise<AuthResponse> {
  try {
    console.log("🔵 [FRONTEND] Register function called with data:", data);
    console.log("🔵 [FRONTEND] Data types:", {
      email: typeof data.email,
      name: typeof data.name,
      hospitalName: typeof data.hospitalName,
      phone: typeof data.phone,
      password: typeof data.password,
      confirmPassword: typeof data.confirmPassword,
    });

    // Transform camelCase to snake_case for backend
    const requestData = {
      email: data.email,
      name: data.name,
      hospital_name: data.hospitalName,
      phone: data.phone,
      password: data.password,
      confirm_password: data.confirmPassword,
    };

    console.log("🔵 [FRONTEND] Transformed request data:", requestData);
    console.log("🔵 [FRONTEND] API_BASE_URL:", API_BASE_URL);
    console.log("🔵 [FRONTEND] Full URL:", `${API_BASE_URL}/auth/register`);
    console.log("🔵 [FRONTEND] Request body (stringified):", JSON.stringify(requestData));

    console.log("🔵 [FRONTEND] Making fetch request...");
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestData),
    });
    console.log("🔵 [FRONTEND] Fetch request completed");

  console.log("🔵 [FRONTEND] Response status:", response.status);
  console.log("🔵 [FRONTEND] Response ok:", response.ok);

  if (!response.ok) {
    console.error("🔴 [FRONTEND] Registration failed with status:", response.status);
    let errorMessage = `Registration failed: ${response.status}`;
    try {
      const errorData = await response.json();
      console.error("🔴 [FRONTEND] Error response data:", errorData);
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch (e) {
      console.error("🔴 [FRONTEND] Failed to parse error JSON:", e);
      const errorText = await response.text();
      console.error("🔴 [FRONTEND] Error response text:", errorText);
      errorMessage = errorText || errorMessage;
    }
    throw new Error(errorMessage);
  }

    console.log("🟢 [FRONTEND] Registration successful, parsing response...");
    const responseData = await response.json();
    console.log("🟢 [FRONTEND] Response data:", responseData);
    const mapped = mapAuthResponse(responseData);
    console.log("🟢 [FRONTEND] Mapped response:", mapped);
    
    // Store tokens
    if (mapped.accessToken) {
      setAccessToken(mapped.accessToken);
    }
    if (mapped.refreshToken) {
      setRefreshToken(mapped.refreshToken);
    }
    
    return {
      user: mapped.user,
      accessToken: mapped.accessToken,
      refreshToken: mapped.refreshToken,
    };
  } catch (error) {
    console.error("🔴 [FRONTEND] Error in register function:", error);
    if (error instanceof Error) {
      console.error("🔴 [FRONTEND] Error message:", error.message);
      console.error("🔴 [FRONTEND] Error stack:", error.stack);
    }
    throw error;
  }
}

/**
 * Logout - clear token
 */
export async function logout(): Promise<void> {
  const token = getAccessToken();
  
  if (token) {
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: "POST",
        headers: getAuthHeaders(),
      });
    } catch (error) {
      console.error("Logout error:", error);
    }
  }
  
  removeAllTokens();
}

/**
 * Get current authenticated user
 */
export async function getCurrentUser(): Promise<User | null> {
  try {
    const token = getAccessToken();
    if (!token) {
      return null;
    }

    const response = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: getAuthHeaders(),
    });
    
    if (response.status === 401) {
      removeAllTokens();
      return null;
    }
    
    if (!response.ok) {
      throw new Error(`Failed to get current user: ${response.status}`);
    }
    
    const userData = await response.json();
    // Map snake_case to camelCase
    return {
      id: userData.id || "",
      email: userData.email || "",
      name: userData.name,
      hospitalId: userData.hospital_id || userData.hospitalId || "",
      hospitalName: userData.hospital_name || userData.hospitalName,
      role: userData.role,
      hasContract: userData.has_contract ?? userData.hasContract ?? false,
      createdAt: userData.created_at || userData.createdAt || new Date().toISOString(),
    };
  } catch (error) {
    console.error("Error fetching current user:", error);
    removeAllTokens();
    return null;
  }
}

/**
 * Refresh access token
 */
export async function refreshAccessToken(): Promise<string | null> {
  try {
    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      return null;
    }

    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      removeAllTokens();
      return null;
    }

    const data = await response.json();
    if (data.access_token || data.accessToken) {
      const token = data.access_token || data.accessToken;
      setAccessToken(token);
      return token;
    }

    return null;
  } catch (error) {
    console.error("Token refresh error:", error);
    removeAllTokens();
    return null;
  }
}

/**
 * Forgot password - send reset email
 */
export async function forgotPassword(data: ForgotPasswordData): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/auth/forgot-password`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    let errorMessage = `Failed to send reset email: ${response.status}`;
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch {
      const errorText = await response.text();
      errorMessage = errorText || errorMessage;
    }
    throw new Error(errorMessage);
  }
}

/**
 * Reset password with token
 */
export async function resetPassword(data: ResetPasswordData): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/auth/reset-password`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    let errorMessage = `Failed to reset password: ${response.status}`;
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch {
      const errorText = await response.text();
      errorMessage = errorText || errorMessage;
    }
    throw new Error(errorMessage);
  }
}

/**
 * Change password (for authenticated users)
 */
export async function changePassword(data: ChangePasswordData): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/auth/change-password`, {
    method: "POST",
    headers: getAuthHeaders(),
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    let errorMessage = `Failed to change password: ${response.status}`;
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch {
      const errorText = await response.text();
      errorMessage = errorText || errorMessage;
    }
    throw new Error(errorMessage);
  }
}

/**
 * Update hasContract field (temporary endpoint for testing)
 */
export async function updateHasContract(hasContract: boolean): Promise<User> {
  const response = await fetch(`${API_BASE_URL}/auth/update-has-contract`, {
    method: "PATCH",
    headers: getAuthHeaders(),
    body: JSON.stringify({ has_contract: hasContract }),
  });

  if (!response.ok) {
    let errorMessage = `Failed to update hasContract: ${response.status}`;
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch {
      const errorText = await response.text();
      errorMessage = errorText || errorMessage;
    }
    throw new Error(errorMessage);
  }

  const userData = await response.json();
  // Map snake_case to camelCase
  return {
    id: userData.id || "",
    email: userData.email || "",
    name: userData.name,
    hospitalId: userData.hospital_id || userData.hospitalId || "",
    hospitalName: userData.hospital_name || userData.hospitalName,
    role: userData.role,
    hasContract: userData.has_contract ?? userData.hasContract ?? false,
    createdAt: userData.created_at || userData.createdAt || new Date().toISOString(),
  };
}

