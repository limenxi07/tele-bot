import React, { useEffect, useState } from 'react';
import { useSwipeable } from 'react-swipeable';
import EventCard from './components/EventCard';
import { Event } from './types/Event';
import { validateToken, getEvents, swipeEvent } from './services/api';
import './App.css';

function App() {
  const [events, setEvents] = useState<Event[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [authenticated, setAuthenticated] = useState(false);
  const [swiping, setSwiping] = useState(false);
  const [swipeDirection, setSwipeDirection] = useState<string | null>(null);

  // Handle authentication on mount
  useEffect(() => {
    const authenticate = async () => {
      try {
        // Get token from URL
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('token');

        if (!token) {
          setError('No authentication token found. Please get a new link from the Telegram bot.');
          setLoading(false);
          return;
        }

        // Validate token
        const authResponse = await validateToken(token);
        
        // Store user_id for future requests
        localStorage.setItem('user_id', authResponse.user_id.toString());
        localStorage.setItem('username', authResponse.username);
        
        setAuthenticated(true);

        // Load events
        const eventsData = await getEvents('upcoming');
        setEvents(eventsData);
        setCurrentIndex(0);
        
        setLoading(false);
      } catch (err: any) {
        console.error('Auth error:', err);
        setError(err.response?.data?.error || 'Authentication failed. Please get a new link from the bot.');
        setLoading(false);
      }
    };

    authenticate();
  }, []);

  const handleSwipe = async (direction: 'left' | 'right') => {
    if (swiping || currentIndex >= events.length) return;
    
    setSwiping(true);
    setSwipeDirection(direction);

    const currentEvent = events[currentIndex];

    try {
      const interested = direction === 'right';
      await swipeEvent(currentEvent.id, interested);
      
      console.log(`Swiped ${direction} on: ${currentEvent.title}`);
      
      // Delay to show animation
      setTimeout(() => {
        setCurrentIndex(prev => prev + 1);
        setSwipeDirection(null);
        setSwiping(false);
      }, 300);
    } catch (err) {
      console.error('Swipe error:', err);
      setSwipeDirection(null);
      setSwiping(false);
    }
  };

  const handlers = useSwipeable({
    onSwipedLeft: () => handleSwipe('left'),
    onSwipedRight: () => handleSwipe('right'),
    preventScrollOnSwipe: true,
    trackMouse: true
  });

  if (loading) {
    return (
      <div className="app-container">
        <div className="loading">
          <h2>Loading your events...</h2>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="app-container">
        <div className="error">
          <h2>⚠️ Authentication Error</h2>
          <p>{error}</p>
          <p>Please send /sort to the Telegram bot to get a new link.</p>
        </div>
      </div>
    );
  }

  if (!authenticated) {
    return (
      <div className="app-container">
        <div className="loading">
          <h2>Authenticating...</h2>
        </div>
      </div>
    );
  }

  if (currentIndex >= events.length) {
    return (
      <div className="app-container">
        <div className="empty-state">
          <h2>🎉 All caught up!</h2>
          <p>You've reviewed all your events.</p>
          <p>Forward more event messages to the bot to see them here.</p>
        </div>
      </div>
    );
  }

  const currentEvent = events[currentIndex];

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>Event Sorter</h1>
        <p className="stats">
          {currentIndex + 1} of {events.length} events
        </p>
      </header>

      <div 
        className={`card-container ${swipeDirection ? `swipe-${swipeDirection}` : ''}`}
        {...handlers}
      >
        <div className="event-card-wrapper">
          <EventCard event={currentEvent} />
        </div>
      </div>

      <div className="action-buttons">
        <button 
          className="btn btn-reject"
          onClick={() => handleSwipe('left')}
          disabled={swiping}
        >
          ✕
        </button>
        <button 
          className="btn btn-accept"
          onClick={() => handleSwipe('right')}
          disabled={swiping}
        >
          ♥
        </button>
      </div>
    </div>
  );
}

export default App;