import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Configuración del estilo
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def crear_dashboard_completo():
    """Crea un dashboard completo con múltiples gráficos del backtesting"""
    
    # Cargar datos
    df = pd.read_csv('trades_final.csv')
    df['entry_time'] = pd.to_datetime(df['entry_time'])
    df['exit_time'] = pd.to_datetime(df['exit_time'])
    df['day_key'] = pd.to_datetime(df['day_key'])
    
    # Calcular métricas
    total_trades = len(df)
    trades_ganadores = len(df[df['pnl_usdt'] > 0])
    trades_perdedores = len(df[df['pnl_usdt'] < 0])
    win_rate = (trades_ganadores / total_trades) * 100
    pnl_total = df['pnl_usdt'].sum()
    pnl_promedio = df['pnl_usdt'].mean()
    r_multiple_promedio = df['r_multiple'].mean()
    
    # Calcular equity curve
    df_sorted = df.sort_values('exit_time')
    df_sorted['pnl_acumulado'] = df_sorted['pnl_usdt'].cumsum()
    
    # Calcular drawdown
    df_sorted['max_acumulado'] = df_sorted['pnl_acumulado'].expanding().max()
    df_sorted['drawdown'] = df_sorted['pnl_acumulado'] - df_sorted['max_acumulado']
    max_drawdown = df_sorted['drawdown'].min()
    
    # Crear figura con subplots - MÁS GRÁFICOS Y MÁS COMPACTO
    fig = plt.figure(figsize=(22, 16))
    fig.suptitle('📊 DASHBOARD COMPLETO - BACKTESTING BTC 1TPD', fontsize=18, fontweight='bold', y=0.96)
    
    # 1. Equity Curve (Gráfico principal)
    ax1 = plt.subplot(3, 4, (1, 3))  # Ocupa 3 columnas
    ax1.plot(df_sorted['exit_time'], df_sorted['pnl_acumulado'], linewidth=2.5, color='#2E8B57', alpha=0.8)
    ax1.fill_between(df_sorted['exit_time'], df_sorted['pnl_acumulado'], alpha=0.3, color='#2E8B57')
    ax1.axhline(y=0, color='red', linestyle='--', alpha=0.7, linewidth=2)
    ax1.set_title('💰 EQUITY CURVE', fontsize=12, fontweight='bold', pad=8)
    ax1.set_ylabel('PnL Acumulado (USDT)', fontsize=10)
    ax1.tick_params(axis='both', labelsize=9)
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='x', rotation=45)
    
    # 2. Métricas de Rendimiento (Panel compacto)
    ax2 = plt.subplot(3, 4, 4)
    ax2.axis('off')
    metricas_texto = f"""📊 MÉTRICAS

🎯 Trades: {total_trades}
✅ Ganadores: {trades_ganadores}
❌ Perdedores: {trades_perdedores}
📈 Win Rate: {win_rate:.1f}%

💰 PnL Total: {pnl_total:.2f} USDT
📊 Promedio: {pnl_promedio:.2f} USDT
🎲 R-Múltiple: {r_multiple_promedio:.2f}

📉 Max DD: {max_drawdown:.2f} USDT
📅 {df['day_key'].min().strftime('%Y-%m')} a {df['day_key'].max().strftime('%Y-%m')}"""
    ax2.text(0.05, 0.95, metricas_texto, transform=ax2.transAxes, fontsize=9, 
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle="round,pad=0.3", facecolor='lightblue', alpha=0.9))
    
    # 3. Distribución de R-múltiples
    ax3 = plt.subplot(3, 4, 5)
    bins = np.arange(-2, 3, 0.5)
    ax3.hist(df['r_multiple'], bins=bins, alpha=0.7, color='#FF6B6B', edgecolor='black', linewidth=0.8)
    ax3.axvline(x=0, color='red', linestyle='--', alpha=0.7, linewidth=1.5)
    ax3.axvline(x=r_multiple_promedio, color='green', linestyle='-', linewidth=1.5, label=f'Prom: {r_multiple_promedio:.2f}')
    ax3.set_title('📈 R-MÚLTIPLES', fontsize=10, fontweight='bold', pad=6)
    ax3.set_xlabel('R-Múltiple', fontsize=9)
    ax3.set_ylabel('Frecuencia', fontsize=9)
    ax3.tick_params(axis='both', labelsize=8)
    ax3.legend(fontsize=8)
    ax3.grid(True, alpha=0.3)
    
    # 4. Trades por día de la semana
    ax4 = plt.subplot(3, 4, 6)
    df['dia_semana'] = df['entry_time'].dt.day_name()
    dias_orden = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dias_espanol = ['L', 'M', 'X', 'J', 'V', 'S', 'D']
    trades_por_dia = df['dia_semana'].value_counts().reindex(dias_orden, fill_value=0)
    colores = plt.cm.Set3(np.linspace(0, 1, len(trades_por_dia)))
    bars = ax4.bar(dias_espanol, trades_por_dia.values, color=colores, alpha=0.8, edgecolor='black', linewidth=0.8)
    ax4.set_title('📅 TRADES POR DÍA', fontsize=10, fontweight='bold', pad=6)
    ax4.set_ylabel('Número', fontsize=9)
    ax4.tick_params(axis='both', labelsize=8)
    ax4.grid(True, alpha=0.3)
    
    # 5. Trades Ganadores vs Perdedores
    ax5 = plt.subplot(3, 4, 7)
    labels = ['Ganadores', 'Perdedores']
    sizes = [trades_ganadores, trades_perdedores]
    colors = ['#4CAF50', '#F44336']
    wedges, texts, autotexts = ax5.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', 
                                      startangle=90, textprops={'fontsize': 8})
    ax5.set_title('🎯 GANADORES VS PERDEDORES', fontsize=10, fontweight='bold', pad=6)
    
    # 6. PnL por Trade
    ax6 = plt.subplot(3, 4, 8)
    colores_pnl = ['#4CAF50' if x > 0 else '#F44336' for x in df['pnl_usdt']]
    ax6.bar(range(len(df)), df['pnl_usdt'], color=colores_pnl, alpha=0.7, edgecolor='black', linewidth=0.3)
    ax6.axhline(y=0, color='black', linestyle='-', alpha=0.5, linewidth=1.5)
    ax6.set_title('💵 PnL POR TRADE', fontsize=10, fontweight='bold', pad=6)
    ax6.set_xlabel('Trade #', fontsize=9)
    ax6.set_ylabel('PnL (USDT)', fontsize=9)
    ax6.tick_params(axis='both', labelsize=8)
    ax6.grid(True, alpha=0.3)
    
    # 7. Distribución de PnL
    ax7 = plt.subplot(3, 4, 9)
    ax7.hist(df['pnl_usdt'], bins=15, alpha=0.7, color='#9C27B0', edgecolor='black', linewidth=0.8)
    ax7.axvline(x=0, color='red', linestyle='--', alpha=0.7, linewidth=1.5)
    ax7.axvline(x=pnl_promedio, color='green', linestyle='-', linewidth=1.5, label=f'Prom: {pnl_promedio:.2f}')
    ax7.set_title('📊 DISTRIBUCIÓN PnL', fontsize=10, fontweight='bold', pad=6)
    ax7.set_xlabel('PnL (USDT)', fontsize=9)
    ax7.set_ylabel('Frecuencia', fontsize=9)
    ax7.tick_params(axis='both', labelsize=8)
    ax7.legend(fontsize=8)
    ax7.grid(True, alpha=0.3)
    
    # 8. Trades por mes
    ax8 = plt.subplot(3, 4, 10)
    df['mes'] = df['entry_time'].dt.to_period('M')
    trades_por_mes = df['mes'].value_counts().sort_index()
    meses_str = [str(mes) for mes in trades_por_mes.index]
    colores_mes = plt.cm.viridis(np.linspace(0, 1, len(trades_por_mes)))
    bars = ax8.bar(meses_str, trades_por_mes.values, color=colores_mes, alpha=0.8, edgecolor='black', linewidth=0.8)
    ax8.set_title('📅 TRADES POR MES', fontsize=10, fontweight='bold', pad=6)
    ax8.set_ylabel('Número', fontsize=9)
    ax8.tick_params(axis='both', labelsize=8)
    ax8.tick_params(axis='x', rotation=45)
    ax8.grid(True, alpha=0.3)
    
    # 9. Duración de trades
    ax9 = plt.subplot(3, 4, 11)
    df['duracion_horas'] = (df['exit_time'] - df['entry_time']).dt.total_seconds() / 3600
    ax9.hist(df['duracion_horas'], bins=12, alpha=0.7, color='#FF9800', edgecolor='black', linewidth=0.8)
    ax9.axvline(x=df['duracion_horas'].mean(), color='red', linestyle='-', linewidth=1.5, 
                label=f'Prom: {df["duracion_horas"].mean():.1f}h')
    ax9.set_title('⏱️ DURACIÓN TRADES', fontsize=10, fontweight='bold', pad=6)
    ax9.set_xlabel('Duración (horas)', fontsize=9)
    ax9.set_ylabel('Frecuencia', fontsize=9)
    ax9.tick_params(axis='both', labelsize=8)
    ax9.legend(fontsize=8)
    ax9.grid(True, alpha=0.3)
    
    # 10. Drawdown
    ax10 = plt.subplot(3, 4, 12)
    ax10.fill_between(df_sorted['exit_time'], df_sorted['drawdown'], alpha=0.7, color='#FF4444')
    ax10.set_title('📉 DRAWDOWN', fontsize=10, fontweight='bold', pad=6)
    ax10.set_ylabel('Drawdown (USDT)', fontsize=9)
    ax10.tick_params(axis='both', labelsize=8)
    ax10.tick_params(axis='x', rotation=45)
    ax10.grid(True, alpha=0.3)
    
    # Ajustar layout - COMPACTO CON MÁS GRÁFICOS
    plt.tight_layout()
    plt.subplots_adjust(top=0.94, hspace=0.25, wspace=0.2)
    
    # Guardar dashboard
    plt.savefig('dashboard_completo.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    
    print("🎉 Dashboard completo creado y guardado como 'dashboard_completo.png'")
    print(f"📊 Resumen: {total_trades} trades, {win_rate:.1f}% win rate, {pnl_total:.2f} USDT total")

if __name__ == "__main__":
    crear_dashboard_completo()
