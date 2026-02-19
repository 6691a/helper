import { useState } from "react";
import {
  Alert,
  ScrollView,
  StyleSheet,
  View,
  ActivityIndicator,
  Pressable,
  Text,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { router, useLocalSearchParams } from "expo-router";
import { Ionicons } from "@expo/vector-icons";
import { ThemedText } from "@/components/themed-text";
import { ScreenHeader } from "@/components/screen-header";
import { useThemeColor } from "@/hooks/use-theme-color";
import { memoryApi } from "@/services/api/memory";
import type { Memory, MemoryType } from "@/services/api/types";
import { formatDateTime } from "@/lib/date-utils";

export default function MemoryDetailScreen() {
  const params = useLocalSearchParams();
  const [isDeleting, setIsDeleting] = useState(false);

  // 테마 색상
  const backgroundColor = useThemeColor({}, "background");
  const borderColor = useThemeColor(
    { light: "#e5e7eb", dark: "#374151" },
    "border",
  );
  const mutedColor = useThemeColor(
    { light: "#6b7280", dark: "#9ca3af" },
    "text",
  );
  const labelColor = useThemeColor(
    { light: "#374151", dark: "#d1d5db" },
    "text",
  );
  const typeBadgeBg = useThemeColor(
    { light: "#eff6ff", dark: "#1e3a5f" },
    "background",
  );
  const typeBadgeColor = useThemeColor(
    { light: "#4a9eff", dark: "#60a5fa" },
    "tint",
  );

  // 파라미터 파싱
  const memory: Memory = {
    id: Number(params.id),
    type: params.type as MemoryType,
    keywords: params.keywords as string,
    content: params.content as string,
    original_text: params.original_text as string,
    created_at: params.created_at as string,
    updated_at: params.updated_at as string,
    metadata_: params.metadata_ ? JSON.parse(params.metadata_ as string) : null,
  };

  const handleDelete = () => {
    Alert.alert(
      "메모리 삭제",
      "이 메모리를 삭제하시겠습니까? 삭제된 메모리는 복구할 수 없습니다.",
      [
        {
          text: "취소",
          style: "cancel",
        },
        {
          text: "삭제",
          style: "destructive",
          onPress: async () => {
            try {
              setIsDeleting(true);
              await memoryApi.deleteMemory(memory.id);
              router.back();
            } catch (error) {
              setIsDeleting(false);
              Alert.alert(
                "삭제 실패",
                error instanceof Error
                  ? error.message
                  : "메모리 삭제 중 오류가 발생했습니다",
              );
            }
          },
        },
      ],
    );
  };

  if (isDeleting) {
    return (
      <SafeAreaView
        style={[styles.container, { backgroundColor }]}
        edges={["top"]}
      >
        <ScreenHeader title="메모리 상세" />
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#4a9eff" />
          <ThemedText style={styles.loadingText}>삭제 중...</ThemedText>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor }]}
      edges={["top"]}
    >
      <ScreenHeader title="메모리 상세" />

      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* 메모리 타입 배지 */}
        <View style={styles.typeContainer}>
          <View style={[styles.typeBadge, { backgroundColor: typeBadgeBg }]}>
            <Text style={[styles.typeBadgeText, { color: typeBadgeColor }]}>
              {getMemoryTypeLabel(memory.type)}
            </Text>
          </View>
        </View>

        {/* 키워드 */}
        <View style={[styles.section, { borderColor }]}>
          <ThemedText style={[styles.label, { color: labelColor }]}>
            키워드
          </ThemedText>
          <ThemedText style={styles.value}>{memory.keywords}</ThemedText>
        </View>

        {/* 내용 */}
        <View style={[styles.section, { borderColor }]}>
          <ThemedText style={[styles.label, { color: labelColor }]}>
            내용
          </ThemedText>
          <ThemedText style={styles.value}>{memory.content}</ThemedText>
        </View>

        {/* 원본 텍스트 */}
        <View style={[styles.section, { borderColor }]}>
          <ThemedText style={[styles.label, { color: labelColor }]}>
            원본 텍스트
          </ThemedText>
          <ThemedText style={[styles.originalValue, { color: mutedColor }]}>
            {`"${memory.original_text}"`}
          </ThemedText>
        </View>

        {/* 메타데이터 (있을 경우) */}
        {memory.metadata_ && Object.keys(memory.metadata_).length > 0 && (
          <View style={[styles.section, { borderColor }]}>
            <ThemedText style={[styles.label, { color: labelColor }]}>
              추가 정보
            </ThemedText>
            {Object.entries(memory.metadata_).map(([key, value]) => (
              <View key={key} style={styles.metadataRow}>
                <ThemedText style={[styles.metadataKey, { color: mutedColor }]}>
                  {key}:
                </ThemedText>
                <ThemedText style={styles.metadataValue}>
                  {String(value)}
                </ThemedText>
              </View>
            ))}
          </View>
        )}

        {/* 생성 시간 */}
        <View style={[styles.section, { borderColor }]}>
          <View style={styles.dateRow}>
            <Ionicons name="time-outline" size={16} color={mutedColor} />
            <ThemedText style={[styles.dateLabel, { color: mutedColor }]}>
              생성
            </ThemedText>
            <ThemedText style={[styles.dateValue, { color: mutedColor }]}>
              {formatDateTime(memory.created_at)}
            </ThemedText>
          </View>
        </View>

        {/* 수정 시간 */}
        <View style={[styles.section, { borderColor }]}>
          <View style={styles.dateRow}>
            <Ionicons name="refresh-outline" size={16} color={mutedColor} />
            <ThemedText style={[styles.dateLabel, { color: mutedColor }]}>
              수정
            </ThemedText>
            <ThemedText style={[styles.dateValue, { color: mutedColor }]}>
              {formatDateTime(memory.updated_at)}
            </ThemedText>
          </View>
        </View>

        {/* 삭제 버튼 */}
        <View style={styles.deleteButtonContainer}>
          <ThemedText style={[styles.deleteWarning, { color: mutedColor }]}>
            삭제된 메모리는 복구할 수 없습니다
          </ThemedText>
          <Pressable style={styles.deleteButton} onPress={handleDelete}>
            <Ionicons name="trash-outline" size={20} color="#fff" />
            <Text style={styles.deleteButtonText}>메모리 삭제</Text>
          </Pressable>
        </View>
      </ScrollView>
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
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 40,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    gap: 12,
  },
  loadingText: {
    fontSize: 14,
  },
  typeContainer: {
    flexDirection: "row",
    marginBottom: 20,
  },
  typeBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  typeBadgeText: {
    fontSize: 14,
    fontWeight: "600",
  },
  section: {
    marginBottom: 20,
    paddingBottom: 20,
    borderBottomWidth: 1,
  },
  label: {
    fontSize: 12,
    fontWeight: "600",
    marginBottom: 8,
    textTransform: "uppercase",
    letterSpacing: 0.5,
  },
  value: {
    fontSize: 16,
    lineHeight: 24,
  },
  originalValue: {
    fontSize: 15,
    lineHeight: 22,
    fontStyle: "italic",
  },
  metadataRow: {
    flexDirection: "row",
    marginTop: 6,
    gap: 8,
  },
  metadataKey: {
    fontSize: 14,
    fontWeight: "500",
  },
  metadataValue: {
    fontSize: 14,
    flex: 1,
  },
  dateRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
  },
  dateLabel: {
    fontSize: 14,
    fontWeight: "500",
  },
  dateValue: {
    fontSize: 14,
  },
  deleteButtonContainer: {
    marginTop: 20,
    gap: 12,
  },
  deleteWarning: {
    fontSize: 13,
    textAlign: "center",
  },
  deleteButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    backgroundColor: "#ef4444",
    borderRadius: 8,
    padding: 14,
  },
  deleteButtonText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
  },
});
