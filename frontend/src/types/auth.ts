export interface AuthMessageResponse {
  message: string;
  user: { id: string; email: string; full_name?: string };
}
