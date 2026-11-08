"use client";

import { useEffect, useState, useCallback } from "react";
import { User, getUser, getToken, logoutUser, fetchMe } from "./auth";

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [ready, setReady] = useState(false);

  const sync = useCallback(() => {
    const current = getUser();
    setUser(current);
    setReady(true);
  }, []);

  useEffect(() => {
    sync();

    // Verify token with backend if we have a token stored
    const token = getToken();
    if (token) {
      fetchMe()
        .then((u) => {
          if (u) setUser(u);
        })
        .catch(() => {
          // Token expired or invalid
        });
    }

    const onAuthChange = () => {
      sync();
    };

    window.addEventListener("storage", onAuthChange);
    window.addEventListener("rethread_auth_change", onAuthChange);

    return () => {
      window.removeEventListener("storage", onAuthChange);
      window.removeEventListener("rethread_auth_change", onAuthChange);
    };
  }, [sync]);

  const signedIn = Boolean(user);
  const isLoggedIn = Boolean(user);

  return {
    user,
    ready,
    signedIn,
    isLoggedIn,
    logout: logoutUser,
    refresh: sync,
  };
}

