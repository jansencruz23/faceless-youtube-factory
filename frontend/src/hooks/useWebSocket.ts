"use client"

import { useEffect, useRef, useState, useCallback } from "react";
import { WSEvent, ProjectStatus } from "@/types";

interface UseWebSocketOptions {
    projectId: string;
    onStatusChange?: (status: ProjectStatus, progress: number) => void;
    onError?: (message: string) => void;
    onCompleted?: (videoUrl: string) => void;
    onPublished?: (youtubeUrl: string) => void;
}

export function useWebSocket({
    projectId,
    onStatusChange,
    onError,
    onCompleted,
    onPublished
}: UseWebSocketOptions) {
    const wsRef = useRef<WebSocket | null>(null);
    const [isConnected, setIsConnected] = useState(false);
    const [lastEvent, setLastEvent] = useState<WSEvent | null>(null);
    const reconnectAttempts = useRef(0);
    const maxReconnectAttempts = 5;

    const connect = useCallback(() => {
        const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
        const ws = new WebSocket(`${wsUrl}/api/v1/ws/projects/${projectId}`);

        ws.onopen = () => {
            console.log("WebSocket connected");
            setIsConnected(true);
            reconnectAttempts.current = 0;
        };

        ws.onmessage = (event) => {
            try {
                const data: WSEvent = JSON.parse(event.data);
                setLastEvent(data);

                switch (data.type) {
                    case "status_change":
                        onStatusChange?.(data.status, data.progress);
                        break;
                    case "error":
                        onError?.(data.message);
                        break;
                    case "completed":
                        onCompleted?.(data.video_url);
                        break;
                    case "published":
                        onPublished?.(data.youtube_url);
                        break;
                }
            } catch (error) {
                console.error("Error parsing WebSocket message:", error);
            }
        };

        ws.onclose = () => {
            console.log("WebSocket disconnected");
            setIsConnected(false);

            // Attempt to reconnect
            if (reconnectAttempts.current < maxReconnectAttempts) {
                reconnectAttempts.current += 1;
                const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
                console.log(`Reconnecting in ${delay}ms...`);
                setTimeout(connect, delay);
            }
        };

        ws.onerror = (error) => {
            console.error("WebSocket error:", error);
        };

        wsRef.current = ws;
    }, [projectId, onStatusChange, onError, onCompleted, onPublished]);

    useEffect(() => {
        connect();

        return () => {
            if (wsRef.current) {
                wsRef.current.close();
            }
        };
    }, [connect]);

    const disconnect = useCallback(() => {
        if (wsRef.current) {
            wsRef.current.close();
            wsRef.current = null;
        }
    }, []);

    return {
        isConnected,
        lastEvent,
        disconnect
    };
}