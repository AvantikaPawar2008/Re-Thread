/**
 * RE-THREAD authentication client.
 * Manages user authentication tokens, profiles, and backend session sync.
 */

export interface User {
  id: number;
  full_name: string;
  name?: string;
  email: string;
  city: string;
  bio: string;
  interests: string;
  created_at?: string | null;
}

export const INTERESTS = [
  "Mending & Repair",
  "Upcycling Crafts",
  "Donation & Charity",
  "Textile Recycling",
  "Thrifting & Resale",
  "Eco-friendly Care",
] as const;

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const TOKEN_KEY = "rethread_auth_token";
const USER_KEY = "rethread_auth_user";

export function validateEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY);
}

export function getUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY) || sessionStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

function notifyAuthChange() {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new Event("rethread_auth_change"));
}

function normalizeUser(user: any): User {
  if (!user) return user;
  return {
    ...user,
    name: user.name || user.full_name || "",
  };
}

function storeSession(token: string, user: User, remember: boolean = true) {
  if (typeof window === "undefined") return;
  const normalized = normalizeUser(user);
  if (remember) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(normalized));
  } else {
    sessionStorage.setItem(TOKEN_KEY, token);
    sessionStorage.setItem(USER_KEY, JSON.stringify(normalized));
  }
  notifyAuthChange();
}

export function logoutUser(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(USER_KEY);
  notifyAuthChange();
}

export async function loginUser(email: string, password: string, remember: boolean = true): Promise<User> {
  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email: email.trim().toLowerCase(), password }),
  });

  if (!res.ok) {
    const errorText = await res.text();
    let message = "Login failed.";
    try {
      const parsed = JSON.parse(errorText);
      message = parsed.detail || message;
    } catch {
      // fallback
    }
    throw new Error(message);
  }

  const data = await res.json();
  storeSession(data.token, data.user, remember);
  return data.user;
}

export async function registerUser(data: {
  full_name: string;
  email: string;
  password: string;
  city?: string;
}): Promise<User> {
  const res = await fetch(`${API_BASE_URL}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      full_name: data.full_name.trim(),
      email: data.email.trim().toLowerCase(),
      password: data.password,
      city: data.city || "Pune",
    }),
  });

  if (!res.ok) {
    const errorText = await res.text();
    let message = "Account registration failed.";
    try {
      const parsed = JSON.parse(errorText);
      message = parsed.detail || message;
    } catch {
      // fallback
    }
    throw new Error(message);
  }

  const result = await res.json();
  storeSession(result.token, result.user, true);
  return result.user;
}

export async function updateProfile(patch: {
  full_name?: string;
  city?: string;
  bio?: string;
  interests?: string;
}): Promise<User> {
  const token = getToken();
  if (!token) {
    throw new Error("You must be logged in to update your profile.");
  }

  const res = await fetch(`${API_BASE_URL}/auth/me`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(patch),
  });

  if (!res.ok) {
    const errorText = await res.text();
    let message = "Profile update failed.";
    try {
      const parsed = JSON.parse(errorText);
      message = parsed.detail || message;
    } catch {
      // fallback
    }
    throw new Error(message);
  }

  const updatedUser = (await res.json()) as User;
  // Preserve storage location (local vs session)
  if (localStorage.getItem(TOKEN_KEY)) {
    localStorage.setItem(USER_KEY, JSON.stringify(updatedUser));
  } else {
    sessionStorage.setItem(USER_KEY, JSON.stringify(updatedUser));
  }
  notifyAuthChange();
  return updatedUser;
}

export async function fetchMe(): Promise<User | null> {
  const token = getToken();
  if (!token) return null;

  try {
    const res = await fetch(`${API_BASE_URL}/auth/me`, {
      method: "GET",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    if (res.ok) {
      const user = (await res.json()) as User;
      if (localStorage.getItem(TOKEN_KEY)) {
        localStorage.setItem(USER_KEY, JSON.stringify(user));
      } else {
        sessionStorage.setItem(USER_KEY, JSON.stringify(user));
      }
      return user;
    } else if (res.status === 401) {
      logoutUser();
      return null;
    }
  } catch {
    // Network or server error - keep stored user
  }
  return getUser();
}
