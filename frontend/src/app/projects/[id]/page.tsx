"use client";
import { useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { useApi } from "@/lib/useApi";
import { useWebSocket } from "@/hooks/useWebSocket";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScriptTab } from "@/components/projects/ScriptTab";
import { CastingStudio } from "@/components/projects/CastingStudio";
import { YouTubeSettingsTab } from "@/components/projects/YouTubeSettingsTab";
import { PreviewTab } from "@/components/projects/PreviewTab";
import { ProjectStatus } from "@/types";
import {
    FileText,
    Users,
    Youtube,
    Play,
    Loader2,
    AlertCircle,
    CheckCircle2,
    XCircle,
    Trash2,
    Folder,
} from "lucide-react";

const statusConfig: Record<
    ProjectStatus,
    { label: string; variant: "default" | "secondary" | "destructive" | "success" | "warning" }
> = {
    draft: { label: "Draft", variant: "secondary" },
    generating_script: { label: "Writing Script...", variant: "default" },
    casting: { label: "Casting Voices...", variant: "default" },
    generating_images: { label: "Generating Images...", variant: "default" },
    generating_audio: { label: "Generating Audio...", variant: "default" },
    generating_video: { label: "Composing Video...", variant: "default" },
    completed: { label: "Completed", variant: "success" },
    uploading_youtube: { label: "Uploading to YouTube...", variant: "warning" },
    published: { label: "Published on YouTube", variant: "success" },
    failed: { label: "Failed", variant: "destructive" },
};

