import { config } from './config';
import { requireSupabase } from './supabase';

export type Me = {
  id: string;
  email: string | null;
  created_at: string;
};

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

// Calls the backend with the signed-in user's Supabase access token. The backend verifies it
// against Supabase's JWKS (backend/app/services/auth.py).
export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const { data } = await requireSupabase().auth.getSession();
  const token = data.session?.access_token;
  if (!token) {
    throw new ApiError(401, 'Not signed in');
  }
  const headers = new Headers(init.headers);
  headers.set('Authorization', `Bearer ${token}`);
  headers.set('Accept', 'application/json');

  const response = await fetch(`${config.apiUrl}${path}`, { ...init, headers });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      if (typeof body?.detail === 'string') detail = body.detail;
    } catch {
      // Not JSON; keep the status text.
    }
    throw new ApiError(response.status, detail || `Request failed (${response.status})`);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

// The first call for a new account also creates the backend's user row.
export const getMe = () => apiFetch<Me>('/me');
