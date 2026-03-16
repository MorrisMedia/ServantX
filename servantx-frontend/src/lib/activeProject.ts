const ACTIVE_PROJECT_KEY = 'servantx_active_project_id';

export function getActiveProjectId(): string | null {
  if (typeof window === 'undefined') return null;
  return window.localStorage.getItem(ACTIVE_PROJECT_KEY);
}

export function setActiveProjectId(projectId: string): void {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem(ACTIVE_PROJECT_KEY, projectId);
}

export function clearActiveProjectId(): void {
  if (typeof window === 'undefined') return;
  window.localStorage.removeItem(ACTIVE_PROJECT_KEY);
}
