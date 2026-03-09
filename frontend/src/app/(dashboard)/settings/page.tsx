"use client";

import { useState } from "react";
import { ModelSelection } from "@/components/settings/model-selection";
import { RetrievalConfig } from "@/components/settings/retrieval-config";
import { defaultModelConfig } from "@/lib/dummy-data";
import type { ModelConfig } from "@/lib/types";

export default function SettingsPage() {
  const [config, setConfig] = useState<ModelConfig>(defaultModelConfig);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold tracking-tight">Settings</h2>
        <p className="text-sm text-muted-foreground">
          Configure model and retrieval preferences.
        </p>
      </div>

      <div className="space-y-4 max-w-2xl">
        <ModelSelection config={config} onChange={setConfig} />
        <RetrievalConfig config={config} onChange={setConfig} />
      </div>
    </div>
  );
}
