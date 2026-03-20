const getApiUrl = (): string => {
  const envUrl = import.meta.env.VITE_API_URL;
  if (envUrl) {
    return envUrl;
  }

  if (typeof window !== "undefined") {
    const { protocol, hostname } = window.location;
    const localHosts = new Set(["localhost", "127.0.0.1"]);
    if (!localHosts.has(hostname)) {
      if (hostname === "www.servantx.ai" || hostname === "servantx.ai") {
        return `${protocol}//api.servantx.ai`;
      }

      if (hostname.startsWith("app.")) {
        return `${protocol}//${hostname.replace(/^app\./, "api.")}`;
      }
    }
  }

  return "http://localhost:8000";
};

export const API_BASE_URL = getApiUrl();

export interface ContactFormData {
  orgName: string;
  state: string;
  contactName: string;
  role: string;
  email: string;
  phone?: string;
  revenue: string;
  hospitalType?: string[];
  interestAreas: string[];
  payers?: string;
  timeframe: string;
  approval: string;
  nextStep: string;
  additionalInfo?: string;
}

export interface GeneralContactFormData {
  name: string;
  email: string;
  subject: string;
  message: string;
}

export async function submitContactForm(data: ContactFormData): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/contact`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(
      errorText ||
        `Failed to submit contact form: ${response.status} ${response.statusText}`
    );
  }
}

export async function submitGeneralContactForm(data: GeneralContactFormData): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/contact/general`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(
      errorText ||
        `Failed to submit contact form: ${response.status} ${response.statusText}`
    );
  }
}
