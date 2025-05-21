import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, Modal, StyleSheet, TextInput, Button, Alert, KeyboardAvoidingView, ScrollView, Keyboard, TouchableWithoutFeedback, Platform } from 'react-native';
import { signOut } from 'firebase/auth'; // Import signOut from Firebase
import { auth } from '../firebase/firebaseConfig'; // Import Firebase auth instance

interface UserProfile {
  firstName: string;
  lastName: string;
  dateOfBirth: string;
  weight: string;
  height: string;
}

interface HamburgerMenuProps {
  userProfile: UserProfile;
  onSave: (profile: UserProfile) => void;
}

const HamburgerMenu: React.FC<HamburgerMenuProps> = ({ userProfile, onSave }) => {
  const [modalVisible, setModalVisible] = useState(false);
  const [menuVisible, setMenuVisible] = useState(false);
  const [profile, setProfile] = useState(userProfile);

  useEffect(() => {
    setProfile(userProfile);
  }, [userProfile]);

  const handleChange = (field: keyof UserProfile, value: string) => {
    setProfile({ ...profile, [field]: value });
  };

  const handleSave = () => {
    onSave(profile);
    setModalVisible(false);
  };

  const handleLogout = async () => {
    try {
      await signOut(auth); // Log out the user
      console.log('User logged out successfully');
      Alert.alert('Success', 'You have been logged out.');
    } catch (error) {
      console.error('Logout error:', error);
      Alert.alert('Error', 'Failed to log out. Please try again.');
    }
  };

  return (
    <View>
      <TouchableOpacity onPress={() => setMenuVisible(!menuVisible)} style={styles.hamburgerIcon}>
        <View style={styles.line} />
        <View style={styles.line} />
        <View style={styles.line} />
      </TouchableOpacity>

      {menuVisible && (
        <View style={styles.menuContainer}>
          <TouchableOpacity onPress={() => { setMenuVisible(false); setModalVisible(true); }}>
            <Text style={styles.menuItem}>Profile</Text>
          </TouchableOpacity>
          <TouchableOpacity onPress={handleLogout}>
            <Text style={styles.menuItem}>Logout</Text>
          </TouchableOpacity>
        </View>
      )}

      <Modal
        animationType="slide"
        transparent={false}
        visible={modalVisible}
        onRequestClose={() => setModalVisible(false)}
      >
        <TouchableWithoutFeedback onPress={Keyboard.dismiss}>
          <View style={styles.modalOverlay}>
            {/* <KeyboardAvoidingView
              behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
              style={{ flex: 1, justifyContent: 'center' }}
            > */}
              {/* <ScrollView contentContainerStyle={{ flexGrow: 1 }}> */}
                <View style={styles.modalContent}>
                  <Text style={styles.modalTitle}>Edit Profile</Text>

                  <TextInput
                    style={styles.input}
                    placeholder="First Name"
                    value={profile.firstName}
                    onChangeText={(text) => handleChange('firstName', text)}
                  />
                  <TextInput
                    style={styles.input}
                    placeholder="Last Name"
                    value={profile.lastName}
                    onChangeText={(text) => handleChange('lastName', text)}
                  />
                  <TextInput
                    style={styles.input}
                    placeholder="Date of Birth (YYYY-MM-DD)"
                    value={profile.dateOfBirth}
                    onChangeText={(text) => handleChange('dateOfBirth', text)}
                  />
                  <TextInput
                    style={styles.input}
                    placeholder="Weight (kg)"
                    keyboardType="numeric"
                    value={profile.weight}
                    onChangeText={(text) => handleChange('weight', text)}
                  />
                  <TextInput
                    style={styles.input}
                    placeholder="Height (cm)"
                    keyboardType="numeric"
                    value={profile.height}
                    onChangeText={(text) => handleChange('height', text)}
                  />

                  <View style={styles.buttonRow}>
                    <Button title="Cancel" onPress={() => setModalVisible(false)} />
                    <Button title="Save" onPress={handleSave} />
                  </View>
                </View>
              {/* </ScrollView> */}
            {/* </KeyboardAvoidingView> */}
          </View>
        </TouchableWithoutFeedback>
      </Modal>
    </View>
  );
};

const styles = StyleSheet.create({
  hamburgerIcon: {
    padding: 10,
    marginLeft: 10,
  },
  line: {
    width: 25,
    height: 3,
    backgroundColor: '#333',
    marginVertical: 2,
    borderRadius: 2,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    padding: 20,
  },
  modalContent: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 20,
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 12,
  },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 4,
    padding: 8,
    marginBottom: 12,
  },
  buttonRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  menuContainer: {
    position: 'absolute',
    top: 50,
    left: 10,
    backgroundColor: '#ffffff', // Changed to solid white background
    borderRadius: 8,
    padding: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 1,
    shadowRadius: 3.84,
    elevation: 5,
    zIndex: 1000, // Ensures the menu is layered above other content
  },
  menuItem: {
    padding: 10,
    fontSize: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#ccc',
  },
});

export default HamburgerMenu;
