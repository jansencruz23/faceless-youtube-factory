"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import {
    getYouTubeConnection,
    getYouTubeAuthUrl,
    disconnectYouTube,
} from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Youtube, CheckCircle2, Loader2, LogOut } from "lucide-react";

export default function YouTubeConnectPage() {
    const router = useRouter();
    const { data: connection, isLoading, refetch } = useQuery({
        queryKey: ["youtube-connection"],
        queryFn: getYouTubeConnection,
    });
    const connectMutation = useMutation({
        mutationFn: getYouTubeAuthUrl,
        onSuccess: (data) => {
            // Redirect to Google OAuth
            window.location.href = data.auth_url;
        },
    });
    const disconnectMutation = useMutation({
        mutationFn: disconnectYouTube,
        onSuccess: () => {
            refetch();
        },
    });
    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
        );
    }
    return (
        <div className="max-w-lg mx-auto">
            <Card className="glass">
                <CardHeader className="text-center">
                    <div className="mx-auto w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center mb-4">
                        <Youtube className="h-8 w-8 text-red-500" />
                    </div>
                    <CardTitle>YouTube Integration</CardTitle>
                    <CardDescription>
                        Connect your YouTube account to upload videos directly
                    </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                    {connection?.connected ? (
                        <>
                            {/* Connected State */}
                            <div className="p-4 rounded-lg bg-green-500/10 border border-green-500/20">
                                <div className="flex items-center gap-3">
                                    <CheckCircle2 className="h-5 w-5 text-green-500" />
                                    <div>
                                        <p className="font-medium">Connected</p>
                                        <p className="text-sm text-muted-foreground">
                                            {connection.channel_title}
                                        </p>
                                    </div>
                                </div>
                            </div>
                            <div className="space-y-2 text-sm text-muted-foreground">
                                <p>✓ Upload videos directly to YouTube</p>
                                <p>✓ AI-generated metadata (titles, descriptions, tags)</p>
                                <p>✓ Set privacy settings before publishing</p>
                            </div>
                            <div className="flex gap-2">
                                <Button
                                    variant="outline"
                                    className="flex-1"
                                    onClick={() => router.push("/")}
                                >
                                    Back to Dashboard
                                </Button>
                                <Button
                                    variant="destructive"
                                    onClick={() => disconnectMutation.mutate()}
                                    disabled={disconnectMutation.isPending}
                                >
                                    {disconnectMutation.isPending ? (
                                        <Loader2 className="h-4 w-4 animate-spin" />
                                    ) : (
                                        <LogOut className="h-4 w-4" />
                                    )}
                                </Button>
                            </div>
                        </>
                    ) : (
                        <>
                            {/* Not Connected State */}
                            <div className="space-y-2 text-sm text-muted-foreground">
                                <p>By connecting your YouTube account, you can:</p>
                                <ul className="list-disc list-inside space-y-1 ml-2">
                                    <li>Upload videos directly from this app</li>
                                    <li>Generate SEO-optimized titles and descriptions</li>
                                    <li>Manage privacy settings</li>
                                    <li>Track upload status in real-time</li>
                                </ul>
                            </div>
                            <Button
                                className="w-full"
                                onClick={() => connectMutation.mutate()}
                                disabled={connectMutation.isPending}
                            >
                                {connectMutation.isPending ? (
                                    <Loader2 className="h-4 w-4 animate-spin mr-2" />
                                ) : (
                                    <Youtube className="h-4 w-4 mr-2" />
                                )}
                                Connect YouTube Account
                            </Button>
                            <p className="text-xs text-muted-foreground text-center">
                                We only request permission to upload videos. We never access your
                                private videos or analytics.
                            </p>
                        </>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}