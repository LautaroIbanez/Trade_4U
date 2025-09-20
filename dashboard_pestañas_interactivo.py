import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.widgets as widgets
import seaborn as sns
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Configuración del estilo
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class DashboardInteractivo:
    def __init__(self):
        self.df = None
        self.metricas = {}
        self.cargar_datos()
        self.crear_dashboard()
    
    def cargar_datos(self):
        """Carga y procesa los datos del backtesting"""
        self.df = pd.read_csv('trades_final.csv')
        self.df['entry_time'] = pd.to_datetime(self.df['entry_time'])
        self.df['exit_time'] = pd.to_datetime(self.df['exit_time'])
        self.df['day_key'] = pd.to_datetime(self.df['day_key'])
        
        # Calcular métricas
        self.metricas['total_trades'] = len(self.df)
        self.metricas['trades_ganadores'] = len(self.df[self.df['pnl_usdt'] > 0])
        self.metricas['trades_perdedores'] = len(self.df[self.df['pnl_usdt'] < 0])
        self.metricas['win_rate'] = (self.metricas['trades_ganadores'] / self.metricas['total_trades']) * 100
        self.metricas['pnl_total'] = self.df['pnl_usdt'].sum()
        self.metricas['pnl_promedio'] = self.df['pnl_usdt'].mean()
        self.metricas['r_multiple_promedio'] = self.df['r_multiple'].mean()
        
        # Calcular equity curve
        self.df_sorted = self.df.sort_values('exit_time')
        self.df_sorted['pnl_acumulado'] = self.df_sorted['pnl_usdt'].cumsum()
        
        # Calcular drawdown
        self.df_sorted['max_acumulado'] = self.df_sorted['pnl_acumulado'].expanding().max()
        self.df_sorted['drawdown'] = self.df_sorted['pnl_acumulado'] - self.df_sorted['max_acumulado']
        self.metricas['max_drawdown'] = self.df_sorted['drawdown'].min()
    
    def crear_dashboard(self):
        """Crea el dashboard interactivo con pestañas"""
        # Crear figura principal
        self.fig = plt.figure(figsize=(16, 10))
        self.fig.suptitle('📊 DASHBOARD COMPLETO - BACKTESTING BTC 1TPD', fontsize=14, fontweight='bold', y=0.95)
        
        # Crear botones de pestañas
        self.crear_botones_pestañas()
        
        # Crear área de gráficos
        self.crear_area_graficos()
        
        # Mostrar pestaña inicial
        self.mostrar_pestaña_principal()
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.88, bottom=0.1, left=0.05, right=0.95, hspace=0.3, wspace=0.2)
        plt.show()
    
    def crear_botones_pestañas(self):
        """Crea los botones para cambiar entre pestañas"""
        # Botón Pestaña Principal
        ax_btn1 = plt.axes([0.05, 0.92, 0.12, 0.05])
        self.btn_principal = widgets.Button(ax_btn1, '📊 PRINCIPAL', color='lightblue', hovercolor='lightcyan')
        self.btn_principal.on_clicked(self.mostrar_pestaña_principal)
        
        # Botón Pestaña Detallado
        ax_btn2 = plt.axes([0.20, 0.92, 0.12, 0.05])
        self.btn_detallado = widgets.Button(ax_btn2, '📈 DETALLADO', color='lightgreen', hovercolor='lightcyan')
        self.btn_detallado.on_clicked(self.mostrar_pestaña_detallado)
        
        # Botón Pestaña Precios
        ax_btn3 = plt.axes([0.35, 0.92, 0.12, 0.05])
        self.btn_precios = widgets.Button(ax_btn3, '💰 PRECIOS', color='lightcoral', hovercolor='lightcyan')
        self.btn_precios.on_clicked(self.mostrar_pestaña_precios)
    
    def crear_area_graficos(self):
        """Crea el área donde se mostrarán los gráficos"""
        # Área principal para los gráficos (2x3)
        self.ax_principal = []
        self.ax_detallado = []
        
        # Crear subplots para pestaña principal
        for i in range(6):
            if i < 2:  # Equity curve ocupa 2 columnas
                ax = plt.subplot(2, 3, (1, 2))
                self.ax_principal.append(ax)
                break
            else:
                ax = plt.subplot(2, 3, i+1)
                self.ax_principal.append(ax)
        
        # Crear subplots para pestaña detallado
        for i in range(6):
            if i < 2:  # PnL por trade ocupa 2 columnas
                ax = plt.subplot(2, 3, (1, 2))
                self.ax_detallado.append(ax)
                break
            else:
                ax = plt.subplot(2, 3, i+1)
                self.ax_detallado.append(ax)
    
    def mostrar_pestaña_principal(self, event=None):
        """Muestra la pestaña principal"""
        # Limpiar todos los subplots
        for ax in self.fig.get_axes():
            if ax not in [self.btn_principal.ax, self.btn_detallado.ax]:
                ax.clear()
        
        # 1. Equity Curve
        ax1 = plt.subplot(2, 3, (1, 2))
        ax1.plot(self.df_sorted['exit_time'], self.df_sorted['pnl_acumulado'], linewidth=2, color='#2E8B57', alpha=0.8)
        ax1.fill_between(self.df_sorted['exit_time'], self.df_sorted['pnl_acumulado'], alpha=0.3, color='#2E8B57')
        ax1.axhline(y=0, color='red', linestyle='--', alpha=0.7, linewidth=1.5)
        ax1.set_title('💰 EQUITY CURVE', fontsize=11, fontweight='bold', pad=8)
        ax1.set_ylabel('PnL Acumulado (USDT)', fontsize=9)
        ax1.tick_params(axis='both', labelsize=8)
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)
        
        # 2. Métricas
        ax2 = plt.subplot(2, 3, 3)
        ax2.axis('off')
        metricas_texto = f"""📊 MÉTRICAS

🎯 Trades: {self.metricas['total_trades']}
✅ Ganadores: {self.metricas['trades_ganadores']}
❌ Perdedores: {self.metricas['trades_perdedores']}
📈 Win Rate: {self.metricas['win_rate']:.1f}%

💰 PnL Total: {self.metricas['pnl_total']:.2f} USDT
📊 Promedio: {self.metricas['pnl_promedio']:.2f} USDT
🎲 R-Múltiple: {self.metricas['r_multiple_promedio']:.2f}

📉 Max DD: {self.metricas['max_drawdown']:.2f} USDT"""
        ax2.text(0.05, 0.95, metricas_texto, transform=ax2.transAxes, fontsize=8, 
                 verticalalignment='top', fontfamily='monospace',
                 bbox=dict(boxstyle="round,pad=0.3", facecolor='lightblue', alpha=0.9))
        
        # 3. R-múltiples
        ax3 = plt.subplot(2, 3, 4)
        bins = np.arange(-2, 3, 0.5)
        ax3.hist(self.df['r_multiple'], bins=bins, alpha=0.7, color='#FF6B6B', edgecolor='black', linewidth=0.6)
        ax3.axvline(x=0, color='red', linestyle='--', alpha=0.7, linewidth=1.2)
        ax3.axvline(x=self.metricas['r_multiple_promedio'], color='green', linestyle='-', linewidth=1.2, 
                   label=f'Prom: {self.metricas["r_multiple_promedio"]:.2f}')
        ax3.set_title('📈 R-MÚLTIPLES', fontsize=9, fontweight='bold', pad=6)
        ax3.set_xlabel('R-Múltiple', fontsize=8)
        ax3.set_ylabel('Frecuencia', fontsize=8)
        ax3.tick_params(axis='both', labelsize=7)
        ax3.legend(fontsize=7)
        ax3.grid(True, alpha=0.3)
        
        # 4. Ganadores vs Perdedores
        ax4 = plt.subplot(2, 3, 5)
        labels = ['Ganadores', 'Perdedores']
        sizes = [self.metricas['trades_ganadores'], self.metricas['trades_perdedores']]
        colors = ['#4CAF50', '#F44336']
        wedges, texts, autotexts = ax4.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', 
                                          startangle=90, textprops={'fontsize': 8})
        ax4.set_title('🎯 GANADORES VS PERDEDORES', fontsize=9, fontweight='bold', pad=6)
        
        # 5. Drawdown
        ax5 = plt.subplot(2, 3, 6)
        ax5.fill_between(self.df_sorted['exit_time'], self.df_sorted['drawdown'], alpha=0.7, color='#FF4444')
        ax5.set_title('📉 DRAWDOWN', fontsize=9, fontweight='bold', pad=6)
        ax5.set_ylabel('Drawdown (USDT)', fontsize=8)
        ax5.tick_params(axis='both', labelsize=7)
        ax5.tick_params(axis='x', rotation=45)
        ax5.grid(True, alpha=0.3)
        
        plt.draw()
    
    def mostrar_pestaña_detallado(self, event=None):
        """Muestra la pestaña detallado"""
        # Limpiar todos los subplots
        for ax in self.fig.get_axes():
            if ax not in [self.btn_principal.ax, self.btn_detallado.ax]:
                ax.clear()
        
        # 1. PnL por Trade
        ax1 = plt.subplot(2, 3, (1, 2))
        colores_pnl = ['#4CAF50' if x > 0 else '#F44336' for x in self.df['pnl_usdt']]
        ax1.bar(range(len(self.df)), self.df['pnl_usdt'], color=colores_pnl, alpha=0.7, edgecolor='black', linewidth=0.2)
        ax1.axhline(y=0, color='black', linestyle='-', alpha=0.5, linewidth=1.2)
        ax1.set_title('💵 PnL POR TRADE', fontsize=11, fontweight='bold', pad=8)
        ax1.set_xlabel('Número de Trade', fontsize=9)
        ax1.set_ylabel('PnL (USDT)', fontsize=9)
        ax1.tick_params(axis='both', labelsize=8)
        ax1.grid(True, alpha=0.3)
        
        # 2. Distribución PnL
        ax2 = plt.subplot(2, 3, 3)
        ax2.hist(self.df['pnl_usdt'], bins=12, alpha=0.7, color='#9C27B0', edgecolor='black', linewidth=0.6)
        ax2.axvline(x=0, color='red', linestyle='--', alpha=0.7, linewidth=1.2)
        ax2.axvline(x=self.metricas['pnl_promedio'], color='green', linestyle='-', linewidth=1.2, 
                   label=f'Prom: {self.metricas["pnl_promedio"]:.2f}')
        ax2.set_title('📊 DISTRIBUCIÓN PnL', fontsize=9, fontweight='bold', pad=6)
        ax2.set_xlabel('PnL (USDT)', fontsize=8)
        ax2.set_ylabel('Frecuencia', fontsize=8)
        ax2.tick_params(axis='both', labelsize=7)
        ax2.legend(fontsize=7)
        ax2.grid(True, alpha=0.3)
        
        # 3. Trades por día
        ax3 = plt.subplot(2, 3, 4)
        self.df['dia_semana'] = self.df['entry_time'].dt.day_name()
        dias_orden = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        dias_espanol = ['L', 'M', 'X', 'J', 'V', 'S', 'D']
        trades_por_dia = self.df['dia_semana'].value_counts().reindex(dias_orden, fill_value=0)
        colores = plt.cm.Set3(np.linspace(0, 1, len(trades_por_dia)))
        bars = ax3.bar(dias_espanol, trades_por_dia.values, color=colores, alpha=0.8, edgecolor='black', linewidth=0.6)
        ax3.set_title('📅 TRADES POR DÍA', fontsize=9, fontweight='bold', pad=6)
        ax3.set_ylabel('Número', fontsize=8)
        ax3.tick_params(axis='both', labelsize=7)
        ax3.grid(True, alpha=0.3)
        
        # 4. Trades por mes
        ax4 = plt.subplot(2, 3, 5)
        self.df['mes'] = self.df['entry_time'].dt.to_period('M')
        trades_por_mes = self.df['mes'].value_counts().sort_index()
        meses_str = [str(mes) for mes in trades_por_mes.index]
        colores_mes = plt.cm.viridis(np.linspace(0, 1, len(trades_por_mes)))
        bars = ax4.bar(meses_str, trades_por_mes.values, color=colores_mes, alpha=0.8, edgecolor='black', linewidth=0.6)
        ax4.set_title('📅 TRADES POR MES', fontsize=9, fontweight='bold', pad=6)
        ax4.set_ylabel('Número', fontsize=8)
        ax4.tick_params(axis='both', labelsize=7)
        ax4.tick_params(axis='x', rotation=45)
        ax4.grid(True, alpha=0.3)
        
        # 5. Duración de trades
        ax5 = plt.subplot(2, 3, 6)
        self.df['duracion_horas'] = (self.df['exit_time'] - self.df['entry_time']).dt.total_seconds() / 3600
        ax5.hist(self.df['duracion_horas'], bins=10, alpha=0.7, color='#FF9800', edgecolor='black', linewidth=0.6)
        ax5.axvline(x=self.df['duracion_horas'].mean(), color='red', linestyle='-', linewidth=1.2, 
                   label=f'Prom: {self.df["duracion_horas"].mean():.1f}h')
        ax5.set_title('⏱️ DURACIÓN TRADES', fontsize=9, fontweight='bold', pad=6)
        ax5.set_xlabel('Duración (horas)', fontsize=8)
        ax5.set_ylabel('Frecuencia', fontsize=8)
        ax5.tick_params(axis='both', labelsize=7)
        ax5.legend(fontsize=7)
        ax5.grid(True, alpha=0.3)
        
        plt.draw()
    
    def mostrar_pestaña_precios(self, event=None):
        """Muestra la pestaña de precios con operaciones"""
        # Limpiar todos los subplots
        for ax in self.fig.get_axes():
            if ax not in [self.btn_principal.ax, self.btn_detallado.ax, self.btn_precios.ax]:
                ax.clear()
        
        # 1. Gráfico principal de precios con operaciones
        ax1 = plt.subplot(2, 3, (1, 3))  # Ocupa 3 columnas
        ax1.plot(self.df_sorted['exit_time'], self.df_sorted['exit_price'], linewidth=1.5, color='#333333', alpha=0.7, label='Precio de Cierre')
        
        # Marcar operaciones de compra (long)
        long_trades = self.df[self.df['side'] == 'long']
        ax1.scatter(long_trades['entry_time'], long_trades['entry_price'], 
                   color='green', marker='^', s=60, alpha=0.8, label='Entrada Long', zorder=5)
        ax1.scatter(long_trades['exit_time'], long_trades['exit_price'], 
                   color='darkgreen', marker='v', s=60, alpha=0.8, label='Salida Long', zorder=5)
        
        # Marcar operaciones de venta (short)
        short_trades = self.df[self.df['side'] == 'short']
        ax1.scatter(short_trades['entry_time'], short_trades['entry_price'], 
                   color='red', marker='v', s=60, alpha=0.8, label='Entrada Short', zorder=5)
        ax1.scatter(short_trades['exit_time'], short_trades['exit_price'], 
                   color='darkred', marker='^', s=60, alpha=0.8, label='Salida Short', zorder=5)
        
        # Conectar entradas con salidas
        for _, trade in self.df.iterrows():
            color = 'green' if trade['side'] == 'long' else 'red'
            alpha = 0.3 if trade['pnl_usdt'] < 0 else 0.6
            ax1.plot([trade['entry_time'], trade['exit_time']], 
                    [trade['entry_price'], trade['exit_price']], 
                    color=color, alpha=alpha, linewidth=1)
        
        ax1.set_title('💰 OPERACIONES SOBRE PRECIOS DE CIERRE', fontsize=12, fontweight='bold', pad=10)
        ax1.set_ylabel('Precio (USDT)', fontsize=10)
        ax1.tick_params(axis='both', labelsize=9)
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)
        ax1.legend(fontsize=8, loc='upper left')
        
        # 2. Resumen de operaciones por tipo
        ax2 = plt.subplot(2, 3, 4)
        long_count = len(self.df[self.df['side'] == 'long'])
        short_count = len(self.df[self.df['side'] == 'short'])
        long_pnl = self.df[self.df['side'] == 'long']['pnl_usdt'].sum()
        short_pnl = self.df[self.df['side'] == 'short']['pnl_usdt'].sum()
        
        tipos = ['Long', 'Short']
        counts = [long_count, short_count]
        colors = ['#4CAF50', '#F44336']
        
        bars = ax2.bar(tipos, counts, color=colors, alpha=0.7, edgecolor='black', linewidth=0.8)
        ax2.set_title('📊 OPERACIONES POR TIPO', fontsize=10, fontweight='bold', pad=8)
        ax2.set_ylabel('Número de Trades', fontsize=9)
        ax2.tick_params(axis='both', labelsize=8)
        
        # Agregar valores en las barras
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{count}', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        ax2.grid(True, alpha=0.3)
        
        # 3. PnL por tipo de operación
        ax3 = plt.subplot(2, 3, 5)
        pnl_tipos = [long_pnl, short_pnl]
        colors_pnl = ['#4CAF50' if x > 0 else '#F44336' for x in pnl_tipos]
        
        bars = ax3.bar(tipos, pnl_tipos, color=colors_pnl, alpha=0.7, edgecolor='black', linewidth=0.8)
        ax3.axhline(y=0, color='black', linestyle='-', alpha=0.5, linewidth=1)
        ax3.set_title('💵 PnL POR TIPO', fontsize=10, fontweight='bold', pad=8)
        ax3.set_ylabel('PnL (USDT)', fontsize=9)
        ax3.tick_params(axis='both', labelsize=8)
        
        # Agregar valores en las barras
        for bar, pnl in zip(bars, pnl_tipos):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + (5 if height > 0 else -15),
                    f'{pnl:.1f}', ha='center', va='bottom' if height > 0 else 'top', 
                    fontsize=9, fontweight='bold')
        
        ax3.grid(True, alpha=0.3)
        
        # 4. Win Rate por tipo
        ax4 = plt.subplot(2, 3, 6)
        long_wins = len(self.df[(self.df['side'] == 'long') & (self.df['pnl_usdt'] > 0)])
        short_wins = len(self.df[(self.df['side'] == 'short') & (self.df['pnl_usdt'] > 0)])
        long_wr = (long_wins / long_count * 100) if long_count > 0 else 0
        short_wr = (short_wins / short_count * 100) if short_count > 0 else 0
        
        wr_values = [long_wr, short_wr]
        colors_wr = ['#4CAF50', '#F44336']
        
        bars = ax4.bar(tipos, wr_values, color=colors_wr, alpha=0.7, edgecolor='black', linewidth=0.8)
        ax4.set_title('🎯 WIN RATE POR TIPO', fontsize=10, fontweight='bold', pad=8)
        ax4.set_ylabel('Win Rate (%)', fontsize=9)
        ax4.tick_params(axis='both', labelsize=8)
        ax4.set_ylim(0, 100)
        
        # Agregar valores en las barras
        for bar, wr in zip(bars, wr_values):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{wr:.1f}%', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        ax4.grid(True, alpha=0.3)
        
        plt.draw()

def crear_dashboard_interactivo():
    """Función principal para crear el dashboard interactivo"""
    dashboard = DashboardInteractivo()
    return dashboard

if __name__ == "__main__":
    print("🎉 Iniciando Dashboard Interactivo...")
    dashboard = crear_dashboard_interactivo()
    print("📊 Dashboard interactivo creado exitosamente!")
    print("💡 Usa los botones en la parte superior para cambiar entre pestañas")
