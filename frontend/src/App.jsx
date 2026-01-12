import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuth } from './hooks/useAuth';
import { useEvents, useStats } from './hooks/useEvents';

const queryClient = new QueryClient();

function EventCard({ event }) {
  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-4">
      <h3 className="text-xl font-bold mb-2">{event.title}</h3>
      <div className="text-sm text-gray-600 mb-2">
        <span className="font-semibold">{event.event_type}</span>
        {event.organisation && ` • ${event.organisation}`}
      </div>
      <p className="text-gray-700 mb-3">{event.synopsis}</p>
      <div className="grid grid-cols-2 gap-2 text-sm">
        <div>
          <span className="font-semibold">📅 Date:</span> {event.date}
        </div>
        {event.location && (
          <div>
            <span className="font-semibold">📍 Location:</span> {event.location}
          </div>
        )}
        {event.deadline && (
          <div className="col-span-2">
            <span className="font-semibold">⏰ Deadline:</span> {event.deadline}
          </div>
        )}
        {event.fee !== null && (
          <div>
            <span className="font-semibold">💰 Fee:</span> {event.fee === 0 ? 'Free' : `$${event.fee}`}
          </div>
        )}
      </div>
      {event.signup_link && (
        <a 
          href={event.signup_link}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:underline text-sm mt-2 inline-block"
        >
          🔗 Sign up link
        </a>
      )}
    </div>
  );
}

function Dashboard() {
  const { data: events, isLoading: eventsLoading } = useEvents('upcoming');
  const { data: stats, isLoading: statsLoading } = useStats();

  if (eventsLoading || statsLoading) {
    return <div className="text-center py-8">Loading events...</div>;
  }

  return (
    <div>
      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-2xl font-bold text-blue-600">{stats?.pending_swipes || 0}</div>
          <div className="text-sm text-gray-600">To Review</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-2xl font-bold text-green-600">{stats?.interested || 0}</div>
          <div className="text-sm text-gray-600">Interested</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-2xl font-bold text-red-600">{stats?.urgent_events || 0}</div>
          <div className="text-sm text-gray-600">Urgent</div>
        </div>
        <div className="bg-white rounded-lg shadow p-4">
          <div className="text-2xl font-bold text-gray-600">{stats?.total_events || 0}</div>
          <div className="text-sm text-gray-600">Total</div>
        </div>
      </div>

      {/* Events List */}
      <h2 className="text-2xl font-bold mb-4">Events to Review</h2>
      {events && events.length > 0 ? (
        <div>
          {events.map(event => (
            <EventCard key={event.id} event={event} />
          ))}
        </div>
      ) : (
        <div className="text-center py-12 text-gray-500">
          <p className="text-xl">🎉 All caught up!</p>
          <p>No events to review.</p>
        </div>
      )}
    </div>
  );
}

function AppContent() {
  const { data: auth, isLoading, isError, error } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="text-4xl mb-4">⏳</div>
          <p className="text-xl">Loading...</p>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center max-w-md p-8 bg-white rounded-lg shadow">
          <div className="text-6xl mb-4">🔒</div>
          <h1 className="text-2xl font-bold text-red-600 mb-2">Access Denied</h1>
          <p className="text-gray-600">
            Invalid or expired link. Please request a new one from the bot by typing <code className="bg-gray-100 px-2 py-1 rounded">/sort</code>
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-6xl mx-auto py-6 px-4">
          <h1 className="text-3xl font-bold text-gray-900">
            EventSort
          </h1>
          <p className="text-gray-600">Welcome back, {auth.username}! 👋</p>
        </div>
      </header>
      <main className="max-w-6xl mx-auto py-6 px-4">
        <Dashboard />
      </main>
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}

export default App;
