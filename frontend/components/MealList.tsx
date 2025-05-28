import React from 'react';
import { FlatList, View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { MealEntry } from '../types';
import ReanimatedSwipeable from 'react-native-gesture-handler/ReanimatedSwipeable';

interface MealListProps {
  meals: MealEntry[];
  onDeleteMeal?: (id: string) => void;
}

const renderRightActions = (id: string, onDeleteMeal?: (id: string) => void) => (
  <TouchableOpacity
    style={styles.deleteButton}
    onPress={() => onDeleteMeal && onDeleteMeal(id)}
  >
    <Text style={styles.deleteButtonText}>🗑️</Text>
  </TouchableOpacity>
);

const MealList: React.FC<MealListProps> = ({ meals, onDeleteMeal }) => (
  <FlatList
    data={meals}
    keyExtractor={(item) => item.id.toString()}
    renderItem={({ item }) => (
      <ReanimatedSwipeable
        renderRightActions={() => renderRightActions(item.id, onDeleteMeal)}
      >
        <View style={styles.mealItem}>
          <View style={{ flex: 1 }}>
            <Text style={styles.mealDescription}>{item.description}</Text>
            <Text style={styles.mealNutrition}>
              Calories: {item.calories.toFixed(0)}, Protein: {item.protein?.toFixed(0)}, Fiber: {item.fiber?.toFixed(0)},
              Carbs: {item.carbs?.toFixed(0)}, Fat: {item.fat?.toFixed(0)},
              Sugar: {item.sugar?.toFixed(0)}
            </Text>
          </View>
        </View>
      </ReanimatedSwipeable>
    )}
    ListEmptyComponent={<Text style={styles.emptyText}>No meals logged for this date.</Text>}
  />
);

const styles = StyleSheet.create({
  mealItem: { 
    flexDirection: 'row', 
    alignItems: 'center', 
    padding: 12, 
    borderBottomColor: '#eee', 
    borderBottomWidth: 1,
    backgroundColor: '#fff'
  },
  mealDescription: { fontSize: 16, fontWeight: '500' },
  mealNutrition: { fontSize: 14, color: '#555' },
  emptyText: { textAlign: 'center', color: '#999', marginTop: 20 },
  deleteButton: {
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F44336',
    width: 80,
    height: '100%',
  },
  deleteButtonText: {
    color: 'white',
    fontSize: 24,
    fontWeight: 'bold',
  },
});

export default MealList;
