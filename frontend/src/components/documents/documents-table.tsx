"use client";

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import type { Document } from "@/lib/types";

interface DocumentsTableProps {
  documents: Document[];
}

function statusVariant(
  status: Document["status"]
): "default" | "secondary" | "destructive" {
  switch (status) {
    case "indexed":
      return "default";
    case "processing":
      return "secondary";
    case "failed":
      return "destructive";
  }
}

export function DocumentsTable({ documents }: DocumentsTableProps) {
  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[280px]">Title</TableHead>
            <TableHead>Collection</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Chunks</TableHead>
            <TableHead className="text-right">Size</TableHead>
            <TableHead className="text-right">Created</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {documents.length === 0 ? (
            <TableRow>
              <TableCell
                colSpan={6}
                className="h-24 text-center text-sm text-muted-foreground"
              >
                No documents found.
              </TableCell>
            </TableRow>
          ) : (
            documents.map((doc) => (
              <TableRow key={doc.id}>
                <TableCell className="font-medium text-sm">
                  {doc.title}
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {doc.collection}
                </TableCell>
                <TableCell>
                  <Badge
                    variant={statusVariant(doc.status)}
                    className="text-xs capitalize"
                  >
                    {doc.status}
                  </Badge>
                </TableCell>
                <TableCell className="text-right font-mono text-sm">
                  {doc.chunkCount}
                </TableCell>
                <TableCell className="text-right text-sm text-muted-foreground">
                  {doc.size}
                </TableCell>
                <TableCell className="text-right text-sm text-muted-foreground">
                  {new Date(doc.createdAt).toLocaleDateString("en-IN", {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                  })}
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>
    </div>
  );
}
