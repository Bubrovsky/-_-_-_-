"""
Данный код представляет несколько расширенную версию To-Do листа (списка задач)
Изначально планировалось создать что-то типа аналога Notion, однако далее курс сменился на лаконичность и упрощение интерфейса
для выполнения первостепенной задачи без лишних нагромождений, а именно:
1. формулировка задачи и установка ее приоритетности;
2. установка дедлайна;
3. отметка "дня с делами" в календаре;
4. возможность отмечать выполненные дедлайны в одно касание;
Также было сделано следующее:)
- подобие функционала "сохранить" и "сохранить как" (через проводник) -- полезно для переноса данных с устройства на устройство офлайн
- вывод статистики выполненных / невыполненных задач (общая и по отсортированная по приоритетности)
"""

# Импортируем необходимые модули
import customtkinter as ctk
from tkinter import messagebox as mb
from tkinter import filedialog as fd
from tkcalendar import Calendar
from datetime import datetime
import json
import matplotlib.pyplot as plt

# Устанавливаем изначальную тему приложения
ctk.set_appearance_mode("system") # Есть вариант также выставить темную ("dark"), или светлую ("light") тему окна
ctk.set_default_color_theme("green") # Установка цвета основных интерактивных элементов предлагает следующие варианты:
                                                                #голубой ("blue"), синий("dark-blue"), зеленый("green")

