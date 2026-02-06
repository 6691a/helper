import {StyleSheet} from "react-native";

import {ThemedText} from "@/components/themed-text";
import {ThemedView} from "@/components/themed-view";

export default function TabTwoScreen() {
  return (
      <ThemedView>
        <ThemedText>HI</ThemedText>
      </ThemedView>
  );
}

const styles = StyleSheet.create({
  headerImage: {
    color: "#808080",
    bottom: -90,
    left: -35,
    position: "absolute",
  },
  titleContainer: {
    flexDirection: "row",
    gap: 8,
  },
});
