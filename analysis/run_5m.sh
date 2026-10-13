#!/bin/sh
# Re-run the whole scorecard on the 5-minute exports (13 tickers, May-Oct 2026).
# 1) put D_<TK>.pkl built from the 5m csv files (time, OHLC, VWAP, Volume, Prior-day high/low, date) in RUN/work
# 2) copy analysis/*.py to RUN/analysis, set TK to the 13 tickers (add GOOGL to LIQ), drop the CC-Multi + Pin
#    sections from scorecard.py (no 5m trade lists), then run in RUN: tga_stop.py, scorecard.py, scorecard2.py, scorecard3.py
# Results: RUN/work/SCORE3.pkl (copied to work/SCORE5.pkl). Halves for 5m: before / after 2026-07-27.
