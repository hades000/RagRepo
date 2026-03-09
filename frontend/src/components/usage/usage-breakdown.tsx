import {
  Table,
  TableBody,
  TableCell,
  TableFooter,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { UsageRecord } from "@/lib/types";

interface UsageBreakdownProps {
  records: UsageRecord[];
}

export function UsageBreakdown({ records }: UsageBreakdownProps) {
  const totalQueries = records.reduce((sum, r) => sum + r.queries, 0);
  const totalTokens = records.reduce((sum, r) => sum + r.tokensUsed, 0);
  const totalCost = records.reduce((sum, r) => sum + r.costINR, 0);

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Date</TableHead>
            <TableHead className="text-right">Queries</TableHead>
            <TableHead className="text-right">Tokens</TableHead>
            <TableHead className="text-right">Cost (INR)</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {records.map((record) => (
            <TableRow key={record.date}>
              <TableCell className="text-sm">
                {new Date(record.date).toLocaleDateString("en-IN", {
                  weekday: "short",
                  month: "short",
                  day: "numeric",
                })}
              </TableCell>
              <TableCell className="text-right font-mono text-sm">
                {record.queries}
              </TableCell>
              <TableCell className="text-right font-mono text-sm">
                {record.tokensUsed.toLocaleString()}
              </TableCell>
              <TableCell className="text-right font-mono text-sm">
                ₹{record.costINR.toFixed(2)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
        <TableFooter>
          <TableRow>
            <TableCell className="font-medium text-sm">Total</TableCell>
            <TableCell className="text-right font-mono text-sm font-medium">
              {totalQueries}
            </TableCell>
            <TableCell className="text-right font-mono text-sm font-medium">
              {totalTokens.toLocaleString()}
            </TableCell>
            <TableCell className="text-right font-mono text-sm font-medium">
              ₹{totalCost.toFixed(2)}
            </TableCell>
          </TableRow>
        </TableFooter>
      </Table>
    </div>
  );
}
