import { apiClient } from "./client";
import type { Memory } from "./types";

export const memoryApi = {
  async getMemories(limit = 50, offset = 0): Promise<Memory[]> {
    const response = await apiClient.get<Memory[]>(
      `/api/v1/assistant/memories?limit=${limit}&offset=${offset}`,
    );
    return response as Memory[];
  },

  async getCalendarMarks(): Promise<Record<string, number>> {
    const response = await apiClient.get<Record<string, number>>(
      "/api/v1/assistant/memories/calendar-marks",
    );
    return response as Record<string, number>;
  },

  async getMemoriesByDate(date: string): Promise<Memory[]> {
    const response = await apiClient.get<Memory[]>(
      `/api/v1/assistant/memories/by-date?date=${date}`,
    );
    return response as Memory[];
  },

  async deleteMemory(memoryId: number): Promise<void> {
    await apiClient.delete(`/api/v1/assistant/memories/${memoryId}`);
  },
};
