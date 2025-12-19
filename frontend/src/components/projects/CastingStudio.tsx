"use client";

import { useState, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ProjectDetail, Voice, VoiceSettings } from "@/types";
import { listVoices, updateCast, previewVoice, regenerateAudio, getStaticUrl } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Slider } from "@/components/ui/slider";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Users, Play, Pause, Save, RefreshCw, Loader2 } from "lucide-react";

interface CastingStudioProps {
    project: ProjectDetail;
}

export function CastingStudio({ project }: CastingStudioProps) {
    const queryClient = useQueryClient();
    const audioRef = useRef<HTMLAudioElement | null>(null);
    const [playingCharacter, setPlayingCharacter] = useState<string | null>(null);
    const [editedAssignments, setEditedAssignments] = useState<
        Record<string, VoiceSettings>
    >(project.cast?.assignments || {});
    const [hasChanges, setHasChanges] = useState(false);

    // Fetch available voices
    const { data: voicesData } = useQuery({
        queryKey: ["voices"],
        queryFn: listVoices,
    });

    const voices = voicesData?.voices || [];

    // Get characters from script
    const characters = project.script
        ? [...new Set(project.script.scenes.map((s) => s.speaker))]
        : [];

    // Preview mutation
    const previewMutation = useMutation({
        mutationFn: (data: { character: string; settings: VoiceSettings }) =>
            previewVoice(project.id, {
                character: data.character,
                voice_settings: data.settings,
                sample_text:
                    project.script?.scenes.find((s) => s.speaker === data.character)?.line ||
                    "Hello, this is a voice preview.",
            }),
        onSuccess: (data, variables) => {
            if (audioRef.current) {
                audioRef.current.src = getStaticUrl(data.audio_url);
                audioRef.current.play();
                setPlayingCharacter(variables.character);
            }
        },
    });

    // Save cast mutation
    const saveMutation = useMutation({
        mutationFn: () => updateCast(project.id, editedAssignments),
        onSuccess: () => {
            setHasChanges(false);
            queryClient.invalidateQueries({ queryKey: ["project", project.id] });
        },
    });

    // Regenerate audio mutation
    const regenerateMutation = useMutation({
        mutationFn: () => regenerateAudio(project.id),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["project", project.id] });
        },
    });

    const handleVoiceChange = (character: string, voiceId: string) => {
        setEditedAssignments((prev) => ({
            ...prev,
            [character]: {
                ...prev[character],
                voice_id: voiceId,
            },
        }));
        setHasChanges(true);
    };

    const handlePitchChange = (character: string, value: number) => {
        const pitch = value >= 0 ? `+${value}Hz` : `${value}Hz`;
        setEditedAssignments((prev) => ({
            ...prev,
            [character]: {
                ...prev[character],
                pitch,
            },
        }));
        setHasChanges(true);
    };

    const handleRateChange = (character: string, value: number) => {
        const rate = value >= 0 ? `+${value}%` : `${value}%`;
        setEditedAssignments((prev) => ({
            ...prev,
            [character]: {
                ...prev[character],
                rate,
            },
        }));
        setHasChanges(true);
    };

    const handlePreview = (character: string) => {
        const settings = editedAssignments[character] || {
            voice_id: "en-US-AriaNeural",
            pitch: "+0Hz",
            rate: "+0%",
        };
        previewMutation.mutate({ character, settings });
    };

    const stopPreview = () => {
        if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.currentTime = 0;
        }
        setPlayingCharacter(null);
    };

    const parsePitch = (pitch: string): number => {
        return parseInt(pitch.replace("Hz", "").replace("+", "")) || 0;
    };

    const parseRate = (rate: string): number => {
        return parseInt(rate.replace("%", "").replace("+", "")) || 0;
    };

    if (!project.script) {
        return (
            <Card className="glass">
                <CardContent className="py-12 text-center">
                    <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-muted-foreground">
                        Waiting for script to be generated...
                    </p>
                </CardContent>
            </Card>
        );
    }

    return (
        <div className="space-y-4">
            {/* Hidden audio element */}
            <audio
                ref={audioRef}
                onEnded={() => setPlayingCharacter(null)}
                className="hidden"
            />
            {/* Action Buttons */}
            <div className="flex justify-end gap-2">
                <Button
                    variant="outline"
                    onClick={() => regenerateMutation.mutate()}
                    disabled={regenerateMutation.isPending || !project.cast}
                >
                    {regenerateMutation.isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    ) : (
                        <RefreshCw className="h-4 w-4 mr-2" />
                    )}
                    Regenerate Audio
                </Button>
                <Button
                    onClick={() => saveMutation.mutate()}
                    disabled={!hasChanges || saveMutation.isPending}
                >
                    {saveMutation.isPending ? (
                        <Loader2 className="h-4 w-4 animate-spin mr-2" />
                    ) : (
                        <Save className="h-4 w-4 mr-2" />
                    )}
                    Save Changes
                </Button>
            </div>
            {/* Character Cards */}
            <div className="grid gap-4">
                {characters.map((character) => {
                    const settings = editedAssignments[character] || {
                        voice_id: "en-US-AriaNeural",
                        pitch: "+0Hz",
                        rate: "+0%",
                    };
                    const selectedVoice = voices.find((v) => v.voice_id === settings.voice_id);
                    const isPlaying = playingCharacter === character;
                    return (
                        <Card key={character} className="glass">
                            <CardHeader className="pb-2">
                                <CardTitle className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <Badge variant="secondary">{character}</Badge>
                                        {selectedVoice && (
                                            <span className="text-sm text-muted-foreground">
                                                {selectedVoice.name}
                                            </span>
                                        )}
                                    </div>
                                    <Button
                                        size="sm"
                                        variant={isPlaying ? "secondary" : "outline"}
                                        onClick={() => (isPlaying ? stopPreview() : handlePreview(character))}
                                        disabled={previewMutation.isPending && playingCharacter !== character}
                                    >
                                        {previewMutation.isPending && playingCharacter === character ? (
                                            <Loader2 className="h-4 w-4 animate-spin" />
                                        ) : isPlaying ? (
                                            <>
                                                <Pause className="h-4 w-4 mr-1" />
                                                Stop
                                            </>
                                        ) : (
                                            <>
                                                <Play className="h-4 w-4 mr-1" />
                                                Listen
                                            </>
                                        )}
                                    </Button>
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                {/* Voice Select */}
                                <div className="space-y-2">
                                    <label className="text-sm font-medium">Voice</label>
                                    <Select
                                        value={settings.voice_id}
                                        onValueChange={(value) => handleVoiceChange(character, value)}
                                    >
                                        <SelectTrigger>
                                            <SelectValue placeholder="Select a voice" />
                                        </SelectTrigger>
                                        <SelectContent className="max-h-[300px]">
                                            {voices.map((voice) => (
                                                <SelectItem key={voice.voice_id} value={voice.voice_id}>
                                                    <div className="flex items-center gap-2">
                                                        <span>{voice.name}</span>
                                                        <Badge variant="outline" className="text-xs">
                                                            {voice.gender}
                                                        </Badge>
                                                    </div>
                                                </SelectItem>
                                            ))}
                                        </SelectContent>
                                    </Select>
                                </div>
                                {/* Pitch Slider */}
                                <div className="space-y-2">
                                    <div className="flex justify-between">
                                        <label className="text-sm font-medium">Pitch</label>
                                        <span className="text-sm text-muted-foreground">
                                            {settings.pitch}
                                        </span>
                                    </div>
                                    <Slider
                                        value={[parsePitch(settings.pitch)]}
                                        onValueChange={([value]) => handlePitchChange(character, value)}
                                        min={-20}
                                        max={20}
                                        step={1}
                                    />
                                </div>
                                {/* Rate Slider */}
                                <div className="space-y-2">
                                    <div className="flex justify-between">
                                        <label className="text-sm font-medium">Speed</label>
                                        <span className="text-sm text-muted-foreground">
                                            {settings.rate}
                                        </span>
                                    </div>
                                    <Slider
                                        value={[parseRate(settings.rate)]}
                                        onValueChange={([value]) => handleRateChange(character, value)}
                                        min={-50}
                                        max={100}
                                        step={5}
                                    />
                                </div>
                            </CardContent>
                        </Card>
                    );
                })}
            </div>
        </div>
    );
}