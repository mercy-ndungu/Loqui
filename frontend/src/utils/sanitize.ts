import DOMPurify from "dompurify";

/** Sanitize user-provided text before rendering in the DOM. */
export function sanitizeText(input: string): string {
  return DOMPurify.sanitize(input, { ALLOWED_TAGS: [], ALLOWED_ATTR: [] });
}

/** Sanitize a plain string for use in form fields (trim + strip control chars). */
export function sanitizeInput(input: string): string {
  return input.replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, "").trim();
}
