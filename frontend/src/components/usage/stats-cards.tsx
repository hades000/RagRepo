import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Search, Coins, Zap, Clock } from "lucide-react";
import type { UsageRecord } from "@/lib/types";

interface StatsCardsProps {
  records: UsageRecord[];
}

export function StatsCards({ records }: StatsCardsProps) {
  const totalQueries = records.reduce((sum, r) => sum + r.queries, 0);
  const totalTokens = records.reduce((sum, r) => sum + r.tokensUsed, 0);
  const totalCost = records.reduce((sum, r) => sum + r.costINR, 0);
  const avgLatency = 1.8;

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Queries</CardTitle>
          <Search className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{totalQueries}</div>
          <p className="text-xs text-muted-foreground">Last 7 days</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Tokens</CardTitle>
          <Zap className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold font-mono">
            {totalTokens.toLocaleString()}
          </div>
          <p className="text-xs text-muted-foreground">Last 7 days</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Cost</CardTitle>
          <Coins className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold font-mono">
            ₹{totalCost.toFixed(2)}
          </div>
          <p className="text-xs text-muted-foreground">Last 7 days</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Avg. Latency</CardTitle>
          <Clock className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold font-mono">{avgLatency}s</div>
          <p className="text-xs text-muted-foreground">Per query</p>
        </CardContent>
      </Card>
    </div>
  );
}
