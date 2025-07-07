import React, { useState, useEffect, useRef } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  Animated, 
  TouchableOpacity, 
  Dimensions,
  Keyboard,
  KeyboardAvoidingView,
  Platform,
  Alert,
  ScrollView,
  ActivityIndicator,
  TextInput,
  Vibration
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { MealEntry } from '../types';
import api from "../api/axios";
import { useAuth } from '../hooks/useAuth'; // Custom hook for authentication


interface ChatOverlayProps {
  isVisible: boolean;
  onClose: () => void;
  pendingMeal: MealEntry | null;
  createPendingMeal: (mealData: MealEntry) => void;
  saveMeal: (meal: MealEntry) => Promise<any>;
  cancelMeal: (keepHistory?: boolean) => void;
}

const SCREEN_HEIGHT = Dimensions.get('window').height;
const INITIAL_HEIGHT = 120; // Increased height of the chat bar when collapsed
const MAX_HEIGHT = SCREEN_HEIGHT * 0.5; // Maximum height of expanded overlay

const ChatOverlay: React.FC<ChatOverlayProps> = ({ 
  isVisible, 
  onClose, 
  pendingMeal,
  createPendingMeal,
  saveMeal,
  cancelMeal,
}) => {

  const { user, isLoading: isAuthLoading, login, logout, error: authError } = useAuth();
  const [inputText, setInputText] = useState("");
  const [loading, setLoading] = useState(false);
  const [overlayHeight] = useState(new Animated.Value(INITIAL_HEIGHT));
  const [isExpanded, setIsExpanded] = useState(false);
  const [keyboardHeight, setKeyboardHeight] = useState(0);
  const scrollViewRef = useRef<ScrollView>(null);
  const [isScrolledUp, setIsScrolledUp] = useState(false);
  const [fadeAnim] = useState(new Animated.Value(1));
  const [conversationHistory, setConversationHistory] = useState<string[]>([]);
  const lastConversationLength = useRef(conversationHistory.length);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [awaitingConfirmation, setAwaitingConfirmation] = useState(false);
  const [userFeedback, setUserFeedback] = useState("");
  const [pendingMeals, setPendingMeals] = useState<any[]>([]); // For multiple meals selection


   // For handling food input and conversation
  const handleFoodInput = async (input: string) => {
    setLoading(true);

    try {
      const { data: result } = await api.post("/openai/chat", {
        user_id: user?.uid, // Dynamic user ID
        description: input,
        conversation_id: conversationId,
        user_feedback: userFeedback || undefined,
        model: "gpt-4",
        temperature: 0,
        max_tokens: 150,
      });

      // Always use the conversation ID from the response
      setConversationId(result.conversation_id);

      if (result.message) {
        // Add AI's message to conversation history
        console.log("Message: " + result.message);
        setConversationHistory((prev) => [...prev, `App: ${result.message}`]);
        // Add slight vibration feedback when receiving message
        Vibration.vibrate(30);
      } else if (result.meals && result.meals.length > 0) {
        console.log("Meals found:", result.meals.length);
        
        // Clear any existing single pending meal since we have multiple meals now
        if (pendingMeal) {
          cancelMeal(true); // Keep history but clear the single meal
        }
        
        // Create a selection state for all meals (all selected by default)
        const mealsWithSelection = result.meals.map((meal: any, index: number) => ({
          ...meal,
          id: index, // Add temporary ID for selection tracking
          selected: true // All meals selected by default
        }));
        
        setPendingMeals(mealsWithSelection);
        setAwaitingConfirmation(true);

        const mealInfo = result.meals.length === 1 
          ? `App: Found "${result.meals[0].description}" (${result.meals[0].calories} cal)`
          : `App: Found ${result.meals.length} meals. Please review and select which ones to save.`;

        setConversationHistory((prev) => [...prev, mealInfo]);
        // Add slightly stronger vibration for meal confirmation
        Vibration.vibrate(50);
      }
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setLoading(false);
    }
  };


  // Handle user input
  const addMeal = async () => {
    if (!inputText.trim()) return;

    const input = inputText.trim();
    setInputText(""); // Clear input immediately

    // Add to conversation history
    if (awaitingConfirmation) {
      // If we're awaiting confirmation, append to history
      setConversationHistory((prev) => [...prev, `You: ${input}`]);
      setUserFeedback(input);
    } else if (conversationId && conversationHistory.length > 0) {
      // If we have an existing conversation, append to history
      setConversationHistory((prev) => [...prev, `You: ${input}`]);
      setUserFeedback("");
    } else {
      // Start a new conversation
      setConversationHistory([`You: ${input}`]);
      setUserFeedback("");
    }

    // Add slight vibration feedback when sending message
    Vibration.vibrate(20);

    await handleFoodInput(input);
  };

  // Animate new messages with a fade-in effect
  useEffect(() => {
    if (conversationHistory.length > lastConversationLength.current) {
      // Fade in new messages
      fadeAnim.setValue(0);
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true,
      }).start();
    }
    lastConversationLength.current = conversationHistory.length;
  }, [conversationHistory.length, fadeAnim]);

  // Auto-scroll to bottom whenever conversation history changes
  useEffect(() => {
    if (scrollViewRef.current && conversationHistory.length > 0) {
      setTimeout(() => {
        scrollViewRef.current?.scrollToEnd({ animated: true });
      }, 100); // Small delay to ensure layout is complete
    }
  }, [conversationHistory, isExpanded, awaitingConfirmation]);

  useEffect(() => {
    const keyboardWillShowListener = Keyboard.addListener(
      'keyboardWillShow',
      (e) => {
        // Only update the keyboard height, but don't auto-expand
        // This prevents the overlay from jumping too high
        setKeyboardHeight(e.endCoordinates.height);
        // Only expand if not already expanded
        if (!isExpanded) {
          expandOverlay();
        }
      }
    );
    const keyboardWillHideListener = Keyboard.addListener(
      'keyboardWillHide',
      () => {
        setKeyboardHeight(0);
      }
    );

    return () => {
      keyboardWillShowListener.remove();
      keyboardWillHideListener.remove();
    };
  }, [isExpanded]);

  useEffect(() => {
    if (isVisible) {
      // Start with initial height
      Animated.timing(overlayHeight, {
        toValue: INITIAL_HEIGHT,
        duration: 300,
        useNativeDriver: false,
      }).start();
    } else {
      // Hide completely
      Animated.timing(overlayHeight, {
        toValue: 0,
        duration: 300,
        useNativeDriver: false,
      }).start();
    }
  }, [isVisible]);

  // Auto-expand when meal confirmation is pending
  useEffect(() => {
    if (awaitingConfirmation && (pendingMeal || pendingMeals.length > 0)) {
      expandOverlay();
    }
  }, [awaitingConfirmation, pendingMeal, pendingMeals]);

  const toggleOverlay = () => {
    if (isExpanded) {
      collapseOverlay();
    } else {
      expandOverlay();
    }
  };

  const expandOverlay = () => {
    setIsExpanded(true);
    Animated.spring(overlayHeight, {
      toValue: MAX_HEIGHT,
      tension: 70,
      friction: 12,
      useNativeDriver: false,
    }).start();
  };

  const collapseOverlay = () => {
    setIsExpanded(false);
    Animated.spring(overlayHeight, {
      toValue: INITIAL_HEIGHT,
      tension: 70,
      friction: 12,
      useNativeDriver: false,
    }).start();
    setInputText(''); // Clear input text when collapsing overlay
    Keyboard.dismiss();
  };

  const clearConversation = () => {
    setConversationId(null);
    setAwaitingConfirmation(false);
    setUserFeedback("");
    setConversationHistory([]);
    setInputText(''); 
    setPendingMeals([]); // Clear multiple meals
  }

  const handleClose = () => {
    collapseOverlay();
    clearConversation(); 
    onClose();
  };

  // Functions for handling multiple meal selection
  const toggleMealSelection = (mealId: number) => {
    setPendingMeals(prev => 
      prev.map(meal => 
        meal.id === mealId ? { ...meal, selected: !meal.selected } : meal
      )
    );
  };

  const selectAllMeals = () => {
    setPendingMeals(prev => prev.map(meal => ({ ...meal, selected: true })));
  };

  const deselectAllMeals = () => {
    setPendingMeals(prev => prev.map(meal => ({ ...meal, selected: false })));
  };

  const saveSelectedMeals = async () => {
    const selectedMeals = pendingMeals.filter(meal => meal.selected);
    
    if (selectedMeals.length === 0) {
      Alert.alert('No meals selected', 'Please select at least one meal to save.');
      return;
    }

    try {
      // Save each selected meal
      for (const meal of selectedMeals) {
        const { id, selected, ...mealData } = meal; // Remove temporary properties
        await saveMeal(mealData);
      }
      handleClose();
    } catch (error) {
      console.error('Error saving meals:', error);
      Alert.alert('Error', 'Failed to save meals');
    }
  };

  if (!isVisible) return null;

  return (
    <>
      {isExpanded && (
        <TouchableOpacity 
          style={styles.backdrop}
          activeOpacity={0.7}
          onPress={collapseOverlay}
        />
      )}
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 100 : 0}
        style={styles.container}
      >
        <Animated.View
          style={[
            styles.overlay,
            {
              height: overlayHeight,
              paddingBottom: keyboardHeight > 0 ? 5 : 20,
            }
          ]}
        >
          <View style={styles.header}>
            <TouchableOpacity onPress={toggleOverlay} style={styles.toggleButton}>
              <Ionicons 
                name={isExpanded ? "chevron-down" : "chevron-up"} 
                size={24} 
                color="#007AFF" 
              />
            </TouchableOpacity>
            <Text style={styles.headerTitle}>
              {isExpanded ? "Chat with AI Assistant" : "Ask AI about food"}
            </Text>
            {isExpanded && (
              <TouchableOpacity onPress={handleClose} style={styles.closeButton}>
                <Ionicons name="close" size={24} color="#999" />
              </TouchableOpacity>
            )}
          </View>

          {isExpanded && (
            <View style={styles.conversationContainer}>
              <ScrollView 
                style={styles.scrollView}
                contentContainerStyle={styles.scrollViewContent}
                showsVerticalScrollIndicator={true}
                ref={scrollViewRef}
                keyboardShouldPersistTaps="handled"
                onScroll={(event) => {
                  const { layoutMeasurement, contentOffset, contentSize } = event.nativeEvent;
                  const paddingToBottom = 20;
                  const isAtBottom = layoutMeasurement.height + contentOffset.y >= 
                    contentSize.height - paddingToBottom;
                  setIsScrolledUp(!isAtBottom);
                }}
                scrollEventThrottle={400}
              >
                {conversationHistory.length > 0 ? (
                  conversationHistory.map((message, index) => (
                    <Animated.Text 
                      key={index} 
                      style={[
                        styles.conversationMessage,
                        message.startsWith("You:") ? styles.userMessage : styles.aiMessage,
                        index === conversationHistory.length - 1 && { opacity: fadeAnim }
                      ]}
                    >
                      {message}
                    </Animated.Text>
                  ))
                ) : (
                  <Text style={styles.emptyMessage}>
                    Ask about food or log a meal by typing below
                  </Text>
                )}

                {/* Multiple Meals confirmation UI */}
                {awaitingConfirmation && pendingMeals.length > 0 && (
                  <View style={styles.confirmationContainer}>
                    <View style={styles.confirmationHeader}>
                      <Text style={styles.confirmationTitle}>
                        Select Meals to Save ({pendingMeals.filter(m => m.selected).length}/{pendingMeals.length}):
                      </Text>
                      <View style={styles.selectAllButtons}>
                        <TouchableOpacity onPress={selectAllMeals} style={styles.selectAllButton}>
                          <Text style={styles.selectAllButtonText}>All</Text>
                        </TouchableOpacity>
                        <TouchableOpacity onPress={deselectAllMeals} style={styles.selectAllButton}>
                          <Text style={styles.selectAllButtonText}>None</Text>
                        </TouchableOpacity>
                      </View>
                    </View>
                    
                    {pendingMeals.map((meal, index) => (
                      <TouchableOpacity 
                        key={meal.id} 
                        onPress={() => toggleMealSelection(meal.id)}
                        style={[
                          styles.mealItem,
                          meal.selected ? styles.mealItemSelected : styles.mealItemUnselected
                        ]}
                      >
                        <View style={styles.mealItemHeader}>
                          <Ionicons 
                            name={meal.selected ? "checkbox" : "square-outline"} 
                            size={24} 
                            color={meal.selected ? "#4CAF50" : "#999"} 
                          />
                          <Text style={[styles.mealItemTitle, meal.selected && styles.mealItemTitleSelected]}>
                            {meal.description}
                          </Text>
                        </View>
                        {meal.assumptions && (
                          <Text style={styles.mealItemAssumptions}>{meal.assumptions}</Text>
                        )}
                        <Text style={styles.mealItemNutrition}>
                          {meal.calories?.toFixed(0)} cal • {meal.protein?.toFixed(0)}g protein • {meal.carbs?.toFixed(0)}g carbs • {meal.fat?.toFixed(0)}g fat
                        </Text>
                      </TouchableOpacity>
                    ))}
                    
                    <View style={styles.confirmationButtons}>
                      <TouchableOpacity
                        style={[styles.iconButton, styles.confirmButton]}
                        onPress={saveSelectedMeals}
                      >
                        <Text style={styles.iconButtonText}>✓ Save Selected</Text>
                      </TouchableOpacity>
                      <TouchableOpacity
                        style={[styles.iconButton, styles.cancelButton]}
                        onPress={() => {
                          setPendingMeals([]);
                          setAwaitingConfirmation(false);
                        }}
                      >
                        <Text style={styles.iconButtonText}>✗ Cancel</Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                )}

                {/* Single Meal confirmation UI (fallback for legacy) */}
                {awaitingConfirmation && pendingMeal && pendingMeals.length === 0 && (
                  <View style={styles.confirmationContainer}>
                    <Text style={styles.confirmationTitle}>Confirm Meal:</Text>
                    <Text style={styles.confirmationText}>{pendingMeal.description}</Text>
                    {pendingMeal.assumptions && (
                      <Text style={styles.confirmationText}>{pendingMeal.assumptions}</Text>
                    )}
                    <Text style={styles.confirmationText}>
                      Calories: {pendingMeal.calories.toFixed(0)}, Protein: {pendingMeal.protein?.toFixed(0)}, Fiber: {pendingMeal.fiber?.toFixed(0)},
                      Carbs: {pendingMeal.carbs?.toFixed(0)}, Fat: {pendingMeal.fat?.toFixed(0)},
                      Sugar: {pendingMeal.sugar?.toFixed(0)}
                    </Text>
                    <View style={styles.confirmationButtons}>
                      <TouchableOpacity
                        style={[styles.iconButton, styles.confirmButton]}
                        onPress={async () => {
                          try {
                            await saveMeal(pendingMeal);
                            handleClose();
                          } catch (error) {
                            console.error('Error:', error);
                            Alert.alert('Error', 'Failed to save meal');
                          }
                        }}
                      >
                        <Text style={styles.iconButtonText}>✓</Text>
                      </TouchableOpacity>
                      <TouchableOpacity
                        style={[styles.iconButton, styles.cancelButton]}
                        onPress={() => {
                          cancelMeal(false);
                          setAwaitingConfirmation(false);
                        }}
                      >
                        <Text style={styles.iconButtonText}>✗</Text>
                      </TouchableOpacity>
                    </View>
                  </View>
                )}
              </ScrollView>
              
              {/* Scroll to bottom button */}
              {isScrolledUp && (
                <TouchableOpacity 
                  style={styles.scrollToBottomButton}
                  onPress={() => scrollViewRef.current?.scrollToEnd({ animated: true })}
                >
                  <Ionicons name="chevron-down-circle" size={36} color="#007AFF" />
                </TouchableOpacity>
              )}
              
              {/* Typing indicator */}
              {loading && (
                <View style={styles.typingIndicator}>
                  <ActivityIndicator size="small" color="#007AFF" />
                  <Text style={styles.typingText}>AI is thinking...</Text>
                </View>
              )}
            </View>
          )}

          <View style={styles.inputContainer}>
            <TextInput
              style={styles.input}
              placeholder="What did you eat?"
              value={inputText}
              onChangeText={setInputText}
              editable={!loading}
              onFocus={expandOverlay}
            />
            <TouchableOpacity
              style={[styles.sendButton, loading && styles.sendButtonDisabled]}
              onPress={() => {
                // If there's pending meals or a pending meal, we want to keep the conversation 
                // because the user is providing clarification/feedback
                if (awaitingConfirmation && (pendingMeal || pendingMeals.length > 0)) {
                  // Don't cancel the meals, just add to the conversation
                  // This allows user to provide clarification about the pending meals
                } else {
                  // For regular messages without pending meals, proceed normally
                }
                addMeal(); // This will handle both cases now
              }}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator size="small" color="#fff" />
              ) : (
                <Text style={styles.sendButtonText}>➤</Text>
              )}
            </TouchableOpacity>
          </View>
        </Animated.View>
      </KeyboardAvoidingView>
    </>
  );
};

