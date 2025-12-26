"use client";

import { useAuth } from "@clerk/nextjs";
import { useCallback } from "react";
import { API_BASE } from "./api";

/**
 * Hook that returns fetch function with Clerk auth token included.
 * Use this for all authenticated API calls.
 */
export function useAuthFetch() {
    const { getToken } = useAuth();

    const authFetch = useCallback(
        async <T>(
            endpoint: string,
            options?: RequestInit
        ): Promise<T> => {
            const token = await getToken();
            const url = `${API_BASE}${endpoint}`;

            const headers: Record<string, string> = {
                "Content-Type": "application/json",
                ...(options?.headers as Record<string, string>),
            };

            if (token) {
                headers["Authorization"] = `Bearer ${token}`;
            }

            const response = await fetch(url, {
                ...options,
                headers,
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({
                    detail: "Unknown error",
                }));
                throw new Error(error.detail || `API Error: ${response.status}`);
            }

            return response.json();
        },
        [getToken]
    );

    return authFetch;
}

/**
 * Helper to get auth headers for external use (e.g., with react-query).
 */
export function useAuthHeaders() {
    const { getToken } = useAuth();

    const getAuthHeaders = useCallback(async (): Promise<Record<string, string>> => {
        const token = await getToken();
        if (token) {
            return { Authorization: `Bearer ${token}` };
        }
        return {};
    }, [getToken]);

    return getAuthHeaders;
}
