import { supabase } from './supabase';
import type { InventoryItem, JobAccepted, MealPlan } from './types';

const API_URL = process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000';

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  const headers = new Headers(init.headers);
  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData)) headers.set('Content-Type', 'application/json');

  const res = await fetch(`${API_URL}${path}`, { ...init, headers });
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return (await res.json()) as T;
}

export const api = {
  health: () => request<{ status: string }>('/health'),

  listInventory: () => request<InventoryItem[]>('/inventory'),

  /** Upload a fridge/pantry photo or grocery receipt for Claude to read. */
  uploadInventoryImage: (uri: string, kind: 'fridge' | 'pantry' | 'receipt') => {
    const form = new FormData();
    // React Native's FormData accepts { uri, name, type } objects.
    form.append('file', { uri, name: `${kind}.jpg`, type: 'image/jpeg' } as unknown as Blob);
    form.append('kind', kind);
    return request<JobAccepted>('/inventory/scan', { method: 'POST', body: form });
  },

  generatePlan: () => request<JobAccepted>('/plans', { method: 'POST', body: '{}' }),

  getPlan: (id: string) => request<MealPlan>(`/plans/${id}`),

  rateRecipe: (recipeId: string, stars: number, comment?: string) =>
    request(`/recipes/${recipeId}/ratings`, {
      method: 'POST',
      body: JSON.stringify({ stars, comment }),
    }),
};
