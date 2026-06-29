import api from "./client";
import type { Presentation, PresentationType } from "../types/api";
import { getCsrfHeaders } from "../utils/security";

export async function listPresentations(): Promise<Presentation[]> {
  const { data } = await api.get<Presentation[]>("/presentations");
  return data;
}

export async function uploadPresentation(
  file: File,
  presentation_type: PresentationType,
  onProgress?: (percent: number) => void,
): Promise<{ id: string; title: string; url: string; created_at: string }> {
  const form = new FormData();
  form.append("file", file);
  form.append("presentation_type", presentation_type);

  const { data } = await api.post("/presentations/upload", form, {
    headers: { "Content-Type": "multipart/form-data", ...getCsrfHeaders() },
    onUploadProgress: (event) => {
      if (event.total && onProgress) {
        onProgress(Math.round((event.loaded * 100) / event.total));
      }
    },
  });
  return data;
}

export async function deletePresentation(id: string): Promise<void> {
  await api.delete(`/presentations/${id}`);
}

export async function getPresentation(id: string) {
  const { data } = await api.get(`/presentations/${id}`);
  return data;
}
