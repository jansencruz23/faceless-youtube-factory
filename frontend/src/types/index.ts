export type ProjectStatus =
    | "draft"
    | "generating_script"
    | "casting"
    | "generating_audio"
    | "generating_video"
    | "completed"
    | "uploading_youtube"
    | "published"
    | "failed";

export type PrivacyStatus = "public" | "private" | "unlisted";

export interface Project {
    id: string;
    title: string;
    status: ProjectStatus;
    youtube_video_id?: string;
    youtube_url?: string;
    error_message?: string;
    created_at: string;
    updated_at: string;
}

export interface ScriptScene {
    speaker: string;
    line: string;
    duration: string;
}

export interface Script {
    id: string;
    version: number;
    scenes: ScriptScene[];
    created_at: string;
}

export interface VoiceSettings {
    voice_id: string;
    pitch: string;
    rate: string;
}

export interface Cast {
    id: string;
    assignments: Record<string, VoiceSettings>;
    created_at: string;
}

export interface Asset {
    id: string;
    asset_type: "audio" | "video";
    file_path: string;
    url: string;
    character_name?: string;
    file_size_bytes?: number;
    created_at: string;
}

export interface ProjectDetail extends Project {
    script?: Script;
    cast?: Cast;
    assets: Asset[];
    youtube_metadata?: {
        title: string;
        privacy_status: PrivacyStatus;
        category_id: string;
    };
}

export interface Voice {
    voice_id: string;
    name: string;
    gender: string;
    locale: string;
}

export interface YouTubeConnection {
    connected: boolean;
    channel_id?: string;
    channel_title?: string;
}

export interface YouTubeMetadata {
    title: string;
    description: string;
    tags: string[];
    category_id: string;
}

// WebSocket event types
export interface WSStatusChange {
    type: "status_change";
    status: ProjectStatus;
    progress: number;
}

export interface WSError {
    type: "error";
    message: string;
}

export interface WSCompleted {
    type: "completed";
    video_url: string;
}

export interface WSPublished {
    type: "published";
    youtube_url: string;
}

export type WSEvent =
    | WSStatusChange
    | WSError
    | WSCompleted
    | WSPublished;