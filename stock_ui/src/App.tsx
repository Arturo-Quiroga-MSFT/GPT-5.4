import "./App.css";
import { useAnalysisStream } from "./hooks/useAnalysisStream";
import { TickerForm } from "./components/TickerForm";
import { StatsBar } from "./components/StatsBar";
import { StockChart } from "./components/StockChart";
import { AnalysisPanel } from "./components/AnalysisPanel";
import { StatusBadge } from "./components/StatusBadge";
import { UsageFooter } from "./components/UsageFooter";

function App() {
  const { state, run, reset } = useAnalysisStream();
  const busy = !["idle", "done", "error"].includes(state.phase);

  return (
    <div className="app">
      <header className="app-header">
        <h1>Stock Analysis</h1>
        <p className="subtitle">Powered by GPT-5.4 via Azure OpenAI</p>
      </header>

      <main className="app-main">
        <TickerForm
          onSubmit={(ticker, days) => run({ ticker, days })}
          disabled={busy}
        />

        {state.phase !== "idle" && (
          <div className="status-row">
            <StatusBadge phase={state.phase} message={state.statusMessage} />
            {(state.phase === "done" || state.phase === "error") && (
              <button className="reset-btn" onClick={reset}>
                New analysis
              </button>
            )}
          </div>
        )}

        {state.error && (
          <div className="error-box">{state.error}</div>
        )}

        {state.toolResult && (
          <>
            <StatsBar data={state.toolResult} />
            <StockChart
              data={state.toolResult}
              title={`${state.toolResult.ticker} — Daily Close`}
            />
          </>
        )}

        <AnalysisPanel
          text={state.analysisText}
          streaming={state.phase === "analysing"}
          title={state.toolResult ? `${state.toolResult.ticker} Analysis` : "Analysis"}
          accent="#00b4d8"
        />

        {state.followupToolResult && (
          <StockChart
            data={state.followupToolResult}
            title={`${state.followupToolResult.ticker} — Follow-up Data`}
          />
        )}

        <AnalysisPanel
          text={state.followupText}
          streaming={state.phase === "followup" && !!state.followupText}
          title="Follow-up Analysis"
          accent="#f1c40f"
        />

        {state.usage && <UsageFooter usage={state.usage} />}
      </main>
    </div>
  );
}

export default App;
