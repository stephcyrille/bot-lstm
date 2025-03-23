import keras
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify
from utils.processing.v02.dataset import TradingDataset

model:keras.Sequential = keras.models.load_model('./models/test/best_model_EURUSD_candle.keras')
app = Flask(__name__)


@app.route('/predict', methods=['POST'])
def predict():
    data = request.json  # Récupérer les données JSON

    # Create DataFrame from dictionary
    df = pd.json_normalize(data['data'])
    df['DATETIME'] = pd.to_datetime(df['DATETIME'])
    df = df.set_index('DATETIME')
    df = df.sort_index()
    # Sauvegarde en CSV
    # df.to_csv("pred_data.csv")

    # delete the last row
    dataset = TradingDataset(df)
    dataset.prepare_data()

    last_prev_lines:np.ndarray = dataset.feature_sequence[-1]
    prev_seq = last_prev_lines.reshape(1, dataset.SEQUENCE_LENGTH, last_prev_lines.shape[1])
    predicted_price_scaled = model.predict(prev_seq)
    predicted_price = dataset.target_scaler.inverse_transform(predicted_price_scaled)

    # create a route by timeframe, this route will be for hourly prediction
    timeframe = df.index[-1] + pd.Timedelta(hours=1)


    res_data = {
        'DATETIME': timeframe.timestamp(),
        "HIGH": float(predicted_price[0][0]),
        "LOW": float(predicted_price[0][1]),
        "CLOSE": float(predicted_price[0][2])
    }

    # Create a timeframe from the system's current date
    current_time = pd.Timestamp.now()
    current_time.timestamp
    
    return jsonify(res_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    