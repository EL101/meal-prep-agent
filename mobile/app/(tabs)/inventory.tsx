import * as ImagePicker from 'expo-image-picker';
import { useCallback, useEffect, useState } from 'react';
import { Button, FlatList, StyleSheet } from 'react-native';

import { Text, View } from '@/components/Themed';
import { api } from '@/lib/api';
import type { InventoryItem } from '@/lib/types';

type ScanKind = 'fridge' | 'pantry' | 'receipt';

export default function InventoryScreen() {
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [message, setMessage] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setItems(await api.listInventory());
    } catch (e) {
      setMessage(String(e));
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function scan(kind: ScanKind) {
    const perm = await ImagePicker.requestCameraPermissionsAsync();
    if (!perm.granted) return setMessage('Camera permission is needed to scan.');
    const result = await ImagePicker.launchCameraAsync({ quality: 0.7 });
    if (result.canceled) return;
    const job = await api.uploadInventoryImage(result.assets[0].uri, kind);
    setMessage(`Scan ${job.id} ${job.status}. Items you need to confirm will be flagged.`);
  }

  return (
    <View style={styles.container}>
      <View style={styles.buttons}>
        <Button title="Fridge" onPress={() => scan('fridge')} />
        <Button title="Pantry" onPress={() => scan('pantry')} />
        <Button title="Receipt" onPress={() => scan('receipt')} />
      </View>
      {message && <Text style={styles.muted}>{message}</Text>}
      <FlatList
        data={items}
        keyExtractor={(i) => i.id}
        onRefresh={refresh}
        refreshing={false}
        renderItem={({ item }) => (
          <View style={styles.row}>
            <Text>
              {item.name} · {item.quantity} {item.unit}
              {item.needs_confirmation ? '  (confirm?)' : ''}
            </Text>
            {item.expires_on && <Text style={styles.muted}>Expires {item.expires_on}</Text>}
          </View>
        )}
        ListEmptyComponent={<Text style={styles.muted}>Scan your fridge, pantry, or a receipt.</Text>}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, gap: 12 },
  buttons: { flexDirection: 'row', justifyContent: 'space-around' },
  row: { paddingVertical: 10, borderBottomWidth: StyleSheet.hairlineWidth, borderColor: '#8884' },
  muted: { opacity: 0.6 },
});
