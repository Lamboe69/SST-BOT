# Trade Execution Rules - Candle Close Confirmation

## Key Rule: WAIT FOR CANDLE CLOSE

The bot now follows strict candle close confirmation:

### ✅ CORRECT Execution:
1. **Price breaks swing high/low during candle** → WAIT
2. **Candle CLOSES above/below swing level** → EXECUTE TRADE
3. **Use closing price as entry** → PLACE ORDER

### ❌ WRONG Execution:
- Taking trade while candle is still forming
- Using intracandle price movements
- Not waiting for 5-minute candle to close

## Trading Logic:

### CHOCH Signals:
- **SELL**: Wait for candle to CLOSE below swing low after PDH touch
- **BUY**: Wait for candle to CLOSE above swing high after PDL touch

### BOS Signals:
- **BUY**: Wait for candle to CLOSE above swing high after PDH break
- **SELL**: Wait for candle to CLOSE below swing low after PDL break

## Timing:
- Bot analyzes every 5 minutes (after each candle closes)
- Uses the CLOSING PRICE of the completed candle
- No intracandle execution

This ensures trades are only taken on confirmed breaks, not false breakouts.