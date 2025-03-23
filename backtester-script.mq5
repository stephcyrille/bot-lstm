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
#include <JAson.mqh>

//+---------------------------------------------------------------------------------------------------------------+
//| Inputs variables                                                                                              |
//+---------------------------------------------------------------------------------------------------------------+
input group                "Global Parameters"
input int                  SessionStart   = 8;                             // Start Hour (CET)
input int                  SessionEnd     = 17;                            // End Hour (CET)
input ENUM_TIMEFRAMES      BotTimeFrame      = PERIOD_H1;                  // The Selected timeframe in the program
input ulong                Magic             = 20250310;                   // The Bot unique identifier on running
input group                "Trading param"    
input double               RiskPercent       = 1.0;                        // Risk % per trade
input double               Lots              = 0.2;                        // The trade lot size 
input double               ATR_Multiplier    = 1.5;                        // StopLoss Multiplier
input string               Commentary        = "Take a short";             // Commentary on order
input group                "Indicators parameters"
input int                  EMA_PeriodFast    = 20;                         // EMA Fast Period
input int                  EMA_PeriodSlow    = 50;                         // EMA Slow Period
input int                  RSI_Period        = 14;                         // RSI Period
input int                  BB_Period         = 20;                         // Bollinger Bands Period
input double               BB_Deviation      = 2.0;                        // Bollinger Deviation
input int                  ATR_Period        = 14;                         // ATR Period
input int                  MACD_Fast_Period  = 12;                         // MACD Fast Period
input int                  MACD_Slow_Period  = 26;                         // MASCD Slow Period
input int                  MACD_Sign_Period  = 9;                          // MACD Signal Period
input int                  MinATR            = 10;                         // Min ATR (pips) to trade

//+---------------------------------------------------------------------------------------------------------------+
//| Indicators handlers definition                                                                                |
//+---------------------------------------------------------------------------------------------------------------+
int emaHandleFast, emaHandleSlow, rsiHandle, bbHandle, atrHandle, macdHadle;
double minATR;

//+---------------------------------------------------------------------------------------------------------------+
//| Others variables                                                                                              |
//+---------------------------------------------------------------------------------------------------------------+
CTrade trade;                                                              // Trade Object instance
double predictedNextClosePrice;                                            // Next close price by the LSTM model

//+---------------------------------------------------------------------------------------------------------------+
//| Variables pour les prédictions                                                                                |
//+---------------------------------------------------------------------------------------------------------------+
datetime predictionTime[];  // Timestamps des prédictions
double predictionOpen[];    // Prix d'ouverture prédits
double predictionHigh[];    // Prix le plus haut prédit
double predictionLow[];     // Prix le plus bas prédit
double predictionClose[];   // Prix de clôture prédit

