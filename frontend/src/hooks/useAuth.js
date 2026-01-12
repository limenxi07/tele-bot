import { useQuery } from '@tanstack/react-query';
import { api, getTokenFromUrl, setUserId } from '../api/client';

export const useAuth = () => {
  const token = getTokenFromUrl();
  
  return useQuery({
    queryKey: ['auth', token],
    queryFn: async () => {
      // Validate token with your existing endpoint
      const { data } = await api.post('/auth/validate-token', null, {
        params: { token }
      });
      
      // Store user_id for future requests
      setUserId(data.user_id);
      
      return data;
    },
    enabled: !!token,
    retry: false,
    staleTime: Infinity, // Token validation doesn't need to re-run
  });
};
