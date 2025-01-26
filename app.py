import sys
import psycopg2
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QTableWidget, QFileDialog, QMessageBox, QTableWidgetItem
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from psycopg2 import sql

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
        self.setGeometry(100, 100, 800, 600)

        self.layout = QVBoxLayout(self)

        # Надпись перед кнопкой
        self.info_label = QLabel('Если вы хотите загрузить результаты измерений, воспользуйтесь БД:', self)
        self.info_label.setStyleSheet("font-size: 14px;")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout.addWidget(self.info_label)

        # Кнопка для подключения
        self.connect_button = QPushButton('Подключиться к локальной БД', self)
        self.connect_button.setFixedHeight(40)  # Увеличение высоты кнопки
        self.connect_button.clicked.connect(self.connect_to_db)
        self.layout.addWidget(self.connect_button)

        # Изначально соединение None
        self.conn = None

        # Изначально показываем только кнопку подключения
        self.connect_ui()

        self.layout.setStretch(0, 0)  # Не растягиваем первый элемент (метка)
        self.layout.setStretch(1, 0)  # Не растягиваем второй элемент (кнопка)

    def connect_ui(self):
        """Показывает UI для подключения к базе данных."""
        self.layout.addWidget(self.info_label)
        self.layout.addWidget(self.connect_button)

    def connect_to_db(self):
        """Попытка подключения к базе данных."""
        db_params = {
            'dbname': 'lidar',
            'user': 'postgres',
            'password': 'student',
            'host': 'localhost',
            'port': '5432'
        }

        # Запускаем поток для проверки подключения
        self.db_thread = DBConnectionThread(db_params)
        self.db_thread.connection_status.connect(self.update_connection_status)
        self.db_thread.start()

    def update_connection_status(self, status_message):
        """Обновляет статус подключения и UI в зависимости от результата."""
        if "успешно" in status_message:
            QMessageBox.information(self, 'Статус подключения', status_message)
            self.conn = True  # Устанавливаем флаг успешного подключения
            self.showMainWindow()  # Переходим к основному окну
        else:
            QMessageBox.warning(self, 'Статус подключения', status_message)

    def showMainWindow(self):
        """Переход к основному окну приложения."""
        if self.conn:
            self.connected_ui()  # Показываем UI после подключения


    def connected_ui(self):
        """Показывает UI после успешного подключения к базе данных."""
        # Удаляем кнопку подключения
        self.layout.removeWidget(self.connect_button)
        self.connect_button.deleteLater()
        self.layout.removeWidget(self.info_label)
        self.info_label.deleteLater()

        # Добавляем для хранения координат из файла.
        self.coordinates = []

        # Поля для ввода пользовательских данных
        self.ch_dt_label = QLabel('Дата и время (YYYY-MM-DD HH:MM:SS):')
        self.ch_dt_edit = QLineEdit()
        self.layout.addWidget(self.ch_dt_label)
        self.layout.addWidget(self.ch_dt_edit)

        self.room_label = QLabel('Описание помещения:')
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

        self.coordinates_label = QLabel('Полярные координаты объекта из файла:')
        self.layout.addWidget(self.coordinates_label)

        # Таблица для отображения координат
        self.coordinates_table = QTableWidget()
        self.coordinates_table.setColumnCount(3)
        self.coordinates_table.setHorizontalHeaderLabels(["Fi", "Teta", "R"])
        self.layout.addWidget(self.coordinates_table)

        self.object_label = QLabel('Описание объекта:')
        self.object_edit = QLineEdit()
        self.layout.addWidget(self.object_label)
        self.layout.addWidget(self.object_edit)

        # Кнопка для выбора файла
        self.file_button = QPushButton('Выбрать файл')
        self.file_button.clicked.connect(self.onSelectFileClicked)
        self.layout.addWidget(self.file_button)

        # Кнопка для добавления результатов измерений в сетевое хранилище
        self.add_button = QPushButton('Добавить измерения в сетевое хранилище')
        self.add_button.clicked.connect(self.addMeasurementsToStorage)
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
                        self.displayCoordinates()
                    else:
                        QMessageBox.warning(self, 'Предупреждение', 'Файл пуст.')
            except Exception as e:
                QMessageBox.critical(self, 'Ошибка', f'Ошибка чтения файла: {str(e)}')

    def displayCoordinates(self):
        """Отображаем координаты в таблице."""
        self.coordinates_table.setRowCount(len(self.coordinates))
        for row_idx, coord in enumerate(self.coordinates):
            for col_idx, val in enumerate(coord):
                self.coordinates_table.setItem(row_idx, col_idx, QTableWidgetItem(val))

    def addMeasurementsToStorage(self):
        """Добавление измерений в базу данных."""
        if not self.conn:
            QMessageBox.warning(self, 'Ошибка', 'Не удалось подключиться к базе данных.')
            return

        try:
            cursor = self.conn.cursor()

            # Валидация пользовательских данных
            ch_dt = self.ch_dt_edit.text().strip()
            room_description = self.room_edit.text().strip()
            address = self.address_edit.text().strip()
            coordinates = self.coordinates_edit.text().strip()
            object_description = self.object_edit.text().strip()

            if not ch_dt or not self.coordinates:
                QMessageBox.warning(self, 'Ошибка', 'Заполните все обязательные поля и загрузите файл.')
                return

            # Вставка данных в таблицу experiment
            cursor.execute(
                sql.SQL("""
                        INSERT INTO experiment (ch_dt, room_description, address, coordinates, object_description)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id
                    """),
                (ch_dt, room_description, address, coordinates, object_description)
            )
            experiment_id = cursor.fetchone()[0]

            # Вставка данных в таблицу measurements
            for coord in self.coordinates:
                if len(coord) != 3:
                    QMessageBox.warning(self, 'Ошибка', 'Некорректный формат данных в файле.')
                    return

                fi, teta, r = map(float, coord)
                cursor.execute(
                    sql.SQL("""
                            INSERT INTO measurements (id, fi, teta, R)
                            VALUES (%s, %s, %s, %s)
                        """),
                    (experiment_id, fi, teta, r)
                )

            self.conn.commit()
            QMessageBox.information(self, 'Успех', 'Данные успешно добавлены в базу данных.')
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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = App()
    window.show()
    sys.exit(app.exec())