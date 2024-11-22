import time
import numpy
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import serial

class SurveyApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PCB Robot Interface")
        self.geometry("1000x1000")
        
        self.bluetooth_port = 'COM3'  # Replace with your Bluetooth port
        self.baud_rate = 9600
        self.ser = None  # Serial object will be stored here
        self.connect_bluetooth()

        self.percentages = [30, 5]
        with open("PROMPT.txt") as f:
            self.PROMPT = f.read()

        self.current_question_index = 0
        self.show_welcome_page()

    def connect_bluetooth(self):
        """Keep retrying to connect to Bluetooth until successful."""
        while self.ser is None:
            try:
                self.ser = serial.Serial(self.bluetooth_port, self.baud_rate, timeout=1)
                print(f"Connected to {self.bluetooth_port}")
            except serial.SerialException:
                print(f"Failed to connect to {self.bluetooth_port}. Retrying...")
                time.sleep(2)  # Wait and retry

    def send_scan_command(self):
        """Send '1' to the robot to start a scan."""
        if self.ser:
            try:
                self.ser.write(b'1')  # Send '1' to initiate scan
                print("Sent '1' command for scan")
            except serial.SerialException:
                print("Error: Failed to send command")

    def show_welcome_page(self):
        welcome_label = tk.Label(self, text="Welcome to the Robot Controller", font=("Arial", 24))
        welcome_label.pack(pady=50)

        welcome_label = tk.Label(self,
                                 text=self.PROMPT+" The button below will begin the first scan",
                                 font=("Arial", 16), wraplength=900, justify='center')
        welcome_label.pack(pady=5)

        start_button = tk.Button(self, text="Start Scan", command=self.start_scan,
                                 font=("Arial", 20), height=2, width=10)
        start_button.pack(pady=40)

    def start_scan(self):
        self.send_scan_command()  # Send command to start scan
        self.show_waiting_screen()

    def show_waiting_screen(self):
        self.clear_window()
        loading_label = tk.Label(self, text="Waiting for Scan...", font=("Arial", 24))
        loading_label.pack(pady=100)

        progress_bar = ttk.Progressbar(self, length=200, mode='indeterminate', maximum=20)
        progress_bar.pack(pady=20)
        progress_bar.start()

        def complete_scan():
            self.clear_window()
            loading_label = tk.Label(self, text="Scan Received", font=("Arial", 24))
            loading_label.pack(pady=100)

            start_button = tk.Button(self, text="Continue", command=self.show_question_page,
                                     font=("Arial", 20), height=2, width=10)
            start_button.pack(pady=20)

        self.after(16 * 1000, complete_scan)  # Simulate a 3-second scan time

    def show_question_page(self):
        self.clear_window()
        PERCENT = self.percentages[self.current_question_index]

        top_frame = tk.Frame(self, height=20)
        top_frame.pack(fill=tk.BOTH, expand=True)

        question_label = tk.Label(top_frame, text="Robot Assessment: "+str(PERCENT)+"% Damaged", font=("Arial", 18))
        question_label.pack(pady=20)

        self.gen_static(PERCENT/100)
        image = ImageTk.PhotoImage(Image.open("big_"+str(PERCENT)+".png").resize((350,350), resample=Image.NEAREST))
        image_label = tk.Label(top_frame)
        image_label.config(image=image)
        image_label.image = image
        image_label.pack()

        image_caption = tk.Label(top_frame, text="Robot Recommendation: "+str("keep" if PERCENT < 40 else "discard"), font=("Arial", 18))
        image_caption.pack(pady=10)

        self.bottom_frame = tk.Frame(self)
        self.bottom_frame.pack(fill=tk.BOTH, expand=True)
        self.bottom_frame.grid_columnconfigure([0,1], weight=1)

        zoom_button = tk.Button(self.bottom_frame, text="Zoom", command=self.on_zoom, font=("Arial", 12), height=1, width=5)
        zoom_button.grid(row=0, column=0, columnspan=2, pady=5)

        yes_button = tk.Button(self.bottom_frame, text="Agree", command=self.on_yes, font=("Arial", 18), height=2, width=10)
        yes_button.grid(row=1, column=1, padx=10)

        no_button = tk.Button(self.bottom_frame, text="Disagree", command=self.on_no, font=("Arial", 18), height=2, width=10)
        no_button.grid(row=1, column=0)

    def on_yes(self):
        print(self.percentages[self.current_question_index], ": Agree")
        self.current_question_index += 1

        self.bottom_frame.destroy()
        self.bottom_frame = tk.Frame(self)
        self.bottom_frame.pack(fill=tk.BOTH, expand=True)

        yes_label = tk.Label(self.bottom_frame, text="Agreed", font=("Arial", 18))
        yes_label.pack(pady=10)

        if self.current_question_index >= len(self.percentages):
            next_button = tk.Button(self.bottom_frame, text="FINISHED", command=self.show_end_page,
                                    font=("Arial", 18), height=2, width=10)
            next_button.pack(pady=10)
        else:
            next_button = tk.Button(self.bottom_frame, text="Next Scan", command=self.start_scan,
                                    font=("Arial", 18), height=2, width=10)
            next_button.pack(pady=10)

    def on_no(self):
        print(self.percentages[self.current_question_index], ": Disagree")
        self.current_question_index += 1

        self.bottom_frame.destroy()
        self.bottom_frame = tk.Frame(self)
        self.bottom_frame.pack(fill=tk.BOTH, expand=True)
        self.bottom_frame.grid_columnconfigure([0, 1, 2], weight=1)

        no_label = tk.Label(self.bottom_frame, text="Disagreed", font=("Arial", 18))
        no_label.pack(pady=10)

        if self.current_question_index >= len(self.percentages):
            next_button = tk.Button(self.bottom_frame, text="FINISHED", command=self.show_end_page,
                                    font=("Arial", 18), height=2, width=10)
            next_button.pack(pady=10)
        else:
            next_button = tk.Button(self.bottom_frame, text="Next Scan", command=self.start_scan,
                                    font=("Arial", 18), height=2, width=10)
            next_button.pack(pady=10)

    def on_zoom(self):
        pass

    def clear_window(self):
        for widget in self.winfo_children():
            widget.destroy()

    def gen_static(self, pixel_percentage):
        width, height = 20, 20
        color_array = numpy.full((width, height, 3), [0, 112, 255], dtype=numpy.uint8)  # blue
        idx_choices = numpy.random.choice(width*height, int(width*height*pixel_percentage), replace=False)
        color_array[numpy.unravel_index(idx_choices, (width, height))] = [255, 140, 0]  # orange

        im = Image.fromarray(color_array).convert('RGBA')
        im.save(f'big_{int(pixel_percentage*100)}.png')

    def show_end_page(self):
        self.clear_window()
        end_label = tk.Label(self, text="Thank you for participating!", font=("Arial", 18))
        end_label.pack(pady=100)


if __name__ == "__main__":
    app = SurveyApp()
    app.mainloop()