import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { NutritionNeeds } from '../types';

interface NutritionSummaryProps {
  totals: { calories: number; protein: number; fat: number; carbs: number; sugar: number };
  nutritionNeeds: NutritionNeeds;
}

const NutritionSummary: React.FC<NutritionSummaryProps> = ({ totals, nutritionNeeds }) => (
  <View style={styles.nutritionTable}>
    {['calories', 'protein', 'carbs', 'fat', 'sugar'].map((key) => (
      <View style={styles.nutritionRow} key={key}>
        <Text style={styles.nutritionLabel}>{key.charAt(0).toUpperCase() + key.slice(1)}{key !== 'calories' ? ' (g)' : ''}</Text>
        <View style={styles.nutritionValuesContainer}>
          <Text style={[styles.nutritionValue, styles.nutritionValueColumn]}>
            {totals[key as keyof typeof totals].toFixed(0)}/{nutritionNeeds[key as keyof typeof nutritionNeeds]}
          </Text>
          <Text style={[
            totals[key as keyof typeof totals] < nutritionNeeds[key as keyof typeof nutritionNeeds]
              ? styles.pos_remaining
              : styles.neg_remaining,
            styles.nutritionValueColumn,
          ]}>
            {Math.round(nutritionNeeds[key as keyof typeof nutritionNeeds] - totals[key as keyof typeof totals])}
          </Text>
        </View>
      </View>
    ))}
  </View>
);

const styles = StyleSheet.create({
  nutritionTable: { marginBottom: 16, borderWidth: 1, borderColor: '#ccc', borderRadius: 4, padding: 8 },
  nutritionRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 4 },
  nutritionLabel: { fontSize: 16, fontWeight: '600' },
  nutritionValue: { fontSize: 16 },
  nutritionValuesContainer: { flexDirection: 'row', justifyContent: 'flex-end', width: 160 },
  nutritionValueColumn: { flex: 1, textAlign: 'right' },
  neg_remaining: { fontSize: 16, color: 'red' },
  pos_remaining: { fontSize: 16, color: 'green' },
});

export default NutritionSummary;
