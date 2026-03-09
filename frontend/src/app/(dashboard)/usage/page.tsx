"use client";

import { useState } from "react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { StatsCards } from "@/components/usage/stats-cards";
import { UsageBreakdown } from "@/components/usage/usage-breakdown";
import { usageRecords } from "@/lib/dummy-data";

export default function UsagePage() {
  const [tab, setTab] = useState("overview");

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold tracking-tight">Usage</h2>
        <p className="text-sm text-muted-foreground">
          Monitor token usage and costs.
        </p>
      </div>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="breakdown">Daily Breakdown</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="mt-4">
          <StatsCards records={usageRecords} />
        </TabsContent>

        <TabsContent value="breakdown" className="mt-4">
          <UsageBreakdown records={usageRecords} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
