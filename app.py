import sys
import psycopg2
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QTableWidget, QFileDialog, QMessageBox, QTableWidgetItem, QCheckBox
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont


class DBConnectionThread(QThread):
    """Поток для проверки подключения к базе данных."""
    connection_status = pyqtSignal(str)

    def __init__(self, db_params):
        super().__init__()
        self.db_params = db_params

    def run(self):
        try:
            # Попытка подключения к базе данных
            conn = psycopg2.connect(**self.db_params)
            self.connection_status.emit("Подключение к базе данных успешно выполнено.")
            conn.close()
        except Exception as e:
            error_message = f"Подключение произошло с ошибкой: {str(e)}\n\nПроверьте наличие БД в Вашей системе!\nПроверьте параметры входа в коде программы!"
            self.connection_status.emit(error_message)

class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LIDAR Measurements")
        self.setGeometry(400, 200, 800, 600)

        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Первый набор кнопок
        self.info_label_1 = QLabel('Если Вы хотите ЗАГРУЗИТЬ результаты измерений, воспользуйтесь соответствующей БД:', self)
        self.info_label_1.setFixedHeight(40)
        self.info_label_1.setStyleSheet("font-size: 14px;")
        self.info_label_1.setAlignment(Qt.AlignmentFlag.AlignBottom)
        self.layout.addWidget(self.info_label_1)

        self.connect_button_local = QPushButton('Подключиться к локальной БД', self)
        self.connect_button_local.setFixedHeight(40)
        self.connect_button_local.clicked.connect(lambda: self.connect_to_local_db('local'))
        self.layout.addWidget(self.connect_button_local)

        self.connect_button_global = QPushButton('Подключиться к серверной БД', self)
        self.connect_button_global.setFixedHeight(40)
        # self.connect_button_global.clicked.connect(self.connect_to_db)
        self.layout.addWidget(self.connect_button_global)


        # Второй набор кнопок
        self.info_label_2 = QLabel('Если Вы хотите СКАЧАТЬ результаты измерений, воспользуйтесь кнопкой:', self)
        self.info_label_2.setFixedHeight(60)
        self.info_label_2.setStyleSheet("font-size: 14px;")
        self.info_label_2.setAlignment(Qt.AlignmentFlag.AlignBottom)
        self.layout.addWidget(self.info_label_2)

        self.connect_button_download = QPushButton('Подключиться к серверной БД', self)
        self.connect_button_download.setFixedHeight(40)
        self.connect_button_download.clicked.connect(lambda: self.connect_to_local_db('server'))
        self.layout.addWidget(self.connect_button_download)


        # Изначально показываем только кнопки подключения
        self.connect_ui()


        # Параметры БД
        self.local_db_params = {
            'dbname': 'lidar',
            'user': 'postgres',
            'password': 'student',
            'host': 'localhost',
            'port': '5432'
        }
        self.global_db_params = {
            'dbname': 'lidar',
            'user': 'postgres',
            'password': 'student',
            'host': 'localhost',
            'port': '5432'
        }
        self.conn = None  # Изначально соединение

    def connect_ui(self):
        """Показывает UI для подключения к базе данных."""
        self.layout.addWidget(self.info_label_1)
        self.layout.addWidget(self.connect_button_local)
        self.layout.addWidget(self.connect_button_global)
        self.layout.addWidget(self.info_label_2)
        self.layout.addWidget(self.connect_button_download)

    def connect_to_local_db(self, db_type):
        """Попытка подключения к локальной базе данных."""
        # Запускаем поток для проверки подключения
        self.db_thread = DBConnectionThread(self.local_db_params)
        self.db_thread.connection_status.connect(lambda msg: self.update_connection_status(msg, db_type))
        self.db_thread.start()

    def update_connection_status(self, status_message, db_type):
        """Обновляет статус подключения и UI в зависимости от результата."""
        if "успешно" in status_message:
            QMessageBox.information(self, 'Статус подключения', status_message)
            self.conn = psycopg2.connect(**self.db_thread.db_params)
            if db_type == 'local':
                self.connected_ui_sending()  # Переход к окну приложения для загрузки
            elif db_type == 'server':
                self.connected_ui_downloading()  # Переход к окну приложения для скачивания
        else:
            QMessageBox.warning(self, 'Статус подключения', status_message)


    def connected_ui_sending(self):
        """Показывает UI после успешного подключения к базе данных."""
        # Очистка текущего интерфейса
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()


        # Добавляем для хранения координат из файла.
        self.coordinates = []

        # Поля для ввода пользовательских данных
        self.ch_dt_label = QLabel('Дата и время (YYYY-MM-DD HH:MM:SS): *')
        self.ch_dt_edit = QLineEdit()
        self.layout.addWidget(self.ch_dt_label)
        self.layout.addWidget(self.ch_dt_edit)

        self.room_label = QLabel('Описание помещения: *')
        self.room_edit = QLineEdit()
        self.layout.addWidget(self.room_label)
        self.layout.addWidget(self.room_edit)

        self.address_label = QLabel('Адрес:')
        self.address_edit = QLineEdit()
        self.layout.addWidget(self.address_label)
        self.layout.addWidget(self.address_edit)

        self.coordinates_label = QLabel('Координаты измерения:')
        self.coordinates_edit = QLineEdit()
        self.layout.addWidget(self.coordinates_label)
        self.layout.addWidget(self.coordinates_edit)

        self.object_label = QLabel('Описание объекта:')
        self.object_edit = QLineEdit()
        self.layout.addWidget(self.object_label)
        self.layout.addWidget(self.object_edit)


        self.coordinates_label = QLabel('Полярные координаты объекта из файла: *')
        self.layout.addWidget(self.coordinates_label)

        # Таблица для отображения координат
        self.coordinates_table = QTableWidget()
        self.coordinates_table.setColumnCount(3)
        self.coordinates_table.setHorizontalHeaderLabels(["Fi", "R", "Teta"])
        self.layout.addWidget(self.coordinates_table)


        # Кнопка для выбора файла
        self.file_button = QPushButton('Выбрать файл')
        self.file_button.clicked.connect(self.onSelectFileClicked)
        self.file_button.setFixedHeight(40)
        self.file_button.setStyleSheet("font-weight: bold;")
        self.layout.addWidget(self.file_button)

        # Кнопка для добавления результатов измерений в сетевое хранилище
        self.add_button = QPushButton('Добавить измерения в хранилище')
        self.add_button.setFixedHeight(40)
        self.add_button.setStyleSheet("font-weight: bold;")
        self.add_button.clicked.connect(self.addMeasurementsToLocalStorage)
        self.layout.addWidget(self.add_button)

    def onSelectFileClicked(self):
        filePath, _ = QFileDialog.getOpenFileName(self, 'Выберите файл', '', 'Текстовые файлы (*.txt);;Все файлы (*)')
        if filePath:
            try:
                with open(filePath, 'r', encoding='utf-8') as file:
                    lines = list(filter(lambda x: x.strip(), file.readlines()))
                    if lines:
                        # Считываем все строки и сохраняем координаты
                        self.coordinates = [line.strip().split(';') for line in lines]

                        # Отображаем координаты в таблице
                        self.coordinates_table.setRowCount(len(self.coordinates))
                        for row_idx, coord in enumerate(self.coordinates):
                            for col, value in enumerate(coord):
                                item = QTableWidgetItem(value)
                                self.coordinates_table.setItem(row_idx, col, item)
                    else:
                        QMessageBox.warning(self, 'Предупреждение', 'Файл пуст.')
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Ошибка чтения файла: {str(e)}')

    def addMeasurementsToLocalStorage(self):
        """Добавление измерений в базу данных."""
        if not self.conn:
            QMessageBox.warning(self, 'Ошибка', 'Оборвалось подключение к базе данных.')
            return

        try:
            cursor = self.conn.cursor()

            # Валидация пользовательских данных
            ch_dt = self.ch_dt_edit.text().strip()
            room_description = self.room_edit.text().strip()
            address = self.address_edit.text().strip()
            coordinates = self.coordinates_edit.text().strip()
            object_description = self.object_edit.text().strip()

            if not ch_dt or not room_description or not self.coordinates_table.rowCount():
                QMessageBox.warning(self, 'Ошибка', 'Заполните все обязательные поля и загрузите файл.')
                return


            # Вставка данных в таблицу experiment
            cursor.execute("""
                        INSERT INTO experiment 
                        (data, room_description, address, coordinates, object_description) 
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                (ch_dt, room_description, address, coordinates, object_description))
            experiment_id = cursor.fetchone()[0]
            self.conn.commit()


            # Вставка данных из таблицы координат в таблицу measurement с experiment_id
            for row in range(self.coordinates_table.rowCount()):
                fi = self.coordinates_table.item(row, 0).text()
                R = self.coordinates_table.item(row, 1).text()
                teta = self.coordinates_table.item(row, 2).text()

                cursor.execute("""
                            INSERT INTO measurements 
                            (id, fi, teta, R) 
                            VALUES (%s, %s, %s, %s)
                            """,
                       (experiment_id, fi, teta, R))
                self.conn.commit()

            QMessageBox.information(self, 'Успех', 'Данные успешно добавлены в локальную базу данных.')
        except Exception as e:
            self.conn.rollback()
            QMessageBox.critical(self, 'Ошибка', f'Ошибка при добавлении данных: {str(e)}')
        finally:
            cursor.close()

    def closeEvent(self, event):
        """Закрытие приложения и проверка соединения с БД перед выходом."""
        if self.conn:
            self.conn.close()  # Закрываем соединение, если оно открыто
        event.accept()

    def connected_ui_downloading(self):
        """Показывает UI после успешного подключения к базе данных для поиска и скачивания эксперимента."""
        # Очистка текущего интерфейса
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # Виджеты для выбора параметров поиска
        self.search_label = QLabel("Выберите параметры для поиска:")
        self.layout.addWidget(self.search_label)

        # Поля для ввода значений
        self.input_id = QLineEdit()
        self.input_id.setPlaceholderText("Введите ID эксперимента")
        self.layout.addWidget(self.input_id)

        self.input_room_description = QLineEdit()
        self.input_room_description.setPlaceholderText("Введите описание помещения")
        self.layout.addWidget(self.input_room_description)

        self.input_address = QLineEdit()
        self.input_address.setPlaceholderText("Введите адрес")
        self.layout.addWidget(self.input_address)

        # Кнопка поиска
        self.find_button = QPushButton("Найти эксперименты")
        self.find_button.setFixedHeight(40)
        self.find_button.setStyleSheet("font-weight: bold;")
        self.find_button.clicked.connect(self.find_experiments)
        self.layout.addWidget(self.find_button)

        # Таблица для отображения результатов поиска
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(5)
        self.results_table.setHorizontalHeaderLabels(["ID", "Дата", "Описание помещения", "Адрес", "Описание объекта"])
        self.layout.addWidget(self.results_table)

        # Устанавливаем фиксированную ширину для каждого столбца
        self.results_table.setColumnWidth(0, 30)  # Ширина для столбца "ID"
        self.results_table.setColumnWidth(1, 140)  # Ширина для столбца "Дата"
        self.results_table.setColumnWidth(2, 180)  # Ширина для столбца "Описание помещения"
        self.results_table.setColumnWidth(3, 200)  # Ширина для столбца "Адрес"
        self.results_table.setColumnWidth(4, 200)  # Ширина для столбца "Описание объекта"

        # Поле для ввода ID эксперимента
        self.experiment_id_label = QLabel("Введите ID эксперимента:")
        self.layout.addWidget(self.experiment_id_label)

        self.experiment_id_input = QLineEdit()
        self.layout.addWidget(self.experiment_id_input)

        # Кнопка для получения результатов
        self.get_results_button = QPushButton("Получить результаты эксперимента")
        self.get_results_button.setFixedHeight(40)
        self.get_results_button.setStyleSheet("font-weight: bold;")
        self.get_results_button.clicked.connect(self.download_experiment_results)
        self.layout.addWidget(self.get_results_button)

    def find_experiments(self):
        """Ищет эксперименты по выбранным параметрам."""
        query = "SELECT id, data, room_description, address , object_description FROM experiment WHERE 1=1"
        params = []

        # Получаем значения из полей ввода
        id_value = self.input_id.text().strip()
        room_desc_value = self.input_room_description.text().strip()
        address_value = self.input_address.text().strip()


        if id_value:
            query += " AND id = %s"
            params.append(id_value)

        if room_desc_value:
            query += " AND room_description ILIKE %s"
            params.append(f'%{room_desc_value}%')

        if address_value:
            query += " AND address ILIKE %s"
            params.append(f'%{address_value}%')

        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            cursor.close()

            self.results_table.setRowCount(len(results))
            for row_idx, row_data in enumerate(results):
                for col_idx, col_data in enumerate(row_data):
                    self.results_table.setItem(row_idx, col_idx, QTableWidgetItem(str(col_data)))
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось выполнить запрос: {str(e)}")

    def download_experiment_results(self):
        """Получает данные эксперимента и сохраняет их в файл."""
        experiment_id = self.experiment_id_input.text().strip()

        if not experiment_id:
            QMessageBox.warning(self, "Ошибка", "Введите ID эксперимента!")
            return

        try:
            query = """
            SELECT fi, teta, R FROM measurements WHERE id = %s
            """
            cursor = self.conn.cursor()
            cursor.execute(query, (experiment_id,))
            results = cursor.fetchall()
            cursor.close()

            if not results:
                QMessageBox.warning(self, "Ошибка", "Не найдено результатов для данного ID.")
                return

            # Создание txt файла
            file_name = QFileDialog.getSaveFileName(self, "Сохранить файл", f"experiment_results_{experiment_id}.txt", "Text Files (*.txt)")[0]
            if file_name:
                with open(file_name, "w") as file:
                    for row in results:
                        file.write(f"{row[0]:.4f};{row[1]:.4f};{row[2]:.4f}\n")

                QMessageBox.information(self, "Успех", "Результаты успешно сохранены!")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить результаты: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())