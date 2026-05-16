import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score, cross_val_predict
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report

print("Iniciando pipeline de Machine Learning...")

# ---------------------------------------------------------
# 1. ENSEÑAR EL VOCABULARIO COMPLETO AL ENCODER
# (Esto evita el error de "unseen labels" con servicios raros)
# ---------------------------------------------------------
df_completo = pd.read_csv('../data/dataset_final.csv')
le_servicio = LabelEncoder()
le_protocolo = LabelEncoder()

# Hacemos fit sobre TODO el dataset para que conozca todas las palabras
le_servicio.fit(df_completo['Servicio'])
le_protocolo.fit(df_completo['Protocolo'])

# ---------------------------------------------------------
# 2. CARGAR Y PREPARAR DATOS DE ENTRENAMIENTO (Sin fuga de datos)
# ---------------------------------------------------------
df_train = pd.read_csv('../data/dataset_entrenamiento.csv')
df_train['Servicio_enc'] = le_servicio.transform(df_train['Servicio'])
df_train['Protocolo_enc'] = le_protocolo.transform(df_train['Protocolo'])

X_train = df_train[['Puerto', 'Protocolo_enc', 'Servicio_enc', 'CVSS_Score']]
y_train = df_train['Criticidad']

# Inicializar el modelo con pesos balanceados
modelo = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)

# ---------------------------------------------------------
# 3. VALIDACIÓN CRUZADA (K-FOLD) - EVALUACIÓN HONESTA
# ---------------------------------------------------------
print("\n--- 1. EVALUACIÓN DEL MODELO (CROSS-VALIDATION) ---")
kf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# F1-Score Promedio
scores = cross_val_score(modelo, X_train, y_train, cv=kf, scoring='f1_macro')
print(f'F1-score macro promedio: {scores.mean():.3f} (+/- {scores.std():.3f})')

# Reporte de clasificación usando predicciones cruzadas (sin sobreajuste)
y_pred_honesto = cross_val_predict(modelo, X_train, y_train, cv=kf)
print("\nReporte de Clasificación (Realista):")
print(classification_report(y_train, y_pred_honesto, zero_division=0))

# Ahora sí, entrenamos el modelo final con todos los datos limpios
modelo.fit(X_train, y_train)

# ---------------------------------------------------------
# 4. COMPARATIVA FINAL: JOAQUÍN VS MODELO VS NVD (BASELINE)
# ---------------------------------------------------------
print("\n--- 2. COMPARATIVA CONTRA BASELINE MANUAL ---")
baseline = pd.read_csv('../data/baseline_manual.csv')

# Transformar datos del baseline usando el encoder entrenado
baseline['Servicio_enc'] = le_servicio.transform(baseline['Servicio'])
baseline['Protocolo_enc'] = le_protocolo.transform(baseline['Protocolo'])

# Predecir sobre los 50 hallazgos manuales
X_baseline = baseline[['Puerto', 'Protocolo_enc', 'Servicio_enc', 'CVSS_Score']]
baseline['Criticidad_Modelo'] = modelo.predict(X_baseline)

# Calcular aciertos (La NVD es el "Árbitro")
aciertos_joaquin = (baseline['Criticidad_Joaquin'] == baseline['Criticidad_NVD']).sum()
aciertos_modelo = (baseline['Criticidad_Modelo'] == baseline['Criticidad_NVD']).sum()

print(f'Joaquín (Contexto) acertó vs NVD: {aciertos_joaquin}/50 ({aciertos_joaquin*2}%)')
print(f'Modelo de ML acertó vs NVD:      {aciertos_modelo}/50 ({aciertos_modelo*2}%)')

# Imprimir un par de casos de estudio para el informe (ej: la bindshell)
casos_estudio = baseline[baseline['Servicio'].isin(['bindshell', 'exec', 'ajp13'])]
print("\n[Casos de Estudio para el Informe - Discrepancia de Criterios]")
print(casos_estudio[['Puerto', 'Servicio', 'Criticidad_NVD', 'Criticidad_Joaquin', 'Criticidad_Modelo']].to_string(index=False))
