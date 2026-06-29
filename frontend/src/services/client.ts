import axios from "axios";
import { API_BASE_URL, getCsrfHeaders, initCsrfToken } from "@/utils/security";

export { API_BASE_URL };

const api = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
    Accept: "application/json",
  },
  timeout: 120_000,
});

api.interceptors.request.use((config) => {
  Object.assign(config.headers, getCsrfHeaders());
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (import.meta.env.DEV && error.response) {
      console.debug("[Loqui API]", error.response.status, error.config?.url, error.response.data);
    }
    if (error.response?.status === 401) {
      window.dispatchEvent(new CustomEvent("loqui:unauthorized"));
    }
    if (error.response?.status === 403 && error.config && !error.config._csrfRetry) {
      await initCsrfToken();
      error.config._csrfRetry = true;
      Object.assign(error.config.headers, getCsrfHeaders());
      return api.request(error.config);
    }
    return Promise.reject(error);
  },
);

export default api;
