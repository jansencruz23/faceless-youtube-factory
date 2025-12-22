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

async function fetchAPI<T>(
    endpoint: string,
    options?: RequestInit
): Promise<T> {
    const url = `${API_BASE}${endpoint}`;

    const response = await fetch(url, {
        headers: {
            "Content-Type": "application/json",
            ...options?.headers,
        },
        ...options,
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Unknown error"}));
        throw new Error(error.detail || `API Error: ${response.status}`);
    }

    return response.json();
}

// Projects
export async function createProject(data: {
    title: string;
    script_prompt: string;
    auto_upload: boolean;
    image_mode?: "per_scene" | "single" | "upload" | "none";
    scenes_per_image?: number;
    background_image_url?: string;
}): Promise<Project> {
    return fetchAPI("/api/v1/projects", {
        method: "POST",
        body: JSON.stringify(data),
    });
}

export async function uploadBackgroundImage(file: File): Promise<{ url: string }> {
    const formData = new FormData();
    formData.append("file", file);
    
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const response = await fetch(`${baseUrl}/api/v1/projects/upload-background`, {
        method: "POST",
        body: formData,
    });
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Upload failed" }));
        throw new Error(error.detail || `Upload Error: ${response.status}`);
    }
    
    return response.json();
}

export async function listProjects(
    page = 1,
    pageSize = 20
): Promise<{ items: Project[]; total: number; page: number; page_size: number }> {
    return fetchAPI(`/api/v1/projects?page=${page}&page_size=${pageSize}`);
}

export async function getProject(id: string): Promise<ProjectDetail> {
    return fetchAPI(`/api/v1/projects/${id}`);
}

export async function regenerateAudio(projectId: string): Promise<{ message: string }> {
    return fetchAPI(`/api/v1/projects/${projectId}/regenerate-audio`, {
        method: "POST"
    });
}

export async function regenerateVideo(projectId: string): Promise<{ message: string }> {
    return fetchAPI(`/api/v1/projects/${projectId}/regenerate-video`, {
        method: "POST",
    });
}

export async function cancelProject(projectId: string): Promise<{ message: string }> {
    return fetchAPI(`/api/v1/projects/${projectId}/cancel`, {
        method: "POST",
    });
}

export async function deleteProject(projectId: string): Promise<{ message: string }> {
    return fetchAPI(`/api/v1/projects/${projectId}`, {
        method: "DELETE",
    });
} 

// Casting
export async function listVoices(): Promise<{ voices: Voice[] }> {
    return fetchAPI("/api/v1/voices");
}

export async function updateCast(
    projectId: string,
    assignments: Record<string, { voice_id: string; pitch: string; rate: string }>
): Promise<{ message: string }> {
    return fetchAPI(`/api/v1/projects/${projectId}/cast`, {
        method: "PUT",
        body: JSON.stringify({ assignments }),
    });
}

export async function previewVoice(
    projectId: string,
    data: {
        character: string;
        voice_settings: { voice_id: string; pitch: string; rate: string };
        sample_text: string;
    }
): Promise<{ audio_url: string }> {
    return fetchAPI(`/api/v1/projects/${projectId}/preview-voice`, {
        method: "POST",
        body: JSON.stringify(data),
    });
}

// YouTube
export async function getYouTubeAuthUrl(): Promise<{ auth_url: string; state: string }> {
    return fetchAPI("/api/v1/youtube/auth-url");
}

export async function getYouTubeConnection(): Promise<YouTubeConnection> {
    return fetchAPI("/api/v1/youtube/connection");
}

export async function disconnectYouTube(): Promise<{ message: string }> {
    return fetchAPI("/api/v1/youtube/disconnect", {
        method: "DELETE",
    });
}   

export async function generateYouTubeMetadata(
    projectId: string,
    context?: string
): Promise<YouTubeMetadata> {
    return fetchAPI(`/api/v1/youtube/projects/${projectId}/generate-metadata`, {
        method: "POST",
        body: JSON.stringify({ video_context: context }),
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
    }
): Promise<{ message: string }> {
    return fetchAPI(`/api/v1/youtube/projects/${projectId}/upload-to-youtube`, {
        method: "POST",
        body: JSON.stringify(metadata),
    });
}

export async function uploadVideo(file: File): Promise<{ url: string }> {
    const formData = new FormData();
    formData.append("file", file);
    
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const response = await fetch(`${baseUrl}/api/v1/projects/upload-video`, {
        method: "POST",
        body: formData,
    });
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Upload failed" }));
        throw new Error(error.detail);
    }
    
    return response.json();
}

export async function uploadMusic(file: File): Promise<{ url: string }> {
    const formData = new FormData();
    formData.append("file", file);
    
    const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    const response = await fetch(`${baseUrl}/api/v1/projects/upload-music`, {
        method: "POST",
        body: formData,
    });
    
    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: "Upload failed" }));
        throw new Error(error.detail);
    }
    
    return response.json();
}