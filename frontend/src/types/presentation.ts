export interface Presentation {
  id: string;
  title: string;
  created_at: string;
  file_url: string;
}

export type PresentationType = "pitch" | "interview" | "networking" | "general";

export interface PresentationDetail extends Presentation {
  presentation_type: PresentationType;
  url: string | null;
}
