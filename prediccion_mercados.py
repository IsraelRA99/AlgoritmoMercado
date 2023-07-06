# -*- coding: utf-8 -*-
"""Prediccion_Mercados.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Y-yb69tMB8Qcw0mP3cjbqagift1z-66k

### **Librerías Principales para el Funcionamiento del Algoritmo**
"""

pip install yfinance

pip install yahoo-finance

pip install yahoofinancials

# Commented out IPython magic to ensure Python compatibility.
# Manipulación y tratamiento de Datos
import numpy as np
import pandas as pd

# Visualización de datos
import plotly.express as px
import matplotlib.pyplot as plt
# %matplotlib inline
plt.style.use('ggplot')

# Descargar datos de yahoo
import yfinance as yf
from yahoofinancials import YahooFinancials

# Métrica de Evaluación
from sklearn.metrics import mean_squared_error
from statsmodels.tools.eval_measures import rmse
from sklearn import metrics

# No presentar advertencias
import warnings
warnings.filterwarnings("ignore")

"""### **Extracción de los Datos Históricos del Activo de Renta Variable de su Preferencia**

"""

#Se pide el token del activo de renta variable
while True:
    try:
        nombre_token = input("Ingrese el valor del token: ")
        token = yf.Ticker(nombre_token)
        #Extrae el nombre del token elegido y se muestra para validar que no se haya equivocado
        token.info["longName"]
        break
    except:
        #Si el valor del token no es válido, te vuelve a pedir un valor hasta que sea válido
        print("El token no es válido, ingrese de nuevo un token que se encuentre en Yahoo Finance...\n")

#Dependiendo del token que se ha escogido, se extrae de la base de datos de Yahoo Finance los datos históricos de dicho token
df = yf.download(nombre_token,
                      #El periodo viene a ser "max" para que se extraigan los precios desde el inicio de la apertura del activo de renta variable
                      period = "max",
                      progress = False)
df

"""### **Tratamiento de los Datos Históricos**"""

#Eliminamos los datos que no vamos a usar en el análisis de nuestro algoritmo y renombramos la variable "Close"
df["Precio Real"] = df["Close"]
df = df.drop(["Open"], axis=1)
df = df.drop(["High"], axis=1)
df = df.drop(["Low"], axis=1)
df = df.drop(["Adj Close"], axis=1)
df = df.drop(["Volume"], axis=1)
df = df.drop(["Close"], axis=1)
df

#En este punto, rellenamos los valores faLtantes que hay en el histórico del activo por temas de que esos días en activo no tuvo ninguna operación
#Le decimos que se tiene una frecuencia diaria y que los valores que son vacíos se rellenen con el día anterior de un valor vacío, dando a entender que el precio no se movió
df = df.asfreq(freq = "D", method = "ffill")
df

#Se grafica los precios del activo seleccionado con sus respectivas fechas, a lo largo de su apertura
titulo = "Gráfico de precios del " + token.info["longName"] + " a lo largo de su apertura"
fig = px.line(df, x = df.index, y = df["Precio Real"], template = "plotly_dark", title = titulo)
fig.show()

"""### **Entrenamiento de los Datos Históricos**"""

#En esta parte, definimos los datos de entrenamiento y los datos de testeo (80% para el entrenamiento y 20% para el testeo)
train_data = df[:round(len(df) * 0.8)]
test_data = df[round(len(df) * 0.8):]
#En esta parte mostramos el total de datos que tiene cada variable y el total de datos que hay en total
train_data.shape, test_data.shape, df.shape

#Utilizamos la librería del skLearn para poder escalar los valores de entrenamiento y testeo
from sklearn.preprocessing import MinMaxScaler
scaler = MinMaxScaler()

#Normalizamos los valores de entrenamiento y testeo para que el entrenamiento de éste sea óptimo
scaler.fit(train_data)
train_data_escalado = scaler.transform(train_data)
test_data_escalado = scaler.transform(test_data)
test_data_escalado

#Realizamos una agrupación de bloques para el lado del entrenamiento, quiere decir que se agrupará de time_step en time_step para que el siguiente dato sea la predicción
#Se tomará un dato del entrenamiento y su siguiente valor será una "Predicción"
time_step = 1
X_train = []
Y_train = []
#total es el total de datos de entrenamiento
total = len(train_data_escalado)

for i in range(time_step, total):
    # X: Bloques agrupados en time_step
    X_train.append(train_data_escalado[i - time_step:i, 0])
    # Y: el siguiente dato
    Y_train.append(train_data_escalado[i, 0])
X_train, Y_train = np.array(X_train), np.array(Y_train)

#En la matriz del X_train agruparemos los datos que se entrenan con la "predicción" del siguiente precio usando reshape
X_train = np.reshape(X_train, (X_train.shape[0], X_train.shape[1], 1))

#En esta parte, gracias a la librería keras, armamos la cantidad de neuronas que tendrá nuestro modelo, qué activación tendrá y cuántos valores mostrará
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM

