import { Project, ProjectDetail, Voice, YouTubeConnection, YouTubeMetadata} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

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
}): Promise<Project> {
    return fetchAPI("/api/v1/projeects", {
        method: "POST",
        body: JSON.stringify(data),
    });
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

