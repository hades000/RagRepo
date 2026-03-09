import { Card, CardContent } from "@/components/ui/card";
import type { SearchResult } from "@/lib/types";

interface ResponseContainerProps {
  result: SearchResult | null;
  isLoading: boolean;
}

export function ResponseContainer({
  result,
  isLoading,
}: ResponseContainerProps) {
  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-4 space-y-3">
          <div className="h-4 w-3/4 animate-pulse rounded bg-zinc-100" />
          <div className="h-4 w-full animate-pulse rounded bg-zinc-100" />
          <div className="h-4 w-5/6 animate-pulse rounded bg-zinc-100" />
          <div className="h-4 w-2/3 animate-pulse rounded bg-zinc-100" />
        </CardContent>
      </Card>
    );
  }

  if (!result) {
    return (
      <Card>
        <CardContent className="p-4">
          <p className="text-sm text-muted-foreground">
            Run a query to see results.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-sm leading-relaxed text-foreground whitespace-pre-line">
          {result.answer}
        </p>
      </CardContent>
    </Card>
  );
}
