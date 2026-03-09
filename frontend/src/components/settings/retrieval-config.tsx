"use client";

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

interface RetrievalConfigProps {
  config: ModelConfig;
  onChange: (config: ModelConfig) => void;
}

const searchModes: ModelConfig["searchMode"][] = [
  "hybrid",
  "semantic",
  "keyword",
];

export function RetrievalConfig({ config, onChange }: RetrievalConfigProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Retrieval Configuration
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <label className="text-sm text-muted-foreground">
              Chunk Size (chars)
            </label>
            <Input
              type="number"
              value={config.chunkSize}
              readOnly
              className="font-mono text-sm bg-zinc-50"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm text-muted-foreground">
              Chunk Overlap (chars)
            </label>
            <Input
              type="number"
              value={config.chunkOverlap}
              readOnly
              className="font-mono text-sm bg-zinc-50"
            />
          </div>
        </div>

        <div className="space-y-2">
          <label className="text-sm text-muted-foreground">Search Mode</label>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="outline"
                className="w-full justify-between text-sm capitalize"
              >
                {config.searchMode}
                <ChevronDown className="ml-2 h-4 w-4 text-muted-foreground" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-[200px]">
              {searchModes.map((mode) => (
                <DropdownMenuItem
                  key={mode}
                  onClick={() => onChange({ ...config, searchMode: mode })}
                  className="text-sm capitalize"
                >
                  {mode}
                  {config.searchMode === mode && (
                    <Check className="ml-auto h-4 w-4" />
                  )}
                </DropdownMenuItem>
              ))}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardContent>
    </Card>
  );
}
