import { createContext, useCallback, useContext, useEffect, useState } from "react";
import apiClient from "../api/client";

const AuthContext = createContext(null);
const TOKEN_KEY = "token";

function isTokenValid(token) {
    if (!token) return false;
    try {
        const payload = JSON.parse(atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
        return Boolean(payload.sub) && (!payload.exp || payload.exp * 1000 > Date.now());
    } catch {
        return false;
    }
}

export function AuthProvider({ children }) {
    const [token, setToken] = useState(() => localStorage.getItem(TOKEN_KEY));
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    const clearSession = useCallback(() => {
        localStorage.removeItem(TOKEN_KEY);
        setToken(null);
        setUser(null);
    }, []);

    const reloadIdentity = useCallback(async (accessToken) => {
        const bearer = accessToken ?? localStorage.getItem(TOKEN_KEY);
        if (!bearer) throw new Error("Not authenticated");
        const { data } = await apiClient.get("/auth/me", {
            headers: { Authorization: `Bearer ${bearer}` },
        });
        setUser(data);
        return data;
    }, []);

    useEffect(() => {
        let cancelled = false;

        async function restoreSession() {
            setLoading(true);
            try {
                let accessToken = localStorage.getItem(TOKEN_KEY);
                if (!isTokenValid(accessToken)) {
                    const response = await apiClient.post("/auth/refresh");
                    accessToken = response.data.access_token;
                    localStorage.setItem(TOKEN_KEY, accessToken);
                }
                const { data } = await apiClient.get("/auth/me", {
                    headers: { Authorization: `Bearer ${accessToken}` },
                });
                if (!cancelled) {
                    setToken(accessToken);
                    setUser(data);
                }
            } catch {
                if (!cancelled) clearSession();
            } finally {
                if (!cancelled) setLoading(false);
            }
        }

        restoreSession();
        return () => { cancelled = true; };
    }, [clearSession]);

    const login = async (username, password) => {
        const formData = new URLSearchParams({ username, password });
        const response = await apiClient.post("/auth/login", formData.toString(), {
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
        });
        const accessToken = response.data.access_token;
        if (!isTokenValid(accessToken)) throw new Error("Invalid authentication token.");

        localStorage.setItem(TOKEN_KEY, accessToken);
        try {
            await reloadIdentity(accessToken);
            setToken(accessToken);
        } catch (error) {
            clearSession();
            throw error;
        }
        return response.data;
    };

    const logout = async () => {
        try {
            await apiClient.post("/auth/logout");
        } finally {
            clearSession();
        }
    };

    const permissions = user?.permissions ?? [];
    const hasPermission = (permission) => permissions.includes(permission);

    return (
        <AuthContext.Provider value={{
            user, token, permissions, hasPermission,
            loading, login, logout, reloadIdentity,
        }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) throw new Error("useAuth must be used within AuthProvider");
    return context;
}