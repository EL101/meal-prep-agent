import * as SecureStore from 'expo-secure-store';

// Supabase session storage backed by the iOS Keychain / Android Keystore, so access and refresh
// tokens are encrypted at rest. A session is larger than the ~2 KB SecureStore recommends per
// value, so it's split across numbered chunks. The key itself holds a small index naming which
// set of chunks is current.

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

// Each write goes to a fresh generation ('a' or 'b', alternating) and only then switches the
// index to it, so a read sees either the old value or the new one, never chunks from both.
// '' is the format before generations, whose chunks are `${key}.${i}`.
type Gen = '' | 'a' | 'b';
type Index = {
  current: [Gen, number] | null;
  // Chunk sets that may still exist and should be deleted: an old generation, or a write that
  // was interrupted. Recorded before chunks are written, so removeItem can always find them.
  stale: [Gen, number][];
};

const chunkKey = (key: string, gen: Gen, i: number) => (gen ? `${key}.${gen}.${i}` : `${key}.${i}`);

async function readIndex(key: string): Promise<Index> {
  const raw = await SecureStore.getItemAsync(key);
  if (!raw) return { current: null, stale: [] };
  const legacy = Number(raw);
  if (Number.isInteger(legacy)) return { current: legacy > 0 ? ['', legacy] : null, stale: [] };
  try {
    const index = JSON.parse(raw) as Index;
    return { current: index.current ?? null, stale: index.stale ?? [] };
  } catch {
    return { current: null, stale: [] };
  }
}

// One entry per generation, keeping the highest count, so the index stays small.
function merge(sets: [Gen, number][]): [Gen, number][] {
  const most = new Map<Gen, number>();
  for (const [gen, count] of sets) most.set(gen, Math.max(count, most.get(gen) ?? 0));
  return [...most];
}

const writeIndex = (key: string, index: Index) =>
  SecureStore.setItemAsync(key, JSON.stringify(index));

// Deletes from the end, so an interrupted removal leaves earlier chunks for the next retry.
async function removeChunks(key: string, gen: Gen, from: number, to: number) {
  for (let i = to - 1; i >= from; i--) {
    await SecureStore.deleteItemAsync(chunkKey(key, gen, i));
  }
}

export const secureStorage = {
  async getItem(key: string): Promise<string | null> {
    const { current } = await readIndex(key);
    if (!current) return null;
    const [gen, count] = current;
    const parts: string[] = [];
    for (let i = 0; i < count; i++) {
      const part = await SecureStore.getItemAsync(chunkKey(key, gen, i));
      if (part === null) return null; // Damaged value: treat as signed out.
      parts.push(part);
    }
    return parts.join('');
  },

  async setItem(key: string, value: string): Promise<void> {
    const { current, stale } = await readIndex(key);
    const gen: Gen = current?.[0] === 'a' ? 'b' : 'a';
    const chunks = toChunks(value);

    // 1. Note that this generation's chunks are about to exist, then write them. The index
    //    still points at the old value, so an interruption here leaves it readable.
    await writeIndex(key, { current, stale: merge([...stale, [gen, chunks.length]]) });
    for (let i = 0; i < chunks.length; i++) {
      await SecureStore.setItemAsync(chunkKey(key, gen, i), chunks[i]);
    }

    // 2. Switch to the new value in one write; the old chunks become stale.
    const leftovers = merge([...stale, ...(current ? [current] : [])]);
    await writeIndex(key, { current: [gen, chunks.length], stale: leftovers });

    // 3. Clean up. Chunks of this generation below chunks.length are the live ones.
    for (const [staleGen, count] of leftovers) {
      await removeChunks(key, staleGen, staleGen === gen ? chunks.length : 0, count);
    }
    await writeIndex(key, { current: [gen, chunks.length], stale: [] });
  },

  async removeItem(key: string): Promise<void> {
    // Chunks first, index last, so the index survives until every chunk is gone.
    const { current, stale } = await readIndex(key);
    for (const [gen, count] of [...stale, ...(current ? [current] : [])]) {
      await removeChunks(key, gen, 0, count);
    }
    await SecureStore.deleteItemAsync(key);
  },
};
