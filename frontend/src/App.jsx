import { useEffect, useRef, useState } from 'react';

const SUGGESTIONS = [
  'What destinations can I choose from?',
  'Tell me about Tokyo and the weather on 2026-04-12',
  "I'd like to book 5 nights in Bali starting 2026-07-10 for 2 travelers (name: Priya Shah)",
];

function ToolTrace({ trace }) {
  if (!trace?.length) return null;
  return (
    <details className="trace">
      <summary>Agent activity ({trace.length} step{trace.length === 1 ? '' : 's'})</summary>
      <ol>
        {trace.map((step, i) => (
          <li key={i}>
            <code>{step.tool}</code>
            <span className="trace-args">{JSON.stringify(step.args)}</span>
          </li>
        ))}
      </ol>
    </details>
  );
}

function Bubble({ role, content, trace }) {
  if (!content && (!trace || trace.length === 0)) return null;
  return (
    <div className={`bubble ${role}`}>
      <div className="bubble-role">{role === 'user' ? 'You' : 'TravelMate'}</div>
      {content && <div className="bubble-content">{content}</div>}
      {role === 'assistant' && <ToolTrace trace={trace} />}
    </div>
  );
}

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content:
        "Hi! I'm TravelMate. I can suggest destinations, check the weather, and book your trip. Where are you thinking of going?",
      trace: [],
    },
  ]);
  const [history, setHistory] = useState([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const [bookings, setBookings] = useState([]);
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, busy]);

  async function refreshBookings() {
    try {
      const r = await fetch('/api/bookings');
      if (r.ok) {
        const data = await r.json();
        setBookings(data.bookings || []);
      }
    } catch {
      /* ignore */
    }
  }

  useEffect(() => {
    refreshBookings();
  }, []);

  async function send(text) {
    if (!text.trim() || busy) return;
    setError(null);
    setBusy(true);
    const userMsg = { role: 'user', content: text, trace: [] };
    setMessages((m) => [...m, userMsg]);
    setInput('');
    try {
      const r = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, history }),
      });
      if (!r.ok) throw new Error(await r.text());
      const data = await r.json();
      setHistory(data.history || []);
      setMessages((m) => [
        ...m,
        { role: 'assistant', content: data.reply, trace: data.tool_trace || [] },
      ]);
      if ((data.tool_trace || []).some((t) => t.tool === 'create_booking')) {
        refreshBookings();
      }
    } catch (e) {
      setError(String(e.message || e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>TravelMate</h1>
          <p className="tag">Multi-agent AI travel booking · OpenAI · MCP · A2A</p>
        </div>
        <div className="badges">
          <span className="badge">Orchestrator</span>
          <span className="badge">WeatherAgent</span>
          <span className="badge">BookingAgent</span>
          <span className="badge mcp">MCP</span>
        </div>
      </header>

      <main className="main">
        <section className="chat-card">
          <div className="messages" ref={scrollRef}>
            {messages.map((m, i) => (
              <Bubble key={i} {...m} />
            ))}
            {busy && (
              <div className="bubble assistant">
                <div className="bubble-role">TravelMate</div>
                <div className="typing">
                  <span></span><span></span><span></span>
                </div>
              </div>
            )}
          </div>

          <div className="suggestions">
            {SUGGESTIONS.map((s) => (
              <button key={s} onClick={() => send(s)} disabled={busy} className="chip">
                {s}
              </button>
            ))}
          </div>

          {error && <div className="error">{error}</div>}

          <form
            className="composer"
            onSubmit={(e) => {
              e.preventDefault();
              send(input);
            }}
          >
            <input
              type="text"
              placeholder="Where would you like to travel?"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={busy}
            />
            <button type="submit" disabled={busy || !input.trim()}>
              Send
            </button>
          </form>
        </section>

        <aside className="sidebar">
          <h2>Bookings</h2>
          {bookings.length === 0 && <p className="muted">No bookings yet — say the word.</p>}
          {bookings.map((b) => (
            <div key={b.confirmation_code} className="booking">
              <div className="code">{b.confirmation_code}</div>
              <div>
                {b.city}, {b.country}
              </div>
              <div className="muted">
                {b.travel_date} · {b.nights} night{b.nights === 1 ? '' : 's'} · {b.num_travelers} traveler
                {b.num_travelers === 1 ? '' : 's'}
              </div>
              <div className="muted">Total: ${b.total_price_usd.toLocaleString()}</div>
              <div className="muted small">Booked for {b.traveler_name}</div>
            </div>
          ))}
        </aside>
      </main>
    </div>
  );
}
