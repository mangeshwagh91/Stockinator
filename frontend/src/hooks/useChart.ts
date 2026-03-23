import { useQuery } from '@tanstack/react-query';
import { fetchChart, ChartData } from '@/services/api';

export function useChart(symbol: string | null, period = '1mo', interval = '1d') {
  return useQuery<ChartData>({
    queryKey: ['chart', symbol, period, interval],
    queryFn: () => fetchChart(symbol!, period, interval),
    enabled: !!symbol,
    staleTime: 30_000,
    refetchOnWindowFocus: true,
    retry: 1,
  });
}
