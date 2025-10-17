# 1. Importar bibliotecas
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

# 2. Carregar os dados
df = pd.read_csv('vendas_cafe.csv')

# 3. Criar variável alvo (exemplo: comprou ou não)
# Suponha que 'Quantidade' > 0 significa que comprou
df['Comprou'] = df['Quantidade'].apply(lambda x: 1 if x > 0 else 0)

# 4. Selecionar variáveis explicativas
features = ['Produto', 'Local da Loja', 'Método de Pagamento']
X = df[features]
y = df['Comprou']

# 5. Codificar variáveis categóricas
le = LabelEncoder()
for col in X.columns:
	X[col] = le.fit_transform(X[col])

# 6. Dividir em treino e teste
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# 7. Treinar modelo supervisionado (Random Forest)
modelo = RandomForestClassifier()
modelo.fit(X_train, y_train)

# 8. Fazer previsões
y_pred = modelo.predict(X_test)

# 9. Avaliar desempenho
print("Acurácia:", accuracy_score(y_test, y_pred))
print("Relatório de Classificação:\n", classification_report(y_test, y_pred))

# Metricas e análise geral dos dados
kpis_principais = {
    "produtos_mais_vendidos": "ranking por quantidade",
    "produtos_mais_rentaveis": "ranking por receita", 
    "horarios_pico": "top 3 períodos de maior movimento",
    "ticket_medio_ideal": "meta baseada em análise histórica",
    "crescimento_mensal": "variação percentual mês a mês"
}
print("KPIs Principais:", kpis_principais)