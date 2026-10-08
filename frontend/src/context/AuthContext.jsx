import { createContext, useContext, useEffect, useState } from "react";
import apiClient from "../api/client";
import { readStoredValue, writeStoredValue, removeStoredValue } from "../utils/storage.js";

const AuthContext = createContext(null);

function getUserFromToken(token) {
    if (!token) return null;

    try {
        const payload = JSON.parse(atob(token.split(".")[1]));

        if (!payload.sub || !payload.username || !payload.role) {
            return null;
        }

        if (payload.exp && payload.exp * 1000 < Date.now()) {
            return null;
        }

        return {
            id: Number(payload.sub),
            username: payload.username,
            role: payload.role,
        };
    } catch {
        return null;
    }
}

export function AuthProvider({ children }) {
    const [token, setToken] = useState(() => localStorage.getItem("token"));
    const [user, setUser] = useState(() =>
        getUserFromToken(localStorage.getItem("token"))
    );

    useEffect(() => {
        if (!token) {
            setUser(null);
            return;
        }

        const currentUser = getUserFromToken(token);

        if (!currentUser) {
            localStorage.removeItem("token");
            setToken(null);
            setUser(null);
            return;
        }

        setUser(currentUser);
    }, [token]);

    const login = async (username, password) => {
        const formData = new URLSearchParams({ username, password });

        const response = await apiClient.post(
            "/auth/login",
            formData.toString(),
            {
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            }
        );

        const accessToken = response.data.access_token;
        const currentUser = getUserFromToken(accessToken);

        if (!currentUser) {
            throw new Error("Invalid authentication token.");
        }

        localStorage.setItem("token", accessToken);
        setToken(accessToken);
        setUser(currentUser);

        return response.data;
    };

    const logout = () => {
        localStorage.removeItem("token");
        setToken(null);
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, token, login, logout }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    return useContext(AuthContext);
}
