import { useQuery } from "@tanstack/react-query";
import { fetchBatches, fetchBatchStatus } from "@/lib/api";

export function useBatches() {
  return useQuery({
    queryKey: ["batches"],
    queryFn: fetchBatches,
    staleTime: 10_000,
  });
}

export function useBatchStatus(batchId: string | undefined) {
  return useQuery({
    queryKey: ["batch-status", batchId],
    queryFn: () => fetchBatchStatus(batchId!),
    enabled: !!batchId,
    refetchInterval: (query) => {
      // Poll every 3 seconds while running
      const status = query.state.data?.status;
      return status === "running" ? 3_000 : false;
    },
  });
}
