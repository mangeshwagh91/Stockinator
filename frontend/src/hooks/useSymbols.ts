import { useQuery } from '@tanstack/react-query';
import { fetchSymbols, WatchlistSymbol } from '@/services/api';

export function useSymbols() {
  return useQuery<WatchlistSymbol[]>({
    queryKey: ['symbols'],
    queryFn: fetchSymbols,
    staleTime: 60_000,
    retry: 2,
  });
}
