import { StyleSheet } from 'react-native';

import { Text, View } from '@/components/Themed';

const SOURCE_LABEL = {
  receipt: 'from your receipt',
  kroger_estimate: 'Kroger estimate',
  bls_estimate: 'BLS regional estimate',
} as const;

export default function GroceriesScreen() {
  // TODO: load from the current plan's grocery_list and show SOURCE_LABEL next to each price.
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Grocery list</Text>
      <Text style={styles.muted}>
        Prices are labeled by source: {Object.values(SOURCE_LABEL).join(', ')}.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, gap: 8 },
  title: { fontSize: 18, fontWeight: '600' },
  muted: { opacity: 0.6 },
});
