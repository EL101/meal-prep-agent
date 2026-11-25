import { StyleSheet } from 'react-native';

import { Text, View } from '@/components/Themed';

/**
 * Profile & goals: weekly budget, preferred store, calorie/protein targets,
 * cook days, time per session, servings, equipment, preferences, excluded foods.
 * Backed by GET/PUT /profile.
 */
export default function ProfileScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Profile & goals</Text>
      <Text style={styles.muted}>TODO: form for budget, store, macros, cook days, and excluded foods.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, gap: 8 },
  title: { fontSize: 18, fontWeight: '600' },
  muted: { opacity: 0.6 },
});
