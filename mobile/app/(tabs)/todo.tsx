import React, { useState } from 'react';
import { View, Text, TextInput, Button, ScrollView, StyleSheet, TouchableOpacity } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useHeaderHeight } from '@react-navigation/elements';

export default function Todo() {
  const { top } = useSafeAreaInsets();
  const headerHeight = useHeaderHeight();
  const [tasks, setTasks] = useState([
    { id: 1, text: 'Buy groceries', completed: false },
    { id: 2, text: 'Walk the dog', completed: true },
    { id: 3, text: 'Do laundry', completed: false },
  ]);
  const [input, setInput] = useState('');

  const addTask = () => {
    if (input.trim()) {
      setTasks([...tasks, { id: tasks.length + 1, text: input, completed: false }]);
      setInput('');
    }
  };

  const toggleTask = (id) => {
    setTasks(
      tasks.map((task) =>
        task.id === id ? { ...task, completed: !task.completed } : task
      )
    );
  };

  return (
    <LinearGradient colors={['#FFD1DC', '#AEC6CF', '#C1E1C1']} style={[styles.gradientContainer, { paddingTop: top + headerHeight/2 }]}>
      <View style={styles.container}>
        <View style={styles.inputContainer}>
          <TextInput
            style={styles.input}
            value={input}
            onChangeText={setInput}
            placeholder="Add a new task..."
            placeholderTextColor="#fff"
          />
          <Button title="Add" onPress={addTask} color="#fff" />
        </View>
        <ScrollView style={styles.tasksContainer}>
          {tasks.map((task) => (
            <TouchableOpacity key={task.id} onPress={() => toggleTask(task.id)} style={styles.task}>
              <View style={[styles.checkbox, task.completed && styles.checked]} />
              <Text style={[styles.taskText, task.completed && styles.completedText]}>
                {task.text}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>
      </View>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  gradientContainer: {
    flex: 1,
  },
  container: {
    flex: 1,
    padding: 20,
  },
  inputContainer: {
    flexDirection: 'row',
    marginBottom: 20,
  },
  input: {
    flex: 1,
    height: 40,
    borderColor: 'rgba(255, 255, 255, 0.3)',
    borderWidth: 1,
    borderRadius: 5,
    paddingHorizontal: 10,
    marginRight: 10,
    color: '#fff',
  },
  tasksContainer: {
    flex: 1,
  },
  task: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 15,
    borderBottomWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.2)',
  },
  checkbox: {
    width: 20,
    height: 20,
    borderRadius: 5,
    borderWidth: 2,
    borderColor: '#fff',
    marginRight: 15,
  },
  checked: {
    backgroundColor: '#fff',
  },
  taskText: {
    fontSize: 18,
    color: '#fff',
    textShadowColor: 'rgba(0, 0, 0, 0.1)',
    textShadowOffset: {width: -1, height: 1},
    textShadowRadius: 1
  },
  completedText: {
    textDecorationLine: 'line-through',
    color: 'rgba(255, 255, 255, 0.5)',
  },
});
