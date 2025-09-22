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
    def __init__(self, symbol='BTC/USDT:USDT'):
        self.symbol = symbol
        self.df = None
        self.metricas = {}
        self.cargar_datos()
        self.crear_dashboard()
    
    def cargar_datos(self):
        """Carga y procesa los datos del backtesting"""
        # Construir nombre del archivo basado en el símbolo
        symbol_slug = self.symbol.replace('/', '_').replace(':', '_')
        filename = f'trades_final_{symbol_slug}.csv'
        
        try:
            self.df = pd.read_csv(filename)
        except FileNotFoundError:
            # Si no existe archivo específico, usar el genérico
            self.df = pd.read_csv('trades_final.csv')
            # Validar si existe columna symbol
            if 'symbol' in self.df.columns:
                self.df = self.df[self.df['symbol'] == self.symbol]
            else:
                print(f"⚠️ ADVERTENCIA: El archivo 'trades_final.csv' no contiene columna 'symbol'")
                print(f"📊 Mostrando datos para {self.symbol} sin filtrado por símbolo")
                print(f"💡 Considera agregar columna 'symbol' al CSV para filtrado automático")
        
        # Validar si hay datos para el símbolo
        if len(self.df) == 0:
            print(f"❌ ERROR: No se encontraron operaciones para el símbolo {self.symbol}")
            print(f"📊 Verifica que el archivo CSV contenga datos para este símbolo")
            # Crear métricas vacías para evitar errores
            self.metricas = {
                'total_trades': 0,
                'trades_ganadores': 0,
                'trades_perdedores': 0,
                'win_rate': 0,
                'pnl_total': 0,
                'pnl_promedio': 0,
                'r_multiple_promedio': 0,
                'max_drawdown': 0
            }
            return
        
        self.df['entry_time'] = pd.to_datetime(self.df['entry_time'])
        self.df['exit_time'] = pd.to_datetime(self.df['exit_time'])
        self.df['day_key'] = pd.to_datetime(self.df['day_key'])
        
        # Calcular métricas
        self.metricas['total_trades'] = len(self.df)
        self.metricas['trades_ganadores'] = len(self.df[self.df['pnl_usdt'] > 0])
        self.metricas['trades_perdedores'] = len(self.df[self.df['pnl_usdt'] < 0])
        self.metricas['win_rate'] = (self.metricas['trades_ganadores'] / self.metricas['total_trades']) * 100 if self.metricas['total_trades'] > 0 else 0
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
        self.fig.suptitle(f'📊 DASHBOARD COMPLETO - BACKTESTING {self.symbol} 1TPD', fontsize=14, fontweight='bold', y=0.95)
        
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
        
        # Selector de símbolos
        ax_symbol = plt.axes([0.55, 0.92, 0.15, 0.05])
        self.symbols = ['BTC/USDT:USDT', 'ETH/USDT:USDT', 'ADA/USDT:USDT', 'SOL/USDT:USDT']
        self.radio_symbols = widgets.RadioButtons(ax_symbol, self.symbols, active=self.symbols.index(self.symbol) if self.symbol in self.symbols else 0)
        self.radio_symbols.on_clicked(self.cambiar_simbolo)
        
        # Lista de ejes de botones para conservar al limpiar
        self.axes_botones = [self.btn_principal.ax, self.btn_detallado.ax, self.btn_precios.ax, self.radio_symbols.ax]
    
    def crear_area_graficos(self):
        """Crea el área donde se mostrarán los gráficos"""
        # Definir GridSpecs para cada pestaña
        # Pestaña Principal: 3 filas, 2 columnas (equity curve, drawdown, métricas y análisis)
        self.gs_principal = self.fig.add_gridspec(3, 2, width_ratios=[2, 1], height_ratios=[3, 1, 1], 
                                                 hspace=0.3, wspace=0.2)
        
        # Pestaña Detallado: 2 filas, 3 columnas uniformes
        self.gs_detallado = self.fig.add_gridspec(2, 3, height_ratios=[3, 2], 
                                                 hspace=0.3, wspace=0.2)
        
        # Pestaña Precios: 3 filas, 3 columnas (precio, drawdown, resúmenes)
        self.gs_precios = self.fig.add_gridspec(3, 3, width_ratios=[1, 1, 1], height_ratios=[3, 1, 1], 
                                                 hspace=0.3, wspace=0.2)
    
    def mostrar_pestaña_principal(self, event=None):
        """Muestra la pestaña principal"""
        # Obtener lista de ejes a remover y eliminarlos completamente
        axes_to_remove = [ax for ax in self.fig.axes if ax not in self.axes_botones]
        for ax in axes_to_remove:
            ax.remove()
        
        # 1. Equity Curve (fila superior, primera columna)
        ax1 = self.fig.add_subplot(self.gs_principal[0, 0])
        ax1.plot(self.df_sorted['exit_time'], self.df_sorted['pnl_acumulado'], linewidth=2, color='#2E8B57', alpha=0.8)
        ax1.fill_between(self.df_sorted['exit_time'], self.df_sorted['pnl_acumulado'], alpha=0.3, color='#2E8B57')
        ax1.axhline(y=0, color='red', linestyle='--', alpha=0.7, linewidth=1.5)
        ax1.set_title('💰 EQUITY CURVE', fontsize=12, fontweight='bold', pad=10)
        ax1.set_ylabel('PnL Acumulado (USDT)', fontsize=10)
        ax1.tick_params(axis='both', labelsize=9)
        ax1.grid(True, alpha=0.3)
        ax1.tick_params(axis='x', rotation=45)
        
        # 2. Métricas (fila superior, columna derecha)
        ax2 = self.fig.add_subplot(self.gs_principal[0, 1])
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
        ax2.text(0.05, 0.95, metricas_texto, transform=ax2.transAxes, fontsize=9, 
                 verticalalignment='top', fontfamily='monospace',
                 bbox=dict(boxstyle="round,pad=0.4", facecolor='lightblue', alpha=0.9))
        
        # 3. Resumen de operaciones por tipo (fila media, primera columna)
        ax3 = self.fig.add_subplot(self.gs_principal[1, 0])
        long_count = len(self.df[self.df['side'] == 'long'])
        short_count = len(self.df[self.df['side'] == 'short'])
        
        tipos = ['Long', 'Short']
        counts = [long_count, short_count]
        colors = ['#4CAF50', '#F44336']
        
        bars = ax3.bar(tipos, counts, color=colors, alpha=0.7, edgecolor='black', linewidth=0.8)
        ax3.set_title('📊 OPERACIONES POR TIPO', fontsize=10, fontweight='bold', pad=8)
        ax3.set_ylabel('Número de Trades', fontsize=9)
        ax3.tick_params(axis='both', labelsize=8)
        
        # Agregar valores en las barras
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{count}', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        ax3.grid(True, alpha=0.3)
        
        # 4. PnL por tipo (fila media, columna derecha)
        ax4 = self.fig.add_subplot(self.gs_principal[1, 1])
        long_pnl = self.df[self.df['side'] == 'long']['pnl_usdt'].sum()
        short_pnl = self.df[self.df['side'] == 'short']['pnl_usdt'].sum()
        
        pnl_tipos = [long_pnl, short_pnl]
        colors_pnl = ['#4CAF50' if x > 0 else '#F44336' for x in pnl_tipos]
        
        bars = ax4.bar(tipos, pnl_tipos, color=colors_pnl, alpha=0.7, edgecolor='black', linewidth=0.8)
        ax4.axhline(y=0, color='black', linestyle='-', alpha=0.5, linewidth=1)
        ax4.set_title('💰 PnL POR TIPO', fontsize=10, fontweight='bold', pad=8)
        ax4.set_ylabel('PnL (USDT)', fontsize=9)
        ax4.tick_params(axis='both', labelsize=8)
        
        # Agregar valores en las barras
        for bar, pnl in zip(bars, pnl_tipos):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + (5 if height > 0 else -15),
                    f'{pnl:.1f}', ha='center', va='bottom' if height > 0 else 'top', 
                    fontsize=9, fontweight='bold')
        
        ax4.grid(True, alpha=0.3)
        
        # 5. R-múltiples (fila inferior, izquierda)
        ax5 = self.fig.add_subplot(self.gs_principal[2, 0])
        bins = np.arange(-2, 3, 0.5)
        ax5.hist(self.df['r_multiple'], bins=bins, alpha=0.7, color='#FF6B6B', edgecolor='black', linewidth=0.6)
        ax5.axvline(x=0, color='red', linestyle='--', alpha=0.7, linewidth=1.2)
        ax5.axvline(x=self.metricas['r_multiple_promedio'], color='green', linestyle='-', linewidth=1.2, 
                   label=f'Prom: {self.metricas["r_multiple_promedio"]:.2f}')
        ax5.set_title('📈 R-MÚLTIPLES', fontsize=10, fontweight='bold', pad=8)
        ax5.set_xlabel('R-Múltiple', fontsize=9)
        ax5.set_ylabel('Frecuencia', fontsize=9)
        ax5.tick_params(axis='both', labelsize=8)
        ax5.legend(fontsize=8)
        ax5.grid(True, alpha=0.3)
        
        # 6. Ganadores vs Perdedores (fila inferior, derecha)
        ax6 = self.fig.add_subplot(self.gs_principal[2, 1])
        labels = ['Ganadores', 'Perdedores']
        sizes = [self.metricas['trades_ganadores'], self.metricas['trades_perdedores']]
        colors = ['#4CAF50', '#F44336']
        wedges, texts, autotexts = ax6.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', 
                                          startangle=90, textprops={'fontsize': 9})
        ax6.set_title('🎯 GANADORES VS PERDEDORES', fontsize=10, fontweight='bold', pad=8)
        
        # Ajustar layout
        self.fig.tight_layout()
        self.fig.subplots_adjust(top=0.88, bottom=0.1, left=0.05, right=0.95)
        plt.draw()
    
    def mostrar_pestaña_detallado(self, event=None):
        """Muestra la pestaña detallado"""
        # Obtener lista de ejes a remover y eliminarlos completamente
        axes_to_remove = [ax for ax in self.fig.axes if ax not in self.axes_botones]
        for ax in axes_to_remove:
            ax.remove()
        
        # 1. PnL por Trade (ocupa 2 columnas en fila superior)
        ax1 = self.fig.add_subplot(self.gs_detallado[0, :2])
        colores_pnl = ['#4CAF50' if x > 0 else '#F44336' for x in self.df['pnl_usdt']]
        ax1.bar(range(len(self.df)), self.df['pnl_usdt'], color=colores_pnl, alpha=0.7, edgecolor='black', linewidth=0.2)
        ax1.axhline(y=0, color='black', linestyle='-', alpha=0.5, linewidth=1.2)
        ax1.set_title('💵 PnL POR TRADE', fontsize=12, fontweight='bold', pad=10)
        ax1.set_xlabel('Número de Trade', fontsize=10)
        ax1.set_ylabel('PnL (USDT)', fontsize=10)
        ax1.tick_params(axis='both', labelsize=9)
        ax1.grid(True, alpha=0.3)
        
        # 2. Drawdown compacto (fila superior, columna derecha)
        ax2 = self.fig.add_subplot(self.gs_detallado[0, 2])
        ax2.fill_between(self.df_sorted['exit_time'], self.df_sorted['drawdown'], alpha=0.7, color='#FF4444')
        ax2.axhline(y=self.metricas['max_drawdown'], color='darkred', linestyle='--', alpha=0.8, linewidth=1.5,
                   label=f'Max DD: {self.metricas["max_drawdown"]:.2f}')
        ax2.set_title('📉 DRAWDOWN', fontsize=10, fontweight='bold', pad=8)
        ax2.set_ylabel('Drawdown (USDT)', fontsize=9)
        ax2.tick_params(axis='both', labelsize=8)
        ax2.tick_params(axis='x', rotation=45)
        ax2.legend(fontsize=8)
        ax2.grid(True, alpha=0.3)
        
        # 3. Trades por día (fila inferior, izquierda)
        ax3 = self.fig.add_subplot(self.gs_detallado[1, 0])
        self.df['dia_semana'] = self.df['entry_time'].dt.day_name()
        dias_orden = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        dias_espanol = ['L', 'M', 'X', 'J', 'V', 'S', 'D']
        trades_por_dia = self.df['dia_semana'].value_counts().reindex(dias_orden, fill_value=0)
        colores = plt.cm.Set3(np.linspace(0, 1, len(trades_por_dia)))
        bars = ax3.bar(dias_espanol, trades_por_dia.values, color=colores, alpha=0.8, edgecolor='black', linewidth=0.6)
        ax3.set_title('📅 TRADES POR DÍA', fontsize=10, fontweight='bold', pad=8)
        ax3.set_ylabel('Número', fontsize=9)
        ax3.tick_params(axis='both', labelsize=8)
        ax3.grid(True, alpha=0.3)
        
        # 4. Trades por mes (fila inferior, centro)
        ax4 = self.fig.add_subplot(self.gs_detallado[1, 1])
        self.df['mes'] = self.df['entry_time'].dt.to_period('M')
        trades_por_mes = self.df['mes'].value_counts().sort_index()
        meses_str = [str(mes) for mes in trades_por_mes.index]
        colores_mes = plt.cm.viridis(np.linspace(0, 1, len(trades_por_mes)))
        bars = ax4.bar(meses_str, trades_por_mes.values, color=colores_mes, alpha=0.8, edgecolor='black', linewidth=0.6)
        ax4.set_title('📅 TRADES POR MES', fontsize=10, fontweight='bold', pad=8)
        ax4.set_ylabel('Número', fontsize=9)
        ax4.tick_params(axis='both', labelsize=8)
        ax4.tick_params(axis='x', rotation=45)
        ax4.grid(True, alpha=0.3)
        
        # 5. Distribución PnL (fila inferior, centro)
        ax5 = self.fig.add_subplot(self.gs_detallado[1, 1])
        ax5.hist(self.df['pnl_usdt'], bins=12, alpha=0.7, color='#9C27B0', edgecolor='black', linewidth=0.6)
        ax5.axvline(x=0, color='red', linestyle='--', alpha=0.7, linewidth=1.2)
        ax5.axvline(x=self.metricas['pnl_promedio'], color='green', linestyle='-', linewidth=1.2, 
                   label=f'Prom: {self.metricas["pnl_promedio"]:.2f}')
        ax5.set_title('📊 DISTRIBUCIÓN PnL', fontsize=10, fontweight='bold', pad=8)
        ax5.set_xlabel('PnL (USDT)', fontsize=9)
        ax5.set_ylabel('Frecuencia', fontsize=9)
        ax5.tick_params(axis='both', labelsize=8)
        ax5.legend(fontsize=8)
        ax5.grid(True, alpha=0.3)
        
        # 6. Duración de trades (fila inferior, derecha)
        ax6 = self.fig.add_subplot(self.gs_detallado[1, 2])
        self.df['duracion_horas'] = (self.df['exit_time'] - self.df['entry_time']).dt.total_seconds() / 3600
        ax6.hist(self.df['duracion_horas'], bins=10, alpha=0.7, color='#FF9800', edgecolor='black', linewidth=0.6)
        ax6.axvline(x=self.df['duracion_horas'].mean(), color='red', linestyle='-', linewidth=1.2, 
                   label=f'Prom: {self.df["duracion_horas"].mean():.1f}h')
        ax6.set_title('⏱️ DURACIÓN TRADES', fontsize=10, fontweight='bold', pad=8)
        ax6.set_xlabel('Duración (horas)', fontsize=9)
        ax6.set_ylabel('Frecuencia', fontsize=9)
        ax6.tick_params(axis='both', labelsize=8)
        ax6.legend(fontsize=8)
        ax6.grid(True, alpha=0.3)
        
        # Ajustar layout
        self.fig.tight_layout()
        self.fig.subplots_adjust(top=0.88, bottom=0.1, left=0.05, right=0.95)
        plt.draw()
    
    def mostrar_pestaña_precios(self, event=None):
        """Muestra la pestaña de precios con operaciones"""
        # Obtener lista de ejes a remover y eliminarlos completamente
        axes_to_remove = [ax for ax in self.fig.axes if ax not in self.axes_botones]
        for ax in axes_to_remove:
            ax.remove()
        
        # 1. Gráfico principal de precios con operaciones (fila superior completa)
        ax1 = self.fig.add_subplot(self.gs_precios[0, :])
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
        
        # 2. Drawdown (fila media completa)
        ax2 = self.fig.add_subplot(self.gs_precios[1, :])
        ax2.fill_between(self.df_sorted['exit_time'], self.df_sorted['drawdown'], alpha=0.7, color='#FF4444')
        ax2.axhline(y=self.metricas['max_drawdown'], color='darkred', linestyle='--', alpha=0.8, linewidth=2,
                   label=f'Max DD: {self.metricas["max_drawdown"]:.2f} USDT')
        ax2.set_title('📉 DRAWDOWN', fontsize=10, fontweight='bold', pad=8)
        ax2.set_ylabel('Drawdown (USDT)', fontsize=9)
        ax2.tick_params(axis='both', labelsize=8)
        ax2.tick_params(axis='x', rotation=45)
        ax2.legend(fontsize=8)
        ax2.grid(True, alpha=0.3)
        
        # 3. Resumen de operaciones por tipo (fila inferior, izquierda)
        ax3 = self.fig.add_subplot(self.gs_precios[2, 0])
        long_count = len(self.df[self.df['side'] == 'long'])
        short_count = len(self.df[self.df['side'] == 'short'])
        long_pnl = self.df[self.df['side'] == 'long']['pnl_usdt'].sum()
        short_pnl = self.df[self.df['side'] == 'short']['pnl_usdt'].sum()
        
        tipos = ['Long', 'Short']
        counts = [long_count, short_count]
        colors = ['#4CAF50', '#F44336']
        
        bars = ax3.bar(tipos, counts, color=colors, alpha=0.7, edgecolor='black', linewidth=0.8)
        ax3.set_title('📊 OPERACIONES POR TIPO', fontsize=10, fontweight='bold', pad=8)
        ax3.set_ylabel('Número de Trades', fontsize=9)
        ax3.tick_params(axis='both', labelsize=8)
        
        # Agregar valores en las barras
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                    f'{count}', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        ax3.grid(True, alpha=0.3)
        
        # 4. PnL por tipo de operación (fila inferior, centro)
        ax4 = self.fig.add_subplot(self.gs_precios[2, 1])
        pnl_tipos = [long_pnl, short_pnl]
        colors_pnl = ['#4CAF50' if x > 0 else '#F44336' for x in pnl_tipos]
        
        bars = ax4.bar(tipos, pnl_tipos, color=colors_pnl, alpha=0.7, edgecolor='black', linewidth=0.8)
        ax4.axhline(y=0, color='black', linestyle='-', alpha=0.5, linewidth=1)
        ax4.set_title('💵 PnL POR TIPO', fontsize=10, fontweight='bold', pad=8)
        ax4.set_ylabel('PnL (USDT)', fontsize=9)
        ax4.tick_params(axis='both', labelsize=8)
        
        # Agregar valores en las barras
        for bar, pnl in zip(bars, pnl_tipos):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + (5 if height > 0 else -15),
                    f'{pnl:.1f}', ha='center', va='bottom' if height > 0 else 'top', 
                    fontsize=9, fontweight='bold')
        
        ax4.grid(True, alpha=0.3)
        
        # 5. Win Rate por tipo (fila inferior, derecha)
        ax5 = self.fig.add_subplot(self.gs_precios[2, 2])
        long_wins = len(self.df[(self.df['side'] == 'long') & (self.df['pnl_usdt'] > 0)])
        short_wins = len(self.df[(self.df['side'] == 'short') & (self.df['pnl_usdt'] > 0)])
        long_wr = (long_wins / long_count * 100) if long_count > 0 else 0
        short_wr = (short_wins / short_count * 100) if short_count > 0 else 0
        
        wr_values = [long_wr, short_wr]
        colors_wr = ['#4CAF50', '#F44336']
        
        bars = ax5.bar(tipos, wr_values, color=colors_wr, alpha=0.7, edgecolor='black', linewidth=0.8)
        ax5.set_title('🎯 WIN RATE POR TIPO', fontsize=10, fontweight='bold', pad=8)
        ax5.set_ylabel('Win Rate (%)', fontsize=9)
        ax5.tick_params(axis='both', labelsize=8)
        ax5.set_ylim(0, 100)
        
        # Agregar valores en las barras
        for bar, wr in zip(bars, wr_values):
            height = bar.get_height()
            ax5.text(bar.get_x() + bar.get_width()/2., height + 1,
                    f'{wr:.1f}%', ha='center', va='bottom', fontsize=9, fontweight='bold')
        
        ax5.grid(True, alpha=0.3)
        
        # Ajustar layout
        self.fig.tight_layout()
        self.fig.subplots_adjust(top=0.88, bottom=0.1, left=0.05, right=0.95)
        plt.draw()
    
    def cambiar_simbolo(self, label):
        """Cambia el símbolo y recarga los datos"""
        self.symbol = label
        self.cargar_datos()
        
        # Actualizar título
        self.fig.suptitle(f'📊 DASHBOARD COMPLETO - BACKTESTING {self.symbol} 1TPD', fontsize=14, fontweight='bold', y=0.95)
        
        # Refrescar pestaña activa (asumiendo que la principal está activa)
        self.mostrar_pestaña_principal()

def crear_dashboard_interactivo():
    """Función principal para crear el dashboard interactivo"""
    dashboard = DashboardInteractivo()
    return dashboard

if __name__ == "__main__":
    print("🎉 Iniciando Dashboard Interactivo...")
    dashboard = crear_dashboard_interactivo()
    print("📊 Dashboard interactivo creado exitosamente!")
    print("💡 Usa los botones en la parte superior para cambiar entre pestañas")
