export interface Document {
  id: string;
  title: string;
  collection: string;
  status: "indexed" | "processing" | "failed";
  chunkCount: number;
  size: string;
  createdAt: string;
}

export interface Source {
  docTitle: string;
  chunkIndex: number;
  score: number;
  snippet: string;
}

export interface TokenUsage {
  promptTokens: number;
  completionTokens: number;
  totalTokens: number;
  costINR: number;
}

export interface SearchResult {
  id: string;
  query: string;
  answer: string;
  sources: Source[];
  tokenUsage: TokenUsage;
  timestamp: string;
}

export interface UsageRecord {
  date: string;
  queries: number;
  tokensUsed: number;
  costINR: number;
}

export interface ModelConfig {
  model: string;
  temperature: number;
  topK: number;
  reranking: boolean;
  searchMode: "hybrid" | "semantic" | "keyword";
  chunkSize: number;
  chunkOverlap: number;
}
