"use client";

import { useAuth } from "@clerk/nextjs";
import { useCallback, useMemo } from "react";
import * as api from "./api";

/**
 * Hook that returns all API functions with automatic auth token injection.
 * Use this in components instead of importing from api.ts directly.
 */
export function useApi() {
    const { getToken } = useAuth();

    // Wrap each API function to automatically include the token
    const authedApi = useMemo(() => ({
        // Projects
        createProject: async (data: Parameters<typeof api.createProject>[0]) => {
            const token = await getToken();
            return api.createProject(data, token);
        },
        listProjects: async (page = 1, pageSize = 20, category?: string) => {
            const token = await getToken();
            return api.listProjects(page, pageSize, token, category);
        },
        getProject: async (id: string) => {
            const token = await getToken();
            return api.getProject(id, token);
        },
        regenerateAudio: async (projectId: string) => {
            const token = await getToken();
            return api.regenerateAudio(projectId, token);
        },
        regenerateVideo: async (projectId: string) => {
            const token = await getToken();
            return api.regenerateVideo(projectId, token);
        },
        cancelProject: async (projectId: string) => {
            const token = await getToken();
            return api.cancelProject(projectId, token);
        },
        deleteProject: async (projectId: string) => {
            const token = await getToken();
            return api.deleteProject(projectId, token);
        },

        // Uploads
        uploadBackgroundImage: async (file: File) => {
            const token = await getToken();
            return api.uploadBackgroundImage(file, token);
        },
        uploadVideo: async (file: File) => {
            const token = await getToken();
            return api.uploadVideo(file, token);
        },
        uploadMusic: async (file: File) => {
            const token = await getToken();
            return api.uploadMusic(file, token);
        },

        // Presets (no auth needed)
        getPresetVideos: api.getPresetVideos,
        getPresetMusic: api.getPresetMusic,

        // Casting
        listVoices: api.listVoices,
        updateCast: async (projectId: string, assignments: Parameters<typeof api.updateCast>[1]) => {
            const token = await getToken();
            return api.updateCast(projectId, assignments, token);
        },
        previewVoice: async (projectId: string, data: Parameters<typeof api.previewVoice>[1]) => {
            const token = await getToken();
            return api.previewVoice(projectId, data, token);
        },

        // YouTube
        getYouTubeAuthUrl: async () => {
            const token = await getToken();
            return api.getYouTubeAuthUrl(token);
        },
        getYouTubeConnection: async () => {
            const token = await getToken();
            return api.getYouTubeConnection(token);
        },
        disconnectYouTube: async () => {
            const token = await getToken();
            return api.disconnectYouTube(token);
        },
        generateYouTubeMetadata: async (projectId: string, context?: string) => {
            const token = await getToken();
            return api.generateYouTubeMetadata(projectId, context, token);
        },
        uploadToYouTube: async (projectId: string, metadata: Parameters<typeof api.uploadToYouTube>[1]) => {
            const token = await getToken();
            return api.uploadToYouTube(projectId, metadata, token);
        },
    }), [getToken]);

    return authedApi;
}

/**
 * Helper hook to get a token-fetching function for use with react-query.
 * Returns a function that gets the current auth token.
 */
export function useAuthToken() {
    const { getToken } = useAuth();
    return useCallback(() => getToken(), [getToken]);
}
