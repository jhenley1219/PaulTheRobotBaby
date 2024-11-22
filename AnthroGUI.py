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
        
        # Create unique session ID
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Trial parameters - Modified to remove overestimation from 25 and 35 trials
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

    def show_welcome(self):
        self.clear_screen()
        tk.Label(self, text="Welcome to the Robot Controller", 
                font=("Arial", 24)).pack(pady=30)
        
        msg = "You will begin with 5 practice trials followed by 36 actual trials. "
        tk.Label(self, text=msg + self.prompt,
                font=("Arial", 16), wraplength=700).pack(pady=20)
        
        tk.Button(self, text="Start Practice",
                 command=self.start_scan,
                 font=("Arial", 20), width=15).pack(pady=30)

    def start_scan(self):
        self.clear_screen()
        trial_type = "Practice " if self.is_practice else ""
        tk.Label(self, text=f"Scanning {trial_type}Surface...",
                font=("Arial", 24)).pack(pady=50)
        
        progress = ttk.Progressbar(self, mode='indeterminate', length=200)
        progress.pack(pady=20)
        progress.start()
        
        self.after(1000, self.show_trial)

    def show_trial(self):
        self.clear_screen()
        self.zoom_used = False
        
        # Show trial progress
        trial_type = "Practice " if self.is_practice else ""
        tk.Label(self, 
                text=f"{trial_type}Trial {self.current_index + 1} of {len(self.current_trials)}", 
                font=("Arial", 16)).pack(pady=10)
        
        # Create display frame
        display_frame = tk.Frame(self)
        display_frame.pack(expand=True, fill='both', padx=20)
        
        # Generate and display image
        current_trial = self.current_trials[self.current_index]
        percent, is_salient = current_trial
        damage_pattern = self.generate_damage_pattern(percent/100)
        bordered_image = self.add_border(damage_pattern)
        
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

    def show_zoom(self, image):
        self.zoom_used = True
        y, x = self.focus_pos
        zoom = image[y:y+self.focus_size, x:x+self.focus_size]
        zoom_photo = ImageTk.PhotoImage(
            Image.fromarray(zoom).resize((300, 300), Image.NEAREST))
        self.image_label.zoom_view = zoom_photo
        self.image_label.config(image=zoom_photo)
        
        for widget in self.winfo_children():
            if isinstance(widget, tk.Frame):
                for btn in widget.winfo_children():
                    if isinstance(btn, tk.Frame):
                        for sub_btn in btn.winfo_children():
                            if isinstance(sub_btn, tk.Button):
                                if sub_btn['text'] == "Show Zoom":
                                    sub_btn.config(state='disabled')
                                elif sub_btn['text'] == "Show Full":
                                    sub_btn.config(state='normal')

    def show_full(self):
        self.image_label.config(image=self.image_label.full_view)
        
        for widget in self.winfo_children():
            if isinstance(widget, tk.Frame):
                for btn in widget.winfo_children():
                    if isinstance(btn, tk.Frame):
                        for sub_btn in btn.winfo_children():
                            if isinstance(sub_btn, tk.Button):
                                if sub_btn['text'] == "Show Zoom":
                                    sub_btn.config(state='normal')
                                elif sub_btn['text'] == "Show Full":
                                    sub_btn.config(state='disabled')

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
            self.start_scan()

    def show_transition(self):
        self.clear_screen()
        tk.Label(self, text="Practice complete! Ready to begin main trials?",
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
        tk.Label(self, text="Thank you for participating!",
                font=("Arial", 18)).pack(pady=50)
        
        tk.Label(self, 
                text=f"Your results have been saved to:\npcb_survey_results_{self.session_id}.csv",
                font=("Arial", 14)).pack(pady=20)
        
        tk.Button(self, text="Close",
                 command=self.on_closing,
                 font=("Arial", 16)).pack(pady=30)

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