#property tester_file "backtest_EURUSD_CANDLE.csv";
//+---------------------------------------------------------------------------------------------------------------+
//| Expert initialization function                                                                                |
//+---------------------------------------------------------------------------------------------------------------+
int OnInit(){
   Print("Initializing SCMA LSTM EA...");   
   trade.SetExpertMagicNumber(Magic);
   string fileName = "backtest_EURUSD_CANDLE.csv";
   
   //Print("File path: ", TerminalInfoString(TERMINAL_DATA_PATH) + "\\MQL5\\Files\\");
   
   // Charger les prédictions
   if (!readPredictions(fileName)) {
      Print("Erreur : Impossible de charger les prédictions.");
      return INIT_FAILED;
   }
   Print("File well loaded!!!");
   
   // Create indicator handles
   emaHandleFast     = iMA(_Symbol, BotTimeFrame, EMA_PeriodFast, 0, MODE_EMA, PRICE_CLOSE);
   emaHandleSlow     = iMA(_Symbol, BotTimeFrame, EMA_PeriodSlow, 0, MODE_EMA, PRICE_CLOSE);
   rsiHandle         = iRSI(_Symbol, BotTimeFrame, RSI_Period, PRICE_CLOSE);
   bbHandle          = iBands(_Symbol, BotTimeFrame, BB_Period, 0, BB_Deviation, PRICE_CLOSE);
   atrHandle         = iATR(_Symbol, BotTimeFrame, ATR_Period);
   macdHadle         = iMACD(_Symbol, BotTimeFrame, MACD_Fast_Period, MACD_Slow_Period, MACD_Sign_Period, PRICE_CLOSE);
   minATR            = MinATR * _Point * 10;       // Convert pips to points
   
   if(emaHandleFast == INVALID_HANDLE || emaHandleSlow == INVALID_HANDLE || 
      rsiHandle == INVALID_HANDLE || bbHandle == INVALID_HANDLE || 
      atrHandle == INVALID_HANDLE || macdHadle == INVALID_HANDLE){
      printf("Error on creating indicators");
      return(INIT_FAILED);
   }
  
   //barsTotals = iBars(NULL, BotTimeFrame);
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

   // Array to hold the extracted values
   /*double values[];
   if(onMakePrediction(BotTimeFrame, 200, "http://127.0.0.1:5000/predict", values)){
      // Print the values to verify
      Print("CLOSE: ", values[2]);
      Print("DATETIME: ", values[3]);
      Print("HIGH: ", values[0]);
      Print("LOW: ", values[1]);
   } else {
      Print("Failed to deserialize JSON or extract values.");
   }*/
   
   // Récupérer l'heure serveur pour les logs
   MqlDateTime serverTime;
   TimeToStruct(TimeCurrent(), serverTime);
   
   // Check for new bar
   static datetime lastBar;
   datetime currentBar = iTime(_Symbol, BotTimeFrame, 0);
   if(lastBar == currentBar) return;
   lastBar = currentBar;

   // Check trading session (CET time)
   if(!isTradingSession()) return;
   
   // Get indicator values
   double emaFast    = getIndicatorValue(emaHandleFast, 0);
   double emaSlow    = getIndicatorValue(emaHandleSlow, 0);
   double rsi        = getIndicatorValue(rsiHandle, 0);
   double atr        = getIndicatorValue(atrHandle, 0) / _Point;
   double bbUpper    = getIndicatorValue(bbHandle, 1, 0); // Upper band
   double bbLower    = getIndicatorValue(bbHandle, 2, 0); // Lower band
   double bbBase     = getIndicatorValue(bbHandle, 0, 0); // Base band
   double close      = iClose(_Symbol, BotTimeFrame, 0);
   double macdVal    = MathAbs(getIndicatorValue(macdHadle, 0, 0)); 
   double macdSignal = MathAbs(getIndicatorValue(macdHadle, 1, 0));
   
   // Check volatility filter
   if(atr < MinATR) {
      Print("ATR filtré : ", atr, " pips");
      return;
   }

   // Calculate risk management
   double stopLoss = atr * ATR_Multiplier * _Point;
   double takeProfit = stopLoss * 2;
   double lotSize = calculateLotSize(stopLoss);

   // Check existing positions
   if(PositionsTotal() > 0) return;
   
   // Find the prediction for the current bar
   int predictionIndex = -1;
   for (int i = 0; i < ArraySize(predictionTime); i++) {
      if (predictionTime[i] == currentBar) {
         predictionIndex = i;
         break;
      }
   }

   if (predictionIndex == -1) {
      Print("No prediction found for the current bar.");
      return;
   }

   // Use the predictions
   double predictedHigh = predictionHigh[predictionIndex];
   double predictedLow = predictionLow[predictionIndex];
   double predictedClose = predictionClose[predictionIndex];         
   
   // Generate signals                    
   bool buySignal = (emaSlow > emaFast) && 
                    (close < emaFast) && 
                    (atr >= 0.0015) &&
                    (close < bbLower) &&
                    (macdVal <= macdSignal) &&
                    (rsi <= 35);

   bool sellSignal = (emaFast > emaSlow) && 
                     (close > emaFast) && 
                     (rsi > 70 && rsi < 75) && 
                     (atr >= 0.00170) &&
                     (close > bbUpper) &&
                     (macdVal >= macdSignal);                      
   
   // Ajuster les signaux en fonction des prédictions
   if(buySignal && predictedClose > close){
      //takeProfit = MathAbs(predictedHigh - close);
      //stopLoss = close - predictedLow;
      executeBuy(lotSize, stopLoss, takeProfit, "Buy Trigger");
   }
   else if (sellSignal && predictedClose < close) {
      takeProfit = MathAbs(close - predictedLow);
      stopLoss = MathAbs(predictedHigh - close);
      
      // Loggin debug
      Print(
         "[DEBUG] SellSignal: ", sellSignal, 
         "\nCLOSE: ", close, " | EMAFast: ", emaFast, " | BB Lower: ", bbLower,
         //" | EMASlow: ", emaSlow, 
         "\nBB Base: ", bbBase, " | BB Upper: ", bbUpper, " | RSI: ", rsi, 
         "\nATR: ", atr, " | Hour: ", serverTime.hour);
      
      Print("PREDICTED HIGH: ", predictedHigh,
         "\nPREDICTED LOW: ", predictedLow,
         "\nPREDICTED CLOSE: ", predictedClose);      
      
      executeSell(lotSize, stopLoss, takeProfit, "Sell Trigger");
   } 
   // Run Orders
   //if(buySignal) executeBuy(lotSize, stopLoss, takeProfit, "Buy Trigger");
   //if(sellSignal) executeSell(lotSize, stopLoss, takeProfit, Commentary);
}


