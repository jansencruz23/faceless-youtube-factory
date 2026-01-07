import { Project, ProjectDetail, Voice, YouTubeConnection, YouTubeMetadata} from "@/types";

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Helper to build full URLs for static files served by the backend
export function getStaticUrl(path: string): string {
    if (!path) return "";
    // If already a full URL, return as-is
    if (path.startsWith("http://") || path.startsWith("https://")) {
        return path;
    }
    // Prepend API base to relative paths
    return `${API_BASE}${path.startsWith("/") ? "" : "/"}${path}`;
}

// Core fetch function with auth support
async function fetchAPI<T>(
    endpoint: string,
    options?: RequestInit & { token?: string | null }
): Promise<T> {
    const url = `${API_BASE}${endpoint}`;

    const headers: Record<string, string> = {
        "Content-Type": "application/json",
        ...options?.headers as Record<string, string>,
    };

    // Add authorization header if token provided
    if (options?.token) {
        headers["Authorization"] = `Bearer ${options.token}`;
    }

    const response = await fetch(url, {
        headers,
        ...options,
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Unknown error"}));
        throw new Error(error.detail || `API Error: ${response.status}`);
    }

    return response.json();
}

// File upload helper with auth
async function uploadFile(
    endpoint: string,
    file: File,
    token?: string | null
): Promise<{ url: string }> {
    const formData = new FormData();
    formData.append("file", file);
    
    const headers: Record<string, string> = {};
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }
    
    const response = await fetch(`${API_BASE}${endpoint}`, {
        method: "POST",
        headers,
        body: formData,
    });
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Upload failed" }));
        throw new Error(error.detail || `Upload Error: ${response.status}`);
    }
    
    return response.json();
}

// ============ Projects API ============

export async function createProject(data: {
    title: string;
    script_prompt: string;
    auto_upload: boolean;
    video_format?: "horizontal" | "vertical";
    image_mode?: "per_scene" | "single" | "upload" | "none";
    scenes_per_image?: number;
    background_image_url?: string;
    background_video_url?: string;
    background_music_url?: string;
    music_volume?: number;
    enable_captions?: boolean;
}, token?: string | null): Promise<Project> {
    return fetchAPI("/api/v1/projects", {
        method: "POST",
        body: JSON.stringify(data),
        token,
    });
}

export async function listProjects(
    page = 1,
    pageSize = 20,
    token?: string | null,
    category?: string
): Promise<{ items: Project[]; total: number; page: number; page_size: number }> {
    let url = `/api/v1/projects?page=${page}&page_size=${pageSize}`;
    if (category) {
        url += `&category=${encodeURIComponent(category)}`;
    }
    return fetchAPI(url, { token });
}

export async function getProject(id: string, token?: string | null): Promise<ProjectDetail> {
    return fetchAPI(`/api/v1/projects/${id}`, { token });
}

export async function regenerateAudio(projectId: string, token?: string | null): Promise<{ message: string }> {
    return fetchAPI(`/api/v1/projects/${projectId}/regenerate-audio`, {
        method: "POST",
        token,
    });
}

export async function regenerateVideo(projectId: string, token?: string | null): Promise<{ message: string }> {
    return fetchAPI(`/api/v1/projects/${projectId}/regenerate-video`, {
        method: "POST",
        token,
    });
}

export async function cancelProject(projectId: string, token?: string | null): Promise<{ message: string }> {
    return fetchAPI(`/api/v1/projects/${projectId}/cancel`, {
        method: "POST",
        token,
    });
}

export async function deleteProject(projectId: string, token?: string | null): Promise<{ message: string }> {
    return fetchAPI(`/api/v1/projects/${projectId}`, {
        method: "DELETE",
        token,
    });
} 

// ============ Presets (no auth needed) ============

export interface PresetVideo {
    id: string;
    name: string;
    url: string;
    thumbnail: string | null;
}

export interface PresetMusic {
    id: string;
    name: string;
    url: string;
}

export async function getPresetVideos(): Promise<{ presets: PresetVideo[] }> {
    return fetchAPI("/api/v1/projects/preset-videos");
}

export async function getPresetMusic(): Promise<{ presets: PresetMusic[] }> {
    return fetchAPI("/api/v1/projects/preset-music");
}

// ============ File Uploads ============

export async function uploadBackgroundImage(file: File, token?: string | null): Promise<{ url: string }> {
    return uploadFile("/api/v1/projects/upload-background", file, token);
}

export async function uploadVideo(file: File, token?: string | null): Promise<{ url: string }> {
    return uploadFile("/api/v1/projects/upload-video", file, token);
}

export async function uploadMusic(file: File, token?: string | null): Promise<{ url: string }> {
    return uploadFile("/api/v1/projects/upload-music", file, token);
}

// ============ Casting API ============

export async function listVoices(): Promise<{ voices: Voice[] }> {
    // Voices list doesn't need auth
    return fetchAPI("/api/v1/voices");
}

export async function updateCast(
    projectId: string,
    assignments: Record<string, { voice_id: string; pitch: string; rate: string }>,
    token?: string | null
): Promise<{ message: string }> {
    return fetchAPI(`/api/v1/projects/${projectId}/cast`, {
        method: "PUT",
        body: JSON.stringify({ assignments }),
        token,
    });
}

export async function previewVoice(
    projectId: string,
    data: {
        character: string;
        voice_settings: { voice_id: string; pitch: string; rate: string };
        sample_text: string;
    },
    token?: string | null
): Promise<{ audio_url: string }> {
    return fetchAPI(`/api/v1/projects/${projectId}/preview-voice`, {
        method: "POST",
        body: JSON.stringify(data),
        token,
    });
}

// ============ YouTube API ============

export async function getYouTubeAuthUrl(token?: string | null): Promise<{ auth_url: string; state: string }> {
    return fetchAPI("/api/v1/youtube/auth-url", { token });
}

export async function getYouTubeConnection(token?: string | null): Promise<YouTubeConnection> {
    return fetchAPI("/api/v1/youtube/connection", { token });
}

export async function disconnectYouTube(token?: string | null): Promise<{ message: string }> {
    return fetchAPI("/api/v1/youtube/disconnect", {
        method: "DELETE",
        token,
    });
}   

export async function generateYouTubeMetadata(
    projectId: string,
    context?: string,
    token?: string | null
): Promise<YouTubeMetadata> {
    return fetchAPI(`/api/v1/youtube/projects/${projectId}/generate-metadata`, {
        method: "POST",
        body: JSON.stringify({ video_context: context }),
        token,
    });
}

export async function uploadToYouTube(
    projectId: string,
    metadata: {
        title: string,
        description: string;
        tags: string[],
        category_id: string;
        privacy_status: "public" | "private" | "unlisted";
    },
    token?: string | null
): Promise<{ message: string }> {
    return fetchAPI(`/api/v1/youtube/projects/${projectId}/upload-to-youtube`, {
        method: "POST",
        body: JSON.stringify(metadata),
        token,
    });
}

// ============ Automation API ============

export async function listAutomationProjects(
    apiKey: string,
    category?: string,
    page = 1,
    pageSize = 50
): Promise<{ items: Project[]; total: number; page: number; page_size: number }> {
    let url = `/api/v1/automation/projects?page=${page}&page_size=${pageSize}`;
    if (category) {
        url += `&category=${encodeURIComponent(category)}`;
    }
    return fetchAPI(url, {
        headers: {
            "X-API-Key": apiKey,
        },
    });
}