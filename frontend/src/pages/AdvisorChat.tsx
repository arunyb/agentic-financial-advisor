import { useState, type FormEvent } from "react";
import * as endpoints from "../api/endpoints";
import type { AgentStep } from "../api/types";
import { AgentTraceLedger } from "../components/AgentTraceLedger";
import { AxiosError } from "axios";

interface Turn {
  role: "user" | "assistant";
  content: string;
  trace?: AgentStep[];
  citations?: string[];
}

const SUGGESTIONS = [
  "How is my portfolio allocated right now?",
  "Am I taking on too much risk for my goals?",
  "What should I consider before investing more this month?",
];

export default function AdvisorChat() {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [sessionId, setSessionId] = useState<string | undefined>(undefined);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastTrace, setLastTrace] = useState<AgentStep[]>([]);

  async function send(message: string) {
    if (!message.trim() || sending) return;
    setError(null);
    setTurns((t) => [...t, { role: "user", content: message }]);
    setInput("");
    setSending(true);
    try {
      const resp = await endpoints.sendChatMessage(message, sessionId);
      setSessionId(resp.session_id);
      setLastTrace(resp.agent_trace);
      setTurns((t) => [
        ...t,
        { role: "assistant", content: resp.reply, trace: resp.agent_trace, citations: resp.citations },
      ]);
    } catch (err) {
      const axiosErr = err as AxiosError<{ detail?: string }>;
      setError(
        axiosErr.response?.data?.detail
          ? String(axiosErr.response.data.detail)
          : "The advisor pipeline could not complete. Check that GROQ_API_KEY is configured on the backend."
      );
    } finally {
      setSending(false);
    }
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    send(input);
  }

  return (
    <div className="grid h-[calc(100vh-5rem)] grid-cols-5 gap-6">
      <div className="col-span-3 flex flex-col rounded-lg border border-slate-line bg-white shadow-card">
        <div className="border-b border-slate-line px-5 py-4">
          <h1 className="font-display text-xl text-ink">Advisor</h1>
          <p className="text-xs text-slate-soft">
            Planner → Portfolio → Risk → Recommendation, grounded in your data and the knowledge base.
          </p>
        </div>

        <div className="flex-1 space-y-4 overflow-y-auto px-5 py-4">
          {turns.length === 0 && (
            <div className="space-y-2">
              <p className="text-sm text-slate-soft">Try asking:</p>
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  className="block w-full rounded-md border border-slate-line px-3 py-2 text-left text-sm text-ink/80 hover:border-indigo hover:text-indigo-dark"
                >
                  {s}
                </button>
              ))}
            </div>
          )}

          {turns.map((turn, i) => (
            <div key={i} className={turn.role === "user" ? "flex justify-end" : "flex justify-start"}>
              <div
                className={`max-w-[85%] rounded-lg px-4 py-2.5 text-sm leading-relaxed ${
                  turn.role === "user"
                    ? "bg-indigo text-white"
                    : "border border-slate-line bg-paperdim text-ink"
                }`}
              >
                <p className="whitespace-pre-wrap">{turn.content}</p>
                {turn.citations && turn.citations.length > 0 && (
                  <p className="mt-2 text-[11px] text-ink/50">
                    Sources: {turn.citations.join(", ")}
                  </p>
                )}
              </div>
            </div>
          ))}

          {sending && <p className="font-mono text-xs text-slate-soft">Agents are working…</p>}
          {error && <p className="text-sm text-amber">{error}</p>}
        </div>

        <form onSubmit={handleSubmit} className="border-t border-slate-line p-4">
          <div className="flex gap-2">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about your portfolio, risk, or next steps…"
              className="flex-1 rounded-md border border-slate-line px-3 py-2 text-sm focus:border-indigo"
            />
            <button
              type="submit"
              disabled={sending}
              className="rounded-md bg-indigo px-4 py-2 text-sm font-medium text-white hover:bg-indigo-dark disabled:opacity-60"
            >
              Send
            </button>
          </div>
        </form>
      </div>

      <div className="col-span-2">
        {lastTrace.length > 0 ? (
          <AgentTraceLedger steps={lastTrace} />
        ) : (
          <div className="rounded-lg border border-dashed border-slate-line p-6 text-center text-sm text-slate-soft">
            The agent trace for your next question will appear here.
          </div>
        )}
      </div>
    </div>
  );
}
