"""
Script unificado: análises visuais + KPIs + modelo supervisionado (Random Forest)

Entrada:
  - Caminho para CSV/ZIP com os dados de vendas de café (mesmo formato usado nos seus scripts)
  - Pode ser passado por argumento de linha de comando ou editado na constante CSV_PATH

Saídas no console:
  (A) Relatório de insights (produtos, ticket médio, horários/dias, crescimento/queda, testes)
  (B) KPIs resumidos (como no esboço do seu modelo)
  (C) Métricas do modelo (acurácia + classification_report)

Gráficos (matplotlib):
  (1) Vendas por hora do dia (barra)
  (2) Receita por dia da semana (barra)
  (3) Vendas x Receita por tipo (barras, eixo duplo)
  (4) Tendência mensal de vendas por tipo (linha)
  (5) Variação % mês a mês por tipo (linha)

Arquivos adicionais gerados:
  - classification_report.txt (relatório do modelo salvo em texto)

Observações:
  - O bloco de ML roda somente se houver colunas: 'Quantidade', 'Produto', 'Local da Loja', 'Método de Pagamento'.
  - Os gráficos/insights rodam com as colunas: 'hour_of_day','money','coffee_name','Weekday','Date','Time_of_Day'.
  - Se alguma família de colunas não existir, o script pula aquela parte e imprime um aviso legível.
"""

import os, sys, warnings
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

# ===================== CONFIG =====================
CSV_PATH = r"C:\Users\thall\OneDrive\Área de Trabalho\EAD\2_sem\Projeto_Aplicado_I\codigos\Coffe_sales.csv"
if len(sys.argv) > 1:
    CSV_PATH = sys.argv[1]

if not os.path.exists(CSV_PATH):
    raise FileNotFoundError(
        f"Arquivo não encontrado:\n{CSV_PATH}\n"
        "Confirme o caminho e o nome do arquivo (ex.: Coffee_sales.csv)."
    )

# ===================== LOAD =====================
# pandas lê CSVs dentro de um .zip automaticamente (quando há um único CSV dentro)
with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=FutureWarning)
    df = pd.read_csv(CSV_PATH)

# ===================== NORMALIZAÇÕES BÁSICAS =====================
# Datas e ordenação de weekday se disponível
if 'Date' in df.columns:
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

weekday_order = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
if 'Weekday' in df.columns:
    try:
        df['Weekday'] = pd.Categorical(df['Weekday'], categories=weekday_order, ordered=True)
    except Exception:
        pass

# ===================== FUNÇÕES AUXILIARES =====================

def fmt_currency(x: float) -> str:
    try:
        return f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(x)


def has_cols(frame: pd.DataFrame, cols: set) -> bool:
    missing = set(cols) - set(frame.columns)
    if missing:
        print(f"[Aviso] Colunas ausentes: {missing}")
        return False
    return True

