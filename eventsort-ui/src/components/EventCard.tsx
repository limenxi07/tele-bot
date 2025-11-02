import React from 'react';
import { Event } from '../types/Event';
import './EventCard.css';

interface EventCardProps {
  event: Event;
}

const EventCard: React.FC<EventCardProps> = ({ event }) => {
  return (
    <div className="event-card">
      <div className="event-card-content">
        <div className="event-header">
          <h2 className="event-title">{event.title}</h2>
          <span className="event-type">{event.event_type.toUpperCase()}</span>
        </div>

        <div className="event-details">
          <div className="event-detail">
            <span className="icon">📅</span>
            <span>{event.date}</span>
          </div>

          <div className="event-detail">
            <span className="icon">📍</span>
            <span>{event.location || 'TBC'}</span>
          </div>

          {event.organisation && (
            <div className="event-detail">
              <span className="icon">🏢</span>
              <span>{event.organisation}</span>
            </div>
          )}

          {event.fee !== null && event.fee > 0 && (
            <div className="event-detail">
              <span className="icon">💰</span>
              <span>${event.fee}</span>
            </div>
          )}

          {event.refreshments && event.refreshments !== 'none' && (
            <div className="event-detail">
              <span className="icon">🍽️</span>
              <span>{event.refreshments}</span>
            </div>
          )}

          {event.target_audience && event.target_audience !== 'all students' && (
            <div className="event-detail">
              <span className="icon">👥</span>
              <span>{event.target_audience}</span>
            </div>
          )}

          {event.key_speakers && event.key_speakers !== 'None' && (
            <div className="event-detail">
              <span className="icon">🎤</span>
              <span>{event.key_speakers}</span>
            </div>
          )}
        </div>

        <div className="event-synopsis">
          <p>{event.synopsis}</p>
        </div>

        {event.signup_link && event.signup_link !== 'TBC' && event.signup_link !== 'None' && (
          <a 
            href={event.signup_link} 
            target="_blank" 
            rel="noopener noreferrer" 
            className="signup-link"
            onClick={(e) => e.stopPropagation()}
          >
            🔗 Sign Up
          </a>
        )}
      </div>

      <div className="swipe-hint">
        <span className="swipe-left">👈 Not Interested</span>
        <span className="swipe-right">Interested 👉</span>
      </div>
    </div>
  );
};

export default EventCard;