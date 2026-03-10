import { useState, type FormEvent } from "react";

interface Props {
  onSubmit: (ticker: string, days: number) => Promise<void> | void;
  disabled: boolean;
}

export function TickerForm({ onSubmit, disabled }: Props) {
  const [ticker, setTicker] = useState("MSFT");
  const [days, setDays] = useState(60);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const t = ticker.trim().toUpperCase();
    if (!t || days < 1 || days > 365) return;
    onSubmit(t, days);
  }

  return (
    <form className="ticker-form" onSubmit={handleSubmit}>
      <div className="field">
        <label htmlFor="ticker">Ticker</label>
        <input
          id="ticker"
          type="text"
          value={ticker}
          onChange={(e) => setTicker(e.target.value.toUpperCase())}
          maxLength={10}
          placeholder="e.g. AAPL"
          disabled={disabled}
          autoComplete="off"
        />
      </div>
      <div className="field">
        <label htmlFor="days">Days</label>
        <input
          id="days"
          type="number"
          value={days}
          min={1}
          max={365}
          onChange={(e) => setDays(Number(e.target.value))}
          disabled={disabled}
        />
      </div>
      <button type="submit" disabled={disabled}>
        {disabled ? "Analysing…" : "Analyse"}
      </button>
    </form>
  );
}