class App:
    def __init__(self, root):
        # Инициализируем главное окно приложения
        self.root = root
        self.root.title("DoNote") # Задаем название окну
        self.tasks = []# Создаем список для вводимых задач, которые необходимо выполнить
        self.load_tasks()
        self.root.geometry("950x600") # Создаем дефолтное рназрешение для окна приложения
        self.create_widgets()
        self.update_display()
        self.update_calendar_markings()

        # Немного кастомизации:
        # Как было отмечено выше, CustomTkInter предлагает возможность менять тему отображаемого окна -
        # сделаем эту возможность доступной для пользователя через интерфейс самого приложения
        self.theme_switch = ctk.StringVar(value="off")
        self.switch_mode = ctk.CTkSwitch(self.root, text="Тёмная тема", font=("Calibri Light", 12, "bold"),variable=self.theme_switch, onvalue="on", offvalue="off",
            command=self.change_appearance_mode_event)
        self.switch_mode.pack(padx=10, pady=20)

    def create_widgets(self):
        # Раздеол с элементами интерфейса
        input_frame = ctk.CTkFrame(self.root)
        input_frame.pack(side='left', padx=(10, 5), pady=(20, 10), fill='y')

        self.input_label = ctk.CTkLabel(input_frame, text="Введите задачу:", font=("Bahnschrift", 16, "bold")) # Статичный (неинтерактивный) элемент
        self.input_label.pack(pady=(5, 0))
        self.task_input = ctk.CTkEntry(input_frame, width=250, font=("Calibri Light", 14)) # Поле для ввода задачи
        self.task_input.pack(pady=(0, 10))

        # Чтобы выбрать планируемую дату (крайний срок) - добавляем календарь в поле ввода задач
        self.calendar = Calendar(input_frame)
        self.calendar.pack(pady=(10, 10))

        self.prior_label = ctk.CTkLabel(input_frame, text="Выберите приоритет:", font=("Bahnschrift", 16, "bold")) # Статичный элемент
        self.prior_label.pack(pady=(10, 0))
        self.priority_var = ctk.StringVar(value="опциональная задача") # Дефолтное значение, которое будет выбрано среди всех вариантов приоритета с помощью CTkRadioButton

        # Создаем "варианты" для выбора приоритета с помощью CTkRadioButton
        for prior in ["опциональная задача", "низкий", "средний", "высокий", "обязательная задача"]:
            ch_prior = ctk.CTkRadioButton(input_frame, text=prior, variable=self.priority_var, value=prior, font=("Calibri Light", 14))
            ch_prior.pack(anchor='w')

        # Создаем раздел для ввода точного времени
        self.time_label = ctk.CTkLabel(input_frame, text="Время (ЧЧ:ММ):", font=("Bahnschrift", 16, "bold"))
        self.time_label.pack(pady=(10, 0))

        time_frame = ctk.CTkFrame(input_frame)
        time_frame.pack(pady=(0, 10))

        # Создаем поля для ввода "часов" и "минут"
        self.hours_input = ctk.CTkEntry(time_frame, width=50, font=("Arial", 14, "bold"))
        self.hours_input.pack(side="left", padx=(0, 5))
        self.minutes_input = ctk.CTkEntry(time_frame, width=50, font=("Arial", 14, "bold"))
        self.minutes_input.pack(side="left", padx=(5, 0))

        # Сощдаем поле с задачами + также не забываем о том, что задачи могут не поместиться в статичном окне -
        # добавляем прокрутку на колесо мыши
        self.task_frame = ctk.CTkScrollableFrame(self.root)
        self.task_frame.pack(side='left', padx=5, pady=10, fill='both', expand=True)

        # Создаем кнопку добавления задачи в список
        self.add_button = ctk.CTkButton(input_frame, text="Добавить задачу", command=self.add_task, font=("Bahnschrift", 14, "bold"))
        self.add_button.pack(pady=(10, 5))

        # Создаем кнопку "сохранить"
        self.save_tasks_button = ctk.CTkButton(self.root, text="Сохранить задачи", command=self.save_tasks, font=("Bahnschrift", 14, "bold"))
        self.save_tasks_button.pack(pady=(5, 5))

        # Создаем кнопку сохранения файла через проводник
        self.save_to_file_button = ctk.CTkButton(self.root, text="Сохранить в файле", command=self.save_to_file, font=("Bahnschrift", 14, "bold"))
        self.save_to_file_button.pack(pady=(5, 5))

        # Создаем кнопку загрузки .json-файла через проводник
        self.load_button = ctk.CTkButton(self.root, text="Загрузить из файла", command=self.load_from_file, font=("Bahnschrift", 14, "bold"))
        self.load_button.pack(pady=(5, 5))

        # Создаем небольшой раздел для элементов статистики (диаграммы)
        self.stats_frame = ctk.CTkFrame(self.root)
        self.stats_frame.pack(pady=(5, 5))

        self.stat_choice = ctk.StringVar(value="None") # Поскольку CTkRadioButton используется только "для красоты" - для однородности выставляем нулевое значение первоначально отмеченной кнопки
        # Кнопка для отображения общей статистики выполненных / невыполненных задач
        self.com_stat = ctk.CTkRadioButton(self.stats_frame, variable=self.stat_choice, value="common", font=("Calibri Light", 14, "bold"), text="Общая статистика", command=self.show_stats)
        self.com_stat.pack(anchor='w')

        # Кнопка для отображения выполненных / невыполненных задач по их приоритетности
        self.prior_stat = ctk.CTkRadioButton(self.stats_frame, variable=self.stat_choice, value="priority", font=("Calibri Light", 14, "bold"), text="По степени важности", command=self.show_stats)
        self.prior_stat.pack(anchor='w')

    def add_task(self):
        task_text = self.task_input.get()
        priority = self.priority_var.get()
        hour = self.hours_input.get()
        minute = self.minutes_input.get()
        due_date = self.calendar.get_date()

        due_time = f"{due_date} {hour.zfill(2)}:{minute.zfill(2)}"

        # Чтобы даты в календаре, на которые есть задачи, отображались цветом, необходимо преобразовать данные по времени для datetime
        due_timestamp = datetime.strptime(due_time, "%m/%d/%y %H:%M")

        # Собираем все введенные данные в словарь для единообразия вводимых данных
        task = {
            "text": task_text,
            "priority": priority,
            "due_time": due_time,
            "status": False,
            "due_timestamp": due_timestamp
        }

        self.tasks.append(task)
        self.update_display()
        self.clear_entries()
        self.update_statistics()
        self.update_calendar_markings()

        # Создаем функции для отображения диаграмм по статистике выполненных / невыполненных задач
    def show_stats(self):
        if self.stat_choice.get() == "common":
            self.general_stats()
        else:
            self.prior_stats()

    def general_stats(self):
        completed_tasks = sum(1 for task in self.tasks if task["status"])
        total_tasks = len(self.tasks)
        not_completed_tasks = total_tasks - completed_tasks
        labels = ['Выполненные задачи', 'Невыполненные задачи'] # Разделяем по двум параметрам: "выполнено" - "не выполнено"
        sizes = [completed_tasks, not_completed_tasks]
        colors = ['skyblue', 'salmon']

        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%', startangle=140)
        plt.axis('equal')
        plt.title('Соотношение выполненных и невыполненных задач')
        plt.show()

    def prior_stats(self):
        priorities = ["опциональная задача", "низкий", "средний", "высокий", "обязательная задача"]
        completed_counts = [sum(1 for task in self.tasks if task["priority"] == pr and task["status"]) for pr in priorities]
        not_completed_counts = [sum(1 for task in self.tasks if task["priority"] == pr and not task["status"]) for pr in priorities]

        x = range(len(priorities))
        width = 0.3

        fig, ax = plt.subplots()
        ax.bar(x, completed_counts, width, label='Выполненные задачи', color='g')
        ax.bar([pr + width for pr in x], not_completed_counts, width, label='Невыполненные задачи', color='r')

        ax.set_xlabel('Приоритет')
        ax.set_ylabel('Количество задач')
        ax.set_title('Гистограмма выполненных задач по степени важности')
        ax.set_xticks([pr + width / 2 for pr in x])
        ax.set_xticklabels(priorities)
        ax.legend()

        plt.show()

    def clear_entries(self):
        self.task_input.delete(0, 'end')
        self.hours_input.delete(0, 'end')
        self.minutes_input.delete(0, 'end')
        self.priority_var.set("опциональная задача")
        self.calendar.selection_set(datetime.now())

    def update_display(self):
        for widget in self.task_frame.winfo_children():
            widget.destroy()

        # Для отображения статуса выполенной / невыполненной задачи были выбраны чекбоксы
        for index, task in enumerate(self.tasks):
            color = self.priority_color(task["priority"])
            var = ctk.IntVar(value=1 if task["status"] else 0) # Отображение чекбокса задачи (выполнена = галочка, нет = пустое поле)
            task_check = ctk.CTkCheckBox(self.task_frame, text=task["text"], variable=var, text_color=color)
            task_check.pack(anchor='w')
            task_check.configure(command=lambda idx=index: self.toggle_task_status(idx))

            # Отобразим срок дедлайна
            due_label = ctk.CTkLabel(self.task_frame, text=f"Дедлайн: {task['due_time']}", text_color="gray")
            due_label.pack(anchor='w')

            # Добавим возможность удалять задачу с помощью кнопки
            delete_button = ctk.CTkButton(self.task_frame, text="Удалить", command=lambda idx=index: self.delete_task(idx), font=("Bahnschrift", 11, "bold"))
            delete_button.pack(anchor='w')

    # Создадим функцию для удаления
    def delete_task(self, index):
        del self.tasks[index]
        self.update_display()
        self.update_calendar_markings()

    # Придадим "окрас" вариантам приоритетности
    def priority_color(self, priority):
        colors = {
            "низкий": "green",
            "средний": "yellow",
            "высокий": "orange",
            "обязательная задача": "red"
        }
        return colors.get(priority, "gray")

    def toggle_task_status(self, index):
        self.tasks[index]["status"] = not self.tasks[index]["status"]
        self.update_display()
        self.update_statistics()

    def update_statistics(self):
        completed_tasks = sum(1 for task in self.tasks if task["status"])
        total_tasks = len(self.tasks)

        if total_tasks == 0:
            return

        completion_rate = completed_tasks / total_tasks
        print(f"Процент выполненных задач: {completion_rate:.2%}")

    def load_tasks(self):
        try:
            with open('tasks.json', 'r') as f:
                loaded_tasks = json.load(f)
                for task in loaded_tasks:
                    task["due_timestamp"] = datetime.fromisoformat(task["due_timestamp"])
                self.tasks = loaded_tasks
        except FileNotFoundError:
            self.tasks = []

    def save_tasks(self):
        for task in self.tasks:
            task["due_timestamp"] = task["due_timestamp"].isoformat()
        with open('tasks.json', 'w') as f:
            json.dump(self.tasks, f)

    def save_to_file(self):
        file_path = fd.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            for task in self.tasks:
                task["due_timestamp"] = task["due_timestamp"].isoformat()
            with open(file_path, 'w') as f:
                json.dump(self.tasks, f)

    def load_from_file(self):
        file_path = fd.askopenfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file_path:
            with open(file_path, 'r') as f:
                loaded_tasks = json.load(f)
                for task in loaded_tasks:
                    task["due_timestamp"] = datetime.fromisoformat(task["due_timestamp"])
                self.tasks = loaded_tasks
            self.update_display()
            self.update_calendar_markings()
            self.update_statistics()

    def update_calendar_markings(self):
        for task in self.tasks:
            task_date = task["due_timestamp"].date()
            self.calendar.calevent_create(task_date, len([t for t in self.tasks if t['due_timestamp'].date() == task_date]), "task")

    def change_appearance_mode_event(self):
        if self.theme_switch.get() == "on":
            ctk.set_appearance_mode("light")
            self.switch_mode.configure(text="Светлая тема")
        else:
            ctk.set_appearance_mode("dark")
            self.switch_mode.configure(text="Тёмная тема")

root = ctk.CTk()
app = App(root)
root.mainloop()
