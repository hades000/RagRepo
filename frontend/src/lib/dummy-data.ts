import type {
  Document,
  SearchResult,
  UsageRecord,
  ModelConfig,
} from "./types";

export const documents: Document[] = [
  {
    id: "doc-001",
    title: "Q3 Financial Report 2025",
    collection: "Finance",
    status: "indexed",
    chunkCount: 24,
    size: "2.4 MB",
    createdAt: "2025-12-01",
  },
  {
    id: "doc-002",
    title: "Employee Onboarding Guide",
    collection: "HR",
    status: "indexed",
    chunkCount: 18,
    size: "1.1 MB",
    createdAt: "2025-11-15",
  },
  {
    id: "doc-003",
    title: "API Integration Spec v2",
    collection: "Engineering",
    status: "indexed",
    chunkCount: 32,
    size: "3.8 MB",
    createdAt: "2025-11-28",
  },
  {
    id: "doc-004",
    title: "Product Roadmap 2026",
    collection: "Product",
    status: "processing",
    chunkCount: 0,
    size: "540 KB",
    createdAt: "2026-01-10",
  },
  {
    id: "doc-005",
    title: "Security Audit Report",
    collection: "Compliance",
    status: "indexed",
    chunkCount: 41,
    size: "5.2 MB",
    createdAt: "2025-10-20",
  },
  {
    id: "doc-006",
    title: "Customer Support Playbook",
    collection: "Support",
    status: "indexed",
    chunkCount: 15,
    size: "980 KB",
    createdAt: "2025-09-30",
  },
  {
    id: "doc-007",
    title: "Infrastructure Runbook",
    collection: "Engineering",
    status: "failed",
    chunkCount: 0,
    size: "4.1 MB",
    createdAt: "2026-01-05",
  },
  {
    id: "doc-008",
    title: "Brand Guidelines v3",
    collection: "Marketing",
    status: "indexed",
    chunkCount: 12,
    size: "7.6 MB",
    createdAt: "2025-08-22",
  },
  {
    id: "doc-009",
    title: "Data Retention Policy",
    collection: "Compliance",
    status: "processing",
    chunkCount: 0,
    size: "320 KB",
    createdAt: "2026-02-14",
  },
  {
    id: "doc-010",
    title: "Vendor Evaluation Matrix",
    collection: "Procurement",
    status: "indexed",
    chunkCount: 8,
    size: "420 KB",
    createdAt: "2025-12-18",
  },
];

