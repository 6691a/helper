import { useCallback, useState } from "react";
import {
  ActivityIndicator,
  FlatList,
  Pressable,
  RefreshControl,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { router, useFocusEffect } from "expo-router";
import { ThemedText } from "@/components/themed-text";
import { useThemeColor } from "@/hooks/use-theme-color";
import { memoryApi } from "@/services/api/memory";
import type { Memory } from "@/services/api/types";

export default function HomeScreen() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const backgroundColor = useThemeColor({}, "background");
  const cardBackground = useThemeColor(
    { light: "#fff", dark: "#1f2937" },
    "background",
  );
  const borderColor = useThemeColor(
    { light: "#e5e7eb", dark: "#374151" },
    "border",
  );

  const typeBadgeBg = useThemeColor(
    { light: "#eff6ff", dark: "#1e3a5f" },
    "background",
  );
  const typeBadgeColor = useThemeColor(
    { light: "#4a9eff", dark: "#60a5fa" },
    "tint",
  );
  const mutedColor = useThemeColor(
    { light: "#9ca3af", dark: "#6b7280" },
    "text",
  );

  const loadMemories = async () => {
    try {
      const data = await memoryApi.getMemories(50, 0);
      setMemories(data);
    } catch (error) {
      console.error("[Home] Failed to load memories:", error);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  // 화면이 포커스될 때마다 메모리 목록 새로고침
  useFocusEffect(
    useCallback(() => {
      loadMemories();
    }, []),
  );

  const handleRefresh = () => {
    setIsRefreshing(true);
    loadMemories();
  };

  const renderMemoryItem = ({ item }: { item: Memory }) => (
    <Pressable
      onPress={() => {
        router.push({
          pathname: "/memory-detail",
          params: {
            id: item.id.toString(),
            type: item.type,
            keywords: item.keywords,
            content: item.content,
            original_text: item.original_text,
            created_at: item.created_at,
            updated_at: item.updated_at,
            metadata_: item.metadata_ ? JSON.stringify(item.metadata_) : "",
          },
        });
      }}
    >
      <View
        style={[
          styles.memoryCard,
          { borderColor, backgroundColor: cardBackground },
        ]}
      >
        <View style={styles.memoryHeader}>
          <Text
            style={[
              styles.memoryType,
              { backgroundColor: typeBadgeBg, color: typeBadgeColor },
            ]}
          >
            {getMemoryTypeLabel(item.type)}
          </Text>
          <Text style={[styles.memoryKeywords, { color: mutedColor }]}>
            {item.keywords}
          </Text>
        </View>
        <ThemedText style={styles.memoryContent}>{item.content}</ThemedText>
        {item.original_text && (
          <ThemedText style={[styles.originalText, { color: mutedColor }]}>
            {`"${item.original_text}"`}
          </ThemedText>
        )}
      </View>
    </Pressable>
  );

  if (isLoading) {
    return (
      <SafeAreaView
        style={[styles.container, { backgroundColor }]}
        edges={["top"]}
      >
        <View style={styles.centerContainer}>
          <ActivityIndicator size="large" color="#4a9eff" />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor }]}
      edges={["top"]}
    >
      <FlatList
        data={memories}
        renderItem={renderMemoryItem}
        keyExtractor={(item) => item.id.toString()}
        contentContainerStyle={
          memories.length === 0 ? styles.emptyListContent : styles.listContent
        }
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl refreshing={isRefreshing} onRefresh={handleRefresh} />
        }
        ListEmptyComponent={
          <View style={styles.emptyContainer}>
            <ThemedText style={[styles.emptyText, { color: mutedColor }]}>
              아직 저장된 메모리가 없습니다
            </ThemedText>
          </View>
        }
      />
    </SafeAreaView>
  );
}

function getMemoryTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    item: "물건",
    place: "장소",
    schedule: "일정",
    person: "인물",
    memo: "메모",
  };
  return labels[type] || type;
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  centerContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  listContent: {
    padding: 16,
  },
  emptyListContent: {
    flexGrow: 1,
    padding: 16,
    justifyContent: "center",
  },
  memoryCard: {
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
  },
  memoryHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 8,
  },
  memoryType: {
    fontSize: 12,
    fontWeight: "600",
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  memoryKeywords: {
    fontSize: 12,
  },
  memoryContent: {
    fontSize: 16,
    lineHeight: 24,
    marginBottom: 8,
  },
  originalText: {
    fontSize: 14,
    fontStyle: "italic",
  },
  emptyContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  emptyText: {
    fontSize: 16,
  },
});
