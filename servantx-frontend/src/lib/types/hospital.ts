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