///////////////////////////////////////////////////////////////////////////////
//                     DEFINE MY PERSONAL FUNCTIONS                          //
///////////////////////////////////////////////////////////////////////////////
//+---------------------------------------------------------------------------------------------------------------+
//| Function that calculate the lot size for each trading                                                         |
//+---------------------------------------------------------------------------------------------------------------+
double calculateLotSize(double slPoints){
   double tickValue = SymbolInfoDouble(_Symbol, SYMBOL_TRADE_TICK_VALUE);
   double riskAmount = AccountInfoDouble(ACCOUNT_BALANCE) * RiskPercent / 100;
   double pipSize = SymbolInfoDouble(_Symbol, SYMBOL_POINT) * 10;
   double lotSize = riskAmount / ((slPoints/pipSize) * tickValue);
   
   // PrintFormat("Lot Calculé: %f | Risque: %f$ | Stop-Loss: %f pips | TickVal %f | Points %f", lotSize, riskAmount, slPoints, tickValue, _Point);
   return NormalizeDouble(lotSize, 2);
}
//+---------------------------------------------------------------------------------------------------------------+
//| Function that checks if we are on market time period                                                          |
//+---------------------------------------------------------------------------------------------------------------+
bool isTradingSession(){
   MqlDateTime serverTime;
   TimeToStruct(TimeCurrent(), serverTime); // server time UTC
   int hour = serverTime.hour;
   // Convert CET (UTC+1) in UTC
   int cetStart = SessionStart - 1;
   int cetEnd = SessionEnd - 1;
   return (hour >= cetStart && hour < cetEnd);
}

//+---------------------------------------------------------------------------------------------------------------+
//| Get Indicator Buffer value function                                                                           |
//+---------------------------------------------------------------------------------------------------------------+
double getIndicatorValue(int handle, int buffer=0, int shift=0){
   double value[1];
   CopyBuffer(handle, buffer, shift, 1, value);
   return value[0];
}

//+---------------------------------------------------------------------------------------------------------------+
//| Execute buy action function                                                                                   |
//+---------------------------------------------------------------------------------------------------------------+
void executeBuy(double lots, double sl, double tp, string comment){
   double entryPrice = SymbolInfoDouble(_Symbol, SYMBOL_ASK);
   entryPrice = NormalizeDouble(entryPrice, _Digits);
   
   double takeProfit = entryPrice + tp;
   takeProfit = NormalizeDouble(takeProfit, _Digits);
   
   double stopLoss = entryPrice - sl;
   stopLoss = NormalizeDouble(stopLoss, _Digits);
   
   trade.Buy(lots, _Symbol, entryPrice, stopLoss, takeProfit, comment);
}

