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
