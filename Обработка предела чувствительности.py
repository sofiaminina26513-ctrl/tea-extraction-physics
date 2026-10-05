import matplotlib.pyplot as plt  # Главная библиотека для построения графиков
import numpy as np  # Библиотека для математических операций с массивами
import pandas as pd  # Библиотека для работы с таблицами и Excel
from scipy.stats import (
    norm,
)  # Модуль для расчета кривой нормального распределения
import os  # Добавлено для автоматического поиска папки

#БЛОК НАСТРОЕК ФАЙЛОВ
# Автоматически определяем папку, в которой находится запущенный скрипт
current_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in locals() else os.getcwd()

# Файл теперь ищется в той же папке, где лежит этот скрипт (без жестких путей вроде C:\Users\...)
excel_file_path = os.path.join(current_dir, "Таблица значений.xlsx")
source_sheet_name = "Предел чувствительности"
column_name = "lna"  # Точное название столбца с 30 числами в Excel

# Путь для сохранения картинки в ту же папку
output_image_name = os.path.join(current_dir, "пч.png")
new_sheet_name = "Результаты группировки"  # Имя нового листа, который создастся в вашем Excel

#ЗАГРУЗКА ДАННЫХ ИЗ EXCEL
# Загружаем файл Excel в переменную 'df_input'
df_input = pd.read_excel(excel_file_path, sheet_name=source_sheet_name)

# Берем только нужный нам столбец, удаляем пустые ячейки (.dropna())
# и превращаем данные в обычный список чисел (.tolist())
data = df_input[column_name].dropna().tolist()

#ГРУППИРОВКА ДАННЫХ ПО ИНТЕРВАЛАМ
# Задаем вручную границы наших 6 столбцов (всего 7 точек)
bins = [0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35]

# Задаем текстовые подписи для этих интервалов, которые пойдут в таблицу
labels = [
    "от 0.05 до 0.10",
    "от 0.10 до 0.15",
    "от 0.15 до 0.20",
    "от 0.20 до 0.25",
    "от 0.25 до 0.30",
    "от 0.30 до 0.35",
]

# Создаем таблицу в Python для расчетов
df_calc = pd.DataFrame(data, columns=["Концентрация"])

# Разбиваем данные по интервалам. Параметр right=False означает,
# что левая граница входит в интервал, а правая — нет
df_calc["Интервал"] = pd.cut(
    df_calc["Концентрация"], bins=bins, labels=labels, right=False
)

# Считаем, сколько раз значения попали в каждый интервал
table = (
    df_calc["Interval"] if "Interval" in df_calc else df_calc["Интервал"]
).value_counts()
table = table.reindex(labels).reset_index(
    name="Количество человек"
)  # Сортируем по порядку интервалов

# Настраиваем красивую нумерацию строк для Excel (чтобы начиналась с 1, а не с 0)
table.index = table.index + 1
table.index.name = "№ столбца"

#ЗАПИСЬ РЕЗУЛЬТАТОВ ОБРАТНО В EXCEL
# Открываем Excel-файл в режиме добавления ('mode="a"')
# Если лист с таким именем уже существовал, мы его перезапишем ('replace')
with pd.ExcelWriter(
    excel_file_path, engine="openpyxl", mode="a", if_sheet_exists="replace"
) as writer:
    table.to_excel(writer, sheet_name=new_sheet_name)

print(
    f"✔️ Распределенные данные успешно сохранены в {excel_file_path} на лист '{new_sheet_name}'"
)

#ПОСТРОЕНИЕ И ОФОРМЛЕНИЕ ДИАГРАММЫ
# Создаем пустое окно для графика размером 10 на 6 дюймов
plt.figure(figsize=(10, 6))

# Строим гистограмму частот стандартными средствами Matplotlib
plt.hist(
    data,
    bins=bins,
    edgecolor="black",
    color="#4C72B0",
    alpha=0.8,
    label="Измеренные данные (частота)",
)

#ДОБАВЛЕНИЕ МАТЕМАТИЧЕСКОЙ КРИВОЙ ГАУССА
# Автоматически находим среднее значение (mu) и стандартное отклонение (std) ваших данных
mu, std = norm.fit(data)

# Создаем 100 ровных точек на оси X от 0.04 до 0.36, чтобы линия графика была плавной и округлой
x = np.linspace(0.04, 0.36, 100)

# Рассчитываем высоту теоретической кривой нормального распределения для этих 100 точек.
p = norm.pdf(x, mu, std) * len(data) * np.diff(bins)[0]

# Рисуем саму кривую поверх столбцов
plt.plot(
    x,
    p,
    color="#C44E52",
    linewidth=2.5,
    linestyle="--",
    label="Теоретическая кривая Гаусса",
)

#НАСТРОЙКА ОСЕЙ, СЕТКИ И ТЕКСТА
plt.title(
    "Гистограмма распределения пороговой концентрации чая (n=30)",
    fontsize=13,
    fontweight="bold",
    pad=15,
)

plt.xlabel(
    "Пороговая концентрация вкуса (относительные единицы)",
    fontsize=11,
    labelpad=10,
)

plt.ylabel(
    "Частота встречаемости (количество человек)", fontsize=11, labelpad=10
)

plt.xticks(bins, fontsize=10)
plt.yticks(range(0, 11, 1), fontsize=10)
plt.grid(axis="y", linestyle=":", alpha=0.5)
plt.legend(loc="upper right", fontsize=10)

plt.tight_layout()

# СОХРАНЕНИЕ ГРАФИКА
plt.savefig(output_image_name, dpi=300)

# Выводим график на экран в интерактивном окне
plt.show()

# Закрываем сессию построения, чтобы очистить оперативную память компьютера
plt.close()

print(
    f"✔️ График успешно сгенерирован и сохранен в высоком качестве: {output_image_name}"
)