const styles = StyleSheet.create({
  backdrop: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0,0,0,0.3)',
    zIndex: 999,
  },
  container: {
    position: 'absolute',
    bottom: 90, // Adjusted position from bottom
    left: 0,
    right: 0,
    zIndex: 1500, // Increased z-index to ensure it appears above everything
  },
  overlay: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -3 },
    shadowOpacity: 0.25, // Increased shadow opacity
    shadowRadius: 8, // Increased shadow radius
    elevation: 8, // Increased elevation for Android
    paddingHorizontal: 16,
    paddingTop: 10,
    borderWidth: 1, // Added border
    borderColor: '#ddd', // Light border color
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingBottom: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  headerTitle: {
    flex: 1,
    textAlign: 'center',
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
  },
  toggleButton: {
    padding: 5,
  },
  closeButton: {
    padding: 5,
  },
  conversationContainer: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 5,
  },
  scrollView: {
    flex: 1,
  },
  scrollViewContent: {
    paddingBottom: 20,
    flexGrow: 1, // This ensures content expands to fill the available space
  },
  conversationMessage: {
    fontSize: 15,
    lineHeight: 20,
    marginBottom: 10,
    padding: 12,
    borderRadius: 12,
    maxWidth: '85%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 1,
    elevation: 1,
  },
  userMessage: {
    alignSelf: 'flex-end',
    backgroundColor: '#e1f5fe',
    color: '#01579b',
    borderBottomRightRadius: 4,
  },
  aiMessage: {
    alignSelf: 'flex-start',
    backgroundColor: '#f5f5f5',
    color: '#333',
    borderBottomLeftRadius: 4,
  },
  emptyMessage: {
    textAlign: 'center',
    color: '#999',
    fontStyle: 'italic',
    marginTop: 20,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingTop: 10,
  },
  input: {
    flex: 1,
    height: 40,
    borderColor: '#ddd',
    borderWidth: 1,
    borderRadius: 20,
    paddingHorizontal: 15,
    backgroundColor: '#f9f9f9',
  },
  sendButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#007AFF',
    justifyContent: 'center',
    alignItems: 'center',
    marginLeft: 10,
  },
  sendButtonDisabled: {
    backgroundColor: '#ccc',
  },
  sendButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: 'bold',
  },
  // New styles for meal confirmation
  confirmationContainer: {
    padding: 16,
    backgroundColor: '#e6f0ff',
    borderRadius: 8,
    marginVertical: 10,
    borderWidth: 1,
    borderColor: '#b3d1ff',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 3,
    elevation: 3,
  },
  confirmationTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 8,
    color: '#333',
  },
  confirmationText: {
    fontSize: 16,
    marginBottom: 8,
    color: '#555',
  },
  confirmationButtons: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginTop: 10,
  },
  iconButton: {
    minWidth: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
    marginHorizontal: 10,
    paddingHorizontal: 15,
  },
  confirmButton: {
    backgroundColor: '#4CAF50',
  },
  cancelButton: {
    backgroundColor: '#F44336',
  },
  iconButtonText: {
    fontSize: 16,
    color: 'white',
    fontWeight: 'bold',
    textAlign: 'center',
  },
  // Scroll to bottom button styles
  scrollToBottomButton: {
    position: 'absolute',
    right: 10,
    bottom: 10,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    borderRadius: 20,
    padding: 5,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 3,
    elevation: 5,
  },
  // Typing indicator styles
  typingIndicator: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 8,
    marginVertical: 8,
    backgroundColor: '#f0f0f0',
    borderRadius: 16,
    alignSelf: 'flex-start',
    marginLeft: 10,
  },
  typingText: {
    marginLeft: 8,
    fontSize: 14,
    color: '#555',
    fontStyle: 'italic',
  },
  // Multiple meals selection styles
  confirmationHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  selectAllButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  selectAllButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: '#007AFF',
    borderRadius: 15,
  },
  selectAllButtonText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  mealItem: {
    padding: 12,
    marginVertical: 4,
    borderRadius: 8,
    borderWidth: 2,
  },
  mealItemSelected: {
    backgroundColor: '#e8f5e8',
    borderColor: '#4CAF50',
  },
  mealItemUnselected: {
    backgroundColor: '#f8f8f8',
    borderColor: '#ddd',
  },
  mealItemHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  mealItemTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 10,
    flex: 1,
    color: '#333',
  },
  mealItemTitleSelected: {
    color: '#2E7D32',
  },
  mealItemAssumptions: {
    fontSize: 13,
    color: '#666',
    fontStyle: 'italic',
    marginBottom: 4,
    paddingLeft: 34,
  },
  mealItemNutrition: {
    fontSize: 14,
    color: '#555',
    paddingLeft: 34,
  },
});

export default ChatOverlay;