import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText, Search, BarChart3, Clock } from "lucide-react";
import { getDashboardStats, searchResults } from "@/lib/dummy-data";

export default function DashboardPage() {
  const stats = getDashboardStats();
  const recentQueries = searchResults.slice(0, 5);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold tracking-tight">Dashboard</h2>
        <p className="text-sm text-muted-foreground">
          Overview of your RAG service.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Documents
            </CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalDocuments}</div>
            <p className="text-xs text-muted-foreground">
              Across {stats.totalCollections} collections
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Queries Today
            </CardTitle>
            <Search className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.queriesToday}</div>
            <p className="text-xs text-muted-foreground">
              Avg. latency {stats.avgLatency}s
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Cost (INR)
            </CardTitle>
            <BarChart3 className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              ₹{stats.totalCostINR.toFixed(2)}
            </div>
            <p className="text-xs text-muted-foreground">
              This billing cycle
            </p>
          </CardContent>
        </Card>
      </div>

      <div>
        <h3 className="text-sm font-medium mb-3">Recent Queries</h3>
        <Card>
          <CardContent className="p-0">
            <div className="divide-y">
              {recentQueries.map((result) => (
                <div
                  key={result.id}
                  className="flex items-start justify-between gap-4 px-4 py-3"
                >
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm text-foreground">
                      {result.query}
                    </p>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      {result.tokenUsage.totalTokens} tokens · ₹
                      {result.tokenUsage.costINR.toFixed(2)}
                    </p>
                  </div>
                  <div className="flex shrink-0 items-center gap-1.5 text-xs text-muted-foreground">
                    <Clock className="h-3 w-3" />
                    {new Date(result.timestamp).toLocaleDateString("en-IN", {
                      month: "short",
                      day: "numeric",
                    })}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
