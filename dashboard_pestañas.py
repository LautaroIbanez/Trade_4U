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

def crear_dashboard_pestañas():
    """Crea un dashboard con pestañas para organizar mejor los gráficos"""
    
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
    
    # Crear figura principal
    fig = plt.figure(figsize=(20, 12))
    fig.suptitle('📊 DASHBOARD COMPLETO - BACKTESTING BTC 1TPD', fontsize=20, fontweight='bold', y=0.95)
    
    # ===== PESTAÑA 1: ANÁLISIS PRINCIPAL =====
    # 1. Equity Curve (Gráfico principal)
    ax1 = plt.subplot(2, 3, (1, 2))  # Ocupa 2 columnas
    ax1.plot(df_sorted['exit_time'], df_sorted['pnl_acumulado'], linewidth=3, color='#2E8B57', alpha=0.8)
    ax1.fill_between(df_sorted['exit_time'], df_sorted['pnl_acumulado'], alpha=0.3, color='#2E8B57')
    ax1.axhline(y=0, color='red', linestyle='--', alpha=0.7, linewidth=2)
    ax1.set_title('💰 EQUITY CURVE - PnL Acumulado', fontsize=14, fontweight='bold', pad=15)
    ax1.set_ylabel('PnL Acumulado (USDT)', fontsize=12)
    ax1.tick_params(axis='both', labelsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.tick_params(axis='x', rotation=45)
    
    # 2. Métricas de Rendimiento
    ax2 = plt.subplot(2, 3, 3)
    ax2.axis('off')
    metricas_texto = f"""📊 MÉTRICAS DE RENDIMIENTO

🎯 Total de Trades: {total_trades}
✅ Trades Ganadores: {trades_ganadores}
❌ Trades Perdedores: {trades_perdedores}
📈 Win Rate: {win_rate:.1f}%

💰 PnL Total: {pnl_total:.2f} USDT
📊 PnL Promedio: {pnl_promedio:.2f} USDT
🎲 R-Múltiple Promedio: {r_multiple_promedio:.2f}

📉 Máximo Drawdown: {max_drawdown:.2f} USDT
📅 Período: {df['day_key'].min().strftime('%Y-%m-%d')} a {df['day_key'].max().strftime('%Y-%m-%d')}"""
    ax2.text(0.05, 0.95, metricas_texto, transform=ax2.transAxes, fontsize=11, 
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle="round,pad=0.5", facecolor='lightblue', alpha=0.9))
    
    # 3. Distribución de R-múltiples
    ax3 = plt.subplot(2, 3, 4)
    bins = np.arange(-2, 3, 0.5)
    ax3.hist(df['r_multiple'], bins=bins, alpha=0.7, color='#FF6B6B', edgecolor='black', linewidth=1)
    ax3.axvline(x=0, color='red', linestyle='--', alpha=0.7, linewidth=2)
    ax3.axvline(x=r_multiple_promedio, color='green', linestyle='-', linewidth=2, label=f'Promedio: {r_multiple_promedio:.2f}')
    ax3.set_title('📈 DISTRIBUCIÓN R-MÚLTIPLES', fontsize=12, fontweight='bold', pad=10)
    ax3.set_xlabel('R-Múltiple', fontsize=10)
    ax3.set_ylabel('Frecuencia', fontsize=10)
    ax3.tick_params(axis='both', labelsize=9)
    ax3.legend(fontsize=9)
    ax3.grid(True, alpha=0.3)
    
    # 4. Trades Ganadores vs Perdedores
    ax4 = plt.subplot(2, 3, 5)
    labels = ['Ganadores', 'Perdedores']
    sizes = [trades_ganadores, trades_perdedores]
    colors = ['#4CAF50', '#F44336']
    wedges, texts, autotexts = ax4.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', 
                                      startangle=90, textprops={'fontsize': 10})
    ax4.set_title('🎯 GANADORES VS PERDEDORES', fontsize=12, fontweight='bold', pad=10)
    
    # 5. Drawdown
    ax5 = plt.subplot(2, 3, 6)
    ax5.fill_between(df_sorted['exit_time'], df_sorted['drawdown'], alpha=0.7, color='#FF4444')
    ax5.set_title('📉 DRAWDOWN', fontsize=12, fontweight='bold', pad=10)
    ax5.set_ylabel('Drawdown (USDT)', fontsize=10)
    ax5.tick_params(axis='both', labelsize=9)
    ax5.tick_params(axis='x', rotation=45)
    ax5.grid(True, alpha=0.3)
    
    # Ajustar layout de la primera pestaña
    plt.tight_layout()
    plt.subplots_adjust(top=0.90, hspace=0.3, wspace=0.25)
    
    # Guardar primera pestaña
    plt.savefig('dashboard_pestaña1_principal.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    
    # ===== PESTAÑA 2: ANÁLISIS DETALLADO =====
    # Crear nueva figura para la segunda pestaña
    fig2 = plt.figure(figsize=(20, 12))
    fig2.suptitle('📊 DASHBOARD COMPLETO - ANÁLISIS DETALLADO', fontsize=20, fontweight='bold', y=0.95)
    
    # 1. PnL por Trade
    ax1 = plt.subplot(2, 3, (1, 2))  # Ocupa 2 columnas
    colores_pnl = ['#4CAF50' if x > 0 else '#F44336' for x in df['pnl_usdt']]
    ax1.bar(range(len(df)), df['pnl_usdt'], color=colores_pnl, alpha=0.7, edgecolor='black', linewidth=0.5)
    ax1.axhline(y=0, color='black', linestyle='-', alpha=0.5, linewidth=2)
    ax1.set_title('💵 PnL POR TRADE', fontsize=14, fontweight='bold', pad=15)
    ax1.set_xlabel('Número de Trade', fontsize=12)
    ax1.set_ylabel('PnL (USDT)', fontsize=12)
    ax1.tick_params(axis='both', labelsize=10)
    ax1.grid(True, alpha=0.3)
    
    # 2. Distribución de PnL
    ax2 = plt.subplot(2, 3, 3)
    ax2.hist(df['pnl_usdt'], bins=20, alpha=0.7, color='#9C27B0', edgecolor='black', linewidth=1)
    ax2.axvline(x=0, color='red', linestyle='--', alpha=0.7, linewidth=2)
    ax2.axvline(x=pnl_promedio, color='green', linestyle='-', linewidth=2, label=f'Promedio: {pnl_promedio:.2f}')
    ax2.set_title('📊 DISTRIBUCIÓN PnL', fontsize=12, fontweight='bold', pad=10)
    ax2.set_xlabel('PnL (USDT)', fontsize=10)
    ax2.set_ylabel('Frecuencia', fontsize=10)
    ax2.tick_params(axis='both', labelsize=9)
    ax2.legend(fontsize=9)
    ax2.grid(True, alpha=0.3)
    
    # 3. Trades por día de la semana
    ax3 = plt.subplot(2, 3, 4)
    df['dia_semana'] = df['entry_time'].dt.day_name()
    dias_orden = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dias_espanol = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
    trades_por_dia = df['dia_semana'].value_counts().reindex(dias_orden, fill_value=0)
    colores = plt.cm.Set3(np.linspace(0, 1, len(trades_por_dia)))
    bars = ax3.bar(dias_espanol, trades_por_dia.values, color=colores, alpha=0.8, edgecolor='black', linewidth=1)
    ax3.set_title('📅 TRADES POR DÍA DE LA SEMANA', fontsize=12, fontweight='bold', pad=10)
    ax3.set_ylabel('Número de Trades', fontsize=10)
    ax3.tick_params(axis='both', labelsize=9)
    ax3.tick_params(axis='x', rotation=45)
    ax3.grid(True, alpha=0.3)
    
    # 4. Trades por mes
    ax4 = plt.subplot(2, 3, 5)
    df['mes'] = df['entry_time'].dt.to_period('M')
    trades_por_mes = df['mes'].value_counts().sort_index()
    meses_str = [str(mes) for mes in trades_por_mes.index]
    colores_mes = plt.cm.viridis(np.linspace(0, 1, len(trades_por_mes)))
    bars = ax4.bar(meses_str, trades_por_mes.values, color=colores_mes, alpha=0.8, edgecolor='black', linewidth=1)
    ax4.set_title('📅 TRADES POR MES', fontsize=12, fontweight='bold', pad=10)
    ax4.set_ylabel('Número de Trades', fontsize=10)
    ax4.tick_params(axis='both', labelsize=9)
    ax4.tick_params(axis='x', rotation=45)
    ax4.grid(True, alpha=0.3)
    
    # 5. Duración de trades
    ax5 = plt.subplot(2, 3, 6)
    df['duracion_horas'] = (df['exit_time'] - df['entry_time']).dt.total_seconds() / 3600
    ax5.hist(df['duracion_horas'], bins=15, alpha=0.7, color='#FF9800', edgecolor='black', linewidth=1)
    ax5.axvline(x=df['duracion_horas'].mean(), color='red', linestyle='-', linewidth=2, 
                label=f'Promedio: {df["duracion_horas"].mean():.1f}h')
    ax5.set_title('⏱️ DURACIÓN DE TRADES', fontsize=12, fontweight='bold', pad=10)
    ax5.set_xlabel('Duración (horas)', fontsize=10)
    ax5.set_ylabel('Frecuencia', fontsize=10)
    ax5.tick_params(axis='both', labelsize=9)
    ax5.legend(fontsize=9)
    ax5.grid(True, alpha=0.3)
    
    # Ajustar layout de la segunda pestaña
    plt.tight_layout()
    plt.subplots_adjust(top=0.90, hspace=0.3, wspace=0.25)
    
    # Guardar segunda pestaña
    plt.savefig('dashboard_pestaña2_detallado.png', dpi=300, bbox_inches='tight', facecolor='white')
    plt.show()
    
    print("🎉 Dashboard con pestañas creado exitosamente!")
    print("📊 Pestaña 1 (Principal): 'dashboard_pestaña1_principal.png'")
    print("📊 Pestaña 2 (Detallado): 'dashboard_pestaña2_detallado.png'")
    print(f"📈 Resumen: {total_trades} trades, {win_rate:.1f}% win rate, {pnl_total:.2f} USDT total")

if __name__ == "__main__":
    crear_dashboard_pestañas()