export const searchResults: SearchResult[] = [
  {
    id: "sr-001",
    query: "What were the key findings in the Q3 financial report?",
    answer:
      "The Q3 2025 financial report highlighted a 12% increase in revenue compared to Q2, driven primarily by enterprise contract renewals. Operating expenses remained stable at ₹4.2 Cr, with a notable reduction in infrastructure costs due to the migration to reserved instances. Net margin improved to 18.3%, exceeding the target of 16%. The report recommends continued investment in the product-led growth channel, which accounted for 34% of new acquisitions.",
    sources: [
      {
        docTitle: "Q3 Financial Report 2025",
        chunkIndex: 3,
        score: 0.92,
        snippet:
          "Revenue for Q3 2025 reached ₹18.7 Cr, representing a 12% quarter-over-quarter increase...",
      },
      {
        docTitle: "Q3 Financial Report 2025",
        chunkIndex: 7,
        score: 0.87,
        snippet:
          "Operating expenses were maintained at ₹4.2 Cr through strategic cost optimization...",
      },
      {
        docTitle: "Q3 Financial Report 2025",
        chunkIndex: 12,
        score: 0.71,
        snippet:
          "Product-led growth contributed 34% of new customer acquisitions during the quarter...",
      },
    ],
    tokenUsage: {
      promptTokens: 820,
      completionTokens: 156,
      totalTokens: 976,
      costINR: 0.68,
    },
    timestamp: "2026-03-09T14:23:00Z",
  },
  {
    id: "sr-002",
    query: "Summarize the employee onboarding process",
    answer:
      "The onboarding process spans three phases over 90 days. Phase 1 (Week 1) covers IT setup, access provisioning, and compliance training. Phase 2 (Weeks 2–4) involves team introductions, role-specific training modules, and assignment of a buddy mentor. Phase 3 (Weeks 5–12) focuses on gradual ramp-up with milestone check-ins at day 30, 60, and 90. All new hires are required to complete the security awareness certification by day 14.",
    sources: [
      {
        docTitle: "Employee Onboarding Guide",
        chunkIndex: 1,
        score: 0.95,
        snippet:
          "The onboarding program is structured into three distinct phases spanning 90 calendar days...",
      },
      {
        docTitle: "Employee Onboarding Guide",
        chunkIndex: 4,
        score: 0.82,
        snippet:
          "Each new hire is assigned a buddy mentor from their immediate team for the first 30 days...",
      },
    ],
    tokenUsage: {
      promptTokens: 640,
      completionTokens: 132,
      totalTokens: 772,
      costINR: 0.54,
    },
    timestamp: "2026-03-09T11:45:00Z",
  },
  {
    id: "sr-003",
    query: "What are the API rate limits for v2?",
    answer:
      "The v2 API enforces tiered rate limits based on the authentication plan. Free tier: 100 requests/minute, 10,000 requests/day. Standard tier: 500 requests/minute, 100,000 requests/day. Enterprise tier: 2,000 requests/minute with no daily cap. All tiers share a maximum payload size of 10 MB per request. Rate limit headers (X-RateLimit-Remaining, X-RateLimit-Reset) are included in every response.",
    sources: [
      {
        docTitle: "API Integration Spec v2",
        chunkIndex: 9,
        score: 0.89,
        snippet:
          "Rate limiting is enforced per API key with limits varying by subscription tier...",
      },
      {
        docTitle: "API Integration Spec v2",
        chunkIndex: 11,
        score: 0.76,
        snippet:
          "Response headers include X-RateLimit-Remaining and X-RateLimit-Reset for client-side handling...",
      },
      {
        docTitle: "API Integration Spec v2",
        chunkIndex: 15,
        score: 0.63,
        snippet:
          "Maximum request payload size is capped at 10 MB across all tiers...",
      },
    ],
    tokenUsage: {
      promptTokens: 710,
      completionTokens: 144,
      totalTokens: 854,
      costINR: 0.6,
    },
    timestamp: "2026-03-08T16:30:00Z",
  },
  {
    id: "sr-004",
    query: "What security vulnerabilities were identified in the audit?",
    answer:
      "The security audit identified 3 critical, 7 high, and 12 medium-severity vulnerabilities. Critical findings included an unauthenticated endpoint in the admin API, a SQL injection vector in the legacy search module, and an expired TLS certificate on the staging environment. All critical issues have been remediated. High-severity items include insufficient logging on authentication failures and missing CORS restrictions on two internal services.",
    sources: [
      {
        docTitle: "Security Audit Report",
        chunkIndex: 2,
        score: 0.94,
        snippet:
          "Executive summary: 22 vulnerabilities identified across 3 severity levels...",
      },
      {
        docTitle: "Security Audit Report",
        chunkIndex: 5,
        score: 0.88,
        snippet:
          "Critical finding C-1: Unauthenticated access to /admin/config endpoint allowing...",
      },
      {
        docTitle: "Security Audit Report",
        chunkIndex: 8,
        score: 0.79,
        snippet:
          "High-severity finding H-3: Authentication failure events are not logged...",
      },
    ],
    tokenUsage: {
      promptTokens: 890,
      completionTokens: 168,
      totalTokens: 1058,
      costINR: 0.74,
    },
    timestamp: "2026-03-08T09:15:00Z",
  },
  {
    id: "sr-005",
    query: "What is the data retention policy for customer records?",
    answer:
      "Customer records are retained for 7 years from the date of last account activity, in compliance with regulatory requirements. Personal identifiable information (PII) is encrypted at rest using AES-256 and can be purged upon verified customer request within 30 business days. Anonymized analytics data is retained indefinitely. Backup archives follow a 90-day rotation cycle with geographic redundancy across two regions.",
    sources: [
      {
        docTitle: "Data Retention Policy",
        chunkIndex: 1,
        score: 0.91,
        snippet:
          "Customer data shall be retained for a minimum period of 7 years from last activity date...",
      },
      {
        docTitle: "Data Retention Policy",
        chunkIndex: 3,
        score: 0.74,
        snippet:
          "PII purge requests must be fulfilled within 30 business days of verified identity...",
      },
    ],
    tokenUsage: {
      promptTokens: 580,
      completionTokens: 128,
      totalTokens: 708,
      costINR: 0.5,
    },
    timestamp: "2026-03-07T13:00:00Z",
  },
];

export const usageRecords: UsageRecord[] = [
  { date: "2026-03-03", queries: 42, tokensUsed: 38400, costINR: 26.88 },
  { date: "2026-03-04", queries: 35, tokensUsed: 31200, costINR: 21.84 },
  { date: "2026-03-05", queries: 58, tokensUsed: 52100, costINR: 36.47 },
  { date: "2026-03-06", queries: 27, tokensUsed: 24800, costINR: 17.36 },
  { date: "2026-03-07", queries: 44, tokensUsed: 40600, costINR: 28.42 },
  { date: "2026-03-08", queries: 51, tokensUsed: 46900, costINR: 32.83 },
  { date: "2026-03-09", queries: 38, tokensUsed: 34200, costINR: 23.94 },
];

export const defaultModelConfig: ModelConfig = {
  model: "gpt-4o-mini",
  temperature: 0.3,
  topK: 5,
  reranking: true,
  searchMode: "hybrid",
  chunkSize: 800,
  chunkOverlap: 150,
};

export function getDashboardStats() {
  const totalDocuments = documents.length;
  const totalCollections = new Set(documents.map((d) => d.collection)).size;
  const todayUsage = usageRecords[usageRecords.length - 1];
  const totalCostINR = usageRecords.reduce((sum, r) => sum + r.costINR, 0);

  return {
    totalDocuments,
    totalCollections,
    queriesToday: todayUsage.queries,
    avgLatency: 1.8,
    totalCostINR: Math.round(totalCostINR * 100) / 100,
  };
}