//+---------------------------------------------------------------------------------------------------------------+
//| Execute sell action function                                                                                  |
//+---------------------------------------------------------------------------------------------------------------+
void executeSell(double lots, double sl, double tp, string comment){
   double entryPrice = SymbolInfoDouble(_Symbol, SYMBOL_BID);
   entryPrice = NormalizeDouble(entryPrice, _Digits);
   
   double takeProfit = entryPrice - tp;
   takeProfit = NormalizeDouble(takeProfit, _Digits);
   
   double stopLoss = entryPrice + sl;
   stopLoss = NormalizeDouble(stopLoss, _Digits);
   
   trade.Sell(lots, _Symbol, entryPrice, stopLoss, takeProfit, comment);
}
bool onMakePrediction(ENUM_TIMEFRAMES timeFrame, int bars, string url, double &values[]){
   double open[], high[], low[], close[];
   long volume[];
   datetime time[];
   // Create a CJAVal object to parse the JSON
   CJAVal parser;

   // Load data for the last 100 candles
   if (CopyOpen(Symbol(), timeFrame, 0, bars, open) <= 0 || 
       CopyHigh(Symbol(), timeFrame, 0, bars, high) <= 0 || 
       CopyLow(Symbol(), timeFrame, 0, bars, low) <= 0 || 
       CopyClose(Symbol(), timeFrame, 0, bars, close) <= 0 || 
       CopyTickVolume(Symbol(), timeFrame, 0, bars, volume) <= 0 ||
       CopyTime(Symbol(), timeFrame, 0, bars, time) <= 0)
   {
      Print("Error retrieving data");
      return false;
   }
   
   // --- Initialization of indicators ---
   double ema[], rsi[], macd[], signal[], upper_band[], lower_band[], percent_b[], atr[];
   ArrayResize(upper_band, bars);
   ArrayResize(lower_band, bars);
   ArrayResize(percent_b, bars);
   

   int emaPeriod = 14;
   int rsiPeriod = 14;
   int macdFast = 12, macdSlow = 26, macdSignal = 9;
   int bollingerPeriod = 20;
   int bollingerDeviation = 2;
   int atrPeriod = 14;

   // Creation of indicator handles
   int emaHandle = iMA(Symbol(), timeFrame, emaPeriod, 0, MODE_EMA, PRICE_CLOSE);
   int rsiHandle = iRSI(Symbol(), timeFrame, rsiPeriod, PRICE_CLOSE);
   int macdHandle = iMACD(Symbol(), timeFrame, macdFast, macdSlow, macdSignal, PRICE_CLOSE);
   int bandsHandle = iBands(Symbol(), timeFrame, bollingerPeriod, 0, bollingerDeviation, PRICE_CLOSE);
   int atrHandle = iATR(Symbol(), timeFrame, atrPeriod);

   // Check handles
   if (emaHandle == INVALID_HANDLE || rsiHandle == INVALID_HANDLE || macdHandle == INVALID_HANDLE ||
       bandsHandle == INVALID_HANDLE || atrHandle == INVALID_HANDLE)
   {
      Print("Error creating indicators");
      return false;
   }

   // Retrieve indicator values
   if (CopyBuffer(emaHandle, 0, 0, bars, ema) <= 0 ||
       CopyBuffer(rsiHandle, 0, 0, bars, rsi) <= 0 ||
       CopyBuffer(macdHandle, 0, 0, bars, macd) <= 0 ||
       CopyBuffer(macdHandle, 1, 0, bars, signal) <= 0 || // Signal line
       CopyBuffer(bandsHandle, 0, 0, bars, upper_band) <= 0 ||
       CopyBuffer(bandsHandle, 1, 0, bars, lower_band) <= 0 || 
       CopyBuffer(atrHandle, 0, 0, bars, atr) <= 0)
   {
      Print("Error retrieving indicators");
      return false;
   }

   // Calculate %B (Bollinger Percent B)
   ArrayResize(percent_b, bars);
   for (int i = 0; i < bars; i++){
      if (upper_band[i] != lower_band[i]){  // Ensure bands are not equal
         percent_b[i] = (close[i] - lower_band[i]) / (upper_band[i] - lower_band[i]);
      } else{
         percent_b[i] = 0;  
      }
   }
   
   // Build the JSON payload with data for the last 100 candles
   string json_payload = "{\"data\":[";

   // Add data in the desired format
   for (int i = 0; i < bars; i++){
      json_payload += "{";
      json_payload += "\"DATETIME\":\"" + TimeToString(time[i], TIME_DATE | TIME_MINUTES | TIME_SECONDS) + "\",";
      json_payload += "\"OPEN\":" + DoubleToString(open[i], 5) + ",";
      json_payload += "\"HIGH\":" + DoubleToString(high[i], 5) + ",";
      json_payload += "\"LOW\":" + DoubleToString(low[i], 5) + ",";
      json_payload += "\"CLOSE\":" + DoubleToString(close[i], 5) + ",";
      json_payload += "\"VOLUME\":" + DoubleToString(volume[i], 0) + ",";
      json_payload += "\"EMA\":" + DoubleToString(ema[i], 5) + ",";
      json_payload += "\"RSI\":" + DoubleToString(rsi[i], 2) + ",";
      json_payload += "\"MACD\":" + DoubleToString(macd[i], 5) + ",";
      json_payload += "\"SIGNAL_LINE\":" + DoubleToString(signal[i], 5) + ",";
      json_payload += "\"UPPER_BAND\":" + DoubleToString(upper_band[i], 5) + ",";
      json_payload += "\"LOWER_BAND\":" + DoubleToString(lower_band[i], 5) + ",";
      
      if (!MathIsValidNumber(percent_b[i]) || percent_b[i] > DBL_MAX || percent_b[i] < -DBL_MAX)
         json_payload += "\"BOLLINGER_PERCENT_B\": null,";
      else
         json_payload += "\"BOLLINGER_PERCENT_B\":" + DoubleToString(percent_b[i], 5) + ",";
      
      json_payload += "\"ATR\":" + DoubleToString(atr[i], 5);
      json_payload += "}";
 
      if (i < bars - 1)
         json_payload += ",";  // Add a comma between objects
   }

   json_payload += "]}";
   
   // Release indicator handles
   IndicatorRelease(emaHandle);
   IndicatorRelease(rsiHandle);
   IndicatorRelease(macdHandle);
   IndicatorRelease(bandsHandle);
   IndicatorRelease(atrHandle);

   // Request configuration
   string Method = "POST";
   string Headers = "Content-Type: application/json\r\n";
   int Timeout = 5000;

   // Convert to `char[]` (not `uchar[]`)
   char Data[];
   StringToCharArray(json_payload, Data);

   // Adjust the array size
   int data_size = StringLen(json_payload);
   ArrayResize(Data, data_size);

   // Define variables for the response
   char Result[];
   string ResponseHeaders;

   // Execute the POST request
   ResetLastError();
   int request_code = WebRequest(Method, url, Headers, Timeout, Data, Result, ResponseHeaders);

   // Check the request
   if (request_code == -1){
      PrintFormat("WebRequest error (%d) : %d", request_code, GetLastError());
      return false;
   }

   // Check received data
   if (ArraySize(Result) > 0){
       //PrintFormat("Received data: %d bytes", ArraySize(Result));
       // Deserialize the JSON string
       if (!parser.Deserialize(Result))
       {
           Print("Failed to parse JSON");
           return false;
       }
       // Resize the array to hold 4 values: HIGH, LOW, CLOSE, DATEIME
       ArrayResize(values, 4);
       // Extract values from the JSON object
       values[0] = parser["HIGH"].ToDbl();       // HIGH as double
       values[1] = parser["LOW"].ToDbl();        // LOW as double
       values[2] = parser["CLOSE"].ToDbl();      // CLOSE as double
       values[3] = (double)StringToTime(parser["DATETIME"].ToStr()); // DATETIME as datetime (converted to double)
       
       return true;
   }
   return false;
}

