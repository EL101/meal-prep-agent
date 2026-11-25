import { useState } from 'react';
import { Button, FlatList, StyleSheet } from 'react-native';

import { Text, View } from '@/components/Themed';
import { api } from '@/lib/api';
import type { MealPlan } from '@/lib/types';

const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];

export default function PlanScreen() {
  const [plan, setPlan] = useState<MealPlan | null>(null);
  const [status, setStatus] = useState<string | null>(null);

  async function generate() {
    try {
      setStatus('Queuing plan…');
      const job = await api.generatePlan();
      // TODO: poll or subscribe (Supabase realtime) until status === 'ready'.
      setStatus(`Plan ${job.id} is ${job.status}`);
      const latest = await api.getPlan(job.id);
      setPlan(latest);
    } catch (e) {
      setStatus(String(e));
    }
  }

  return (
    <View style={styles.container}>
      <Button title="Generate this week's plan" onPress={generate} />
      {status && <Text style={styles.muted}>{status}</Text>}
      <FlatList
        data={plan?.meals ?? []}
        keyExtractor={(m) => `${m.day}-${m.slot}`}
        renderItem={({ item }) => (
          <View style={styles.row}>
            <Text style={styles.day}>
              {DAYS[item.day]} · {item.slot}
            </Text>
            <Text>{item.recipe.title}</Text>
            <Text style={styles.muted}>
              {item.recipe.calories_per_serving} kcal · {item.recipe.protein_g_per_serving} g protein
            </Text>
            {/* TODO: lock/swap buttons → PATCH /plans/{id} and re-solve; 1–5 star rating. */}
          </View>
        )}
        ListEmptyComponent={<Text style={styles.muted}>No plan yet.</Text>}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, gap: 12 },
  row: { paddingVertical: 10, borderBottomWidth: StyleSheet.hairlineWidth, borderColor: '#8884' },
  day: { fontWeight: '600' },
  muted: { opacity: 0.6 },
});
