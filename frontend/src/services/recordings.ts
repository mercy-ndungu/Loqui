import api from "./client";
import type { RecordingUploadResponse } from "@/types";
import { getCsrfHeaders } from "@/utils/security";

export async function uploadRecording(
  presentation_id: string,
  video_file: Blob,
  duration_seconds: number,
  filename: string,
  onProgress?: (percent: number) => void,
): Promise<RecordingUploadResponse> {
  const form = new FormData();
  form.append("presentation_id", presentation_id);
  form.append("duration_seconds", String(duration_seconds));
  form.append("video_file", video_file, filename);

  const { data } = await api.post<RecordingUploadResponse>("/recordings/upload", form, {
    headers: { "Content-Type": "multipart/form-data", ...getCsrfHeaders() },
    onUploadProgress: (event) => {
      if (event.total && onProgress) {
        onProgress(Math.round((event.loaded * 100) / event.total));
      }
    },
  });
  return data;
}

export async function getRecording(id: string) {
  const { data } = await api.get(`/recordings/${id}`);
  return data;
}

export async function deleteRecording(id: string): Promise<void> {
  await api.delete(`/recordings/${id}`);
}
