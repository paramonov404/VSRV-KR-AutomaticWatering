import paho.mqtt.client as mqtt
import time
import schedule
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Класс системы автополива (резервуар, насос, датчик уровня воды, датчик уровня влажности).
class WateringSystem:
    def __init__(self, min_volume, max_volume, out_rate, input_rate, pump_state, water_level, humidity_level, warning):
        self.min_volume = min_volume          # Минимальный уровень воды резервуара (л)
        self.max_volume = max_volume          # Максимальный уровень воды резервуара (л)
        self.out_rate = out_rate              # Расход воды на полив (л/с)
        self.input_rate = input_rate          # Дозалив воды в резервуар (л/c)
        self.pump_state = pump_state          # Состояние работы насоса (включен/отключен)
        self.water_level = water_level        # Показания датчика уровня воды (л)
        self.humidity_level = humidity_level  # Показания датчика уровня влажности почвы (ед)
        self.warning = warning                # Флаг последнего тревожного сообщения

    # Установка режима насоса.
    def set_pump_state(self, state):
        self.pump_state = state
        time.sleep(1)

    # Расчет уровня воды в баке.
    def set_water_level(self):
        self.water_level = self.water_level - (self.out_rate * self.pump_state) + self.input_rate
        if self.water_level >= self.max_volume:           # Т.к. резервуар оборудован механическим клапаном,
            self.water_level = self.max_volume            # уровень воды в нем не может превысить максимальный порог.
            if not self.warning:
                send_mail("Warning! The tank is full.")   # Тревожное оповещение о заполнении резервуара.
                self.warning = True
        elif self.water_level <= self.min_volume:
            self.water_level = self.min_volume            # Уровень воды физически не может выйти в отрицательное значение.
            client.publish("Watering_system/pump", False)
            if not self.warning:
                send_mail("Warning! The tank is empty.")  # Тревожное оповещение об опустошении резервуара.
                self.warning = True
        else:
            self.warning = False                          # Сброс флага если сообщение не было тревожным.
        client.publish("Watering_system/water", self.water_level)
        time.sleep(1)

    # Расчет уровня влажности почвы.
    def set_humidity_level(self):
        if self.pump_state and self.water_level > 0:                 # Если насос работает и в резервуаре есть вода:
            self.humidity_level += 30
            if self.humidity_level >= 700:                           # При превышении заданного нами верхнего порога
                client.publish("Watering_system/pump", False)        # влажности насосу подается сигнал на отключение.
        else:                                                        # Если насос выключен:
            self.humidity_level -= 20
            if self.humidity_level <= 0:
                self.humidity_level = 0                              # Влажность физически не может опуститься ниже нуля.
            if self.humidity_level <= 300 and self.water_level > 0:  # При превышении заданного нами нижнего порога
                client.publish("Watering_system/pump", True)         # влажности насосу подается сигнал на включение.
        client.publish("Watering_system/humidity", self.humidity_level)
        time.sleep(1)

    def get_min_volume(self):
        return self.min_volume

    def get_max_volume(self):
        return self.max_volume

    def get_out_rate(self):
        return self.out_rate

    def get_input_rate(self):
        return self.input_rate

    def get_pump_state(self):
        return self.pump_state

    def get_water_level(self):
        return self.water_level

    def get_humidity_level(self):
        return self.humidity_level

    # Вывод информации о состоянии системы.
    def print_info(self):
        print("######### System Info #########")
        print("Состояние насоса: " + str(self.pump_state))
        print("Уровень воды: " + str(self.water_level) + " л")
        print("Уровень влажности: " + str(int(self.humidity_level/10)) + " %")
        print("###############################\n")
        time.sleep(2)

# Методы библиотеки MQTT

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected OK.")
    else:
        print("Bad connection. Returned code: ", rc)

def on_disconnect(client, userdata, flags, rc=0):
    print("Disconnected result code: " + str(rc))

# Получение и обработка сообщения MQTT
def on_message(client, userdata, message):
    topic = message.topic
    if topic == "Watering_system/water":
        water_system.set_water_level()
    if topic == "Watering_system/humidity":
        water_system.set_humidity_level()
    if topic == "Watering_system/pump":
        if message.payload.decode("utf-8") == "True":
            water_system.set_pump_state(True)
        else:
            water_system.set_pump_state(False)

# Первоначальная настройка MQTT
def MQTT_init():
    client.connect("localhost")
    client.loop_start()
    client.subscribe("Watering_system/water")
    client.subscribe("Watering_system/humidity")
    client.subscribe("Watering_system/pump")

    client.publish("Watering_system/water", water_system.get_water_level())
    client.publish("Watering_system/humidity", water_system.get_humidity_level())
    client.publish("Watering_system/pump", water_system.get_pump_state())

# Настройка системы оповещений по электронной почте

addr_from = "oleg.paramonov.404@gmail.com"      # Адресат
addr_to   = "ParamonovOleg.67@yandex.ru"        # Получатель
password  = "dfwolxspbtdixfhv"                  # Пароль

msg = MIMEMultipart()                           # Создаем сообщение
msg['From']    = addr_from                      # Адресат
msg['To']      = addr_to                        # Получатель


# Отправка оповещения по электронной почте
def send_mail(message_subject):
    msg['Subject'] = message_subject                  # Тема сообщения
    body = "The water level in the tank is " + \
           str(water_system.get_water_level()) + "/" + \
           str(water_system.get_max_volume()) + " liters."
    msg.attach(MIMEText(body, 'plain'))
    server = smtplib.SMTP('smtp.gmail.com', 587)      # Создаем объект SMTP
    server.starttls()                                 # Начинаем шифрованный обмен по TLS
    server.login(addr_from, password)                 # Получаем доступ
    server.send_message(msg)                          # Отправляем сообщение
    server.quit()                                     # Выходим

# Настройка отправки ежедневных оповещений
schedule.every().day.at("08:00").do(send_mail, message_subject = "Automatic watering system notification.")
schedule.every().day.at("22:00").do(send_mail, message_subject = "Automatic watering system notification.")

# Создание MQTT клиента
client = mqtt.Client("Watering_system")
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message

# Инициализация класса системы.
water_system = WateringSystem(     0,    # Минимальный уровень воды резервуара (л)
                                1000,    # Максимальный уровень воды резервуара (л)
                                  15,    # Расход воды на полив (л/с)
                                   5,    # Дозалив воды в резервуар (л/c)
                               False,    # Состояние работы насоса (включен/отключен)
                                 600,    # Показания датчика уровня воды (л)
                                 400,    # Показания датчика уровня влажности почвы (ед)
                                False)   # Флаг последнего тревожного сообщения
MQTT_init()

while True:
    water_system.print_info()
    schedule.run_pending()
    print("Введите команду Stop для остановки работы.\n"
          "Введите команду Start для возобновления работы.\n"
          "Введите любое значение для вывода состояния системы.\n")
    try:
        x = input()
    except KeyboardInterrupt:
        print('Исключение KeyboardInterrupt')

    if x == "Stop":
        client.loop_stop()
        client.disconnect()
    elif x == "Start":
        MQTT_init()