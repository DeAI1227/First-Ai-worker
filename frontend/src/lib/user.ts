const STORAGE_KEY = "ai_investment_terminal_user_id";

export function getStoredUserId(): string {
  if (typeof window === "undefined") {
    return "local-dev";
  }

  return (
    window.localStorage.getItem(STORAGE_KEY) ||
    import.meta.env.VITE_DEFAULT_USER_ID ||
    "local-dev"
  );
}

export function setStoredUserId(userId: string): void {
  if (typeof window === "undefined") {
    return;
  }

  window.localStorage.setItem(STORAGE_KEY, userId.trim() || "local-dev");
}
