import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from './App.jsx';

describe('App', () => {
  beforeEach(() => {
    global.fetch = vi.fn(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve({ bookings: [] }) })
    );
  });

  it('renders the TravelMate header', () => {
    render(<App />);
    expect(screen.getByRole('heading', { name: 'TravelMate' })).toBeInTheDocument();
  });

  it('shows the orchestrator and agent badges', () => {
    render(<App />);
    expect(screen.getByText('Orchestrator')).toBeInTheDocument();
    expect(screen.getByText('WeatherAgent')).toBeInTheDocument();
    expect(screen.getByText('BookingAgent')).toBeInTheDocument();
    expect(screen.getByText('MCP')).toBeInTheDocument();
  });

  it('shows the empty-bookings hint when no bookings exist', async () => {
    render(<App />);
    expect(await screen.findByText(/No bookings yet/i)).toBeInTheDocument();
  });

  it('seeds the conversation with the greeting message', () => {
    render(<App />);
    expect(screen.getByText(/Hi! I'm TravelMate/)).toBeInTheDocument();
  });
});
