"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { getYouTubeConnection } from "@/lib/api";
import { Youtube, Plus, Zap } from "lucide-react";

export function Header() {
    const { data: ytConnection } = useQuery({
        queryKey: ["youtube-connection"],
        queryFn: getYouTubeConnection,
    });

    return (
        <header className="border-b border-border/40 glass">
            <div className="container mx-auto px-4">
                <div className="flex h-16 items-center justify-between">
                    {/* Logo */}
                    <Link href="/" className="flex items-center gap-2">
                        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
                            <Zap className="h-5 w-5 text-white" />
                        </div>
                        <span className="font-bold text-lg">Faceless Factory</span>
                    </Link>

                    {/* Right Side */}
                    <div className="flex items-center gap-4">
                        {/* YouTube Status */}
                        {ytConnection?.connected ? (
                            <Link href="/youtube/connect">
                                <Badge variant="default" className="gap-1 bg-green-600 cursor-pointer hover:bg-green-700">
                                    <Youtube className="h-3 w-3" />
                                    {ytConnection.channel_title}
                                </Badge>
                            </Link>
                        ) : (
                            <Link href="/youtube/connect">
                                <Badge variant="outline" className="gap-1 cursor-pointer hover:bg-secondary">
                                    <Youtube className="h-3 w-3" />
                                    Connect YouTube
                                </Badge>
                            </Link>
                        )}

                        {/* New Project */}
                        <Link href="/projects/new">
                            <Button size="sm" className="gap-1">
                                <Plus className="h-4 w-4" />
                                New Project
                            </Button>
                        </Link>
                    </div>
                </div>
            </div>
        </header>
    )
}