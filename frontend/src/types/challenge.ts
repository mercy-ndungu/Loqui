import type { FeedbackScores } from "./feedback";

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
