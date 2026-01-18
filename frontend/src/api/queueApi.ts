import type { QueueArrayResponse, QueueResponse } from '@/schemas/queueSchema';
import apiClient from './apiClient';

interface PatchQueueItemProps {
  roomCode: string;
  itemId: number;
}

export const fetchQueueListAPI = async (roomCode: string) => {
  const response = await apiClient.get<QueueArrayResponse>(
    `/rooms/${roomCode}/queue_list`,
  );
  return response.data;
};

export const patchQueueItemAPI = async ({
  roomCode,
  itemId,
}: PatchQueueItemProps) => {
  const response = await apiClient.patch<QueueResponse>(
    `/rooms/${roomCode}/queue/${itemId}?is_played=true`,
  );
  return response.data;
};
