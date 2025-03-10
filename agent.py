import json
import keras
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify

model = keras.models.load_model('./models/test/best_model_FRA40.keras')
app = Flask(__name__)


@app.route('/predict', methods=['POST'])
def predict():
    data = request.json  # Récupérer les données JSON
    # inputs = np.array(data["inputs"]).reshape(1, -1)  # Transformer en tableau numpy
    # prediction = model.predict(inputs)[0][0]  # Faire la prédiction

    # Create DataFrame from dictionary
    df = pd.json_normalize(data['data'])
    # print(json_result)

    # Sauvegarde en CSV
    df.to_csv("market_data.csv", index=False)

    return jsonify({"prediction": 1})  # Retourner la réponse en JSON

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
    