//+---------------------------------------------------------------------------------------------------------------+
//| Fonction pour lire les prédictions depuis un fichier CSV                                                      |
//+---------------------------------------------------------------------------------------------------------------+
bool readPredictions(string filename) {
   int handle = FileOpen(filename, FILE_READ | FILE_BIN);
   if (handle == INVALID_HANDLE) {
      Print("Erreur : Impossible d'ouvrir le fichier ", filename);
      return false;
   }
   
   // Lire tout le contenu du fichier dans un tableau de bytes
   uchar data[];
   FileReadArray(handle, data);
   FileClose(handle);
   
   // Convertir les bytes en une chaîne UTF-8
   string content = CharArrayToString(data);
   
   // Diviser le contenu en lignes
   string lines[];
   StringSplit(content, '\n', lines);
   
   
   // Traiter chaque ligne
   int row = 0;
   for (int i = 0; i < ArraySize(lines); i++) {
      string line = lines[i];
      line = StringTrim(line); // Supprimer les espaces inutiles

      // Ignorer les lignes vides ou les en-têtes
      if (StringLen(line) == 0 || StringFind(line, "Timestamp") != -1) {
         continue;
      }

      // Diviser la ligne en colonnes
      string columns[];
      StringSplit(line, ',', columns);
      Print("==============", line);

      // Vérifier que la ligne contient 4 colonnes
      if (ArraySize(columns) == 7) {
      // Redimensionner les tableaux
        ArrayResize(predictionTime, row + 1);
        ArrayResize(predictionHigh, row + 1);
        ArrayResize(predictionLow, row + 1);
        ArrayResize(predictionClose, row + 1);
        
        predictionTime[row] = StringToTime(columns[0]);
        predictionHigh[row] = StringToDouble(columns[4]);
        predictionLow[row] = StringToDouble(columns[5]);
        predictionClose[row] = StringToDouble(columns[6]);
        
        row++;
         
      } else {
         Print("Erreur : La ligne ne contient pas 4 colonnes : ", line);
      }
   }

   if (row == 0) {
      Print("Erreur : Aucune donnée valide trouvée dans le fichier.");
      return false;
   }

   FileClose(handle);
   return true;
}

string StringTrim(string str) {
   // Supprimer les espaces au début de la chaîne
   while (StringGetCharacter(str, 0) == ' ') {
      str = StringSubstr(str, 1);
   }

   // Supprimer les espaces à la fin de la chaîne
   while (StringGetCharacter(str, StringLen(str) - 1) == ' ') {
      str = StringSubstr(str, 0, StringLen(str) - 1);
   }

   return str;
}