export default function ProjectDetailPage() {
    const params = useParams();
    const router = useRouter();
    const projectId = params.id as string;
    const queryClient = useQueryClient();
    const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
    const api = useApi();

    // Cancel mutation
    const cancelMutation = useMutation({
        mutationFn: () => api.cancelProject(projectId),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["project", projectId] });
        },
    });

    // Delete mutation
    const deleteMutation = useMutation({
        mutationFn: () => api.deleteProject(projectId),
        onSuccess: () => {
            router.push("/");
        },
    });

    const handleCancel = () => {
        if (confirm("Are you sure you want to cancel this project?")) {
            cancelMutation.mutate();
        }
    };

    const handleDelete = () => {
        if (confirm("Are you sure you want to delete this project? This cannot be undone.")) {
            deleteMutation.mutate();
        }
    };
    const { data: project, isLoading, error } = useQuery({
        queryKey: ["project", projectId],
        queryFn: () => api.getProject(projectId),
        refetchInterval: (query) => {
            const status = query.state.data?.status;
            // Poll more frequently during generation
            if (status && ["generating_script", "casting", "generating_images", "generating_audio", "generating_video", "uploading_youtube"].includes(status)) {
                return 3000;
            }
            return false;
        },
    });

    // Calculate progress based on status
    const progress = (() => {
        if (!project) return 0;
        switch (project.status) {
            case "generating_script": return 10;
            case "casting": return 20;
            case "generating_images": return 35;
            case "generating_audio": return 55;
            case "generating_video": return 80;
            case "uploading_youtube": return 90;
            case "completed":
            case "published": return 100;
            default: return 0;
        }
    })();

    const handleStatusChange = useCallback(
        () => {
            queryClient.invalidateQueries({ queryKey: ["project", projectId] });
        },
        [projectId, queryClient]
    );
    const handleCompleted = useCallback(
        () => {
            queryClient.invalidateQueries({ queryKey: ["project", projectId] });
        },
        [projectId, queryClient]
    );
    // Connect WebSocket for real-time updates
    const { isConnected } = useWebSocket({
        projectId,
        onStatusChange: handleStatusChange,
        onCompleted: handleCompleted,
        onPublished: () => {
            queryClient.invalidateQueries({ queryKey: ["project", projectId] });
        },
        onError: (message) => {
            console.error("WebSocket error:", message);
        },
    });
    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }
    if (error || !project) {
        return (
            <Card className="border-destructive">
                <CardContent className="pt-6">
                    <div className="flex items-center gap-2 text-destructive">
                        <AlertCircle className="h-5 w-5" />
                        <p>Failed to load project: {(error as Error)?.message || "Not found"}</p>
                    </div>
                </CardContent>
            </Card>
        );
    }
    const isProcessing = [
        "generating_script",
        "casting",
        "generating_images",
        "generating_audio",
        "generating_video",
        "uploading_youtube",
    ].includes(project.status);
    const statusInfo = statusConfig[project.status];
    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-start justify-between">
                <div>
                    <h1 className="text-3xl font-bold">{project.title}</h1>
                    <div className="flex items-center gap-2 mt-1">
                        <p className="text-muted-foreground">
                            Created {new Date(project.created_at).toLocaleDateString()}
                        </p>
                        {project.category && (
                            <Badge variant="outline" className="text-xs">
                                <Folder className="h-3 w-3 mr-1" />
                                {project.category}
                            </Badge>
                        )}
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    {/* Cancel Button - Show during processing */}
                    {isProcessing && (
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={handleCancel}
                            disabled={cancelMutation.isPending}
                            className="text-orange-500 border-orange-500 hover:bg-orange-500/10"
                        >
                            {cancelMutation.isPending ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                                <>
                                    <XCircle className="h-4 w-4 mr-1" />
                                    Cancel
                                </>
                            )}
                        </Button>
                    )}
                    {/* Delete Button - Show when not processing */}
                    {!isProcessing && (
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={handleDelete}
                            disabled={deleteMutation.isPending}
                            className="text-red-500 border-red-500 hover:bg-red-500/10"
                        >
                            {deleteMutation.isPending ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                                <>
                                    <Trash2 className="h-4 w-4 mr-1" />
                                    Delete
                                </>
                            )}
                        </Button>
                    )}
                    {/* Connection indicator */}
                    <div
                        className={`h-2 w-2 rounded-full ${isConnected ? "bg-green-500" : "bg-red-500"}`}
                        title={isConnected ? "Connected" : "Disconnected"}
                    />
                    <Badge variant={statusInfo.variant} className="text-sm">
                        {isProcessing && <Loader2 className="h-3 w-3 animate-spin mr-1" />}
                        {project.status === "completed" && <CheckCircle2 className="h-3 w-3 mr-1" />}
                        {statusInfo.label}
                    </Badge>
                </div>
            </div>
            {/* Progress Bar */}
            {isProcessing && (
                <Card className="glass">
                    <CardContent className="py-4">
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm">
                                <span>Progress</span>
                                <span>{Math.round(progress)}%</span>
                            </div>
                            <Progress value={progress} className="h-2" />
                        </div>
                    </CardContent>
                </Card>
            )}
            {/* Error Message */}
            {project.error_message && (
                <Card className="border-destructive glass">
                    <CardContent className="py-4">
                        <div className="flex items-start gap-2 text-destructive">
                            <AlertCircle className="h-5 w-5 mt-0.5" />
                            <div>
                                <p className="font-medium">Error</p>
                                <p className="text-sm">{project.error_message}</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}
            {/* Tabs */}
            <Tabs defaultValue="script" className="space-y-4">
                <TabsList className="grid w-full grid-cols-4 lg:w-auto lg:inline-grid">
                    <TabsTrigger value="script" className="gap-2">
                        <FileText className="h-4 w-4" />
                        <span className="hidden sm:inline">Script</span>
                    </TabsTrigger>
                    <TabsTrigger value="casting" className="gap-2">
                        <Users className="h-4 w-4" />
                        <span className="hidden sm:inline">Casting</span>
                    </TabsTrigger>
                    <TabsTrigger value="youtube" className="gap-2">
                        <Youtube className="h-4 w-4" />
                        <span className="hidden sm:inline">YouTube</span>
                    </TabsTrigger>
                    <TabsTrigger value="preview" className="gap-2">
                        <Play className="h-4 w-4" />
                        <span className="hidden sm:inline">Preview</span>
                    </TabsTrigger>
                </TabsList>
                <TabsContent value="script">
                    <ScriptTab project={project} />
                </TabsContent>
                <TabsContent value="casting">
                    <CastingStudio project={project} />
                </TabsContent>
                <TabsContent value="youtube">
                    <YouTubeSettingsTab project={project} />
                </TabsContent>
                <TabsContent value="preview">
                    <PreviewTab project={project} />
                </TabsContent>
            </Tabs>
        </div>
    );
}