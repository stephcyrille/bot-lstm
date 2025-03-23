//+------------------------------------------------------------------+
//|                                                 SCMA_LSTM_EA.mq5 |
//|                                                      SCMA Empire |
//|                                  https://www.stephanemebenga.com |
//+------------------------------------------------------------------+
#property copyright "SCMA Empire"
#property link      "https://www.stephanemebenga.com"
#property version   "1.00"
//+---------------------------------------------------------------------------------------------------------------+
//| Librairies importation                                                                                        |
//+---------------------------------------------------------------------------------------------------------------+
#include  <Trade\Trade.mqh>                                                // Internal module in charge of trades

//+---------------------------------------------------------------------------------------------------------------+
//| Users Input variables                                                                                         |
//+---------------------------------------------------------------------------------------------------------------+
input int                  AtrPeriod         = 14;                         // The ATR indicator period
input ENUM_TIMEFRAMES      BotTimeFrame      = PERIOD_H1;                  // The Selected timeframe in the program
input double               TriggerFactor     = 2.5;                        // The factor in open close difference    
input double               Lots              = 0.2;                        // The index lot size 
input int                  TpPoints          = 1000;                       // Take profit number of pips
input int                  SlPoints          = 500;                        // Stop-lost number of pips
input string               Commentary        = "ATR Breakout";             // Commentary on order
input int                  TslTriggerPoints  = 200;                          
input int                  TslPoints         = 100;
input ulong                Magic             = 20250311;                   // The Bot unique identifier on running
input int                  RsiPeriod         = 14;                         // The RSI Indicator period size

//+---------------------------------------------------------------------------------------------------------------+
//| Indicators handlers definition                                                                                |
//+---------------------------------------------------------------------------------------------------------------+
int handleAtr;
int handleRsi;

//+---------------------------------------------------------------------------------------------------------------+
//| Others variables                                                                                              |
//+---------------------------------------------------------------------------------------------------------------+
CTrade trade;                                                              // Trade Object instance
int barsTotals;                                                            // Symbol total bars 
double predictedNextClosePrice;                                            // Next close price by the LSTM model

//+---------------------------------------------------------------------------------------------------------------+
//| Expert initialization function                                                                                |
//+---------------------------------------------------------------------------------------------------------------+
int OnInit(){
   Print("Initializing SCMA LSTM EA...");
   trade.SetExpertMagicNumber(Magic);
   
   handleAtr = iATR(_Symbol, BotTimeFrame, AtrPeriod);
   handleRsi = iRSI(Symbol(), BotTimeFrame, RsiPeriod, PRICE_CLOSE);
   if(handleAtr == INVALID_HANDLE || handleRsi == INVALID_HANDLE){
      printf("Error on creating indicators");
      return(INIT_FAILED);
  }
  
   barsTotals = iBars(NULL, BotTimeFrame);
   return(INIT_SUCCEEDED);
}
  
//+---------------------------------------------------------------------------------------------------------------+
//| Expert deinitialization function                                                                              |
//+---------------------------------------------------------------------------------------------------------------+
void OnDeinit(const int reason){

}
 
//+---------------------------------------------------------------------------------------------------------------+
//| Expert tick function                                                                                          |
//+---------------------------------------------------------------------------------------------------------------+
void OnTick(){
   for(int i = 0; i < PositionsTotal(); i++){
      ulong posTicket = PositionGetTicket(i);
        
      if(PositionGetSymbol(POSITION_SYMBOL) != _Symbol) continue;
      if(PositionGetInteger(POSITION_MAGIC) != Magic) continue;
      
      double bid           = SymbolInfoDouble(_Symbol, SYMBOL_BID);
      double ask           = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
      
      double posPriceOpen  = PositionGetDouble(POSITION_PRICE_OPEN);
      double posSl         = PositionGetDouble(POSITION_SL);
      double posTp         = PositionGetDouble(POSITION_TP);
      
      if(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_BUY){
         if(bid > posPriceOpen + TslTriggerPoints * _Point){
            double sl = bid - TslPoints * _Point;
            sl = NormalizeDouble(sl, _Digits);
            
            if(sl > posSl){
               trade.PositionModify(posTicket, sl, posTp);
            }
         }
      } else  if(PositionGetInteger(POSITION_TYPE) == POSITION_TYPE_SELL){
         if(ask < posPriceOpen - TslTriggerPoints * _Point){
            double sl = ask + TpPoints * _Point;
            sl = NormalizeDouble(sl, _Digits);
            
            if(sl < posSl || posSl == 0){
               trade.PositionModify(posTicket, sl, posTp);
            }
         }
      }
   }

   int bars = iBars(NULL, BotTimeFrame);
   if(barsTotals != bars){
      barsTotals = bars;
  
      double   atr[];
      CopyBuffer(handleAtr, 0, 1, 1, atr);
      
      double   open = iOpen(NULL, BotTimeFrame, 1);
      double   close = iClose(NULL, BotTimeFrame, 1);
      
      if(open < close && close - open > atr[0] * TriggerFactor){
         Print("Buy Signal!");
         executeBuy();
      } else if(open > close && open - close > atr[0] * TriggerFactor){
         Print("Sell Signal!");
         executeSell();
      }
   }
}


///////////////////////////////////////////////////////////////////////////////
//                     DEFINE MY PERSONAL FUNCTIONS                          //
///////////////////////////////////////////////////////////////////////////////
//+---------------------------------------------------------------------------------------------------------------+
//| Execute buy action function                                      |
//+---------------------------------------------------------------------------------------------------------------+
void executeBuy(){
   double entryPrice = SymbolInfoDouble(NULL, SYMBOL_ASK);
   entryPrice = NormalizeDouble(entryPrice, _Digits);
   
   double tp = entryPrice + TpPoints * _Point;
   tp = NormalizeDouble(tp, _Digits);
   
   double sl = entryPrice - SlPoints * _Point;
   sl = NormalizeDouble(sl, _Digits);
   
   trade.Buy(Lots, NULL, entryPrice, sl, tp, Commentary);
}

//+---------------------------------------------------------------------------------------------------------------+
//| Execute sell action function                                     |
//+---------------------------------------------------------------------------------------------------------------+
void executeSell(){
   double entryPrice = SymbolInfoDouble(NULL, SYMBOL_BID);
   entryPrice = NormalizeDouble(entryPrice, _Digits);
   
   double tp = entryPrice - TpPoints * _Point;
   tp = NormalizeDouble(tp, _Digits);
   
   double sl = entryPrice + SlPoints * _Point;
   sl = NormalizeDouble(sl, _Digits);
   
   trade.Sell(Lots, NULL, entryPrice, sl, tp, Commentary);
}