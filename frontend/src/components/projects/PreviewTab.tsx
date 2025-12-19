"use client";

import { ProjectDetail } from "@/types";
import { getStaticUrl } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Play, Film, Volume2 } from "lucide-react";

interface PreviewTabProps {
    project: ProjectDetail;
}

export function PreviewTab({ project }: PreviewTabProps) {
    const videoAsset = project.assets.find((a) => a.asset_type === "video");
    const audioAssets = project.assets.filter((a) => a.asset_type === "audio");

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
                    <div className="aspect-video bg-black">
                        <video controls className="w-full h-full">
                            <source src={getStaticUrl(videoAsset.url)} type="video/mp4" />
                        </video>
                    </div>
                    <CardContent className="py-4">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <Play className="h-4 w-4 text-primary" />
                                <span className="font-medium">Final Video</span>
                            </div>
                            {videoAsset.file_size_bytes && (
                                <Badge variant="secondary">
                                    {(videoAsset.file_size_bytes / (1024 * 1024)).toFixed(1)} MB
                                </Badge>
                            )}
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
