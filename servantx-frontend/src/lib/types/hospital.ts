export interface Hospital {
  id: string;
  name: string;
  email?: string;
  phone?: string;
  address?: string;
  state?: string;
  createdAt: string;
  updatedAt: string;
}

export interface HospitalSettings {
  hospital: Hospital;
  preferences?: {
    notifications?: boolean;
    defaultContract?: string;
  };
}

export type PricingMode = "AUTO" | "MEDICARE" | "MEDICAID" | "CONTRACT" | "ALL";

export interface HospitalPricingConfig {
  hospital_id: string;
  pricing_mode: PricingMode;
  state: string;
}



