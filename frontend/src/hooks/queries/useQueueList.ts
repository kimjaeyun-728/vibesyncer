import { fetchQueueListAPI } from '@/api/queueApi';
import { useQuery } from '@tanstack/react-query';
import { QueueArraySchema } from '@/schemas/queueSchema';

const useQueueList = (roomCode: string) => {
  return useQuery({
    queryKey: ['queueList', roomCode],
    queryFn: async () => {
      const rawData = await fetchQueueListAPI(roomCode);
      const validatedData = QueueArraySchema.parse(rawData);
      return validatedData;
    },
    enabled: !!roomCode,
    staleTime: 1000 * 10,
    retry: 1,
  });
};

export default useQueueList;
