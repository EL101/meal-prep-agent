import * as SecureStore from 'expo-secure-store';

// Supabase session storage backed by the iOS Keychain / Android Keystore, so access and refresh
// tokens are encrypted at rest. A session is larger than the ~2 KB SecureStore recommends per
// value, so it's split across numbered chunks, with the chunk count stored under the key itself.

const CHUNK_SIZE = 1800;

const chunkKey = (key: string, i: number) => `${key}.${i}`;

async function chunkCount(key: string): Promise<number> {
  const count = Number(await SecureStore.getItemAsync(key));
  return Number.isInteger(count) && count > 0 ? count : 0;
}

async function removeChunks(key: string, from: number, to: number) {
  for (let i = from; i < to; i++) {
    await SecureStore.deleteItemAsync(chunkKey(key, i));
  }
}

export const secureStorage = {
  async getItem(key: string): Promise<string | null> {
    const count = await chunkCount(key);
    if (count === 0) return null;
    const parts: string[] = [];
    for (let i = 0; i < count; i++) {
      const part = await SecureStore.getItemAsync(chunkKey(key, i));
      if (part === null) return null; // Half-written value: treat as signed out.
      parts.push(part);
    }
    return parts.join('');
  },

  async setItem(key: string, value: string): Promise<void> {
    const previous = await chunkCount(key);
    const count = Math.max(1, Math.ceil(value.length / CHUNK_SIZE));
    for (let i = 0; i < count; i++) {
      await SecureStore.setItemAsync(chunkKey(key, i), value.slice(i * CHUNK_SIZE, (i + 1) * CHUNK_SIZE));
    }
    await SecureStore.setItemAsync(key, String(count));
    await removeChunks(key, count, previous);
  },

  async removeItem(key: string): Promise<void> {
    const count = await chunkCount(key);
    await SecureStore.deleteItemAsync(key);
    await removeChunks(key, 0, count);
  },
};
