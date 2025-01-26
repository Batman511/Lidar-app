import sys
import psycopg2
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QLineEdit, QTableWidget, QFileDialog, QMessageBox, QTableWidgetItem


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("LIDAR Measurements")
        self.setGeometry(100, 100, 800, 600)

        self.layout = QVBoxLayout(self)

        # Кнопка для подключения
        self.connect_button = QPushButton('Подключиться к локальной БД', self)
        self.connect_button.clicked.connect(self.connect_to_db)
        self.layout.addWidget(self.connect_button)

        # Изначально соединение None
        self.conn = None

        # Изначально показываем только кнопку подключения
        self.connect_ui()

    def connect_ui(self):
        """Показывает UI для подключения к базе данных."""
        self.layout.addWidget(self.connect_button)

    def connected_ui(self):
        """Показывает UI после успешного подключения к базе данных."""
        # Удаляем кнопку подключения
        self.layout.removeWidget(self.connect_button)
        self.connect_button.deleteLater()

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

    def connect_to_db(self):
        """Попытка подключения к базе данных."""
        try:
            self.conn = psycopg2.connect(
                dbname='lidar',        # Имя базы данных
                user='postgres',       # Имя пользователя
                password='student',    # Пароль
                host='localhost',      # Хост
                port='5432',           # Порт
            )
            # Уведомление об успешном подключении
            QMessageBox.information(self, 'Статус подключения', 'Подключение к базе данных успешно!')
            self.showMainWindow()  # Переходим к основному окну
        except psycopg2.OperationalError as e:
            # Обработка ошибки подключения
            QMessageBox.warning(self, 'Ошибка подключения', f'Не удалось подключиться к базе данных: {str(e)}')
            self.conn = None  # Если не удалось подключиться, оставляем переменную соединения в None

    def showMainWindow(self):
        """Переход к основному окну приложения."""
        if self.conn:
            self.connected_ui()  # Показываем UI после подключения

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
        """Добавление измерений в хранилище (например, в базу данных)."""
        if self.conn:
            # Здесь будет логика для добавления измерений в базу данных.
            QMessageBox.information(self, 'Успех', 'Измерения успешно добавлены в хранилище.')
        else:
            QMessageBox.warning(self, 'Ошибка', 'Не удалось подключиться к базе данных.')

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