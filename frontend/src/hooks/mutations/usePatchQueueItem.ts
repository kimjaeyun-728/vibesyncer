import { QueueResponseSchema } from '@/schemas/queueSchema';
import { z } from 'zod';
import { useMutation } from '@tanstack/react-query';
import { toast } from 'react-toastify';
import { patchQueueItemAPI } from '@/api/queueApi';
import { useQueryClient } from '@tanstack/react-query';

interface UsePatchQueueItemProps {
  roomCode: string;
  currentSongId: number;
}

const usePatchQueueItem = ({
  roomCode,
  currentSongId,
}: UsePatchQueueItemProps) => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const rawData = await patchQueueItemAPI({
        roomCode,
        itemId: currentSongId,
      });
      const validatedData = QueueResponseSchema.parse(rawData);
      return validatedData;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ['queueList', roomCode],
      });
      toast.success('Song marked as played');
    },
    onError: (error) => {
      if (error instanceof z.ZodError) {
        const errorMessage = error.issues
          .map((err) => `${err.path.join('.')}: ${err.message}`)
          .join(', ');
        toast.error(`[PatchQueueItem] Validation failed: ${errorMessage}`);
      } else {
        toast.error(`[PatchQueueItem] Error: ${error}`);
      }
    },
  });
};

export default usePatchQueueItem;