#lo que estamos diciendo acá es que el modelo será secuencial, tendrá 365 neuronas en el hiperparámetro "units" en la capa de entrada,
#que tendrá una activación "relu" que es la más conocida y usada y que tendrá una neurona de capa de salida
#Se le coloca 365 neuronas por la cantidad de días que tiene un año y que tenga mejor rendimiento
modelo_LSTM = Sequential()
modelo_LSTM.add(LSTM(units = 365, activation = "relu", input_shape = (X_train.shape[1], 1)))
modelo_LSTM.add(Dense(1))
#El optimizador será el modelo de "adam" que es mejor que el "rmsprop" y las pérdidas serán en base al "error cuadrático medio (MSE)"
#que es el más usado en los datos supervisados clasificados
modelo_LSTM.compile(optimizer = "adam", loss = "mse")

modelo_LSTM.summary()

#En la parte de entrenamiento del algoritmo, colocamos los valores separados y ponemos el dato principal para el rendimiento que es el batch_size
#Le colocamos que hará 100 iteraciones de entrenamiento en el hiperparámetro epochs, y el bacth_size es el número de muestras por actualización de degradado
#Una explicación sencilla de este hiperparámetro es que si no lo colocamos, predeterminadamente valdrá uno y analizará todos los datos totales del entrenamiento
#Esto produciría mucho ruido al momento del entrenamiento del modelo y que se demore mucho para entrenar
#En cambio, si colocamos el valor total de los datos del entrenamiento, no produciría ruido, pero a la vez se atascará el entrenamiento
#Entonces le ponemos un valor predeterminado o general para que el entrenamiento del modelo sea óptimo, que es 32
modelo_LSTM.fit(X_train, Y_train, epochs = 100, batch_size = 32)

#Mostramos los errores del entrenamiento del modelo LSTM, se coloca el inicio en 0, el final en 101 y que vaya en un rango de  5 en 5
perdida_LSTM = modelo_LSTM.history.history['loss']
plt.xticks(np.arange(start = 0, stop = 101, step = 5))
plt.plot(range(len(perdida_LSTM)),perdida_LSTM);

"""### **Predicción de los Precios Futuros del Activo Seleccionado**"""

#Agrupamos los datos de testeo como se hizo en los datos de entrenamiemto en base al valor del "time_step"
X_test = []
for i in range(time_step, len(test_data_escalado) + 1):
    X_test.append(test_data_escalado[i - time_step:i, 0])
X_test = np.array(X_test)
X_test = np.reshape(X_test, (X_test.shape[0], X_test.shape[1], 1))

#Predecimos los valores agrupados del testeo para que nos muestre el "siguiente valor"
prediccion = modelo_LSTM.predict(X_test)
#E invertimos la normalización o escalado para poder ver el futuro precio
prediccion = scaler.inverse_transform(prediccion)

#Predecimos los valores agrupados del testeo para que nos muestre el "siguiente valor"
#prediccion2 = modelo_LSTM.predict(X_test)
#Agrupamos los time_step primeros valores que no serán predecidos para la graficación
#prediccion = []
#for i in range (time_step):
#    prediccion.append(test_data_escalado[i, 0])
#for i in range (len(prediccion2)):
#    prediccion.append(prediccion2[i, 0])
#prediccion = np.array(prediccion)
#prediccion = np.reshape(prediccion, (prediccion.shape[0], 1))
#E invertimos la normalización o escalado para poder ver el futuro precio
#prediccion = scaler.inverse_transform(prediccion)

#Agrupamos los valores predecidos a los datos del testeo para compararlos
test_data['Predicciones_LSTM'] = prediccion
test_data

#Mostramos la gráfica total de los datos de testeo: El precio real del activo y el precio predecido
titulo = "Predicción del precio del " + token.info['longName'] + " con el Modelo LSTM"
ai = test_data[["Precio Real","Predicciones_LSTM"]]
fig = px.line(ai, x = test_data.index, y = ai.columns, title = titulo, template = "plotly_dark")
fig.show()

"""### **Validación del Rendimiento del Algoritmo**"""

#Graficamos cuál es la diferencia en promedio de los precios reales y los precios predecidos
dif_error = test_data["Precio Real"] - test_data["Predicciones_LSTM"]
plt.plot(dif_error)
#Mostramos esa diferencia en una tabla
dif_error

#Colocamos una fórmula para mostrar la validación del algoritmo en base al MSE, MAE, RMSE, MAPE y R2
def evaluacion_metrica(y_true, y_pred):
    def mean_absolute_percentage_error(y_true, y_pred):
        y_true, y_pred = np.array(y_true), np.array(y_pred)
        return np.mean(np.abs((y_true - y_pred) / y_true)) * 100
    print("-Resultados de las métricas de evaluación:-")
    print(f"El MSE es : {metrics.mean_squared_error(y_true, y_pred)}")
    print(f"El MAE es : {metrics.mean_absolute_error(y_true, y_pred)}")
    print(f"El RMSE es : {np.sqrt(metrics.mean_squared_error(y_true, y_pred))}")
    print(f"El MAPE es : {mean_absolute_percentage_error(y_true, y_pred)}")
    print(f"El R2 es : {metrics.r2_score(y_true, y_pred)}", end = "\n\n")

#Mostramos los resultados de la valiación de las fórmulas matemáticas
evaluacion_metrica(test_data["Precio Real"], test_data["Predicciones_LSTM"])