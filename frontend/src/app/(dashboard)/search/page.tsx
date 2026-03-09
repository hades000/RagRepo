"use client";

import { useState, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { QueryInput } from "@/components/search/query-input";
import { ResponseContainer } from "@/components/search/response-container";
import { SourcesSection } from "@/components/search/sources-section";
import { TokenBadges } from "@/components/search/token-badges";
import { ConversationHistory } from "@/components/search/conversation-history";
import { searchResults as dummyResults } from "@/lib/dummy-data";
import type { SearchResult } from "@/lib/types";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [activeResult, setActiveResult] = useState<SearchResult | null>(null);
  const [history, setHistory] = useState<SearchResult[]>(dummyResults);

  const handleSearch = useCallback(() => {
    if (!query.trim()) return;

    setIsLoading(true);

    // Simulate search delay, then pick a result from dummy data
    setTimeout(() => {
      const index = history.length % dummyResults.length;
      const result: SearchResult = {
        ...dummyResults[index],
        id: `sr-${Date.now()}`,
        query: query.trim(),
        timestamp: new Date().toISOString(),
      };

      setHistory((prev) => [result, ...prev].slice(0, 5));
      setActiveResult(result);
      setIsLoading(false);
      setQuery("");
    }, 800);
  }, [query, history.length]);

  const handleSelectHistory = useCallback((result: SearchResult) => {
    setActiveResult(result);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold tracking-tight">Search</h2>
        <p className="text-sm text-muted-foreground">
          Query your document knowledge base.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
        <div className="space-y-4">
          <QueryInput
            value={query}
            onChange={setQuery}
            onSubmit={handleSearch}
            isLoading={isLoading}
          />

          <ResponseContainer result={activeResult} isLoading={isLoading} />

          {activeResult && !isLoading && (
            <>
              <SourcesSection sources={activeResult.sources} />
              <TokenBadges usage={activeResult.tokenUsage} />
            </>
          )}
        </div>

        <div className="order-first lg:order-last">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">
                Recent Queries
              </CardTitle>
            </CardHeader>
            <CardContent className="px-2 pb-2">
              <ConversationHistory
                results={history.slice(0, 5)}
                activeId={activeResult?.id ?? null}
                onSelect={handleSelectHistory}
              />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