# ===================== (A) RELATÓRIO + GRÁFICOS =====================
cols_analytics = {"hour_of_day","money","coffee_name","Weekday","Date","Time_of_Day"}
if has_cols(df, cols_analytics):
    print("\n================ RELATÓRIO DE INSIGHTS ================\n")

    # --- Métricas base ---
    coffee_sales  = df['coffee_name'].value_counts()
    coffee_rev    = df.groupby('coffee_name')['money'].sum()
    insights_df = (pd.DataFrame({"Qtd. Vendas": coffee_sales, "Receita Total": coffee_rev})
                   .sort_values("Receita Total", ascending=False))

    hourly_sales  = df['hour_of_day'].value_counts().sort_index()
    weekday_rev   = df.groupby('Weekday')['money'].sum().sort_index()
    weekday_qty   = df.groupby('Weekday')['coffee_name'].count().sort_index()

    ticket_medio_geral = df['money'].mean()
    ticket_por_weekday = (weekday_rev / weekday_qty).reindex(weekday_order)
    ticket_por_periodo = df.groupby('Time_of_Day')['money'].mean().sort_values(ascending=False)

    # Séries mensais por tipo
    monthly_sales = (df.groupby([df['Date'].dt.to_period('M'), 'coffee_name'])
                       .size()
                       .unstack(fill_value=0))
    monthly_sales.index = monthly_sales.index.to_timestamp()
    monthly_chg = monthly_sales.pct_change() * 100

    chg_last  = monthly_chg.tail(3)
    chg_stack = chg_last.stack().reset_index()
    chg_stack.columns = ['Mes','Tipo','Var%']
    top_up   = chg_stack.sort_values('Var%', ascending=False).head(5)
    top_down = chg_stack.sort_values('Var%').head(5)

    # --- Impressões principais ---
    mais_vendido = coffee_sales.idxmax()
    mais_rentavel = coffee_rev.idxmax()
    print(f"• Produto mais vendido: {mais_vendido} ({coffee_sales.max()} unidades)")
    print(f"• Produto mais rentável: {mais_rentavel} ({fmt_currency(coffee_rev.max())})")

    print(f"• Ticket médio geral: {fmt_currency(ticket_medio_geral)}")
    print("• Ticket médio por dia da semana:")
    for d, v in ticket_por_weekday.dropna().items():
        print(f"   - {d}: {fmt_currency(v)}")
    print("• Ticket médio por período do dia:")
    for p, v in ticket_por_periodo.items():
        print(f"   - {p}: {fmt_currency(v)}")

    hora_pico  = hourly_sales.idxmax()
    hora_fraca = hourly_sales.idxmin()
    dia_top    = weekday_rev.idxmax()
    print(f"• Horário de pico de vendas: {hora_pico}h ({hourly_sales.max()} vendas)")
    print(f"• Horário de menor movimento: {hora_fraca}h ({hourly_sales.min()} vendas)")
    print(f"• Dia mais lucrativo: {dia_top} ({fmt_currency(weekday_rev.max())})")
    print("• Receita por dia (ordem):")
    for d, v in weekday_rev.sort_values(ascending=False).items():
        print(f"   - {d}: {fmt_currency(v)}")

    print("\n• Maiores crescimentos recentes (últimos meses):")
    for _, row in top_up.iterrows():
        print(f"   - {row['Mes'].strftime('%Y-%m')} | {row['Tipo']}: {row['Var%']:.1f}%")
    print("• Maiores quedas recentes (últimos meses):")
    for _, row in top_down.iterrows():
        print(f"   - {row['Mes'].strftime('%Y-%m')} | {row['Tipo']}: {row['Var%']:.1f}%")

    # --- Testes (opcional) ---
    try:
        from scipy.stats import f_oneway, kruskal
        groups_types = [g['money'].values for _, g in df.groupby('coffee_name')]
        anova_types  = f_oneway(*groups_types)
        kw_types     = kruskal(*groups_types)
        groups_month = [g['money'].values for _, g in df.groupby(df['Date'].dt.to_period('M'))]
        anova_month  = f_oneway(*groups_month)
        print("\n• Testes de significância:")
        print(f"   - ANOVA entre tipos (p): {anova_types.pvalue:.2e}")
        print(f"   - Kruskal-Wallis entre tipos (p): {kw_types.pvalue:.2e}")
        print(f"   - ANOVA entre meses (p): {anova_month.pvalue:.2e}")
        print("   -> p-valor muito baixo indica diferenças estatisticamente significativas.")
    except Exception as e:
        print(f"\n• Testes de significância: (Aviso) não executados: {e}")

    # --- Recomendações simples ---
    dias_fracos = weekday_rev.sort_values().head(2).index.tolist()
    print("\n================ RECOMENDAÇÕES ========================\n")
    print("• Promoções recomendadas:")
    print(f"   - Focar descontos/combos em: {', '.join(dias_fracos)} (menor receita).")
    print(f"   - Incentivar consumo em {hora_fraca}h com combos/vale-bebida.")
    print("   - Usar upsell (doces/lanches) nos períodos com menor ticket médio.")
    print("• Operações e mão de obra:")
    print(f"   - Escalar equipe extra próximo de {hora_pico}h; reduzir entre horários fracos (ex.: {hora_fraca}h).")
    print("   - Direcionar equipe ociosa para pré-preparo/estoque/limpeza.")
    print("• Portfólio e marketing:")
    print(f"   - Destacar {mais_vendido} e {mais_rentavel} em campanhas.")
    print("   - Considerar promoções para itens de baixo giro; revisar cardápio se persistirem baixos.")
    print("\n=======================================================\n")

    # --- Gráficos ---
    plt.rcParams.update({
        "axes.grid": True, "grid.color": "#bdbdbd", "grid.alpha": 0.35,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.edgecolor": "#000000",
        "axes.titlesize": 22, "axes.titlepad": 14,
        "axes.labelsize": 13, "xtick.labelsize": 12, "ytick.labelsize": 12,
    })
    ORANGE = "#e19b0f"; BLUE = "#93c5fd"; EDGE = "black"

    # (1) Vendas por hora
    try:
        fig, ax = plt.subplots(figsize=(13,7))
        ax.bar(hourly_sales.index, hourly_sales.values, color=ORANGE, edgecolor=EDGE, width=0.8)
        ax.set_title("Distribuição de Vendas por Hora do Dia")
        ax.set_xlabel("Hora"); ax.set_ylabel("Número de Vendas")
        ax.set_xticks(hourly_sales.index)
        ax.set_xticklabels([str(h) for h in hourly_sales.index])
        plt.tight_layout(); plt.show()
    except Exception as e:
        print(f"[Aviso] Gráfico (1) não exibido: {e}")

    # (2) Receita por dia da semana
    try:
        fig, ax = plt.subplots(figsize=(11,7))
        ax.bar(weekday_rev.index.astype(str), weekday_rev.values, color=ORANGE, edgecolor=EDGE, width=0.8)
        ax.set_title("Receita Total por Dia da Semana")
        ax.set_xlabel("Weekday"); ax.set_ylabel("Receita Total")
        plt.tight_layout(); plt.show()
    except Exception as e:
        print(f"[Aviso] Gráfico (2) não exibido: {e}")

    # (3) Vendas x Receita por tipo (eixo duplo)
    try:
        x = range(len(insights_df))
        fig, ax1 = plt.subplots(figsize=(16,8))
        ax1.bar(x, insights_df["Qtd. Vendas"].values, width=0.8, color=BLUE, edgecolor=EDGE, label="Qtd. Vendas")
        ax1.set_ylabel("Quantidade de Vendas"); ax1.set_xlabel("")
        ax2 = ax1.twinx()
        ax2.bar(x, insights_df["Receita Total"].values, width=0.5, color=ORANGE, edgecolor=EDGE, label="Receita Total (right)")
        ax2.set_ylabel("Receita Total")
        ax1.set_title("Vendas (azul) e Receita (laranja) por Tipo de Café")
        ax1.set_xticks(list(x)); ax1.set_xticklabels(insights_df.index, rotation=45, ha="right")
        ax1.legend(loc="upper left"); ax2.legend(loc="upper right")
        plt.tight_layout(); plt.show()
    except Exception as e:
        print(f"[Aviso] Gráfico (3) não exibido: {e}")

    # (4) Tendência mensal por tipo
    try:
        fig, ax = plt.subplots(figsize=(16,8))
        monthly_sales.plot(ax=ax, linewidth=2)
        ax.set_title("Tendência Mensal de Vendas por Tipo de Café")
        ax.set_xlabel("Mês"); ax.set_ylabel("Número de Vendas")
        ax.legend(title="Tipo de Café", bbox_to_anchor=(1.02, 1), loc="upper left", borderaxespad=0.)
        plt.tight_layout(); plt.show()
    except Exception as e:
        print(f"[Aviso] Gráfico (4) não exibido: {e}")

    # (5) Variação % mês a mês por tipo
    try:
        fig, ax = plt.subplots(figsize=(16,8))
        monthly_chg.plot(ax=ax, linewidth=2)
        ax.axhline(0, color="black", linestyle="--", linewidth=1)
        ax.set_title("Crescimento/Queda Percentual nas Vendas por Tipo de Café (Mês a Mês)")
        ax.set_xlabel("Mês"); ax.set_ylabel("Variação %")
        ax.legend(title="Tipo de Café", bbox_to_anchor=(1.02, 1), loc="upper left", borderaxespad=0.)
        plt.tight_layout(); plt.show()
    except Exception as e:
        print(f"[Aviso] Gráfico (5) não exibido: {e}")
