import React, { useState, useEffect } from 'react';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Calendar = () => {
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newEvent, setNewEvent] = useState({
    title: '',
    description: '',
    start_time: new Date().toISOString().slice(0, 16), // Default to current time
    end_time: new Date(Date.now() + 60 * 60 * 1000).toISOString().slice(0, 16), // 1 hour later
    location: '',
    attendees: [],
    created_by: 'current_user'
  });

  useEffect(() => {
    fetchEvents();
  }, []);

  const fetchEvents = async () => {
    try {
      const response = await axios.get(`${API}/calendar/events`);
      setEvents(response.data);
    } catch (error) {
      console.error('Error fetching events:', error);
    } finally {
      setLoading(false);
    }
  };

  const createEvent = async () => {
    try {
      const eventData = {
        ...newEvent,
        start_time: new Date(newEvent.start_time).toISOString(),
        end_time: new Date(newEvent.end_time).toISOString(),
        attendees: newEvent.attendees.filter(a => a.trim() !== '')
      };
      const response = await axios.post(`${API}/calendar/events`, eventData);
      setEvents([response.data, ...events]);
      setNewEvent({
        title: '',
        description: '',
        start_time: new Date().toISOString().slice(0, 16), // Reset to current time
        end_time: new Date(Date.now() + 60 * 60 * 1000).toISOString().slice(0, 16), // 1 hour later
        location: '',
        attendees: [],
        created_by: 'current_user'
      });
      setShowCreateModal(false);
    } catch (error) {
      console.error('Error creating event:', error);
    }
  };

  const deleteEvent = async (eventId, eventTitle) => {
    if (window.confirm(`Are you sure you want to delete "${eventTitle}"?\n\nThis action cannot be undone.`)) {
      try {
        await axios.delete(`${API}/calendar/events/${eventId}`);
        setEvents(events.filter(event => event.id !== eventId));
        
        // Show success message
        alert(`Event "${eventTitle}" has been successfully deleted.`);
        
        // Clear selected event if it was the deleted one
        if (selectedEvent && selectedEvent.id === eventId) {
          setSelectedEvent(null);
        }
      } catch (error) {
        console.error('Error deleting event:', error);
        alert('Failed to delete event. Please try again.');
      }
    }
  };

  const shareEvent = async (event) => {
    try {
      // Format event details for sharing
      const eventDetails = `
🗓️ EVENT INVITATION

📋 ${event.title}
📅 ${new Date(event.start_time).toLocaleDateString('en-US', { 
        weekday: 'long', 
        year: 'numeric', 
        month: 'long', 
        day: 'numeric' 
      })}
⏰ ${new Date(event.start_time).toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
      })} - ${new Date(event.end_time).toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
      })}
📍 ${event.location || 'Location TBD'}

📝 Description:
${event.description || 'No description provided'}

---
Sent from SystemIX AI Platinum Suite
      `.trim();

      // Try to use Web Share API if available
      if (navigator.share) {
        await navigator.share({
          title: `Event: ${event.title}`,
          text: eventDetails,
          url: window.location.href
        });
        alert('Event shared successfully!');
      } else {
        // Fallback: Copy to clipboard
        await navigator.clipboard.writeText(eventDetails);
        alert('Event details copied to clipboard!\n\nYou can now paste and share via email, messaging, or any other platform.');
      }
    } catch (error) {
      console.error('Error sharing event:', error);
      
      // Ultimate fallback: Show details in a modal for manual copying
      const fallbackShare = window.confirm(
        `Share Event: ${event.title}\n\nWould you like to see the event details to copy manually?`
      );
      
      if (fallbackShare) {
        const eventInfo = `Event: ${event.title}\nDate: ${new Date(event.start_time).toLocaleString()}\nLocation: ${event.location || 'TBD'}\nDescription: ${event.description || 'None'}`;
        prompt('Copy these event details to share:', eventInfo);
      }
    }
  };

  const editEvent = async (event) => {
    // Populate the form with existing event data
    setNewEvent({
      ...event,
      start_time: new Date(event.start_time).toISOString().slice(0, 16),
      end_time: new Date(event.end_time).toISOString().slice(0, 16),
      attendees: event.attendees || []
    });
    setEditingEvent(event);
    setShowCreateModal(true);
  };

  const updateEvent = async () => {
    try {
      const eventData = {
        ...newEvent,
        start_time: new Date(newEvent.start_time).toISOString(),
        end_time: new Date(newEvent.end_time).toISOString(),
        attendees: newEvent.attendees.filter(a => a.trim() !== '')
      };
      
      const response = await axios.put(`${API}/calendar/events/${editingEvent.id}`, eventData);
      setEvents(events.map(event => 
        event.id === editingEvent.id ? response.data : event
      ));
      
      // Reset form and close modal
      setNewEvent({
        title: '',
        description: '',
        start_time: new Date().toISOString().slice(0, 16),
        end_time: new Date(Date.now() + 60 * 60 * 1000).toISOString().slice(0, 16),
        location: '',
        attendees: [],
        created_by: 'current_user'
      });
      setEditingEvent(null);
      setShowCreateModal(false);
      
      alert('Event updated successfully!');
    } catch (error) {
      console.error('Error updating event:', error);
      alert('Failed to update event. Please try again.');
    }
  };

  const getDaysInMonth = (date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDayOfWeek = firstDay.getDay();

    const days = [];
    
    // Add empty cells for days before the first day of the month
    for (let i = 0; i < startingDayOfWeek; i++) {
      days.push(null);
    }
    
    // Add all days of the month
    for (let day = 1; day <= daysInMonth; day++) {
      days.push(new Date(year, month, day));
    }
    
    return days;
  };

  const getEventsForDate = (date) => {
    if (!date) return [];
    return events.filter(event => {
      const eventDate = new Date(event.start_time);
      return eventDate.toDateString() === date.toDateString();
    });
  };

  const formatTime = (dateString) => {
    return new Date(dateString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const isToday = (date) => {
    if (!date) return false;
    return date.toDateString() === new Date().toDateString();
  };

  const isSelected = (date) => {
    if (!date) return false;
    return date.toDateString() === selectedDate.toDateString();
  };

  const navigateMonth = (direction) => {
    setCurrentMonth(prev => {
      const newMonth = new Date(prev);
      newMonth.setMonth(prev.getMonth() + direction);
      return newMonth;
    });
  };

  const days = getDaysInMonth(currentMonth);
  const monthName = currentMonth.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  const selectedDateEvents = getEventsForDate(selectedDate);

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-6"></div>
          <div className="h-96 bg-gray-200 dark:bg-gray-700 rounded-lg"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 animate-fadeIn">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Calendar</h1>
          <p className="text-gray-600 dark:text-gray-400">AI-powered scheduling and meeting insights</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn-primary"
        >
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
          New Event
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Calendar */}
        <div className="lg:col-span-2">
          <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50 dark:border-gray-700/50">
            {/* Calendar Header */}
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-gray-900 dark:text-white">{monthName}</h2>
              <div className="flex space-x-2">
                <button
                  onClick={() => navigateMonth(-1)}
                  className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                </button>
                <button
                  onClick={() => navigateMonth(1)}
                  className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              </div>
            </div>

            {/* Days of Week */}
            <div className="grid grid-cols-7 gap-1 mb-2">
              {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
                <div key={day} className="p-2 text-center text-sm font-medium text-gray-500 dark:text-gray-400">
                  {day}
                </div>
              ))}
            </div>

            {/* Calendar Grid */}
            <div className="grid grid-cols-7 gap-1">
              {days.map((date, index) => {
                const dayEvents = getEventsForDate(date);
                return (
                  <div
                    key={index}
                    onClick={() => date && setSelectedDate(date)}
                    className={`
                      min-h-[80px] p-2 border border-gray-200 dark:border-gray-700 cursor-pointer transition-colors
                      ${date ? 'hover:bg-gray-50 dark:hover:bg-gray-700/50' : ''}
                      ${isToday(date) ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-700' : ''}
                      ${isSelected(date) ? 'bg-blue-100 dark:bg-blue-900/30 border-blue-300 dark:border-blue-600' : ''}
                    `}
                  >
                    {date && (
                      <>
                        <div className={`text-sm font-medium mb-1 ${
                          isToday(date) ? 'text-blue-600 dark:text-blue-400' : 'text-gray-900 dark:text-white'
                        }`}>
                          {date.getDate()}
                        </div>
                        <div className="space-y-1">
                          {dayEvents.slice(0, 2).map((event) => (
                            <div
                              key={event.id}
                              className="text-xs p-1 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded truncate"
                            >
                              {event.title}
                            </div>
                          ))}
                          {dayEvents.length > 2 && (
                            <div className="text-xs text-gray-500 dark:text-gray-400">
                              +{dayEvents.length - 2} more
                            </div>
                          )}
                        </div>
                      </>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Event Details */}
        <div className="space-y-6">
          {/* Today's Stats */}
          <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50 dark:border-gray-700/50">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Today's Overview</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">Total Events</span>
                <span className="text-lg font-bold text-gray-900 dark:text-white">
                  {getEventsForDate(new Date()).length}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">This Week</span>
                <span className="text-lg font-bold text-gray-900 dark:text-white">
                  {events.filter(event => {
                    const eventDate = new Date(event.start_time);
                    const now = new Date();
                    const weekStart = new Date(now.setDate(now.getDate() - now.getDay()));
                    const weekEnd = new Date(weekStart);
                    weekEnd.setDate(weekStart.getDate() + 6);
                    return eventDate >= weekStart && eventDate <= weekEnd;
                  }).length}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">This Month</span>
                <span className="text-lg font-bold text-gray-900 dark:text-white">
                  {events.filter(event => {
                    const eventDate = new Date(event.start_time);
                    return eventDate.getMonth() === new Date().getMonth() && 
                           eventDate.getFullYear() === new Date().getFullYear();
                  }).length}
                </span>
              </div>
            </div>
          </div>

          {/* Selected Date Events */}
          <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-xl p-6 border border-gray-200/50 dark:border-gray-700/50">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              {selectedDate.toLocaleDateString('en-US', { 
                weekday: 'long', 
                year: 'numeric', 
                month: 'long', 
                day: 'numeric' 
              })}
            </h3>
            
            {selectedDateEvents.length > 0 ? (
              <div className="space-y-3">
                {selectedDateEvents.map((event) => (
                  <div key={event.id} className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="font-medium text-gray-900 dark:text-white">{event.title}</h4>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {formatTime(event.start_time)} - {formatTime(event.end_time)}
                      </span>
                    </div>
                    {event.description && (
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">{event.description}</p>
                    )}
                    {event.location && (
                      <div className="flex items-center space-x-1 text-xs text-gray-500 dark:text-gray-400">
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                        <span>{event.location}</span>
                      </div>
                    )}
                    {event.attendees && event.attendees.length > 0 && (
                      <div className="flex items-center space-x-1 text-xs text-gray-500 dark:text-gray-400 mt-1">
                        <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                        </svg>
                        <span>{event.attendees.join(', ')}</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500 dark:text-gray-400">
                <div className="text-4xl mb-2">📅</div>
                <p className="text-sm">No events scheduled</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Create Event Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl p-6 w-full max-w-md max-h-[90vh] overflow-y-auto">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Create New Event</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Title</label>
                <input
                  type="text"
                  value={newEvent.title}
                  onChange={(e) => setNewEvent({ ...newEvent, title: e.target.value })}
                  className="form-input"
                  placeholder="Enter event title"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Description</label>
                <textarea
                  value={newEvent.description}
                  onChange={(e) => setNewEvent({ ...newEvent, description: e.target.value })}
                  className="form-input"
                  rows="3"
                  placeholder="Event description"
                />
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Start Time</label>
                  <input
                    type="datetime-local"
                    value={newEvent.start_time}
                    onChange={(e) => setNewEvent({ ...newEvent, start_time: e.target.value })}
                    className="form-input"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">End Time</label>
                  <input
                    type="datetime-local"
                    value={newEvent.end_time}
                    onChange={(e) => setNewEvent({ ...newEvent, end_time: e.target.value })}
                    className="form-input"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Location</label>
                <input
                  type="text"
                  value={newEvent.location}
                  onChange={(e) => setNewEvent({ ...newEvent, location: e.target.value })}
                  className="form-input"
                  placeholder="Meeting location"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Attendees</label>
                <input
                  type="text"
                  value={newEvent.attendees.join(', ')}
                  onChange={(e) => setNewEvent({ ...newEvent, attendees: e.target.value.split(',').map(a => a.trim()) })}
                  className="form-input"
                  placeholder="Enter attendee emails, separated by commas"
                />
              </div>
            </div>
            
            <div className="flex space-x-3 mt-6">
              <button
                onClick={createEvent}
                className="flex-1 btn-primary"
                disabled={!newEvent.title || !newEvent.start_time || !newEvent.end_time}
              >
                Create Event
              </button>
              <button
                onClick={() => setShowCreateModal(false)}
                className="flex-1 btn-secondary"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Calendar;