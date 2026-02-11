import React, {
  createContext,
  type ReactNode,
  useContext,
  useEffect,
  useReducer,
} from "react";
import type { User } from "@/services/api/types";
import { secureStorage } from "@/lib/secure-storage";
import { authApi } from "@/services/api/auth";

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

type AuthAction =
  | { type: "SET_USER"; payload: User }
  | { type: "SET_LOADING"; payload: boolean }
  | { type: "LOGOUT" }
  | { type: "RESTORE_SESSION"; payload: User | null };

interface AuthContextType extends AuthState {
  login: (sessionToken: string, user: User) => Promise<void>;
  logout: () => Promise<void>;
  updateUser: (user: User) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function authReducer(state: AuthState, action: AuthAction): AuthState {
  switch (action.type) {
    case "SET_USER":
      return {
        ...state,
        user: action.payload,
        isAuthenticated: true,
        isLoading: false,
      };
    case "SET_LOADING":
      return { ...state, isLoading: action.payload };
    case "LOGOUT":
      return { user: null, isAuthenticated: false, isLoading: false };
    case "RESTORE_SESSION":
      return {
        user: action.payload,
        isAuthenticated: !!action.payload,
        isLoading: false,
      };
    default:
      return state;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(authReducer, {
    user: null,
    isLoading: true,
    isAuthenticated: false,
  });

  // Restore session on app start
  useEffect(() => {
    async function restoreSession() {
      try {
        const token = await secureStorage.getSessionToken();

        if (token) {
          // First, load cached user data for fast UI
          const cachedUserData = await secureStorage.getUserData();
          if (cachedUserData) {
            try {
              const cachedUser = JSON.parse(cachedUserData);
              dispatch({
                type: "RESTORE_SESSION",
                payload: cachedUser,
              });
            } catch (parseError) {
              console.error(
                "[Auth] Failed to parse cached user data:",
                parseError,
              );
            }
          }

          // Then validate token and refresh user data in background
          try {
            const user = await authApi.getCurrentUser();
            await secureStorage.setUserData(JSON.stringify(user));
            dispatch({
              type: "SET_USER",
              payload: user,
            });
            return;
          } catch (error) {
            // Token is invalid, clear all stored data
            await secureStorage.clearAll();
            dispatch({ type: "LOGOUT" });
            return;
          }
        }
      } catch (error) {
        console.error("[Auth] Failed to restore session:", error);
        await secureStorage.clearAll();
      }
      dispatch({ type: "RESTORE_SESSION", payload: null });
    }

    restoreSession();
  }, []);

  const login = async (sessionToken: string, user: User) => {
    await secureStorage.setSessionToken(sessionToken);
    await secureStorage.setUserData(JSON.stringify(user));
    dispatch({ type: "SET_USER", payload: user });
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch (error) {
      console.error("Logout API call failed:", error);
    } finally {
      await secureStorage.clearAll();
      dispatch({ type: "LOGOUT" });
    }
  };

  const updateUser = (user: User) => {
    dispatch({ type: "SET_USER", payload: user });
  };

  return (
    <AuthContext.Provider value={{ ...state, login, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
