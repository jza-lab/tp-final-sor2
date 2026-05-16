import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder

# Cargar dataset completo para enseñarle vocabulario a los Encoders
df_completo = pd.read_csv('../data/dataset_final.csv')
le_servicio = LabelEncoder()
le_protocolo = LabelEncoder()
le_servicio.fit(df_completo['Servicio'])
le_protocolo.fit(df_completo['Protocolo'])

# Cargar dataset limpio para entrenar al modelo
df_train = pd.read_csv('../data/dataset_entrenamiento.csv')
df_train['Servicio_enc'] = le_servicio.transform(df_train['Servicio'])
df_train['Protocolo_enc'] = le_protocolo.transform(df_train['Protocolo'])

X_train = df_train[['Puerto', 'Protocolo_enc', 'Servicio_enc', 'CVSS_Score']]
y_train = df_train['Criticidad']

# Entramos al modelo
modelo = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)
modelo.fit(X_train, y_train)

# Cargar tus 50 filas clasificadas manualmente
baseline = pd.read_csv('../data/baseline_manual.csv')
baseline['Servicio_enc'] = le_servicio.transform(baseline['Servicio'])
baseline['Protocolo_enc'] = le_protocolo.transform(baseline['Protocolo'])

# Predecir con el modelo
X_baseline = baseline[['Puerto', 'Protocolo_enc', 'Servicio_enc', 'CVSS_Score']]
baseline['Criticidad_Modelo'] = modelo.predict(X_baseline)

# Comparar las tres columnas
resultado = baseline[['Puerto', 'Servicio', 'Version_Completa', 'Criticidad_NVD', 'Criticidad_Joaquin', 'Criticidad_Modelo']]
print(resultado.to_string())

# Calcular aciertos
aciertos_joaquin = (baseline['Criticidad_Joaquin'] == baseline['Criticidad_NVD']).sum()
aciertos_modelo = (baseline['Criticidad_Modelo'] == baseline['Criticidad_NVD']).sum()
print(f'\nJoaquin acertó: {aciertos_joaquin}/50 ({aciertos_joaquin*2}%)')
print(f'Modelo acertó: {aciertos_modelo}/50 ({aciertos_modelo*2}%)')
