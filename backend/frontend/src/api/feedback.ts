import api from "./client";
import type { FeedbackResponse } from "../types/api";

export async function analyzeFeedback(
  recording_id: string,
  transcription: string,
): Promise<FeedbackResponse> {
  const { data } = await api.post<FeedbackResponse>("/feedback/analyze", {
    recording_id,
    transcription,
  });
  return data;
}

export async function getFeedback(recording_id: string): Promise<FeedbackResponse> {
  const { data } = await api.get<FeedbackResponse>(`/feedback/${recording_id}`);
  return data;
}
