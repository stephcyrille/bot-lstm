import keras
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify
from tensorflow.keras.optimizers import Adam
from utils.processing.v02.dataset import TradingDataset

try:
    model:keras.Sequential = keras.models.load_model('./models/test/best_model_EURUSD_candle_latest.keras')
except Exception as e:
    print(f"Error loading model: {e}")
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
    
    X, y = dataset.feature_sequence, dataset.target_sequence
    X, y = np.array(X), np.array(y)

    for layer in model.layers[:-2]:  # keep last 2 layers trainable
        layer.trainable = False

    # Recompile the model
    model.compile(optimizer=Adam(learning_rate=0.000001, weight_decay = 1e-5), loss='mse')
    model.fit(X, y, epochs=10, batch_size=16)

    # Save the model
    model.save('./models/test/best_model_EURUSD_candle_latest.keras')

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
    