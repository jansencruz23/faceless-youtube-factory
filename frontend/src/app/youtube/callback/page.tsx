"use client";

import { useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { Card, CardContent } from "@/components/ui/card";
import { Loader2, CheckCircle2, AlertCircle } from "lucide-react";

export default function YouTubeCallbackPage() {
    const searchParams = useSearchParams();
    const router = useRouter();

    const connected = searchParams.get("youtube_connected");
    const error = searchParams.get("youtube_error");

    useEffect(() => {
        // Redirect to dashboard after 2 seconds
        const timer = setTimeout(() => {
            router.push("/");
        }, 2000);

        return () => clearTimeout(timer);
    }, [router]);

    if (error) {
        return (
            <div className="flex items-center justify-center min-h-[50vh]">
                <Card className="glass max-w-md">
                    <CardContent className="py-8 text-center">
                        <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
                        <h2 className="text-xl font-semibold mb-2">Connection Failed</h2>
                        <p className="text-muted-foreground mb-4">{error}</p>
                        <p className="text-sm text-muted-foreground">
                            Redirecting to dashboard...
                        </p>
                    </CardContent>
                </Card>
            </div>
        );
    }

    if (connected) {
        return (
            <div className="flex items-center justify-center min-h-[50vh]">
                <Card className="glass max-w-md">
                    <CardContent className="py-8 text-center">
                        <CheckCircle2 className="h-12 w-12 text-green-500 mx-auto mb-4" />
                        <h2 className="text-xl font-semibold mb-2">YouTube Connected!</h2>
                        <p className="text-muted-foreground mb-4">
                            Your account has been successfully linked.
                        </p>
                        <p className="text-sm text-muted-foreground">
                            Redirecting to dashboard...
                        </p>
                    </CardContent>
                </Card>
            </div>
        );
    }

    return (
        <div className="flex items-center justify-center min-h-[50vh]">
            <Card className="glass max-w-md">
                <CardContent className="py-8 text-center">
                    <Loader2 className="h-12 w-12 animate-spin text-primary mx-auto mb-4" />
                    <h2 className="text-xl font-semibold mb-2">Processing...</h2>
                    <p className="text-muted-foreground">
                        Completing YouTube connection...
                    </p>
                </CardContent>
            </Card>
        </div>
    );
}