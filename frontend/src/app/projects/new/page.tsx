"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQuery } from "@tanstack/react-query";
import { createProject, getYouTubeConnection, uploadBackgroundImage, uploadVideo, uploadMusic, getPresetVideos } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, Sparkles, Youtube, Image, Upload, X, Video, Music, Monitor, Smartphone } from "lucide-react";

type ImageMode = "per_scene" | "single" | "upload" | "none";
type VideoFormat = "horizontal" | "vertical";
type BackgroundMode = "preset" | "upload" | "image" | "none";

export default function NewProjectPage() {
    const router = useRouter();
    const fileInputRef = useRef<HTMLInputElement>(null);
    const videoInputRef = useRef<HTMLInputElement>(null);
    const musicInputRef = useRef<HTMLInputElement>(null);

    const [title, setTitle] = useState("");
    const [prompt, setPrompt] = useState("");
    const [autoUpload, setAutoUpload] = useState(false);

    // Video format
    const [videoFormat, setVideoFormat] = useState<VideoFormat>("horizontal");

    // Horizontal mode options
    const [imageMode, setImageMode] = useState<ImageMode>("per_scene");
    const [scenesPerImage, setScenesPerImage] = useState(2);
    const [uploadedImageUrl, setUploadedImageUrl] = useState<string | null>(null);

    // Vertical (shorts) mode options
    const [backgroundMode, setBackgroundMode] = useState<BackgroundMode>("preset");
    const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
    const [uploadedVideoUrl, setUploadedVideoUrl] = useState<string | null>(null);
    const [uploadedMusicUrl, setUploadedMusicUrl] = useState<string | null>(null);
    const [musicVolume, setMusicVolume] = useState(0.3);

    // Upload states
    const [isUploading, setIsUploading] = useState(false);
    const [uploadingType, setUploadingType] = useState<string | null>(null);

    const { data: ytConnection } = useQuery({
        queryKey: ["youtube-connection"],
        queryFn: getYouTubeConnection,
    });

    const { data: presetsData } = useQuery({
        queryKey: ["preset-videos"],
        queryFn: getPresetVideos,
    });

    const createMutation = useMutation({
        mutationFn: createProject,
        onSuccess: (project) => {
            router.push(`/projects/${project.id}`);
        },
    });

    const handleImageUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setIsUploading(true);
        setUploadingType("image");
        try {
            const result = await uploadBackgroundImage(file);
            setUploadedImageUrl(result.url);
        } catch (error) {
            console.error("Upload failed:", error);
        } finally {
            setIsUploading(false);
            setUploadingType(null);
        }
    };

    const handleVideoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setIsUploading(true);
        setUploadingType("video");
        try {
            const result = await uploadVideo(file);
            setUploadedVideoUrl(result.url);
            setBackgroundMode("upload");
        } catch (error) {
            console.error("Upload failed:", error);
        } finally {
            setIsUploading(false);
            setUploadingType(null);
        }
    };

    const handleMusicUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setIsUploading(true);
        setUploadingType("music");
        try {
            const result = await uploadMusic(file);
            setUploadedMusicUrl(result.url);
        } catch (error) {
            console.error("Upload failed:", error);
        } finally {
            setIsUploading(false);
            setUploadingType(null);
        }
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        let backgroundVideoUrl: string | undefined;
        let backgroundImageUrl: string | undefined;
        let finalImageMode: ImageMode = imageMode;

        if (videoFormat === "vertical") {
            // For vertical, determine background video
            if (backgroundMode === "preset" && selectedPreset) {
                backgroundVideoUrl = selectedPreset;
                finalImageMode = "none"; // Skip image generation when using video
            } else if (backgroundMode === "upload" && uploadedVideoUrl) {
                backgroundVideoUrl = uploadedVideoUrl;
                finalImageMode = "none"; // Skip image generation when using video
            } else if (backgroundMode === "image") {
                finalImageMode = "single";
            } else {
                finalImageMode = "none";
            }
        } else {
            // For horizontal
            if (imageMode === "upload" && uploadedImageUrl) {
                backgroundImageUrl = uploadedImageUrl;
            }
        }

        createMutation.mutate({
            title,
            script_prompt: prompt,
            auto_upload: autoUpload,
            video_format: videoFormat,
            image_mode: finalImageMode,
            scenes_per_image: scenesPerImage,
            background_image_url: backgroundImageUrl,
            background_video_url: backgroundVideoUrl,
            background_music_url: uploadedMusicUrl || undefined,
            music_volume: musicVolume,
        });
    };

    const examplePrompts = [
        "Create a 3-minute video explaining quantum computing for beginners with a Host and an Expert",
        "Make a funny educational video about why cats love boxes, with two comedic hosts bantering",
        "Generate a motivational video about building daily habits, with an inspiring narrator",
    ];

    const imageModeOptions = [
        { value: "per_scene" as ImageMode, label: "Per Scene", description: "Multiple AI images" },
        { value: "single" as ImageMode, label: "Single", description: "One AI image" },
        { value: "upload" as ImageMode, label: "Upload", description: "Your image" },
        { value: "none" as ImageMode, label: "None", description: "Solid colors" },
    ];

    const backgroundModeOptions = [
        { value: "preset" as BackgroundMode, label: "Preset Videos", description: "Choose from library" },
        { value: "upload" as BackgroundMode, label: "Upload Video", description: "Your video" },
        { value: "image" as BackgroundMode, label: "AI Image", description: "Generate one image" },
        { value: "none" as BackgroundMode, label: "None", description: "Solid color" },
    ];

    const ratioOptions = [
        { value: 1, label: "1:1" },
        { value: 2, label: "1:2" },
        { value: 3, label: "1:3" },
        { value: 5, label: "1:5" },
    ];

    return (
        <div className="max-w-2xl mx-auto">
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Sparkles className="h-5 w-5 text-primary" />
                        Create New Video
                    </CardTitle>
                    <CardDescription>
                        Describe your video idea and AI will generate the script, voices, and final video
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-6">
                        {/* Title */}
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Video Title</label>
                            <Input
                                placeholder="My Awesome Video"
                                value={title}
                                onChange={(e) => setTitle(e.target.value)}
                                required
                                maxLength={255}
                            />
                        </div>

                        {/* Prompt */}
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Video Description</label>
                            <Textarea
                                placeholder="Describe what your video should be about..."
                                value={prompt}
                                onChange={(e) => setPrompt(e.target.value)}
                                required
                                minLength={10}
                                maxLength={5000}
                                className="min-h-[120px]"
                            />
                            <p className="text-xs text-muted-foreground">
                                {prompt.length}/5000 characters
                            </p>
                        </div>

                        {/* Example Prompts */}
                        <div className="space-y-2">
                            <label className="text-sm font-medium text-muted-foreground">
                                Example prompts (click to use)
                            </label>
                            <div className="space-y-2">
                                {examplePrompts.map((example, i) => (
                                    <button
                                        key={i}
                                        type="button"
                                        onClick={() => setPrompt(example)}
                                        className="w-full text-left text-sm p-3 rounded-lg border border-border hover:border-primary/50 hover:bg-secondary/50 transition-colors"
                                    >
                                        {example}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Video Format Toggle */}
                        <div className="space-y-3">
                            <label className="text-sm font-medium">Video Format</label>
                            <div className="grid grid-cols-2 gap-3">
                                <button
                                    type="button"
                                    onClick={() => setVideoFormat("horizontal")}
                                    className={`p-4 rounded-lg border-2 transition-colors flex flex-col items-center gap-2 ${videoFormat === "horizontal"
                                        ? "border-primary bg-primary/10"
                                        : "border-border hover:border-primary/50"
                                        }`}
                                >
                                    <Monitor className="h-8 w-8" />
                                    <span className="font-medium">Horizontal</span>
                                    <span className="text-xs text-muted-foreground">16:9 YouTube</span>
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setVideoFormat("vertical")}
                                    className={`p-4 rounded-lg border-2 transition-colors flex flex-col items-center gap-2 ${videoFormat === "vertical"
                                        ? "border-primary bg-primary/10"
                                        : "border-border hover:border-primary/50"
                                        }`}
                                >
                                    <Smartphone className="h-8 w-8" />
                                    <span className="font-medium">Vertical</span>
                                    <span className="text-xs text-muted-foreground">9:16 Shorts/TikTok</span>
                                </button>
                            </div>
                        </div>

                        {/* Horizontal Mode Options */}
                        {videoFormat === "horizontal" && (
                            <>
                                <div className="space-y-3">
                                    <label className="text-sm font-medium flex items-center gap-2">
                                        <Image className="h-4 w-4" />
                                        Background Images
                                    </label>
                                    <div className="grid grid-cols-4 gap-2">
                                        {imageModeOptions.map((option) => (
                                            <button
                                                key={option.value}
                                                type="button"
                                                onClick={() => setImageMode(option.value)}
                                                className={`text-center p-2 rounded-lg border transition-colors ${imageMode === option.value
                                                    ? "border-primary bg-primary/10"
                                                    : "border-border hover:border-primary/50"
                                                    }`}
                                            >
                                                <span className="text-sm font-medium block">{option.label}</span>
                                                <span className="text-xs text-muted-foreground">{option.description}</span>
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {imageMode === "per_scene" && (
                                    <div className="space-y-2">
                                        <label className="text-sm font-medium">Image Ratio</label>
                                        <div className="flex gap-2">
                                            {ratioOptions.map((option) => (
                                                <button
                                                    key={option.value}
                                                    type="button"
                                                    onClick={() => setScenesPerImage(option.value)}
                                                    className={`flex-1 p-2 rounded-lg border transition-colors ${scenesPerImage === option.value
                                                        ? "border-primary bg-primary/10"
                                                        : "border-border hover:border-primary/50"
                                                        }`}
                                                >
                                                    {option.label}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {imageMode === "upload" && (
                                    <div className="space-y-2">
                                        <button
                                            type="button"
                                            onClick={() => fileInputRef.current?.click()}
                                            disabled={isUploading}
                                            className="w-full p-4 rounded-lg border-2 border-dashed border-border hover:border-primary/50 transition-colors flex items-center justify-center gap-2"
                                        >
                                            {uploadingType === "image" ? (
                                                <Loader2 className="h-5 w-5 animate-spin" />
                                            ) : uploadedImageUrl ? (
                                                <>
                                                    <Image className="h-5 w-5 text-primary" />
                                                    <span>Image uploaded ✓</span>
                                                </>
                                            ) : (
                                                <>
                                                    <Upload className="h-5 w-5" />
                                                    <span>Upload background image</span>
                                                </>
                                            )}
                                        </button>
                                        <input
                                            ref={fileInputRef}
                                            type="file"
                                            accept="image/*"
                                            onChange={handleImageUpload}
                                            className="hidden"
                                        />
                                    </div>
                                )}
                            </>
                        )}

                        {/* Vertical Mode Options */}
                        {videoFormat === "vertical" && (
                            <>
                                <div className="space-y-3">
                                    <label className="text-sm font-medium flex items-center gap-2">
                                        <Video className="h-4 w-4" />
                                        Background
                                    </label>
                                    <div className="grid grid-cols-4 gap-2">
                                        {backgroundModeOptions.map((option) => (
                                            <button
                                                key={option.value}
                                                type="button"
                                                onClick={() => setBackgroundMode(option.value)}
                                                className={`text-center p-2 rounded-lg border transition-colors ${backgroundMode === option.value
                                                    ? "border-primary bg-primary/10"
                                                    : "border-border hover:border-primary/50"
                                                    }`}
                                            >
                                                <span className="text-sm font-medium block">{option.label}</span>
                                                <span className="text-xs text-muted-foreground">{option.description}</span>
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                {/* Preset Videos Selector */}
                                {backgroundMode === "preset" && (
                                    <div className="space-y-2">
                                        <label className="text-sm font-medium">Select Preset Video</label>
                                        {presetsData?.presets && presetsData.presets.length > 0 ? (
                                            <div className="grid grid-cols-2 gap-2">
                                                {presetsData.presets.map((preset) => (
                                                    <button
                                                        key={preset.id}
                                                        type="button"
                                                        onClick={() => setSelectedPreset(preset.url)}
                                                        className={`p-3 rounded-lg border transition-colors text-left ${selectedPreset === preset.url
                                                            ? "border-primary bg-primary/10"
                                                            : "border-border hover:border-primary/50"
                                                            }`}
                                                    >
                                                        <Video className="h-4 w-4 mb-1" />
                                                        <span className="text-sm">{preset.name}</span>
                                                    </button>
                                                ))}
                                            </div>
                                        ) : (
                                            <p className="text-sm text-muted-foreground p-4 border border-dashed rounded-lg text-center">
                                                No preset videos available. Add videos to static/presets/videos/
                                            </p>
                                        )}
                                    </div>
                                )}

                                {/* Upload Video */}
                                {backgroundMode === "upload" && (
                                    <div className="space-y-2">
                                        <button
                                            type="button"
                                            onClick={() => videoInputRef.current?.click()}
                                            disabled={isUploading}
                                            className="w-full p-4 rounded-lg border-2 border-dashed border-border hover:border-primary/50 transition-colors flex items-center justify-center gap-2"
                                        >
                                            {uploadingType === "video" ? (
                                                <Loader2 className="h-5 w-5 animate-spin" />
                                            ) : uploadedVideoUrl ? (
                                                <>
                                                    <Video className="h-5 w-5 text-primary" />
                                                    <span>Video uploaded ✓</span>
                                                </>
                                            ) : (
                                                <>
                                                    <Upload className="h-5 w-5" />
                                                    <span>Upload background video</span>
                                                </>
                                            )}
                                        </button>
                                        <input
                                            ref={videoInputRef}
                                            type="file"
                                            accept="video/mp4,video/webm,video/quicktime"
                                            onChange={handleVideoUpload}
                                            className="hidden"
                                        />
                                    </div>
                                )}

                                {/* Background Music */}
                                <div className="space-y-3">
                                    <label className="text-sm font-medium flex items-center gap-2">
                                        <Music className="h-4 w-4" />
                                        Background Music (Optional)
                                    </label>
                                    <button
                                        type="button"
                                        onClick={() => musicInputRef.current?.click()}
                                        disabled={isUploading}
                                        className="w-full p-3 rounded-lg border border-dashed border-border hover:border-primary/50 transition-colors flex items-center justify-center gap-2"
                                    >
                                        {uploadingType === "music" ? (
                                            <Loader2 className="h-5 w-5 animate-spin" />
                                        ) : uploadedMusicUrl ? (
                                            <>
                                                <Music className="h-5 w-5 text-primary" />
                                                <span>Music uploaded ✓</span>
                                                <button
                                                    type="button"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        setUploadedMusicUrl(null);
                                                    }}
                                                    className="ml-2 p-1 hover:bg-secondary rounded"
                                                >
                                                    <X className="h-4 w-4" />
                                                </button>
                                            </>
                                        ) : (
                                            <>
                                                <Upload className="h-4 w-4" />
                                                <span className="text-sm">Upload music</span>
                                            </>
                                        )}
                                    </button>
                                    <input
                                        ref={musicInputRef}
                                        type="file"
                                        accept="audio/mpeg,audio/wav,audio/mp3"
                                        onChange={handleMusicUpload}
                                        className="hidden"
                                    />

                                    {uploadedMusicUrl && (
                                        <div className="space-y-1">
                                            <label className="text-xs text-muted-foreground">Music Volume: {Math.round(musicVolume * 100)}%</label>
                                            <input
                                                type="range"
                                                min="0"
                                                max="1"
                                                step="0.1"
                                                value={musicVolume}
                                                onChange={(e) => setMusicVolume(parseFloat(e.target.value))}
                                                className="w-full"
                                            />
                                        </div>
                                    )}
                                </div>
                            </>
                        )}

                        {/* Auto-upload option */}
                        {ytConnection?.connected && (
                            <div className="flex items-center gap-3 p-4 rounded-lg bg-secondary/50">
                                <input
                                    type="checkbox"
                                    id="auto-upload"
                                    checked={autoUpload}
                                    onChange={(e) => setAutoUpload(e.target.checked)}
                                    className="h-4 w-4 rounded border-border"
                                />
                                <label htmlFor="auto-upload" className="flex items-center gap-2 text-sm">
                                    <Youtube className="h-4 w-4 text-red-500" />
                                    Auto-upload to YouTube when ready
                                </label>
                            </div>
                        )}

                        {/* Submit */}
                        <Button
                            type="submit"
                            className="w-full"
                            disabled={
                                createMutation.isPending ||
                                !title ||
                                !prompt ||
                                (videoFormat === "horizontal" && imageMode === "upload" && !uploadedImageUrl) ||
                                (videoFormat === "vertical" && backgroundMode === "preset" && !selectedPreset) ||
                                (videoFormat === "vertical" && backgroundMode === "upload" && !uploadedVideoUrl)
                            }
                        >
                            {createMutation.isPending ? (
                                <>
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                    Creating...
                                </>
                            ) : (
                                <>
                                    <Sparkles className="h-4 w-4" />
                                    Generate {videoFormat === "vertical" ? "Short" : "Video"}
                                </>
                            )}
                        </Button>

                        {createMutation.isError && (
                            <p className="text-sm text-destructive text-center">
                                {(createMutation.error as Error).message}
                            </p>
                        )}
                    </form>
                </CardContent>
            </Card>
        </div>
    );
}