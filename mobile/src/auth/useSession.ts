import type { Session } from '@supabase/supabase-js';
import { useEffect, useState } from 'react';

import { supabase } from '../lib/supabase';

/** The current Supabase session, restored from storage on launch. `loading` until then. */
export function useSession() {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(Boolean(supabase));

  useEffect(() => {
    if (!supabase) return;
    // onAuthStateChange fires INITIAL_SESSION with whatever was in storage, then every
    // sign-in, refresh and sign-out after that.
    const { data } = supabase.auth.onAuthStateChange((_event, next) => {
      setSession(next);
      setLoading(false);
    });
    return () => data.subscription.unsubscribe();
  }, []);

  return { session, loading };
}
