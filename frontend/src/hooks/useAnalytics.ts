import { useQuery } from "@tanstack/react-query";
import {
  fetchWinRates,
  fetchSurvival,
  fetchTechniques,
  fetchAccusations,
} from "@/lib/api";

export function useWinRates(batchId?: string) {
  return useQuery({
    queryKey: ["analytics", "winrates", batchId],
    queryFn: () => fetchWinRates(batchId),
    staleTime: 30_000,
  });
}

export function useSurvival(batchId?: string) {
  return useQuery({
    queryKey: ["analytics", "survival", batchId],
    queryFn: () => fetchSurvival(batchId),
    staleTime: 30_000,
  });
}

export function useTechniques(batchId?: string) {
  return useQuery({
    queryKey: ["analytics", "techniques", batchId],
    queryFn: () => fetchTechniques(batchId),
    staleTime: 30_000,
  });
}

export function useAccusations(batchId?: string) {
  return useQuery({
    queryKey: ["analytics", "accusations", batchId],
    queryFn: () => fetchAccusations(batchId),
    staleTime: 30_000,
  });
}
