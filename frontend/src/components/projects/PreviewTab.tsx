"use client";

import { ProjectDetail } from "@/types";
import { getStaticUrl } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Play, Film, Volume2, Download, Copy, Check } from "lucide-react";
import { useState } from "react";

interface PreviewTabProps {
    project: ProjectDetail;
}

export function PreviewTab({ project }: PreviewTabProps) {
    const videoAsset = project.assets.find((a) => a.asset_type === "video");
    const audioAssets = project.assets.filter((a) => a.asset_type === "audio");
    const [copied, setCopied] = useState(false);

    const handleDownload = () => {
        if (videoAsset) {
            const url = getStaticUrl(videoAsset.url);
            const link = document.createElement("a");
            link.href = url;
            link.download = `${project.title.replace(/[^a-zA-Z0-9]/g, "_")}.mp4`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }
    };

    const handleCopyPath = () => {
        if (videoAsset) {
            // Copy the full URL to clipboard
            const url = getStaticUrl(videoAsset.url);
            navigator.clipboard.writeText(url);
            setCopied(true);
            setTimeout(() => setCopied(false), 2000);
        }
    };

    if (!videoAsset && audioAssets.length === 0) {
        return (
            <Card>
                <CardContent className="py-12 text-center">
                    <Film className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-muted-foreground">Video is being generated...</p>
                </CardContent>
            </Card>
        );
    }

    return (
        <div className="space-y-6">
            {/* Video Player */}
            {videoAsset && (
                <Card className="overflow-hidden">
                    {/* Detect vertical video by URL (shorts folder) */}
                    {videoAsset.url.includes("shorts/") ? (
                        // Vertical video - smaller, centered
                        <div className="flex justify-center bg-black py-4">
                            <div className="w-48 aspect-[9/16]">
                                <video controls className="w-full h-full rounded-lg" key={project.updated_at}>
                                    <source src={`${getStaticUrl(videoAsset.url)}?t=${new Date(project.updated_at).getTime()}`} type="video/mp4" />
                                </video>
                            </div>
                        </div>
                    ) : (
                        // Horizontal video - full width
                        <div className="aspect-video bg-black">
                            <video controls className="w-full h-full" key={project.updated_at}>
                                <source src={`${getStaticUrl(videoAsset.url)}?t=${new Date(project.updated_at).getTime()}`} type="video/mp4" />
                            </video>
                        </div>
                    )}
                    <CardContent className="py-4">
                        <div className="flex items-center justify-between flex-wrap gap-3">
                            <div className="flex items-center gap-2">
                                <Play className="h-4 w-4 text-primary" />
                                <span className="font-medium">
                                    {videoAsset.url.includes("shorts/") ? "Short Video" : "Final Video"}
                                </span>
                                {videoAsset.file_size_bytes && (
                                    <Badge variant="secondary">
                                        {(videoAsset.file_size_bytes / (1024 * 1024)).toFixed(1)} MB
                                    </Badge>
                                )}
                            </div>
                            <div className="flex items-center gap-2">
                                <Button
                                    variant="outline"
                                    size="sm"
                                    onClick={handleCopyPath}
                                    className="gap-1"
                                >
                                    {copied ? (
                                        <>
                                            <Check className="h-4 w-4 text-green-500" />
                                            Copied!
                                        </>
                                    ) : (
                                        <>
                                            <Copy className="h-4 w-4" />
                                            Copy URL
                                        </>
                                    )}
                                </Button>
                                <Button
                                    variant="default"
                                    size="sm"
                                    onClick={handleDownload}
                                    className="gap-1"
                                >
                                    <Download className="h-4 w-4" />
                                    Download
                                </Button>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}
            {/* Audio Clips */}
            {audioAssets.length > 0 && (
                <Card>
                    <CardContent className="py-4">
                        <h3 className="font-medium mb-4 flex items-center gap-2">
                            <Volume2 className="h-4 w-4" />
                            Audio Clips ({audioAssets.length})
                        </h3>
                        <div className="space-y-3">
                            {audioAssets.map((asset, index) => (
                                <div key={asset.id} className="flex items-center gap-4 p-3 rounded-lg bg-secondary/30">
                                    <span className="text-sm text-muted-foreground w-8">#{index + 1}</span>
                                    {asset.character_name && <Badge variant="outline">{asset.character_name}</Badge>}
                                    <audio controls className="flex-1 h-8">
                                        <source src={getStaticUrl(asset.url)} type="audio/mpeg" />
                                    </audio>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
