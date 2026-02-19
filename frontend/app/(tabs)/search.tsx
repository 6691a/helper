import { useCallback, useEffect, useRef, useState } from "react";
import {
  Animated,
  ActivityIndicator,
  FlatList,
  Platform,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { router, useFocusEffect } from "expo-router";
import { ThemedText } from "@/components/themed-text";
import { useThemeColor } from "@/hooks/use-theme-color";
import { useColorScheme } from "@/hooks/use-color-scheme";
import { memoryApi } from "@/services/api/memory";
import type { Memory } from "@/services/api/types";

// ─── constants ────────────────────────────────────────────────────────────────

const CELL_HEIGHT = 54; // fixed row height for smooth animation

// ─── date helpers ─────────────────────────────────────────────────────────────

function toDateString(date: Date): string {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function getMonthRows(year: number, month: number): (Date | null)[][] {
  const firstDay = new Date(year, month - 1, 1).getDay();
  const lastDate = new Date(year, month, 0).getDate();
  const cells: (Date | null)[] = [];
  for (let i = 0; i < firstDay; i++) cells.push(null);
  for (let d = 1; d <= lastDate; d++) cells.push(new Date(year, month - 1, d));
  while (cells.length % 7 !== 0) cells.push(null);
  const rows: (Date | null)[][] = [];
  for (let i = 0; i < cells.length; i += 7) rows.push(cells.slice(i, i + 7));
  return rows;
}

/** Returns the row index that contains `date` within `rows`. */
function getRowForDate(date: Date, rows: (Date | null)[][]): number {
  const ds = toDateString(date);
  for (let r = 0; r < rows.length; r++) {
    if (rows[r].some((d) => d !== null && toDateString(d) === ds)) return r;
  }
  return 0;
}

const _today = new Date();
const todayString = toDateString(_today);

// ─── type helpers ─────────────────────────────────────────────────────────────

const TYPE_COLORS: Record<string, string> = {
  item: "#3b82f6",
  place: "#10b981",
  schedule: "#f59e0b",
  person: "#8b5cf6",
  memo: "#6b7280",
};

const TYPE_LABELS: Record<string, string> = {
  item: "물건",
  place: "장소",
  schedule: "일정",
  person: "인물",
  memo: "메모",
};

function typeColor(type: string): string {
  return TYPE_COLORS[type] ?? "#6b7280";
}
function typeLabel(type: string): string {
  return TYPE_LABELS[type] ?? type;
}
function formatDateHeader(dateStr: string): string {
  const d = new Date(dateStr);
  const wds = ["일", "월", "화", "수", "목", "금", "토"];
  const isToday = dateStr === todayString;
  return `${d.getMonth() + 1}월 ${d.getDate()}일 ${wds[d.getDay()]}요일${isToday ? " (오늘)" : ""}`;
}
function formatTime(s: string): string {
  return s.includes(" ")
    ? s.split(" ")[1].substring(0, 5)
    : s.substring(11, 16);
}

// ─── DayCell ──────────────────────────────────────────────────────────────────

const WEEKDAYS = ["일", "월", "화", "수", "목", "금", "토"];

interface DayCellProps {
  date: Date | null;
  count: number;
  isSelected: boolean;
  isToday: boolean;
  isDark: boolean;
  onPress: () => void;
}

function DayCell({
  date,
  count,
  isSelected,
  isToday,
  isDark,
  onPress,
}: DayCellProps) {
  if (date === null) return <View style={styles.dayCell} />;

  const dayIdx = date.getDay();
  const numColor = isSelected
    ? "#fff"
    : isToday
      ? "#4a9eff"
      : dayIdx === 0
        ? "#ef4444"
        : dayIdx === 6
          ? "#3b82f6"
          : isDark
            ? "#e5e7eb"
            : "#1f2937";

  return (
    <Pressable style={styles.dayCell} onPress={onPress}>
      <View
        style={[
          styles.dayCircle,
          isSelected && styles.dayCircleSelected,
          isToday && !isSelected && styles.dayCircleToday,
        ]}
      >
        <Text style={[styles.dayNumber, { color: numColor }]}>
          {date.getDate()}
        </Text>
      </View>
      <View style={styles.dotRow}>
        {count > 0 && (
          <View
            style={[
              styles.dot,
              {
                backgroundColor: isSelected
                  ? "rgba(255,255,255,0.8)"
                  : "#4a9eff",
              },
            ]}
          />
        )}
      </View>
    </Pressable>
  );
}

// ─── Screen ───────────────────────────────────────────────────────────────────

export default function CalendarScreen() {
  const [calendarMarks, setCalendarMarks] = useState<Record<string, number>>(
    {},
  );
  const [viewDate, setViewDate] = useState<Date>(() => new Date(_today));
  const [isExpanded, setIsExpanded] = useState(false);
  const [selectedDate, setSelectedDate] = useState<string>(todayString);
  const [selectedMemories, setSelectedMemories] = useState<Memory[]>([]);
  const [isLoadingMarks, setIsLoadingMarks] = useState(true);
  const [isLoadingMemories, setIsLoadingMemories] = useState(false);

  const selectedDateRef = useRef(selectedDate);
  selectedDateRef.current = selectedDate;
  const hasMounted = useRef(false);
  const isExpandedRef = useRef(isExpanded);
  isExpandedRef.current = isExpanded;

  // ── animated values ──────────────────────────────────────────────────────

  // Initialise to correctly show the 2 rows containing today
  const initialRows = getMonthRows(_today.getFullYear(), _today.getMonth() + 1);
  const initialStartRow = Math.min(
    getRowForDate(_today, initialRows),
    initialRows.length - 2,
  );

  const heightAnim = useRef(new Animated.Value(2 * CELL_HEIGHT)).current;
  const scrollAnim = useRef(
    new Animated.Value(-(initialStartRow * CELL_HEIGHT)),
  ).current;
  const handleWidthAnim = useRef(new Animated.Value(32)).current;

  // ── colors ────────────────────────────────────────────────────────────────

  const colorScheme = useColorScheme();
  const isDark = colorScheme === "dark";

  const pageBg = isDark ? "#0f1117" : "#f2f4f7";
  const cardBg = isDark ? "#1c2128" : "#ffffff";
  const primaryText = isDark ? "#f3f4f6" : "#111827";
  const secondaryText = isDark ? "#6b7280" : "#9ca3af";
  const separatorColor = isDark ? "#1f2937" : "#f3f4f6";
  const handleColor = isDark ? "#374151" : "#dde1e7";
  const weekdayMuted = isDark ? "#6b7280" : "#9ca3af";

  const badgeBg = useThemeColor(
    { light: "#f0f6ff", dark: "#1e2d45" },
    "background",
  );
  const badgeText = useThemeColor(
    { light: "#3b82f6", dark: "#60a5fa" },
    "tint",
  );

  // ── derived calendar data ─────────────────────────────────────────────────

  const displayYear = viewDate.getFullYear();
  const displayMonth = viewDate.getMonth() + 1;
  const monthRows = getMonthRows(displayYear, displayMonth);
  const monthLabel = `${displayYear}년 ${displayMonth}월`;

  // ── sync animations when viewDate or expanded state changes ──────────────

  useEffect(() => {
    const rows = getMonthRows(displayYear, displayMonth);
    const fullHeight = rows.length * CELL_HEIGHT;
    const collapsed2Height = 2 * CELL_HEIGHT;
    const startRow = Math.min(getRowForDate(viewDate, rows), rows.length - 2);
    const targetScroll = -(startRow * CELL_HEIGHT);

    if (isExpanded) {
      Animated.parallel([
        Animated.spring(heightAnim, {
          toValue: fullHeight,
          friction: 10,
          tension: 80,
          useNativeDriver: false,
        }),
        Animated.spring(scrollAnim, {
          toValue: 0,
          friction: 10,
          tension: 80,
          useNativeDriver: false,
        }),
      ]).start();
    } else {
      Animated.parallel([
        Animated.spring(heightAnim, {
          toValue: collapsed2Height,
          friction: 10,
          tension: 80,
          useNativeDriver: false,
        }),
        Animated.spring(scrollAnim, {
          toValue: targetScroll,
          friction: 10,
          tension: 80,
          useNativeDriver: false,
        }),
      ]).start();
    }
  }, [displayYear, displayMonth, isExpanded, viewDate]); // eslint-disable-line react-hooks/exhaustive-deps

  // ── data loading ──────────────────────────────────────────────────────────

  const loadMarks = useCallback(async () => {
    try {
      const marks = await memoryApi.getCalendarMarks();
      setCalendarMarks(marks);
    } catch (e) {
      console.error("[Calendar] loadMarks:", e);
    } finally {
      setIsLoadingMarks(false);
    }
  }, []);

  const loadMemories = useCallback(async (dateStr: string) => {
    setIsLoadingMemories(true);
    try {
      const list = await memoryApi.getMemoriesByDate(dateStr);
      setSelectedMemories(list);
    } catch (e) {
      console.error("[Calendar] loadMemories:", e);
      setSelectedMemories([]);
    } finally {
      setIsLoadingMemories(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      setIsLoadingMarks(true);
      loadMarks();
      if (hasMounted.current) loadMemories(selectedDateRef.current);
      hasMounted.current = true;
    }, [loadMarks, loadMemories]),
  );

  useEffect(() => {
    loadMemories(selectedDate);
  }, [selectedDate, loadMemories]);

  // ── navigation ────────────────────────────────────────────────────────────

  const goBack = () => {
    setViewDate((prev) =>
      isExpandedRef.current
        ? new Date(prev.getFullYear(), prev.getMonth() - 1, 1)
        : (() => {
            const d = new Date(prev);
            d.setDate(d.getDate() - 14);
            return d;
          })(),
    );
  };

  const goForward = () => {
    setViewDate((prev) =>
      isExpandedRef.current
        ? new Date(prev.getFullYear(), prev.getMonth() + 1, 1)
        : (() => {
            const d = new Date(prev);
            d.setDate(d.getDate() + 14);
            return d;
          })(),
    );
  };

  // ── expand / collapse ─────────────────────────────────────────────────────

  const toggleExpanded = () => {
    const expanding = !isExpanded;
    Animated.spring(handleWidthAnim, {
      toValue: expanding ? 52 : 32,
      friction: 7,
      tension: 120,
      useNativeDriver: false,
    }).start();
    setIsExpanded(expanding);
  };

  // ── memory row renderer ───────────────────────────────────────────────────

  const renderItem = ({ item, index }: { item: Memory; index: number }) => {
    const isLast = index === selectedMemories.length - 1;
    return (
      <Pressable
        onPress={() =>
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
          })
        }
        style={({ pressed }) => [
          styles.memoryRow,
          { opacity: pressed ? 0.55 : 1 },
        ]}
      >
        <View
          style={[
            styles.typeIndicator,
            { backgroundColor: typeColor(item.type) },
          ]}
        />
        <View style={styles.memoryBody}>
          <View style={styles.memoryTop}>
            <View style={[styles.typeBadge, { backgroundColor: badgeBg }]}>
              <Text style={[styles.typeBadgeText, { color: badgeText }]}>
                {typeLabel(item.type)}
              </Text>
            </View>
            <Text style={[styles.memoryTime, { color: secondaryText }]}>
              {formatTime(item.created_at)}
            </Text>
          </View>
          <ThemedText style={styles.memoryContent} numberOfLines={2}>
            {item.content}
          </ThemedText>
        </View>
        {!isLast && (
          <View
            style={[styles.rowSeparator, { backgroundColor: separatorColor }]}
          />
        )}
      </Pressable>
    );
  };

  // ── render ────────────────────────────────────────────────────────────────

  return (
    <SafeAreaView
      style={[styles.container, { backgroundColor: pageBg }]}
      edges={["top"]}
    >
      {/* ── Calendar card ──────────────────────────────────────────────── */}
      <View
        style={[
          styles.card,
          { backgroundColor: cardBg },
          Platform.select({
            ios: {
              shadowColor: "#000",
              shadowOffset: { width: 0, height: 2 },
              shadowOpacity: isDark ? 0.28 : 0.06,
              shadowRadius: 16,
            },
            android: { elevation: isDark ? 6 : 3 },
          }),
        ]}
      >
        {/* Month nav */}
        <View style={styles.monthRow}>
          <Pressable onPress={goBack} hitSlop={10} style={styles.navBtn}>
            <Text style={[styles.navIcon, { color: secondaryText }]}>‹</Text>
          </Pressable>
          <Text style={[styles.monthLabel, { color: primaryText }]}>
            {monthLabel}
          </Text>
          <Pressable onPress={goForward} hitSlop={10} style={styles.navBtn}>
            <Text style={[styles.navIcon, { color: secondaryText }]}>›</Text>
          </Pressable>
        </View>

        {/* Weekday header */}
        <View style={styles.weekdayRow}>
          {WEEKDAYS.map((wd, i) => (
            <Text
              key={wd}
              style={[
                styles.weekdayLabel,
                {
                  color:
                    i === 0 ? "#ef4444" : i === 6 ? "#3b82f6" : weekdayMuted,
                },
              ]}
            >
              {wd}
            </Text>
          ))}
        </View>

        {/* Animated calendar grid */}
        {isLoadingMarks ? (
          <View style={styles.calendarLoader}>
            <ActivityIndicator size="small" color="#4a9eff" />
          </View>
        ) : (
          <Animated.View style={[styles.calendarOuter, { height: heightAnim }]}>
            <Animated.View style={{ transform: [{ translateY: scrollAnim }] }}>
              {monthRows.map((row, ri) => (
                <View
                  key={ri}
                  style={[styles.calendarRow, { height: CELL_HEIGHT }]}
                >
                  {row.map((date, ci) => {
                    const ds = date ? toDateString(date) : `null-${ri}-${ci}`;
                    return (
                      <DayCell
                        key={ds}
                        date={date}
                        count={
                          date ? (calendarMarks[toDateString(date)] ?? 0) : 0
                        }
                        isSelected={
                          !!date && toDateString(date) === selectedDate
                        }
                        isToday={!!date && toDateString(date) === todayString}
                        isDark={isDark}
                        onPress={() => {
                          if (date) setSelectedDate(toDateString(date));
                        }}
                      />
                    );
                  })}
                </View>
              ))}
            </Animated.View>
          </Animated.View>
        )}

        {/* Handle — tap to expand / collapse */}
        <Pressable
          onPress={toggleExpanded}
          style={styles.handleArea}
          hitSlop={12}
        >
          <Animated.View
            style={[
              styles.handle,
              { backgroundColor: handleColor, width: handleWidthAnim },
            ]}
          />
        </Pressable>
      </View>

      {/* ── Memory list ────────────────────────────────────────────────── */}
      <View style={styles.listContainer}>
        <View style={styles.listHeader}>
          <Text style={[styles.listHeaderDate, { color: primaryText }]}>
            {formatDateHeader(selectedDate)}
          </Text>
          {!isLoadingMemories && (
            <Text style={[styles.listHeaderCount, { color: secondaryText }]}>
              {selectedMemories.length}개
            </Text>
          )}
        </View>

        {isLoadingMemories ? (
          <View style={styles.loaderWrapper}>
            <ActivityIndicator size="large" color="#4a9eff" />
          </View>
        ) : (
          <FlatList
            data={selectedMemories}
            renderItem={renderItem}
            keyExtractor={(item) => item.id.toString()}
            showsVerticalScrollIndicator={false}
            contentContainerStyle={
              selectedMemories.length === 0
                ? styles.emptyContent
                : styles.listContent
            }
            ListEmptyComponent={
              <View style={styles.emptyWrapper}>
                <Text style={[styles.emptyText, { color: secondaryText }]}>
                  이 날에 저장된 메모리가 없어요
                </Text>
              </View>
            }
          />
        )}
      </View>
    </SafeAreaView>
  );
}

// ─── styles ───────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  container: { flex: 1 },

  // ── Card ──────────────────────────────────────────────────────────────────
  card: {
    marginHorizontal: 16,
    marginTop: 12,
    borderRadius: 20,
    paddingTop: 18,
  },
  monthRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 20,
    marginBottom: 14,
  },
  navBtn: { width: 32, alignItems: "center", justifyContent: "center" },
  navIcon: { fontSize: 28, lineHeight: 30, fontWeight: "300" },
  monthLabel: { fontSize: 17, fontWeight: "700", letterSpacing: -0.3 },

  weekdayRow: {
    flexDirection: "row",
    paddingHorizontal: 10,
    marginBottom: 2,
  },
  weekdayLabel: {
    flex: 1,
    textAlign: "center",
    fontSize: 12,
    fontWeight: "500",
  },

  calendarLoader: {
    height: 2 * CELL_HEIGHT,
    alignItems: "center",
    justifyContent: "center",
  },

  // Outer wrapper: clips overflowing rows during animation
  calendarOuter: {
    overflow: "hidden",
    paddingHorizontal: 10,
  },
  calendarRow: {
    flexDirection: "row",
  },

  // ── Day cell ──────────────────────────────────────────────────────────────
  dayCell: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  dayCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: "center",
    justifyContent: "center",
  },
  dayCircleSelected: { backgroundColor: "#4a9eff" },
  dayCircleToday: { borderWidth: 1.5, borderColor: "#4a9eff" },
  dayNumber: { fontSize: 15, fontWeight: "500" },
  dotRow: {
    height: 5,
    alignItems: "center",
    justifyContent: "center",
    marginTop: 1,
  },
  dot: { width: 4, height: 4, borderRadius: 2 },

  // ── Handle ────────────────────────────────────────────────────────────────
  handleArea: { alignItems: "center", paddingVertical: 12 },
  handle: {
    // width driven by Animated.Value
    height: 4,
    borderRadius: 2,
  },

  // ── List ──────────────────────────────────────────────────────────────────
  listContainer: { flex: 1, marginTop: 20 },
  listHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: 20,
    marginBottom: 8,
  },
  listHeaderDate: { fontSize: 14, fontWeight: "600", letterSpacing: -0.2 },
  listHeaderCount: { fontSize: 13 },
  listContent: { paddingBottom: 24 },
  emptyContent: { flexGrow: 1 },
  loaderWrapper: { flex: 1, alignItems: "center", paddingTop: 48 },
  emptyWrapper: { flex: 1, alignItems: "center", paddingTop: 48 },
  emptyText: { fontSize: 14 },

  // ── Memory row ────────────────────────────────────────────────────────────
  memoryRow: {
    flexDirection: "row",
    alignItems: "flex-start",
    paddingVertical: 14,
    paddingHorizontal: 20,
    position: "relative",
  },
  typeIndicator: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginTop: 5,
    marginRight: 12,
    flexShrink: 0,
  },
  memoryBody: { flex: 1 },
  memoryTop: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 5,
  },
  typeBadge: { paddingHorizontal: 7, paddingVertical: 2, borderRadius: 5 },
  typeBadgeText: { fontSize: 11, fontWeight: "600" },
  memoryTime: { fontSize: 12 },
  memoryContent: { fontSize: 14, lineHeight: 20 },
  rowSeparator: {
    position: "absolute",
    bottom: 0,
    left: 20,
    right: 0,
    height: StyleSheet.hairlineWidth,
  },
});