else:
    print("\n[Info] Colunas de análise/plots não encontradas; pulando seção de insights e gráficos.")

# ===================== (B) KPIs RESUMIDOS =====================
# (Esboço textual — sempre exibido)
print("\n================ KPIs (Esboço) ========================")
kpis_principais = {
    "produtos_mais_vendidos": "ranking por quantidade",
    "produtos_mais_rentaveis": "ranking por receita",
    "horarios_pico": "top 3 períodos de maior movimento",
    "ticket_medio_ideal": "meta baseada em análise histórica",
    "crescimento_mensal": "variação percentual mês a mês"
}
print(kpis_principais)
print("=======================================================\n")

# ===================== (C) MODELO SUPERVISIONADO =====================
cols_ml = {"Quantidade", "Produto", "Local da Loja", "Método de Pagamento"}
if has_cols(df, cols_ml):
    print("================ MODELO (Random Forest) ===============")
    work = df.copy()
    # Variável-alvo binária: comprou (1) se Quantidade > 0, senão 0
    work['Comprou'] = work['Quantidade'].apply(lambda x: 1 if x > 0 else 0)

    features = ['Produto', 'Local da Loja', 'Método de Pagamento']
    X = work[features].copy()
    y = work['Comprou'].copy()

    # Codificação label-encoding por coluna
    encoders = {}
    for col in X.columns:
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col].astype(str))
        encoders[col] = le

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.30, random_state=42, stratify=y if y.nunique()==2 else None
    )

    # Modelo
    modelo = RandomForestClassifier(random_state=42)
    modelo.fit(X_train, y_train)

    # Predições + métricas
    y_pred = modelo.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred)

    print(f"Acurácia: {acc:.4f}")
    print("Relatório de Classificação:\n" + report)

    # Salvar relatório
    try:
        with open('classification_report.txt', 'w', encoding='utf-8') as f:
            f.write(f"Acurácia: {acc:.4f}\n\n")
            f.write(report)
        print("[OK] classification_report.txt salvo no diretório atual.")
    except Exception as e:
        print(f"[Aviso] Não foi possível salvar classification_report.txt: {e}")
else:
    print("[Info] Colunas para o modelo não encontradas; pulando seção de ML.")

print("\nFinalizado.")