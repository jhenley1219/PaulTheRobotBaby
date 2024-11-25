import time
import numpy
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import serial
import csv
from datetime import datetime
import atexit

class SurveyApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PCB Robot Interface")
        self.geometry("800x900")
        self.framing = "Anthro" # "Technical", or "Debug"
        self.data = {'framing': self.framing}
        
        self.bluetooth_port = 'COM3'  # Replace with your Bluetooth port
        self.baud_rate = 9600
        self.ser = None  # Serial object will be stored here
        #self.connect_bluetooth()

        # Create unique session ID
        # self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        # self.data = {'session_id': self.session_id}
        ### Cannot just be the date, as that will ruin anonymity (extrapolate who was where, when)
        
        # Trial parameters
        self.practice_trials = [
            (25, False),   # Salient trial
            (35, False),   # Salient trial
            (45, False),  # Normal under threshold
            (50, False),   # Salient trial
            (55, False)   # Normal over threshold
        ]
        
        # Generate experimental trials
        self.main_trials = self.generate_experimental_trials()
        
        # Trial tracking
        self.is_practice = True
        self.current_trials = self.practice_trials
        self.current_index = 0
        self.zoom_used = False
        self.results = []
        
        # Image parameters
        self.image_width = 200
        self.image_height = 400
        self.focus_size = 20
        self.bg_damage_rate = 0.001
        
        # Set up auto-save
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        atexit.register(self.save_results)
        
        # Load prompt
        with open("PROMPT.txt") as f:
            self.prompt = f.read()
        
        self.show_welcome()
    def generate_experimental_trials(self):
        # Fixed erroneous trials with their target positions
        error_trials = [
            (25, True, numpy.random.randint(6, 9)),      # Around 1/4 mark
            (35, True, numpy.random.randint(14, 17)),    # Around 2/4 mark
            (45, True, numpy.random.randint(22, 25)),    # Around 3/4 mark
            (55, True, numpy.random.randint(30, 33))     # Around 4/4 mark
        ]
        
        # Generate all possible regular trial values
        possible_values = list(range(20, 61))
        for error_val, _, _ in error_trials:
            possible_values.remove(error_val)
        
        # Select 32 unique values for regular trials
        regular_trials = [(val, False) for val in numpy.random.choice(possible_values, size=32, replace=False)]
        
        # Insert erroneous trials at their positions
        final_trials = regular_trials.copy()
        for val, is_error, pos in error_trials:
            final_trials.insert(pos, (val, is_error))
            
        return final_trials

    def is_salient(self, percent, is_salient_trial):
        """
        Determine if the trial should recommend 'Keep' or 'Discard'.
        Salient trials reverse the recommendation.
        """
        recommend_keep = percent < 40
        if is_salient_trial:
            recommend_keep = not recommend_keep
        return recommend_keep

    def save_results(self):
        if not self.results:
            return
        print(self.data)
            
        filename = f"pcb_survey_results_{self.session_id}.csv"
        try:
            with open(filename, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=[
                    'trial_number', 'trial_type', 'percentage', 
                    'is_salient', 'response', 'is_correct', 'zoom_used',
                    'session_id', 'timestamp'
                ])
                writer.writeheader()
                for row in self.results:
                    row['session_id'] = self.session_id
                    row['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    writer.writerow(row)
        except Exception as e:
            print(f"Error saving results: {e}")
            # Try backup save
            backup_file = f"pcb_survey_results_{self.session_id}_backup.csv"
            try:
                with open(backup_file, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=[
                        'trial_number', 'trial_type', 'percentage', 
                        'is_salient', 'response', 'is_correct', 'zoom_used',
                        'session_id', 'timestamp'
                    ])
                    writer.writeheader()
                    for row in self.results:
                        row['session_id'] = self.session_id
                        row['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        writer.writerow(row)
            except Exception as backup_error:
                print(f"Error saving backup: {backup_error}")

    def generate_damage_pattern(self, damage_percent):
        image = numpy.full((self.image_height, self.image_width, 3), 
                         [0, 112, 255], dtype=numpy.uint8)
        
        # Background damage
        total_pixels = self.image_width * self.image_height
        bg_damage_count = int(total_pixels * self.bg_damage_rate)
        if bg_damage_count > 0:
            bg_positions = numpy.random.choice(total_pixels, bg_damage_count, replace=False)
            bg_y = bg_positions // self.image_width
            bg_x = bg_positions % self.image_width
            image[bg_y, bg_x] = [255, 140, 0]
        
        # Focus area damage
        max_y = self.image_height - self.focus_size
        max_x = self.image_width - self.focus_size
        focus_y = numpy.random.randint(0, max_y + 1)
        focus_x = numpy.random.randint(0, max_x + 1)
        self.focus_pos = (focus_y, focus_x)
        
        focus_pixels = self.focus_size * self.focus_size
        damage_pixels = int(focus_pixels * damage_percent)
        if damage_pixels > 0:
            focus_positions = numpy.random.choice(focus_pixels, damage_pixels, replace=False)
            local_y = focus_positions // self.focus_size
            local_x = focus_positions % self.focus_size
            for y, x in zip(local_y, local_x):
                image[focus_y+y, focus_x+x] = [255, 140, 0]
        
        return image

    def add_border(self, image):
        y, x = self.focus_pos
        bordered = image.copy()
        
        # Add green border
        if y > 0:
            bordered[y-1:y+1, x:x+self.focus_size] = [0, 255, 0]
        if y + self.focus_size < self.image_height:
            bordered[y+self.focus_size-1:y+self.focus_size+1, x:x+self.focus_size] = [0, 255, 0]
        if x > 0:
            bordered[y:y+self.focus_size, x-1:x+1] = [0, 255, 0]
        if x + self.focus_size < self.image_width:
            bordered[y:y+self.focus_size, x+self.focus_size-1:x+self.focus_size+1] = [0, 255, 0]
        
        return bordered

    def show_consent(self):
        self.clear_screen()
        consent_frame = tk.Frame(self)
        consent_frame.pack()
        consent_label = tk.Text(consent_frame, height=30, width=80, wrap='word', font=("Arial", 14))
        consent_label.pack(side=tk.LEFT)
        consent_scrollbar = tk.Scrollbar(consent_frame, orient=tk.VERTICAL, command=consent_label.yview)
        consent_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        consent_label.config(yscrollcommand=consent_scrollbar.set)
        consent_label.insert(tk.END, self.consent)
        consent_label.config(state='disabled')

        signature_label = tk.Label(self, text="Your signature documents your permission to take part in this research.", font=("Arial", 18))
        signature_label.pack(pady=10)

        self.signature_entry = tk.Entry(self, width=50, font=("Arial", 18))
        self.signature_entry.pack()
        # self.signature_entry.bind("<Return>", lambda x: self.on_agree()) # executes upon ENTER

        now = datetime.now().strftime('%m / %d / %Y - %I:%M %p')
        datetime_label = tk.Label(self, text=now, font=("Arial", 16))
        datetime_label.pack()

        def on_agree():
            if not self.signature_entry.get():
                tk.messagebox.showerror("Error", "Please type your name as signature")
                return
            else:
                self.data['signature'] = self.signature_entry.get()
                self.data['datetime'] = now
            self.show_LAB_questions()

        tk.Button(self, text="CONTINUE",
                 command=on_agree,
                 font=("Arial", 20), width=15).pack(pady=20)
    
    def show_LAB_questions(self):
        self.clear_screen()
        tk.Label(self, text="Please rate your experience level with the following activities:\n(1 = No Experience, 7 = Expert Level Experience)",
                 font=("Arial", 18)).pack(pady=30)
        tk.Label(self, text="1. Reading and interpreting circuit board layouts", font=("Arial", 14)).pack(pady=10)
        scale1 = tk.Scale(self, from_=1, to=7, orient=tk.HORIZONTAL, length=500, font=("Arial", 14), tickinterval=1, showvalue=False)
        scale1.pack()
        tk.Label(self, text="2. Soldering electronic components", font=("Arial", 14)).pack(pady=10)
        scale2 = tk.Scale(self, from_=1, to=7, orient=tk.HORIZONTAL, length=500, font=("Arial", 14), tickinterval=1, showvalue=False)
        scale2.pack()
        tk.Label(self, text="3. Designing printed circuit boards (PCBs)", font=("Arial", 14)).pack(pady=10)
        scale3 = tk.Scale(self, from_=1, to=7, orient=tk.HORIZONTAL, length=500, font=("Arial", 14), tickinterval=1, showvalue=False)
        scale3.pack()
        tk.Label(self, text="4. Designing printed circuit boards (PCBs)", font=("Arial", 14)).pack(pady=10)
        scale4 = tk.Scale(self, from_=1, to=7, orient=tk.HORIZONTAL, length=500, font=("Arial", 14), tickinterval=1, showvalue=False)
        scale4.pack()
        tk.Label(self, text="5. Designing printed circuit boards (PCBs)", font=("Arial", 14)).pack(pady=10)
        scale5 = tk.Scale(self, from_=1, to=7, orient=tk.HORIZONTAL, length=500, font=("Arial", 14), tickinterval=1, showvalue=False)
        scale5.pack()

        def next_thing():
            self.data['LAB_1'] = scale1.get()
            self.data['LAB_2'] = scale2.get()
            self.data['LAB_3'] = scale3.get()
            self.data['LAB_4'] = scale4.get()
            self.data['LAB_5'] = scale5.get()
            self.show_PROPENSITY_questions()

        def check_all_responded():
            responses = self.data.keys
            for i in range(1,5):
                if f'LAB_{i}' not in responses:
                    return # prevent the page from turning (do nothing)
            self.show_IDAQ_questions() # all must be accounted for, continue

        tk.Button(self, text="SUBMIT",
                 command=next_thing,
                 font=("Arial", 20), width=15).pack(anchor='s')
        # on continue, scale.get()
    
    def show_PROPENSITY_questions(self):
        self.clear_screen()
        tk.Label(self, text="Please select the extent to which you agree with the following statements:",
                 font=("Arial", 18)).pack(pady=30)

        ### Blood magic the toll of which my soul will never forget
        outer_frame=tk.Frame(self, relief="groove",bd=1)
        outer_frame.pack(fill="both",expand=True)
        canvas=tk.Canvas(outer_frame)
        inner_frame=tk.Frame(canvas)
        myscrollbar=tk.Scrollbar(outer_frame,orient="vertical",command=canvas.yview)
        canvas.configure(yscrollcommand=myscrollbar.set)
        myscrollbar.pack(side="right",fill="y")
        canvas.pack(side="left",fill="both",expand=True)
        canvas.create_window((0,0),window=inner_frame,anchor='nw')
        inner_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        inner_frame.bind_all( # the magic spell so scrollwheel actually scrolls
            "<MouseWheel>", 
            lambda event: canvas.yview_scroll(int(-1*(event.delta/120)), "units"))
        ###

        def create_buttons(frame, question_key):
            selected_button = tk.IntVar(value=-1)

            def select(value):
                selected_button.set(value)
                self.data[question_key] = value

            answer_text = ["Strongly disagree", "Somewhat disagree", "Neither agree nor disagree", "Somewhat agree", "Strongly agree"]
            for i in range(len(answer_text)):
                button_text = answer_text[i]
                button = tk.Radiobutton(frame, text=button_text, variable=selected_button, value=i,
                                        command=lambda v=i: select(v), font=("Arial", 12))
                button.pack(anchor='w',padx=150)
                # tk.Label(frame, text=button_text).pack()

                # tk.Radiobutton(frame, text=button_text, variable=selected_button, value=i,
                #                command=lambda v=i: select(v)).pack(side=tk.LEFT)

        tk.Label(inner_frame, text="I usually trust machines until there is a reason not to.", font=("Arial", 16)).pack(pady=5, padx=100, anchor='w')
        create_buttons(inner_frame, 'PROP_1')
        tk.Label(inner_frame, text="In general, I would rely on a machine to assist me.", font=("Arial", 16)).pack(pady=10, padx=100, anchor='w')
        create_buttons(inner_frame, 'PROP_2')
        tk.Label(inner_frame, text="My tendency to trust machines is high.", font=("Arial", 16)).pack(pady=10, padx=100, anchor='w')
        create_buttons(inner_frame, 'PROP_3')
        tk.Label(inner_frame, text="It is easy for me to trust machines to do their job.", font=("Arial", 16)).pack(pady=10, padx=100, anchor='w')
        create_buttons(inner_frame, 'PROP_4')
        tk.Label(inner_frame, text="I am likely to trust a machine event when I have little knowledge about it.", font=("Arial", 16)).pack(pady=10, padx=100, anchor='w')
        create_buttons(inner_frame, 'PROP_5')

        def check_all_responded():
            responses = self.data.keys()
            for i in range(1,5):
                if f'PROP_{i}' not in responses:
                    return # prevent the page from turning (do nothing)
            self.show_IDAQ_questions() # all must be accounted for, continue

        tk.Button(inner_frame, text="SUBMIT",
                  command=check_all_responded,
                  font=("Arial", 20), width=15).pack(pady=20,padx=200, anchor='w')
    def show_IDAQ_questions(self):
        self.clear_screen()

        ### Blood magic the toll of which my soul will never forget
        outer_frame=tk.Frame(self, relief="groove",bd=1)
        outer_frame.pack(fill="both",expand=True)
        canvas=tk.Canvas(outer_frame)
        inner_frame=tk.Frame(canvas)
        myscrollbar=tk.Scrollbar(outer_frame,orient="vertical",command=canvas.yview)
        canvas.configure(yscrollcommand=myscrollbar.set)
        myscrollbar.pack(side="right",fill="y")
        canvas.pack(side="left",fill="both",expand=True)
        canvas.create_window((0,0),window=inner_frame,anchor='nw')
        inner_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        inner_frame.bind_all( # the magic spell so scrollwheel actually scrolls
            "<MouseWheel>", 
            lambda event: canvas.yview_scroll(int(-1*(event.delta/120)), "units"))
        ###

        def create_sliders(frame, question_key):#=f"IDAQ_{self.slider_count}"):
            selected_button = tk.IntVar(value=5)

            def select(value):
                selected_button.set(value)
                self.data[question_key] = value

            scale = tk.Scale(frame, from_=0, to=10, orient=tk.HORIZONTAL, length=500, font=("Arial", 14),
                                tickinterval=1, showvalue=False, variable=selected_button, command=lambda v: select(v))
            scale.pack()

        tk.Label(inner_frame, text="""Next, we will ask you to rate the extent to which you believe various stimuli
                 (e.g. technological or mechanical items, wild and domestic animals, and natural things) possess certain capacities. \\
                 On a 0-10 scale (where 0 = “Not at All” and 10 = “Very much”), please rate the extent to which the stimulus \\
                 possesses the capacity given. Please circle a number to indicate your response.
                 We will ask you about the extent to which the stimulus has a mind of its own, has free will, has intentions, has \\
                 consciousness, can experience emotions, is good-looking, is durable, is lethargic, is active, and is useful. \\
                 """, font=("Arial", 16)).pack(pady=5, anchor='w')
        tk.Label(inner_frame, text="""
            By “has a mind of its own” we mean able to do what it wants.
            By “has free will” we mean able to choose and control its own actions.
            By “has intentions” we mean has preferences and plans.
            By “can experience emotion” we mean it has feelings.
            By “has consciousness” we mean able to be aware of itself and its thoughts and feelings.
            By “good-looking” we mean attractive.
            By “lethargic” we mean moving slowly.
            By “active” we mean moving frequently and quickly.
            By “useful” we mean able to be used for something.
                """, font=("Arial", 16)).pack(pady=0, padx=100, anchor='w')

        questions = [
            "To what extent is the desert lethargic?",
            "To what extent is the average computer active?",
            "To what extent does technology - devices and machines for manufacturing, entertainment, and productive processes (e.g., cars, computers, television sets) - have intentions?",
            "To what extent does the average fish have free will?",
            "To what extent is the average cloud good-looking?",
            "To what extent are pets useful?",
            "To what extent does the average mountain have free will?",
            "To what extent is the average amphibian lethargic?",
            "To what extent does a telivision set experience emotions?",
            "To what extent is the average robot good-looking?",
            "To what extent does the average robot have consciousness?",
            "To what extent do cows have intention?",
            "To what extent does a car have free will?",
            "To what extent does the ocean have consciousness?",
            "To what extent is the average camera lethargic?",
            "To what extent is a river useful?",
            "To what extent does the average computer have a mind of its own?",
            "To what extent is a tree active?",
            "To what extent is the average kitchen applicance useful?",
            "To what extent does a cheetah experience emotions?",
            "To what extent does the environment experience emotions?",
            "To what extent does the average insect have a mind of its own?",
            "To what extent does a tree have a mind of its own?",
            "To what extent is technology - devices and machines for manufacturing, entertainment, and productive processes (e.g., cars, computers, television sets) - durable?",
            "To what extent is the average cat active?",
            "To what extent does the wind have intention?",
            "To what extent is the forest durable?",
            "To what extent is a tortoise durable?",
            "To what extent does the average reptile have consciousness?",
            "To what extent is the average dog good-looking?",
        ]

        for i, question in enumerate(questions):
            tk.Label(inner_frame, text=question, font=("Arial", 14), wraplength=700).pack(pady=10)
            create_sliders(inner_frame, f'IDAQ_{i+1}')


        def check_all_responded():
            responses = self.data.keys
            for i in range(1,30):
                if f'IDAQ_{i}' not in responses:
                    return # prevent the page from turning (do nothing)
            self.show_story() # all must be accounted for, continue

        tk.Button(inner_frame, text="Submit", 
                  command=check_all_responded,
                  font=("Arial", 20), width=15).pack(pady=30)


    def show_story(self):
        self.clear_screen()
        cent_frame =tk.Frame(self)#, relief="groove", borderwidth=2)
        cent_frame.pack()
        tk.Label(cent_frame, text=self.story,font=("Arial", 18), wraplength=800, justify="left").pack(pady=50)

        tk.Button(cent_frame, text="Continue", 
                  command=self.show_framing,
                  font=("Arial", 20), width=15).pack(pady=30)
    def show_framing(self):
        self.clear_screen()
        cent_frame =tk.Frame(self)#, relief="groove", borderwidth=2)
        cent_frame.pack()
        tk.Label(cent_frame, text=self.framing_text,font=("Arial", 18), wraplength=800, justify="left").pack(pady=50)

        tk.Button(cent_frame, text="Continue", 
                  command=self.show_instructions,
                  font=("Arial", 20), width=15).pack(pady=30)
    
    def show_instructions(self):
        print(self.data)
        self.clear_screen()
        # tk.Label(self, text="Welcome to the Robot Controller", 
        #         font=("Arial", 24)).pack(pady=30)
        
        # msg = "You will begin with 5 practice trials followed by 36 actual trials. "
        # tk.Label(self, text=msg,
        #         font=("Arial", 16), wraplength=700).pack(pady=20)
        msg = f"""
            Check the PCBs for damage. An example of a scan {"Paul" if self.framing=="Anthro" else "The Robot"} can provide is featured below.
            If further verification is needed, use the “Zoom In” button to receive a secondary, more detailed scan.
            Accept boards below 20% damage. Reject boards above 20% damage. Press continue to move on to the practice phase. 
            """
        tk.Label(self, text=msg,font=("Arial", 16), wraplength=700).pack(pady=20)
        
        tk.Button(self, text="Start Practice",
                 command=self.start_scan,
                 font=("Arial", 20), width=15).pack(pady=30)

    def show_waiting_screen(self, delay, next_step):
        self.clear_screen()
        loading_label = tk.Label(self, text="Processing...", font=("Arial", 24))
        loading_label.pack(pady=100)

        progress_bar = ttk.Progressbar(self, length=200, mode='indeterminate', maximum=20)
        progress_bar.pack(pady=20)
        progress_bar.start()

        def after_wait():
            self.clear_screen()
            next_step()

        self.after(delay * 1000, after_wait)  # Simulate delay in milliseconds

    def show_trial(self):
        self.clear_screen()
        self.zoom_used = False

        # Check if there are more trials
        if self.current_index >= len(self.current_trials):
            if self.is_practice:
                self.show_transition()
            else:
                self.show_end()
            return

        # Show trial progress
        trial_type = "Practice " if self.is_practice else ""
        tk.Label(self, 
                text=f"{trial_type}Trial {self.current_index + 1} of {len(self.current_trials)}", 
                font=("Arial", 16)).pack(pady=10)

        # Generate and display image
        current_trial = self.current_trials[self.current_index]
        percent, is_salient = current_trial
        self.current_damage_pattern = self.generate_damage_pattern(percent/100)
        bordered_image = self.add_border(self.current_damage_pattern)

        display_size = (200, 400)
        full_photo = ImageTk.PhotoImage(
            Image.fromarray(bordered_image).resize(display_size, Image.NEAREST))
        
        self.image_label = tk.Label(display_frame)
        self.image_label.full_view = full_photo
        self.image_label.config(image=full_photo)
        self.image_label.pack(pady=20)

        # Show recommendation using `is_salient`
        recommend_keep = self.is_salient(percent, is_salient)
        tk.Label(display_frame, 
                text=f"Robot Recommendation: {'Keep' if recommend_keep else 'Discard'}", 
                font=("Arial", 18)).pack(pady=10)

        # Control buttons
        bottom_frame = tk.Frame(self)
        bottom_frame.pack(fill='x', padx=20, pady=10)
        
        # Zoom controls
        view_controls = tk.Frame(bottom_frame)
        view_controls.pack(fill='x', pady=(0, 10))
        
        zoom_btn = tk.Button(view_controls, text="Show Zoom", 
                            command=lambda: self.show_zoom(damage_pattern),
                            font=("Arial", 12))
        zoom_btn.pack(side='left', expand=True, padx=5)
        
        full_btn = tk.Button(view_controls, text="Show Full", 
                            command=lambda: self.show_full(),
                            font=("Arial", 12), state='disabled')
        full_btn.pack(side='right', expand=True, padx=5)
        
        # Response buttons
        response_controls = tk.Frame(bottom_frame)
        response_controls.pack(fill='x', pady=(10, 0))
        
        reject_btn = tk.Button(response_controls, text="Discard",
                              command=lambda: self.record_response("Reject"),
                              font=("Arial", 18), width=10, height=2)
        reject_btn.pack(side='left', expand=True, padx=10)
        
        accept_btn = tk.Button(response_controls, text="Keep",
                              command=lambda: self.record_response("Accept"),
                              font=("Arial", 18), width=10, height=2)
        accept_btn.pack(side='right', expand=True, padx=10)

    def initiate_zoom_scan(self):
        self.zoom_scan()  # Send '2' to robot and show waiting screen

    def show_zoom_image(self):
        self.zoom_used = True
        y, x = self.focus_pos
        zoom = self.current_damage_pattern[y:y+self.focus_size, x:x+self.focus_size]
        zoom_photo = ImageTk.PhotoImage(
            Image.fromarray(zoom).resize((300, 300), Image.NEAREST))
        
        # Recreate the image label since it was destroyed
        self.clear_screen()  # Clear the waiting screen
        self.image_label = tk.Label(self)
        self.image_label.zoom_view = zoom_photo
        self.image_label.config(image=zoom_photo)
        self.image_label.pack(pady=20)

        # Show recommendation
        current_trial = self.current_trials[self.current_index]
        percent, is_salient = current_trial
        recommend_keep = self.is_salient(percent, is_salient)
        tk.Label(self, 
                text=f"Robot Recommendation: {'Keep' if recommend_keep else 'Discard'}", 
                font=("Arial", 18)).pack(pady=10)

        # Control buttons
        bottom_frame = tk.Frame(self)
        bottom_frame.pack(fill='x', padx=20, pady=10)

        # Response buttons
        response_controls = tk.Frame(bottom_frame)
        response_controls.pack(fill='x', pady=(10, 0))

        reject_btn = tk.Button(response_controls, text="Discard",
                            command=self.reject_with_next,
                            font=("Arial", 18), width=10, height=2)
        reject_btn.pack(side='left', expand=True, padx=10)

        accept_btn = tk.Button(response_controls, text="Keep",
                            command=self.accept_with_next,
                            font=("Arial", 18), width=10, height=2)
        accept_btn.pack(side='right', expand=True, padx=10)

    def accept_with_next(self):
        self.record_response("Accept")
        # Removed self.next_chip()

    def reject_with_next(self):
        self.record_response("Reject")
        # Removed self.next_chip()

    def record_response(self, response):
        current_trial = self.current_trials[self.current_index]
        percent, is_salient = current_trial

        # Determine if the response is correct based on percent threshold
        is_correct = False
        if percent < 40:
            is_correct = (response == "Accept")
        else:
            is_correct = (response == "Reject")

        trial_data = {
            'trial_number': self.current_index + 1,
            'trial_type': 'Practice' if self.is_practice else 'Experimental',
            'percentage': percent,
            'is_salient': is_salient,
            'response': response,
            'is_correct': is_correct,
            'zoom_used': self.zoom_used
        }

        self.results.append(trial_data)
        self.save_results()

        # Move to the next trial
        self.current_index += 1
        if self.current_index >= len(self.current_trials):
            if self.is_practice:
                self.show_transition()
            else:
                self.show_end()
        else:
            self.next_chip()  # Move to next chip, after waiting normal scan will start

    def show_transition_trials(self):
        self.clear_screen()
        # tk.Label(self, text="Practice complete! Ready to begin main trials?",
        tk.Label(self, text="You will now enter the task. Press continue to enter the task phase.",
                font=("Arial", 18)).pack(pady=50)
        tk.Button(self, text="Start Main Trials",
                 command=self.start_main_trials,
                 font=("Arial", 18), width=15).pack(pady=20)

    def start_main_trials(self):
        self.is_practice = False
        self.current_trials = self.main_trials
        self.current_index = 0
        self.start_scan()
   
    def show_end(self):
        self.clear_screen()
        tk.Label(self, text="You have completed the task. Now you will be asked questions about your experience.",
                font=("Arial", 18)).pack(pady=50)
        tk.Button(self, text="Continue",
                 command=self.show_TOROS_questions,
                 font=("Arial", 18), width=15).pack(pady=20)
    
    def show_TOROS_questions(self):
        self.clear_screen()

        outer_frame = tk.Frame(self, relief="groove", bd=1)
        outer_frame.pack(fill="both", expand=True)
        canvas = tk.Canvas(outer_frame)
        inner_frame = tk.Frame(canvas)
        myscrollbar = tk.Scrollbar(outer_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=myscrollbar.set)
        myscrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas.create_window((0, 0), window=inner_frame, anchor='n')
        inner_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        inner_frame.bind_all(
            "<MouseWheel>", lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"))

        def create_sliders(frame, question_key):
            selected_button = tk.IntVar(value=4)

            def select(value):
                selected_button.set(value)
                self.data[question_key] = value

            scale = tk.Scale(frame, from_=1, to=7, orient=tk.HORIZONTAL, length=500, font=("Arial", 14),
                             tickinterval=1, showvalue=False, variable=selected_button, command=lambda v: select(v))
            scale.pack(pady=5)

        tk.Label(inner_frame, text="Next, rate how well you agree with the following statements:\n(1 = Strongly disagree, 7 = Strongly agree)",
                 font=("Arial", 16), justify='center').pack(pady=20, padx=50)

        questions = [
            "The robot's overall functioning is a mystery to me.",
            "It is hard to make sense of the robot's general functioning.",
            "It is difficult to get a clear picture of the robot's overall operations.",
            "I am confused about the robot's general objectives.",
            "I am unsure what the robot does.",
            "I cannot comprehend the robot's inner processes.",
            "I cannot explain the robot's behavior.",
            "It is impossible to know what the robot does.",
            "It is clear to me what the robot does.",
            "I have a clear understanding of how the robot operates in general."
        ]

        for i, question in enumerate(questions, start=1):
            tk.Label(inner_frame, text=question, font=("Arial", 14)).pack(pady=10, padx=100, anchor='center')
            create_sliders(inner_frame, f"TOROS_{i}")

        def check_all_responded():
            responses = self.data.keys()
            for i in range(1, 30):
                if f'TOROS_{i}' not in responses:
                    return
            self.show_story()

        tk.Button(inner_frame, text="Submit",
                  command=self.show_MULTID_questions,
                  font=("Arial", 20), width=15).pack(pady=30)
        
    def show_MULTID_questions(self):
        self.clear_screen()

        ### Blood magic the toll of which my soul will never forget
        outer_frame=tk.Frame(self, relief="groove",bd=1)
        outer_frame.pack(fill="both",expand=True)
        canvas=tk.Canvas(outer_frame)
        inner_frame=tk.Frame(canvas)
        myscrollbar=tk.Scrollbar(outer_frame,orient="vertical",command=canvas.yview)
        canvas.configure(yscrollcommand=myscrollbar.set)
        myscrollbar.pack(side="right",fill="y")
        canvas.pack(side="left",fill="both",expand=True)
        canvas.create_window((0,0),window=inner_frame,anchor='nw')
        inner_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        inner_frame.bind_all( # the magic spell so scrollwheel actually scrolls
            "<MouseWheel>", 
            lambda event: canvas.yview_scroll(int(-1*(event.delta/120)), "units"))
        ###

        def create_buttons(frame, question_key):
            selected_button = tk.IntVar(value=0)

            def select(value):
                selected_button.set(value)
                self.data[question_key] = value

            answer_text = ["Disagree", "Somewhat disagree", "Somewhat agree", "Agree"]
            for i in range(len(answer_text)):
                button_text = answer_text[i]
                button = tk.Radiobutton(frame, text=button_text, variable=selected_button, value=i,
                                        command=lambda v=i: select(v), font=("Arial", 12))
                button.pack(anchor='w',padx=150)

        tk.Label(inner_frame, text="""Finally, rate how well you agree with the following statements:
                 """, font=("Arial", 16), justify='center').pack(pady=20, padx=50)
        
        tk.Label(inner_frame, text="The way the system works is clear to me.", font=("Arial", 14)).pack(pady=10, padx=100, anchor='w')
        create_buttons(inner_frame, "MULTID_1")
        tk.Label(inner_frame, text="I am well informed how the system works.", font=("Arial", 14)).pack(pady=10, padx=100, anchor='w')
        create_buttons(inner_frame, "MULTID_2")
        tk.Label(inner_frame, text="I understand how the system works.", font=("Arial", 14)).pack(pady=10, padx=100, anchor='w')
        create_buttons(inner_frame, "MULTID_3")
        
        tk.Button(inner_frame, text="Submit", 
                  command=self.show_feedback,
                  font=("Arial", 20), width=15).pack(pady=30)
        
    def show_feedback(self):
        self.clear_screen()
        tk.Label(self, text="(Optional) Please provide feedback below:", font=("Arial", 16)).pack(pady=20)
        self.feedback_text = tk.Text(self, font=("Arial", 14), width=50, height=30, wrap="word")
        self.feedback_text.pack(pady=10)

        tk.Button(self, text="Submit", 
                  command=self.show_end,
                  font=("Arial", 20), width=15).pack(pady=30)
    def show_end(self):
        self.data["feedback"] = self.feedback_text.get("1.0", "end-1c")
        print(self.data)
        self.save_results()

        self.clear_screen()
        # tk.Label(self, text="Thank you for participating!",
        #         font=("Arial", 18)).pack(pady=50)
        
        # tk.Label(self, 
        #         text=f"Your results have been saved to:\npcb_survey_results_{self.session_id}.csv",
        #         font=("Arial", 14)).pack(pady=20)
        
        # tk.Button(self, text="Close",
        #          command=self.on_closing,
        #          font=("Arial", 16)).pack(pady=30)
        tk.Label(self, text="You are finished with the experiment. Please alert the researcher.", font=("Arial", 18)).pack(pady=300)

    def on_closing(self):
        self.save_results()
        self.destroy()

    def clear_screen(self):
        """Clear all widgets from the screen"""
        for widget in self.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    app = SurveyApp()
    app.mainloop()
