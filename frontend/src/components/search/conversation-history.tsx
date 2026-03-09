import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import type { SearchResult } from "@/lib/types";

interface ConversationHistoryProps {
  results: SearchResult[];
  activeId: string | null;
  onSelect: (result: SearchResult) => void;
}

export function ConversationHistory({
  results,
  activeId,
  onSelect,
}: ConversationHistoryProps) {
  if (results.length === 0) {
    return (
      <div className="py-8 text-center">
        <p className="text-sm text-muted-foreground">No recent queries.</p>
      </div>
    );
  }

  return (
    <ScrollArea className="h-[calc(100vh-16rem)]">
      <div className="space-y-1 pr-3">
        {results.map((result) => (
          <button
            key={result.id}
            onClick={() => onSelect(result)}
            className={cn(
              "w-full rounded-md px-3 py-2.5 text-left transition-colors",
              activeId === result.id
                ? "bg-zinc-100 text-foreground"
                : "text-muted-foreground hover:bg-zinc-50 hover:text-foreground"
            )}
          >
            <p className="truncate text-sm">{result.query}</p>
            <p className="mt-1 text-xs text-muted-foreground">
              {new Date(result.timestamp).toLocaleString("en-IN", {
                month: "short",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              })}
            </p>
          </button>
        ))}
      </div>
    </ScrollArea>
  );
}
