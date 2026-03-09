"use client";

import { useCallback, useEffect, useState, type KeyboardEvent } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Search } from "lucide-react";

interface QueryInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  isLoading: boolean;
}

export function QueryInput({
  value,
  onChange,
  onSubmit,
  isLoading,
}: QueryInputProps) {
  const [modKey, setModKey] = useState("Ctrl");

  useEffect(() => {
    if (navigator?.platform?.includes("Mac")) {
      setModKey("⌘");
    }
  }, []);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
        e.preventDefault();
        onSubmit();
      }
    },
    [onSubmit]
  );

  return (
    <div className="space-y-3">
      <Textarea
        placeholder="Ask a question about your documents..."
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        rows={3}
        className="resize-none text-sm"
        disabled={isLoading}
      />
      <div className="flex items-center justify-between">
        <p className="text-xs text-muted-foreground">
          {modKey}+Enter to search
        </p>
        <Button
          onClick={onSubmit}
          disabled={!value.trim() || isLoading}
          size="sm"
        >
          <Search className="mr-2 h-4 w-4" />
          Search
        </Button>
      </div>
    </div>
  );
}
