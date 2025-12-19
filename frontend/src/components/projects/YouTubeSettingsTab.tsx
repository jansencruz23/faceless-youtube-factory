"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ProjectDetail } from "@/types";
import {
    getYouTubeConnection,
    generateYouTubeMetadata,
    uploadToYouTube,
} from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Youtube, Sparkles, Upload, Loader2, AlertCircle, ExternalLink } from "lucide-react";
import Link from "next/link";

interface YouTubeSettingsTabProps {
    project: ProjectDetail;
}

const CATEGORIES = [
    { id: "22", name: "People & Blogs" },
    { id: "27", name: "Education" },
    { id: "28", name: "Science & Technology" },
    { id: "24", name: "Entertainment" },
    { id: "23", name: "Comedy" },
    { id: "26", name: "How-to & Style" },
];

export function YouTubeSettingsTab({ project }: YouTubeSettingsTabProps) {
    const queryClient = useQueryClient();
    const [title, setTitle] = useState(project.youtube_metadata?.title || project.title);
    const [description, setDescription] = useState("");
    const [tags, setTags] = useState<string[]>([]);
    const [tagInput, setTagInput] = useState("");
    const [categoryId, setCategoryId] = useState("22");
    const [privacyStatus, setPrivacyStatus] = useState<"public" | "private" | "unlisted">("private");
    const { data: ytConnection, isLoading: connectionLoading } = useQuery({
        queryKey: ["youtube-connection"],
        queryFn: getYouTubeConnection,
    });

    const generateMutation = useMutation({
        mutationFn: () => generateYouTubeMetadata(project.id),
        onSuccess: (data) => {
            setTitle(data.title);
            setDescription(data.description);
            setTags(data.tags);
            setCategoryId(data.category_id);
        },
    });
    const uploadMutation = useMutation({
        mutationFn: () =>
            uploadToYouTube(project.id, {
                title,
                description,
                tags,
                category_id: categoryId,
                privacy_status: privacyStatus,
            }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["project", project.id] });
        },
    });
    const handleAddTag = () => {
        if (tagInput.trim() && tags.length < 15) {
            setTags([...tags, tagInput.trim()]);
            setTagInput("");
        }
    };
    const handleRemoveTag = (index: number) => {
        setTags(tags.filter((_, i) => i !== index));
    };

    // Not connected
    if (!connectionLoading && !ytConnection?.connected) {
        return (
            <Card className="glass">
                <CardContent className="py-12 text-center">
                    <Youtube className="h-12 w-12 text-red-500 mx-auto mb-4" />
                    <h3 className="text-lg font-semibold mb-2">Connect YouTube</h3>
                    <p className="text-muted-foreground mb-4">
                        Connect your YouTube account to upload videos directly
                    </p>
                    <Link href="/youtube/connect">
                        <Button>
                            <Youtube className="h-4 w-4 mr-2" />
                            Connect YouTube
                        </Button>
                    </Link>
                </CardContent>
            </Card>
        );
    }
    // Already published
    if (project.youtube_url) {
        return (
            <Card className="glass">
                <CardContent className="py-12 text-center">
                    <div className="w-16 h-16 rounded-full bg-green-500/20 flex items-center justify-center mx-auto mb-4">
                        <Youtube className="h-8 w-8 text-green-500" />
                    </div>
                    <h3 className="text-lg font-semibold mb-2">Published on YouTube!</h3>
                    <p className="text-muted-foreground mb-4">
                        Your video is live and ready to watch
                    </p>
                    <a
                        href={project.youtube_url}
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        <Button>
                            <ExternalLink className="h-4 w-4 mr-2" />
                            Watch on YouTube
                        </Button>
                    </a>
                </CardContent>
            </Card>
        );
    }
    // Video not ready
    if (project.status !== "completed") {
        return (
            <Card className="glass">
                <CardContent className="py-12 text-center">
                    <AlertCircle className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-muted-foreground">
                        Video must be completed before uploading to YouTube
                    </p>
                </CardContent>
            </Card>
        );
    }
    return (
        <div className="space-y-4">
            {/* Connected Channel */}
            <Card className="glass">
                <CardContent className="py-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Youtube className="h-5 w-5 text-red-500" />
                            <span className="font-medium">{ytConnection?.channel_title}</span>
                        </div>
                        <Badge variant="default">Connected</Badge>
                    </div>
                </CardContent>
            </Card>
            {/* Metadata Form */}
            <Card className="glass">
                <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                        Video Metadata
                        <Button
                            size="sm"
                            variant="outline"
                            onClick={() => generateMutation.mutate()}
                            disabled={generateMutation.isPending}
                        >
                            {generateMutation.isPending ? (
                                <Loader2 className="h-4 w-4 animate-spin mr-1" />
                            ) : (
                                <Sparkles className="h-4 w-4 mr-1" />
                            )}
                            Generate with AI
                        </Button>
                    </CardTitle>
                    <CardDescription>
                        Configure how your video will appear on YouTube
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                    {/* Title */}
                    <div className="space-y-2">
                        <div className="flex justify-between">
                            <label className="text-sm font-medium">Title</label>
                            <span className="text-xs text-muted-foreground">
                                {title.length}/100
                            </span>
                        </div>
                        <Input
                            value={title}
                            onChange={(e) => setTitle(e.target.value.slice(0, 100))}
                            placeholder="Video title"
                        />
                    </div>
                    {/* Description */}
                    <div className="space-y-2">
                        <label className="text-sm font-medium">Description</label>
                        <Textarea
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            placeholder="Video description..."
                            className="min-h-[120px]"
                        />
                    </div>
                    {/* Tags */}
                    <div className="space-y-2">
                        <div className="flex justify-between">
                            <label className="text-sm font-medium">Tags</label>
                            <span className="text-xs text-muted-foreground">
                                {tags.length}/15
                            </span>
                        </div>
                        <div className="flex gap-2">
                            <Input
                                value={tagInput}
                                onChange={(e) => setTagInput(e.target.value)}
                                placeholder="Add a tag"
                                onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), handleAddTag())}
                            />
                            <Button
                                type="button"
                                variant="secondary"
                                onClick={handleAddTag}
                                disabled={tags.length >= 15}
                            >
                                Add
                            </Button>
                        </div>
                        <div className="flex flex-wrap gap-2 mt-2">
                            {tags.map((tag, i) => (
                                <Badge
                                    key={i}
                                    variant="secondary"
                                    className="cursor-pointer hover:bg-destructive"
                                    onClick={() => handleRemoveTag(i)}
                                >
                                    {tag} ×
                                </Badge>
                            ))}
                        </div>
                    </div>
                    {/* Category & Privacy */}
                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Category</label>
                            <Select value={categoryId} onValueChange={setCategoryId}>
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    {CATEGORIES.map((cat) => (
                                        <SelectItem key={cat.id} value={cat.id}>
                                            {cat.name}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Privacy</label>
                            <Select
                                value={privacyStatus}
                                onValueChange={(v) => setPrivacyStatus(v as typeof privacyStatus)}
                            >
                                <SelectTrigger>
                                    <SelectValue />
                                </SelectTrigger>
                                <SelectContent>
                                    <SelectItem value="private">Private</SelectItem>
                                    <SelectItem value="unlisted">Unlisted</SelectItem>
                                    <SelectItem value="public">Public</SelectItem>
                                </SelectContent>
                            </Select>
                        </div>
                    </div>
                </CardContent>
            </Card>
            {/* Upload Button */}
            <Button
                className="w-full"
                size="lg"
                onClick={() => uploadMutation.mutate()}
                disabled={uploadMutation.isPending || !title}
            >
                {uploadMutation.isPending ? (
                    <>
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                        Uploading...
                    </>
                ) : (
                    <>
                        <Upload className="h-4 w-4 mr-2" />
                        Upload to YouTube
                    </>
                )}
            </Button>
            {uploadMutation.isError && (
                <p className="text-sm text-destructive text-center">
                    {(uploadMutation.error as Error).message}
                </p>
            )}
        </div>
    );
}