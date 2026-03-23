import { useQuery } from "@tanstack/react-query";
import { backendApi } from "@/lib/backendApi";

export const useSystemWorkflow = () => {
  return useQuery({
    queryKey: ["system-workflow"],
    queryFn: backendApi.getWorkflowSummary,
    staleTime: 30_000,
    refetchInterval: 30_000,
    retry: 1,
  });
};
