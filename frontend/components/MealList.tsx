import React from 'react';
import { FlatList, View, Text, StyleSheet } from 'react-native';
import { MealEntry } from '../types';

interface MealListProps {
  meals: MealEntry[];
}

const MealList: React.FC<MealListProps> = ({ meals }) => (
  <FlatList
    data={meals}
    keyExtractor={(item) => item.id.toString()}
    renderItem={({ item }) => (
      <View style={styles.mealItem}>
        <Text style={styles.mealDescription}>{item.description}</Text>
        <Text style={styles.mealNutrition}>
          Calories: {item.calories.toFixed(0)}, Protein: {item.protein?.toFixed(0)},
          Carbs: {item.carbs?.toFixed(0)}, Fat: {item.fat?.toFixed(0)},
          Sugar: {item.sugar?.toFixed(0)}
        </Text>
      </View>
    )}
    ListEmptyComponent={<Text style={styles.emptyText}>No meals logged for this date.</Text>}
  />
);

const styles = StyleSheet.create({
  mealItem: { padding: 12, borderBottomColor: '#eee', borderBottomWidth: 1 },
  mealDescription: { fontSize: 16, fontWeight: '500' },
  mealNutrition: { fontSize: 14, color: '#555' },
  emptyText: { textAlign: 'center', color: '#999', marginTop: 20 },
});

export default MealList;
