import { useQuery } from '@tanstack/react-query';
import { fetchQuote, QuoteData } from '@/services/api';

export function useQuote(symbol: string | null) {
  return useQuery<QuoteData>({
    queryKey: ['quote', symbol],
    queryFn: () => fetchQuote(symbol!),
    enabled: !!symbol,
    refetchInterval: 8_000, // refresh every 8 s
    staleTime: 5_000,
    retry: 1,
  });
}
