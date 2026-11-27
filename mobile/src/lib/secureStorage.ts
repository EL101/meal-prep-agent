import * as SecureStore from 'expo-secure-store';

// Supabase session storage backed by the iOS Keychain, so access and refresh
// tokens are encrypted at rest. A session is larger than the ~2 KB SecureStore recommends per
// value, so it's split across numbered chunks, with the chunk count stored under the key itself.

// Measured in UTF-8 bytes, under the ~2,048-byte limit some iOS versions enforce.
const CHUNK_BYTES = 1800;

const utf8Length = (codePoint: number) =>
  codePoint < 0x80 ? 1 : codePoint < 0x800 ? 2 : codePoint < 0x10000 ? 3 : 4;

// Splits on code-point boundaries, so a multi-byte character or surrogate pair is never cut.
function toChunks(value: string): string[] {
  const chunks: string[] = [];
  let current = '';
  let bytes = 0;
  for (const char of value) {
    const size = utf8Length(char.codePointAt(0)!);
    if (bytes + size > CHUNK_BYTES) {
      chunks.push(current);
      current = '';
      bytes = 0;
    }
    current += char;
    bytes += size;
  }
  chunks.push(current);
  return chunks;
}

const chunkKey = (key: string, i: number) => `${key}.${i}`;

async function chunkCount(key: string): Promise<number> {
  const count = Number(await SecureStore.getItemAsync(key));
  return Number.isInteger(count) && count > 0 ? count : 0;
}

// Deletes from the end, so an interrupted removal leaves the count in place and a retry (or a
// read, which sees a missing chunk and returns null) still knows which chunks may remain.
async function removeChunks(key: string, from: number, to: number) {
  for (let i = to - 1; i >= from; i--) {
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
    const chunks = toChunks(value);
    // The stored count never drops below the chunks that may exist: raise it before writing
    // more chunks, and lower it only after stale ones are gone. An interrupted write then
    // always leaves a count that lets removeItem find every chunk.
    if (chunks.length > previous) {
      await SecureStore.setItemAsync(key, String(chunks.length));
    }
    for (let i = 0; i < chunks.length; i++) {
      await SecureStore.setItemAsync(chunkKey(key, i), chunks[i]);
    }
    await removeChunks(key, chunks.length, previous);
    await SecureStore.setItemAsync(key, String(chunks.length));
  },

  async removeItem(key: string): Promise<void> {
    // Chunks first, count last, so the count survives until every chunk is gone.
    await removeChunks(key, 0, await chunkCount(key));
    await SecureStore.deleteItemAsync(key);
  },
};
