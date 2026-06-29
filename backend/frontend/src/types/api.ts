/** Shared API types matching the Loqui backend. */

export interface User {
  id: string;
  email: string;
  full_name: string;
  created_at: string;
}

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

export interface ImprovImage {
  url: string;
  alt: string;
}

export interface ImprovChallengeResponse {
  challenge_id: string;
  images: ImprovImage[];
}

export interface RandomTopicChallengeResponse {
  challenge_id: string;
  topic: string;
}

export interface ChallengeSummary {
  id: string;
  challenge_type: "improv" | "topic";
  title: string;
  topic_or_images: string | null;
  completed_at: string | null;
  overall_score: number | null;
}

export interface ChallengeUploadResponse {
  challenge_id: string;
  feedback_scores: FeedbackScores;
  overall_score: number;
  improvements: string[];
  strengths: string[];
  feedback_text: Record<string, string>;
}

export interface RecordingUploadResponse {
  id: string;
  video_url: string;
  transcription: string;
  created_at: string;
}

export interface FeedbackScores {
  grammar: number;
  vocabulary: number;
  filler_words_count: number;
  pacing: number;
  overall: number;
}

export interface FeedbackResponse {
  scores: FeedbackScores;
  feedback_text: Record<string, string>;
  improvements: string[];
  strengths: string[];
}

export interface AuthMessageResponse {
  message: string;
  user: { id: string; email: string; full_name?: string };
}
