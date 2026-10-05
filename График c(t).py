# ИМПОРТ БИБЛИОТЕК (Инструменты для работы программы)
import pandas as pd                   # Библиотека для загрузки и работы с Excel таблицами
import numpy as np                    # Библиотека для математических функций (логарифм, экспонента)
import matplotlib.pyplot as plt       # Библиотека для построения графиков и рисунков
import statsmodels.api as sm          # Библиотека для математического сглаживания LOWESS
from scipy.optimize import curve_fit  # Библиотека для подгонки теоретической экспоненты
import os                             # Библиотека для работы с путями (автоопределение папки)

# ОПРЕДЕЛЕНИЕ МАТЕМАТИЧЕСКОЙ МОДЕЛИ
# Функция идеальной экспоненты насыщения: C(t) = C_max * (1 - e^(-k * t))
def expo_model (t, C_max, k):
    return C_max * (1 - np.exp(-k * t))

# НАСТРОЙКА ПУТЕЙ (Относительный путь для репозитория)
current_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()
excel_file = os.path.join(current_dir, "Дополнительные  значения.xlsx")

t_col = "t, c"             # Название колонки с временем
I_col = "I, мА"           # Название колонки с током
x_error = 0.5             # Фиксированная погрешность времени по оси X (0.5 секунды)

# ==============================================================================
# КОНФИГУРАЦИЯ НАСТРОЕК ДЛЯ КАЖДОГО ЛИСТА
# Здесь прописаны индивидуальные константы для формул обработки листов n=1 и n=2
# ==============================================================================
sheets_config = {
    "n=1": {
        "I_start": 2.22,
        "I_end": 1.43,
        "title": "Зависимость c(t) при первой заварке (n=1)",
        "output_image": "n1_final1.png",
        "result_sheet": "Результаты n=1"
    },
    "n=2": {
        "I_start": 2.15,
        "I_end": 1.60,
        "title": "Зависимость c(t) при второй заварке (n=2)",
        "output_image": "n2_final2.png",
        "result_sheet": "Результаты n=2"
    }
}

# ==============================================================================
# ОСНОВНОЙ ЦИКЛ ОБРАБОТКИ ДАННЫХ
# ==============================================================================
for sheet_name, cfg in sheets_config.items():
    print(f"\n--- Обработка листа: {sheet_name} ---")
    
    try:
        # 1. ЗАГРУЗКА И ПОДГОТОВКА ДАННЫХ
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        df = df.sort_values(by=t_col).reset_index(drop=True)
        
        # 2. ПЕРЕСЧЕТ С ЛОГАРИФМОМ И ВЫЧИСЛЕНИЕ ПОГРЕШНОСТЕЙ ПО ИНДИВИДУАЛЬНЫМ ФОРМУЛАМ
        I0 = cfg["I_start"]
        Ik = cfg["I_end"]
        
        # Индивидуальная формула концентрации для текущего листа
        df['c'] = np.log(df[I_col] / I0) / np.log(Ik / I0) * 100
        
        # Расчет погрешности по оси Y
        df["delta c"] = df['c'] * (0.01 / df[I_col] + 0.01 / I0)

        # 3. МАТЕМАТИЧЕСКОЕ СГЛАЖИВАНИЕ (LOWESS) И ЭКСПОНЕНТА
        lowess = sm.nonparametric.lowess
        smoothed_data = lowess(df["c"], df[t_col], frac=0.5)
        df["smooth c"] = smoothed_data[:, 1]

        # Подгонка идеальной экспоненты
        popt, _ = curve_fit(expo_model, df[t_col], df["c"], p0=[100, 0.05])
        C_max_opt, k_opt = popt

        # Сетка для построения плавной теоретической кривой
        t_smooth = np.linspace(df[t_col].min(), df[t_col].max(), 300)
        c_expo_smooth = expo_model(t_smooth, C_max_opt, k_opt)

        # 4. ПОСТРОЕНИЕ И ОФОРМЛЕНИЕ ГРАФИКА
        fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
        fig.subplots_adjust(left=0.15, bottom=0.12, right=0.95, top=0.90)

        # Экспериментальные точки
        plt.errorbar(
            df[t_col], df["c"], 
            xerr=x_error,                   
            yerr=df["delta c"],             
            fmt='o',                        
            color="#8B4513",                
            ecolor="#A0522D",               
            elinewidth=1.5,                 
            capsize=2,                      
            ms=2,                           
            zorder=5,                       
            label="Рассчитанная концентрация с погрешностью"
        )

        # Сглаженный тренд LOWESS
        plt.plot(df[t_col], df["smooth c"], color="#D2691E", linewidth=1.5, zorder=4, label="Сглаженный тренд")

        # Теоретическая экспонента
        plt.plot(t_smooth, c_expo_smooth, 
                 color="#00008B", linewidth=1, linestyle="--", zorder=3, 
                 label=f"Идеальная экспонента ($t$={1/k_opt:.1f} c)")

        # Подписи и заголовки
        plt.title(cfg["title"], fontsize=14, fontweight='bold', pad=15)
        plt.xlabel('Время t, c', fontsize=12)
        plt.ylabel('Концентрация с, % от насыщения', fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.6) 
        plt.legend()

        # 5. СОХРАНЕНИЕ ГРАФИКА И РЕЗУЛЬТАТОВ
        img_path = os.path.join(current_dir, cfg["output_image"])
        plt.savefig(img_path, bbox_inches="tight")
        print(f"✅ График сохранен как: {img_path}")
        plt.close() # Закрываем текущую фигуру, чтобы графики не накладывались в памяти

        # Дописываем результаты расчетов на новый лист в тот же Excel-файл
        with pd.ExcelWriter(excel_file, mode="a", engine="openpyxl", if_sheet_exists="replace") as writer:
            df.to_excel(writer, sheet_name=cfg["result_sheet"], index=False)
        print(f"✅ Расчеты сохранены в Excel на лист '{cfg['result_sheet']}'")

    except Exception as e:
        print(f"❌ Ошибка при обработке листа {sheet_name}: {e}")

# Финальный показ всех графиков (если код запускается интерактивно)
print("\n🎉 Все листы успешно обработаны!")
