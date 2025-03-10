import keras
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify
from utils.agent_dataset import AgentTreadingDataset

model:keras.Sequential = keras.models.load_model('./models/test/best_model_EURUSD.keras')
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
    df.to_csv("market_data.csv")

    # delete the last row
    df = df[:-1]
    dataset = AgentTreadingDataset(df)
    dataset.prepare_data()

    last_prev_lines:np.ndarray = dataset.feature_sequence[-1]
    prev_seq = last_prev_lines.reshape(1, dataset.SEQUENCE_LENGTH, last_prev_lines.shape[1])
    predicted_price_scaled = model.predict(prev_seq)
    predicted_price = dataset.target_scaler.inverse_transform(predicted_price_scaled)

    return jsonify({"prediction": float(predicted_price)})  # Retourner la réponse en JSON

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    