export interface User {
  id: string;
  email: string;
  name?: string;
  hospitalId: string;
  hospitalName?: string;
  role?: string;
  hasContract?: boolean;
  isAdmin?: boolean;
  createdAt: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  name: string;
  hospitalName: string;
  phone: string;
  password: string;
  confirmPassword: string;
}

export interface AuthResponse {
  user: User;
  access_token: string;
  refresh_token?: string;
  token_type?: string;
  message?: string;
}

// Helper to map backend response to frontend format
export function mapAuthResponse(data: any): { user: User; accessToken: string; refreshToken?: string } {
  // Handle both snake_case (backend) and camelCase formats
  const user = data.user || {};
  return {
    user: {
      id: user.id || "",
      email: user.email || "",
      name: user.name,
      hospitalId: user.hospitalId || user.hospital_id || "",
      hospitalName: user.hospitalName || user.hospital_name,
      role: user.role,
      hasContract: user.hasContract ?? user.has_contract ?? false,
      isAdmin: user.isAdmin ?? user.is_admin ?? false,
      createdAt: user.createdAt || user.created_at || new Date().toISOString(),
    },
    accessToken: data.access_token || data.accessToken || "",
    refreshToken: data.refresh_token || data.refreshToken,
  };
}

export interface ForgotPasswordData {
  email: string;
}

export interface ResetPasswordData {
  token: string;
  newPassword: string;
  confirmPassword: string;
}

export interface ChangePasswordData {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}

