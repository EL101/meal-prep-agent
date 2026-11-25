// Mirrors backend/app/schemas. Keep in sync by hand for now (or generate from /openapi.json later).

export type PriceSource = 'receipt' | 'kroger_estimate' | 'bls_estimate';

export interface InventoryItem {
  id: string;
  name: string;
  quantity: number;
  unit: string;
  expires_on: string | null;
  confidence: number;
  needs_confirmation: boolean;
}

export interface Ingredient {
  name: string;
  quantity: number;
  unit: string;
}

export interface Recipe {
  id: string;
  title: string;
  servings: number;
  calories_per_serving: number;
  protein_g_per_serving: number;
  ingredients: Ingredient[];
  steps: string[];
}

export interface PlannedMeal {
  day: number;
  slot: 'breakfast' | 'lunch' | 'dinner' | 'snack';
  recipe: Recipe;
  locked: boolean;
}

export interface GroceryItem {
  name: string;
  quantity: number;
  unit: string;
  price: number;
  price_source: PriceSource;
}

export interface MealPlan {
  id: string;
  status: 'queued' | 'running' | 'ready' | 'failed';
  week_start: string;
  meals: PlannedMeal[];
  grocery_list: GroceryItem[];
  estimated_total: number;
}

/** Returned when the backend queues a Claude job (plan generation, image scan). */
export interface JobAccepted {
  id: string;
  status: 'queued' | 'running' | 'ready' | 'failed';
}
