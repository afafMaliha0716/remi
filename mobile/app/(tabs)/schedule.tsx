import React from 'react';
import { View, Text, ScrollView, StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useHeaderHeight } from '@react-navigation/elements';

const scheduleData = [
  { id: 1, time: '09:00 AM', title: 'Morning Stand-up' },
  { id: 2, time: '11:00 AM', title: 'Work on project A' },
  { id: 3, time: '01:00 PM', title: 'Lunch Break' },
  { id: 4, time: '02:00 PM', title: 'Meeting with Team B' },
  { id: 5, time: '04:00 PM', title: 'Review PRs' },
];

export default function Schedule() {
  const { top } = useSafeAreaInsets();
  const headerHeight = useHeaderHeight();

  return (
    <LinearGradient colors={['#FFD1DC', '#AEC6CF', '#C1E1C1']} style={[styles.gradientContainer, { paddingTop: top + headerHeight/2 }]}>
      <ScrollView style={styles.container}>
        <Text style={styles.header}>Today's Schedule</Text>
        {scheduleData.map((item) => (
          <View key={item.id} style={styles.scheduleItem}>
            <Text style={styles.time}>{item.time}</Text>
            <Text style={styles.title}>{item.title}</Text>
          </View>
        ))}
      </ScrollView>
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
  header: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
    color: '#fff',
    textShadowColor: 'rgba(0, 0, 0, 0.1)',
    textShadowOffset: {width: -1, height: 1},
    textShadowRadius: 1
  },
  scheduleItem: {
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    padding: 15,
    borderRadius: 10,
    marginBottom: 15,
  },
  time: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
    textShadowColor: 'rgba(0, 0, 0, 0.1)',
    textShadowOffset: {width: -1, height: 1},
    textShadowRadius: 1
  },
  title: {
    fontSize: 18,
    marginTop: 5,
    color: '#fff',
    textShadowColor: 'rgba(0, 0, 0, 0.1)',
    textShadowOffset: {width: -1, height: 1},
    textShadowRadius: 1
  },
});
