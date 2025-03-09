from statsmodels.tsa.stattools import adfuller
import pandas as pd


def adf_test(series: pd.Series, verbose:bool=False) -> bool:
    """
    Test de Dickey-Fuller
    :param series: Series -> série temporelle à tester
    :param verbose: bool -> afficher les commentaires
    :return: bool -> True si la série est stationnaire, False sinon
    """
    # Effectuer le test ADF
    result = adfuller(series)

    # Afficher les résultats
    if verbose:
        print('Augmented Dickey-Fuller Test:')
        print('ADF Statistic:', result[0])
        print('p-value:', result[1])
    for key, value in result[4].items():
        if verbose:
            print('Critical Values:')
            print(f'   {key}, {value}')

    # Interprétation des résultats
    if result[1] < 0.05:
        if verbose:
            print("La série est stationnaire")
        return True
    else:
        if verbose:
            print("La série n'est pas stationnaire")
        return False