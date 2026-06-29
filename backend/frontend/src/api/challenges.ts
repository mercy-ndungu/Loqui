import api from "./client";
import type {
  ChallengeSummary,
  ChallengeUploadResponse,
  ImprovChallengeResponse,
  RandomTopicChallengeResponse,
} from "../types/api";
import { getCsrfHeaders } from "../utils/security";

/** Fetch 5 random improv images (public GET endpoint). */
export async function generateImprovChallenge(): Promise<ImprovChallengeResponse> {
  const { data } = await api.get<ImprovChallengeResponse>("/challenges/improv/generate");
  return data;
}

/** Generate a dynamic speaking topic via Claude (public POST endpoint). */
export async function generateRandomTopic(): Promise<RandomTopicChallengeResponse> {
  const { data } = await api.post<RandomTopicChallengeResponse>("/challenges/topics/random");
  return data;
}

export async function listChallenges(): Promise<ChallengeSummary[]> {
  const { data } = await api.get<ChallengeSummary[]>("/challenges");
  return data;
}

export async function uploadChallengeRecording(
  challengeId: string,
  challengeType: "improv" | "topic",
  videoFile: Blob,
  durationSeconds: number,
  filename: string,
  onProgress?: (percent: number) => void,
): Promise<ChallengeUploadResponse> {
  const form = new FormData();
  form.append("challenge_id", challengeId);
  form.append("challenge_type", challengeType);
  form.append("duration_seconds", String(durationSeconds));
  form.append("video_file", videoFile, filename);

  const { data } = await api.post<ChallengeUploadResponse>("/challenges/upload", form, {
    headers: { "Content-Type": "multipart/form-data", ...getCsrfHeaders() },
    onUploadProgress: (event) => {
      if (event.total && onProgress) {
        onProgress(Math.round((event.loaded * 100) / event.total));
      }
    },
  });
  return data;
}
