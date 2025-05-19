import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface ConversationHistoryProps {
  conversationHistory: string[];
}

const ConversationHistory: React.FC<ConversationHistoryProps> = ({ conversationHistory }) => (
  <>
    {conversationHistory.length > 0 && (
      <View style={styles.conversationContainer}>
        {conversationHistory.map((message, index) => (
          <Text key={index} style={styles.conversationMessage}>
            {message}
          </Text>
        ))}
      </View>
    )}
  </>
);

const styles = StyleSheet.create({
  conversationContainer: {
    padding: 10,
    backgroundColor: '#f8f9fa',
    borderRadius: 8,
    marginBottom: 16,
    maxHeight: 150,
  },
  conversationMessage: {
    fontSize: 14,
    marginBottom: 4,
    color: '#333',
  },
});

// No shared types duplicated here.

export default ConversationHistory;
