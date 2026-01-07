"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { getAutomationProject } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ProjectStatus } from "@/types";
import {
    Bot, Youtube, AlertCircle, Clock, CheckCircle2, Loader2,
    ArrowLeft, Download, ExternalLink, Play, Copy
} from "lucide-react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function getStaticUrl(url: string): string {
    if (url.startsWith("http")) return url;
    return `${API_BASE}/static/${url}`;
}

const statusConfig: Record<ProjectStatus, { label: string; variant: "default" | "secondary" | "destructive" | "success" | "warning"; icon: React.ElementType }> = {
    draft: { label: "Draft", variant: "secondary", icon: Clock },
    generating_script: { label: "Writing Script", variant: "default", icon: Loader2 },
    casting: { label: "Casting", variant: "default", icon: Loader2 },
    generating_images: { label: "Generating Images", variant: "default", icon: Loader2 },
    generating_audio: { label: "Generating Audio", variant: "default", icon: Loader2 },
    generating_video: { label: "Composing Video", variant: "default", icon: Loader2 },
    completed: { label: "Completed", variant: "success", icon: CheckCircle2 },
    uploading_youtube: { label: "Uploading", variant: "warning", icon: Youtube },
    published: { label: "Published", variant: "success", icon: Youtube },
    failed: { label: "Failed", variant: "destructive", icon: AlertCircle },
};

export default function AutomationProjectPage() {
    const params = useParams();
    const projectId = params.id as string;
    const [apiKey, setApiKey] = useState<string | null>(null);
    const [copied, setCopied] = useState(false);

    useEffect(() => {
        const stored = localStorage.getItem("automation_api_key");
        setApiKey(stored);
    }, []);

    const { data: project, isLoading, error } = useQuery({
        queryKey: ["automation-project", projectId, apiKey],
        queryFn: () => getAutomationProject(apiKey!, projectId),
        enabled: !!apiKey && !!projectId,
        refetchInterval: 5000,
    });

    if (!apiKey) {
        return (
            <div className="space-y-6">
                <Link href="/automation">
                    <Button variant="ghost" size="sm" className="gap-1">
                        <ArrowLeft className="h-4 w-4" />
                        Back to Automation
                    </Button>
                </Link>
                <Card>
                    <CardContent className="pt-6">
                        <p className="text-muted-foreground">Please connect with your API key first.</p>
                        <Link href="/automation">
                            <Button className="mt-4">Go to Automation</Button>
                        </Link>
                    </CardContent>
                </Card>
            </div>
        );
    }

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }

    if (error || !project) {
        return (
            <div className="space-y-6">
                <Link href="/automation">
                    <Button variant="ghost" size="sm" className="gap-1">
                        <ArrowLeft className="h-4 w-4" />
                        Back to Automation
                    </Button>
                </Link>
                <Card className="border-destructive">
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-2 text-destructive">
                            <AlertCircle className="h-5 w-5" />
                            <p>Failed to load project</p>
                        </div>
                    </CardContent>
                </Card>
            </div>
        );
    }

    const config = statusConfig[project.status as ProjectStatus];
    const StatusIcon = config?.icon || Clock;
    const videoAsset = project.assets?.find((a) => a.asset_type === "video");

    const handleCopyUrl = () => {
        if (videoAsset) {
            navigator.clipboard.writeText(getStaticUrl(videoAsset.url));
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <Link href="/automation">
                        <Button variant="ghost" size="sm" className="gap-1">
                            <ArrowLeft className="h-4 w-4" />
                            Back
                        </Button>
                    </Link>
                    <div className="flex items-center gap-3">
                        <Bot className="h-6 w-6 text-primary" />
                        <h1 className="text-2xl font-bold">{project.title}</h1>
                    </div>
                </div>
                <Badge variant={config?.variant || "secondary"} className="gap-1">
                    <StatusIcon className="h-3 w-3" />
                    {config?.label || project.status}
                </Badge>
            </div>

            {/* Video Preview */}
            {videoAsset && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Play className="h-5 w-5" />
                            Video Preview
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="flex flex-col items-center">
                        <video
                            src={getStaticUrl(videoAsset.url)}
                            controls
                            className="w-full max-w-sm rounded-lg"
                        />
                        <div className="flex gap-2 mt-4">
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={() => window.open(getStaticUrl(videoAsset.url), '_blank')}
                            >
                                <ExternalLink className="h-4 w-4 mr-1" />
                                Open
                            </Button>
                            <Button
                                variant="outline"
                                size="sm"
                                onClick={handleCopyUrl}
                            >
                                <Copy className="h-4 w-4 mr-1" />
                                {copied ? "Copied!" : "Copy URL"}
                            </Button>
                            <a href={getStaticUrl(videoAsset.url)} download>
                                <Button variant="outline" size="sm">
                                    <Download className="h-4 w-4 mr-1" />
                                    Download
                                </Button>
                            </a>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Script */}
            {project.script && (
                <Card>
                    <CardHeader>
                        <CardTitle>Script</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-2">
                            {project.script.scenes?.map((scene: { speaker: string, line: string }, i: number) => (
                                <div key={i} className="p-3 bg-secondary/50 rounded">
                                    <span className="font-semibold">{scene.speaker}: </span>
                                    <span>{scene.line}</span>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Project Info */}
            <Card>
                <CardHeader>
                    <CardTitle>Details</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                            <span className="text-muted-foreground">Category:</span>
                            <span className="ml-2">{project.category || "None"}</span>
                        </div>
                        <div>
                            <span className="text-muted-foreground">Created:</span>
                            <span className="ml-2">{new Date(project.created_at).toLocaleString()}</span>
                        </div>
                        {project.youtube_url && (
                            <div className="col-span-2">
                                <span className="text-muted-foreground">YouTube:</span>
                                <a
                                    href={project.youtube_url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="ml-2 text-red-500 hover:underline"
                                >
                                    {project.youtube_url}
                                </a>
                            </div>
                        )}
                        {project.error_message && (
                            <div className="col-span-2 text-destructive">
                                <span className="text-muted-foreground">Error:</span>
                                <span className="ml-2">{project.error_message}</span>
                            </div>
                        )}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
