import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';

// Fetch events (to review)
export const useEvents = (filter = 'upcoming') => {
  return useQuery({
    queryKey: ['events', filter],
    queryFn: async () => {
      const { data } = await api.get('/events', {
        params: { 
          filter,
          include_raw: false 
        }
      });
      return data;
    },
  });
};

// Fetch interested events
export const useInterestedEvents = () => {
  return useQuery({
    queryKey: ['events', 'interested'],
    queryFn: async () => {
      const { data } = await api.get('/events/interested/all');
      return data;
    },
  });
};

// Swipe mutation
export const useSwipeEvent = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ eventId, interested }) => {
      const { data } = await api.post(`/events/${eventId}/swipe`, {
        interested
      });
      return data;
    },
    onSuccess: () => {
      // Invalidate queries to refresh the list
      queryClient.invalidateQueries({ queryKey: ['events'] });
    },
  });
};

// Get stats
export const useStats = () => {
  return useQuery({
    queryKey: ['stats'],
    queryFn: async () => {
      const { data } = await api.get('/stats');
      return data;
    },
  });
};
