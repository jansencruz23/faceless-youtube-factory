"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useApi } from "@/lib/useApi";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ProjectStatus } from "@/types";
import { Play, Youtube, AlertCircle, Clock, CheckCircle2, Loader2, Folder } from "lucide-react";

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

export default function DashboardPage() {
  const api = useApi();
  const [selectedCategory, setSelectedCategory] = useState<string | undefined>(undefined);

  const { data, isLoading, error } = useQuery({
    queryKey: ["projects", selectedCategory],
    queryFn: () => api.listProjects(1, 100, selectedCategory),
    refetchInterval: 5000,
  });

  // Get unique categories from all projects (fetch all first)
  const { data: allData } = useQuery({
    queryKey: ["projects-all"],
    queryFn: () => api.listProjects(1, 100),
  });

  const categories = allData?.items
    ? [...new Set(allData.items.map(p => p.category).filter(Boolean))]
    : [];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-destructive">
        <CardContent className="pt-6">
          <div className="flex items-center gap-2 text-destructive">
            <AlertCircle className="h-5 w-5" />
            <p>Failed to load projects: {(error as Error).message}</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold">Your Projects</h1>
        <p className="text-muted-foreground">
          {data?.total || 0} project{data?.total !== 1 ? "s" : ""}
        </p>
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
            <Play className="h-12 w-12 text-muted-foreground mb-4" />
            <h2 className="text-xl font-semibold mb-2">No projects yet</h2>
            <p className="text-muted-foreground mb-4">Create your first AI-generated video</p>
            <Link href="/projects/new">
              <Button>Create Project</Button>
            </Link>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {data?.items.map((project) => {
            const config = statusConfig[project.status];
            const StatusIcon = config.icon;
            const isProcessing = ["generating_script", "casting", "generating_images", "generating_audio", "generating_video", "uploading_youtube"].includes(project.status);
            return (
              <Link key={project.id} href={`/projects/${project.id}`}>
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
                        <span
                          onClick={(e) => {
                            e.preventDefault();
                            e.stopPropagation();
                            window.open(project.youtube_url, "_blank", "noopener,noreferrer");
                          }}
                          className="text-red-500 hover:text-red-400 cursor-pointer"
                        >
                          <Youtube className="h-5 w-5" />
                        </span>
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