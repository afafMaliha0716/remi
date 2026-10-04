import { Text, View, StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useHeaderHeight } from '@react-navigation/elements';

export default function AddTask() {
  const { top } = useSafeAreaInsets();
  const headerHeight = useHeaderHeight();

  return (
    <LinearGradient
      colors={['#FFD1DC', '#AEC6CF', '#C1E1C1']}
      style={[styles.container, { paddingTop: top + headerHeight/2 }]}
    >
      <Text style={styles.text}>Add Task Screen</Text>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  text: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
    textShadowColor: 'rgba(0, 0, 0, 0.1)',
    textShadowOffset: {width: -1, height: 1},
    textShadowRadius: 1
  },
});
