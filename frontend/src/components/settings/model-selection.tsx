"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ChevronDown, Check } from "lucide-react";
import type { ModelConfig } from "@/lib/types";

interface ModelSelectionProps {
  config: ModelConfig;
  onChange: (config: ModelConfig) => void;
}

const models = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"];

export function ModelSelection({ config, onChange }: ModelSelectionProps) {
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 1500);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Model Configuration
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <label className="text-sm text-muted-foreground">Model</label>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="outline"
                className="w-full justify-between font-mono text-sm"
              >
                {config.model}
                <ChevronDown className="ml-2 h-4 w-4 text-muted-foreground" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-[200px]">
              {models.map((model) => (
                <DropdownMenuItem
                  key={model}
                  onClick={() => onChange({ ...config, model })}
                  className="font-mono text-sm"
                >
                  {model}
                  {config.model === model && (
                    <Check className="ml-auto h-4 w-4" />
                  )}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <label className="text-sm text-muted-foreground">
              Temperature
            </label>
            <Input
              type="number"
              min={0}
              max={1}
              step={0.1}
              value={config.temperature}
              onChange={(e) =>
                onChange({
                  ...config,
                  temperature: parseFloat(e.target.value) || 0,
                })
              }
              className="font-mono text-sm"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm text-muted-foreground">
              Top K Results
            </label>
            <Input
              type="number"
              min={1}
              max={20}
              value={config.topK}
              onChange={(e) =>
                onChange({
                  ...config,
                  topK: parseInt(e.target.value) || 1,
                })
              }
              className="font-mono text-sm"
            />
          </div>
        </div>

        <div className="space-y-2">
          <label className="text-sm text-muted-foreground">Reranking</label>
          <div>
            <Button
              variant={config.reranking ? "default" : "outline"}
              size="sm"
              onClick={() =>
                onChange({ ...config, reranking: !config.reranking })
              }
            >
              {config.reranking ? "Enabled" : "Disabled"}
            </Button>
          </div>
        </div>

        <div className="pt-2">
          <Button size="sm" onClick={handleSave}>
            {saved ? "Saved" : "Save Changes"}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
