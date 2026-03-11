/**
 * ChatMessage — renders one completed conversation turn:
 *   • Right-aligned user bubble
 *   • Full-width AI response card (stats / chart / analysis text / usage)
 */
import type { CompletedTurn } from "../hooks/useChatSession";
import { StatsBar } from "./StatsBar";
import { StockChart } from "./StockChart";
import { AnalysisPanel } from "./AnalysisPanel";
import { UsageFooter } from "./UsageFooter";
import { FundamentalsCard } from "./FundamentalsCard";

interface Props {
  turn: CompletedTurn;
}

export function ChatMessage({ turn }: Props) {
  return (
    <div className="chat-turn">
      <div className="user-bubble">{turn.userMessage}</div>
      <div className="ai-response">
        {turn.error && <div className="error-box">{turn.error}</div>}
        {turn.fundamentalsResult && <FundamentalsCard data={turn.fundamentalsResult} />}
        {turn.toolResult && <StatsBar data={turn.toolResult} />}
        {turn.toolResult && (
          <StockChart
            data={turn.toolResult}
            title={`${turn.toolResult.ticker} — Daily Close`}
          />
        )}
        {turn.analysisText && (
          <AnalysisPanel
            text={turn.analysisText}
            streaming={false}
            title="Analysis"
            accent="#00b4d8"
          />
        )}
        {turn.usage && <UsageFooter usage={turn.usage} elapsed={turn.elapsed} />}
      </div>
    </div>
  );
}
