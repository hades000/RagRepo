"use client";

import { useState, useMemo } from "react";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DocumentsTable } from "@/components/documents/documents-table";
import { documents } from "@/lib/dummy-data";
import type { Document } from "@/lib/types";

type StatusFilter = "all" | Document["status"];

export default function DocumentsPage() {
  const [filter, setFilter] = useState<StatusFilter>("all");

  const filtered = useMemo(() => {
    if (filter === "all") return documents;
    return documents.filter((d) => d.status === filter);
  }, [filter]);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div>
          <h2 className="text-lg font-semibold tracking-tight">Documents</h2>
          <p className="text-sm text-muted-foreground">
            Manage your indexed documents.
          </p>
        </div>
        <Badge variant="secondary" className="ml-auto text-xs font-mono">
          {documents.length} total
        </Badge>
      </div>

      <Tabs
        value={filter}
        onValueChange={(v) => setFilter(v as StatusFilter)}
      >
        <TabsList>
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="indexed">Indexed</TabsTrigger>
          <TabsTrigger value="processing">Processing</TabsTrigger>
          <TabsTrigger value="failed">Failed</TabsTrigger>
        </TabsList>
      </Tabs>

      <DocumentsTable documents={filtered} />
    </div>
  );
}
