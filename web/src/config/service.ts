export const baseUrl = () => {
  if (import.meta.env.MODE === "development") {
    return "http://localhost:8000";
  }
  return window.location.origin;
};
