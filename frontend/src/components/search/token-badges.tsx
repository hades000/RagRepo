import { Badge } from "@/components/ui/badge";
import type { TokenUsage } from "@/lib/types";

interface TokenBadgesProps {
  usage: TokenUsage;
}

export function TokenBadges({ usage }: TokenBadgesProps) {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <Badge variant="outline" className="font-mono text-xs">
        Prompt: {usage.promptTokens.toLocaleString()}
      </Badge>
      <Badge variant="outline" className="font-mono text-xs">
        Completion: {usage.completionTokens.toLocaleString()}
      </Badge>
      <Badge variant="secondary" className="font-mono text-xs">
        Total: {usage.totalTokens.toLocaleString()}
      </Badge>
      <Badge variant="default" className="font-mono text-xs">
        ₹{usage.costINR.toFixed(2)}
      </Badge>
    </div>
  );
}
