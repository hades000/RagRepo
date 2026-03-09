import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Badge } from "@/components/ui/badge";
import type { Source } from "@/lib/types";

interface SourcesSectionProps {
  sources: Source[];
}

function scoreBadgeVariant(
  score: number
): "default" | "secondary" | "outline" {
  if (score >= 0.8) return "default";
  if (score >= 0.6) return "secondary";
  return "outline";
}

export function SourcesSection({ sources }: SourcesSectionProps) {
  if (sources.length === 0) return null;

  return (
    <Accordion type="single" collapsible>
      <AccordionItem value="sources" className="border-none">
        <AccordionTrigger className="py-2 text-sm font-medium hover:no-underline">
          Sources ({sources.length})
        </AccordionTrigger>
        <AccordionContent>
          <div className="space-y-2">
            {sources.map((source, index) => (
              <div
                key={index}
                className="flex items-start justify-between gap-3 rounded-md border px-3 py-2"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <p className="truncate text-sm font-medium text-foreground">
                      {source.docTitle}
                    </p>
                    <span className="shrink-0 text-xs text-muted-foreground">
                      Chunk {source.chunkIndex}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground line-clamp-2">
                    {source.snippet}
                  </p>
                </div>
                <Badge
                  variant={scoreBadgeVariant(source.score)}
                  className="shrink-0 font-mono text-xs"
                >
                  {source.score.toFixed(2)}
                </Badge>
              </div>
            ))}
          </div>
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}
