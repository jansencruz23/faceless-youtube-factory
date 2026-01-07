"use client";

import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { listAutomationProjects } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ProjectStatus, Project } from "@/types";
import { Bot, Youtube, AlertCircle, Clock, CheckCircle2, Loader2, Folder, Key } from "lucide-react";

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

export default function AutomationPage() {
    const [apiKey, setApiKey] = useState("");
    const [savedApiKey, setSavedApiKey] = useState<string | null>(null);
    const [selectedCategory, setSelectedCategory] = useState<string | undefined>(undefined);

    // Load saved API key from localStorage
    useEffect(() => {
        const stored = localStorage.getItem("automation_api_key");
        if (stored) {
            setSavedApiKey(stored);
            setApiKey(stored);
        }
    }, []);

    const { data, isLoading, error, refetch } = useQuery({
        queryKey: ["automation-projects", savedApiKey, selectedCategory],
        queryFn: () => listAutomationProjects(savedApiKey!, selectedCategory),
        enabled: !!savedApiKey,
        refetchInterval: 5000,
    });

    // Get unique categories
    const categories = data?.items
        ? [...new Set(data.items.map((p: Project) => p.category).filter(Boolean) as string[])]
        : [];

    const handleSaveApiKey = () => {
        localStorage.setItem("automation_api_key", apiKey);
        setSavedApiKey(apiKey);
    };

    if (!savedApiKey) {
        return (
            <div className="space-y-6">
                <div className="flex items-center gap-3">
                    <Bot className="h-8 w-8 text-primary" />
                    <h1 className="text-3xl font-bold">Automation Projects</h1>
                </div>

                <Card>
                    <CardContent className="pt-6 space-y-4">
                        <div className="flex items-center gap-2 text-muted-foreground">
                            <Key className="h-5 w-5" />
                            <p>Enter your Automation API Key to view projects</p>
                        </div>
                        <div className="flex gap-2">
                            <Input
                                type="password"
                                placeholder="Enter AUTOMATION_API_KEY from .env"
                                value={apiKey}
                                onChange={(e) => setApiKey(e.target.value)}
                            />
                            <Button onClick={handleSaveApiKey} disabled={!apiKey}>
                                Connect
                            </Button>
                        </div>
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

    if (error) {
        return (
            <div className="space-y-6">
                <div className="flex items-center gap-3">
                    <Bot className="h-8 w-8 text-primary" />
                    <h1 className="text-3xl font-bold">Automation Projects</h1>
                </div>
                <Card className="border-destructive">
                    <CardContent className="pt-6 space-y-4">
                        <div className="flex items-center gap-2 text-destructive">
                            <AlertCircle className="h-5 w-5" />
                            <p>Invalid API key or connection error</p>
                        </div>
                        <Button
                            variant="outline"
                            onClick={() => {
                                localStorage.removeItem("automation_api_key");
                                setSavedApiKey(null);
                            }}
                        >
                            Change API Key
                        </Button>
                    </CardContent>
                </Card>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <Bot className="h-8 w-8 text-primary" />
                    <h1 className="text-3xl font-bold">Automation Projects</h1>
                </div>
                <div className="flex items-center gap-2">
                    <p className="text-muted-foreground">
                        {data?.total || 0} project{data?.total !== 1 ? "s" : ""}
                    </p>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                            localStorage.removeItem("automation_api_key");
                            setSavedApiKey(null);
                        }}
                    >
                        Disconnect
                    </Button>
                </div>
            </div>

            {/* Category Tabs */}
            {categories.length > 0 && (
                <div className="flex flex-wrap gap-2">
                    <Button
                        variant={selectedCategory === undefined ? "default" : "outline"}
                        size="sm"
                        onClick={() => setSelectedCategory(undefined)}
                    >
                        All
                    </Button>
                    {categories.map((cat) => (
                        <Button
                            key={cat}
                            variant={selectedCategory === cat ? "default" : "outline"}
                            size="sm"
                            onClick={() => setSelectedCategory(cat)}
                        >
                            <Folder className="h-3 w-3 mr-1" />
                            {cat}
                        </Button>
                    ))}
                </div>
            )}

            {data?.items.length === 0 ? (
                <Card>
                    <CardContent className="flex flex-col items-center justify-center py-16">
                        <Bot className="h-12 w-12 text-muted-foreground mb-4" />
                        <h2 className="text-xl font-semibold mb-2">No automation projects yet</h2>
                        <p className="text-muted-foreground">Projects created via n8n will appear here</p>
                    </CardContent>
                </Card>
            ) : (
                <div className="grid gap-4">
                    {data?.items.map((project: Project) => {
                        const config = statusConfig[project.status];
                        const StatusIcon = config.icon;
                        const isProcessing = ["generating_script", "casting", "generating_images", "generating_audio", "generating_video", "uploading_youtube"].includes(project.status);
                        return (
                            <Link key={project.id} href={`/automation/${project.id}`}>
                                <Card className="hover:border-primary/50 transition-colors cursor-pointer">
                                    <CardContent className="flex items-center justify-between py-4">
                                        <div className="flex items-center gap-4">
                                            <div className="flex flex-col">
                                                <h3 className="font-semibold">{project.title}</h3>
                                                <div className="flex items-center gap-2">
                                                    <p className="text-sm text-muted-foreground">
                                                        {new Date(project.created_at).toLocaleDateString()}
                                                    </p>
                                                    {project.category && (
                                                        <Badge variant="outline" className="text-xs">
                                                            {project.category}
                                                        </Badge>
                                                    )}
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-4">
                                            {project.youtube_url && (
                                                <a
                                                    href={project.youtube_url}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    onClick={(e) => e.stopPropagation()}
                                                    className="text-red-500 hover:text-red-400"
                                                >
                                                    <Youtube className="h-5 w-5" />
                                                </a>
                                            )}
                                            <Badge variant={config.variant} className="gap-1">
                                                <StatusIcon className={`h-3 w-3 ${isProcessing ? "animate-spin" : ""}`} />
                                                {config.label}
                                            </Badge>
                                        </div>
                                    </CardContent>
                                </Card>
                            </Link>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
