import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import CubicSpline  # Модуль для сглаживания кривых
from scipy.stats import linregress

# БЛОК НАСТРОЕК 
excel_file_path = r"c:\Users\USER\OneDrive\Desktop\ЧАААЙ!!!\Таблица значений.xlsx"  # Ваш файл Excel
results_sheet_name = "Итоги с погрешностями"  # Имя финального листа
ignore_sheets = ["Предел чувствительности", "Результаты группировки", "Итоги с погрешностями"]  # Листы, которые не трогаем

# ТОЧНЫЕ ИНДЕКСЫ СТОЛБЦОВ:
cup_col_idx = 0  # Номер кружки (Столбец A)
conc_col_idx = 3  # Концентрация чая (Столбец D)
conc_err_idx = 4  # Погрешность концентрации (Столбец E)
ln_conc_col_idx = 5  # Логарифм концентрации (Столбец F)
ln_conc_err_idx = 6  # Погрешность логарифма (Столбец G)

C_crit = 0.182  # Критический порог концентрации


# ПОЛУЧЕНИЕ И ФИЛЬТРАЦИЯ ЛИСТОВ 
xl = pd.ExcelFile(excel_file_path)
tea_sheets = [sheet for sheet in xl.sheet_names if sheet not in ignore_sheets]
print(f"Обнаружены листы для анализа чая: {tea_sheets}")

# ИНИЦИАЛИЗАЦИЯ ДВУХПАНЕЛЬНОГО ГРАФИКА 
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
summary_results = []

# Палитра цветов для марок чая
colors = plt.colormaps["tab10"].resampled(len(tea_sheets))

#ЦИКЛ ОБРАБОТКИ ЛИСТОВ ЧАЯ 
for idx, sheet in enumerate(tea_sheets):
    df_sheet = pd.read_excel(excel_file_path, sheet_name=sheet)

    # Извлекаем только нужные столбцы по заданным индексам и очищаем от пустых строк
    valid_rows = df_sheet.iloc[
        :,
        [
            cup_col_idx,
            conc_col_idx,
            conc_err_idx,
            ln_conc_col_idx,
            ln_conc_err_idx,
        ],
    ].dropna()

    x_all = valid_rows.iloc[:, 0].values  # Кружки
    y_all = valid_rows.iloc[:, 1].values  # Концентрация
    y_err = valid_rows.iloc[:, 2].values  # Погрешность концентрации

    # Данные для логарифмов (без первой точки)
    x_fit = x_all[1:]
    ln_y_fit = valid_rows.iloc[1:, 3].values  # Готовый логарифм из Excel
    ln_y_err = valid_rows.iloc[1:, 4].values  # Погрешность логарифма из Excel

    current_color = colors(idx)

    # ГРАФИК 1: Концентрация со сглаживанием и крестами погрешностей
    # Наносим точки и кресты погрешностей без жестких соединительных зигзагов
    ax1.errorbar(
        x_all,
        y_all,
        yerr=y_err,
        fmt="o",
        linestyle="None",
        color=current_color,
        ecolor="black",
        elinewidth=1,
        capsize=3,
        ms=3,
        label=sheet,
    )

    # Строим математически сглаженную кривую (сплайн) через экспериментальные точки
    cs = CubicSpline(x_all, y_all)
    x_smooth = np.linspace(
        x_all, x_all[-1], 200
    )  # 200 точек для идеальной плавности линии
    y_smooth = cs(x_smooth)

    # Рисуем саму гладкую линию
    ax1.plot(x_smooth, y_smooth, color=current_color, linewidth=1.5)

    # МАТЕМАТИЧЕСКИЙ РАСЧЕТ (РЕГРЕССИЯ И ЭКСТРАПОЛЯЦИЯ)
    k, b, r_value, p_value, std_err = linregress(x_fit, ln_y_fit)

    ln_C_crit = np.log(C_crit)
    x_critical = (ln_C_crit - b) / k

    # Добавляем результаты анализа текущего листа в общий отчет
    summary_results.append(
        {
            "Марка чая (Лист)": sheet,
            "Коэффициент угасания (k)": round(k, 4),
            "Точность модели (R²)": round(r_value**2, 4),
            "Критическая кружка": round(x_critical, 2),
            "Максимум заварок": int(np.floor(x_critical)),
        }
    )

    # ГРАФИК 2: Логарифмы с усами погрешности + Экстраполяция
    # Рисуем экспериментальные логарифмы из Excel с крестами
    ax2.errorbar(
        x_fit,
        ln_y_fit,
        yerr=ln_y_err,
        fmt="s",
        color=current_color,
        ecolor="black",
        elinewidth=1,
        capsize=3,
        ms=3,
    )

    # Рисуем прямую линию регрессии в будущее до точки пересечения с порогом
    x_extrapolate = np.linspace(2, max(x_fit[-1], x_critical) + 0.5, 100)
    y_extrapolate = k * x_extrapolate + b
    ax2.plot(
        x_extrapolate,
        y_extrapolate,
        linestyle="--",
        color=current_color,
        label=f"{sheet} (расчет)",
    )

#НАСТРОЙКА И ОФОРМЛЕНИЕ ПЕРВОЙ ПАНЕЛИ
ax1.set_title(
    "Сглаженная зависимость концентрации чая от заварки",
    fontsize=11,
    fontweight="bold",
)
ax1.set_xlabel("Номер кружки", fontsize=10)
ax1.set_ylabel("Относительная концентрация чая c, у.е.", fontsize=10)
ax1.grid(True, linestyle=":", alpha=0.5)
ax1.legend(fontsize=9, loc="upper right")

# НАСТРОЙКА И ОФОРМЛЕНИЕ ВТОРОЙ ПАНЕЛИ
ax2.set_title(
    "Экстраполяция логарифма концентрации (без 1-й кружки)",
    fontsize=11,
    fontweight="bold",
)
ax2.set_xlabel("Номер кружки", fontsize=10)
ax2.set_ylabel("Логарифм относительной концентрации lnc, у.е.", fontsize=10)
# Линия критического порога вкуса строится только здесь
ax2.axhline(
    y=np.log(C_crit),
    color="#C44E52",
    linestyle=":",
    linewidth=2,
    label="lnc_crit",
)
ax2.grid(True, linestyle=":", alpha=0.5)
ax2.legend(fontsize=9, loc="upper right")

plt.tight_layout()

# СОХРАНЕНИЕ И ВЫВОД НА ЭКРАН
plt.savefig("tea_errorbars_analysis.png", dpi=300)

df_results = pd.DataFrame(summary_results)
with pd.ExcelWriter(
    excel_file_path, engine="openpyxl", mode="a", if_sheet_exists="replace"
) as writer:
    df_results.to_excel(writer, sheet_name=results_sheet_name, index=False)

print(
    f"\n✔️ Все листы обработаны! Результаты сохранены в лист '{results_sheet_name}'"
)
print("\n СВОДНЫЙ ОТЧЕТ С КРИТИЧЕСКИМИ КРУЖКАМИ")
print(df_results.to_string(index=False))

plt.show()
plt.close()
