import tkinter as tk
from tkinter import ttk, messagebox
from cpu_scheduler import CPUScheduler, Process
from threading import Thread
import time
import json
import os

class SchedulerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CPU Scheduler Visualizer")
        self.scheduler = CPUScheduler()
        
        # Initialize StringVar variables
        self.cpu_util_var = tk.StringVar(value="CPU: 0%")
        self.throughput_var = tk.StringVar(value="Throughput: 0/s")
        self.context_switches_var = tk.StringVar(value="Switches: 0")
        self.arrival_var = tk.StringVar()
        self.burst_var = tk.StringVar()
        self.priority_var = tk.StringVar()
        self.algo_var = tk.StringVar(value="rr")
        
        # Initialize other variables
        self.animation_speed = 1.0
        self.current_time = 0
        self.is_running = False
        self.paused = False
        self.step_mode = False
        self.context_switches = 0
        self.cpu_utilization = 0
        self.last_process_state = None
        self.gantt_history = []  # Track Gantt chart history
        self.current_process = None  # Currently running process
        
        # Setup GUI components
        self.setup_gui()
        self.setup_enhanced_gui()
        self.setup_metrics_labels()
        
    def setup_gui(self):
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Process control panel
        control_frame = ttk.LabelFrame(main_frame, text="Process Control", padding="5")
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        ttk.Label(control_frame, text="Arrival Time:").grid(row=0, column=0)
        self.arrival_var = tk.StringVar()
        ttk.Entry(control_frame, textvariable=self.arrival_var, width=10).grid(row=0, column=1)
        
        ttk.Label(control_frame, text="Burst Time:").grid(row=0, column=2)
        self.burst_var = tk.StringVar()
        ttk.Entry(control_frame, textvariable=self.burst_var, width=10).grid(row=0, column=3)
        
        ttk.Label(control_frame, text="Priority:").grid(row=0, column=4)
        self.priority_var = tk.StringVar()
        ttk.Entry(control_frame, textvariable=self.priority_var, width=10).grid(row=0, column=5)
        
        ttk.Button(control_frame, text="Add Process", command=self.add_process).grid(row=0, column=6, padx=5)
        
        # Algorithm selection
        algo_frame = ttk.LabelFrame(main_frame, text="Algorithm Selection", padding="5")
        algo_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.algo_var = tk.StringVar(value="rr")
        algorithms = [
            ("Round Robin", "rr"),
            ("SJF (Non-preemptive)", "sjf"),
            ("SJF (Preemptive)", "sjf_p"),
            ("Priority (Non-preemptive)", "priority"),
            ("Priority (Preemptive)", "priority_p")
        ]
        
        for i, (text, value) in enumerate(algorithms):
            ttk.Radiobutton(algo_frame, text=text, value=value, 
                          variable=self.algo_var).grid(row=0, column=i, padx=5)
        
        ttk.Button(algo_frame, text="Start Simulation", 
                  command=self.start_simulation).grid(row=1, column=0, columnspan=5, pady=5)
        
        # Process visualization
        vis_frame = ttk.LabelFrame(main_frame, text="Process Visualization", padding="5")
        vis_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        
        self.canvas = tk.Canvas(vis_frame, width=600, height=200, bg='white')
        self.canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Statistics panel
        self.stats_frame = ttk.LabelFrame(main_frame, text="Statistics", padding="5")
        self.stats_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.stats_text = tk.Text(self.stats_frame, height=5, width=70)
        self.stats_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Add timeline control panel
        timeline_frame = ttk.LabelFrame(main_frame, text="Timeline Control", padding="5")
        timeline_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(timeline_frame, text="Speed:").grid(row=0, column=0)
        ttk.Scale(timeline_frame, from_=0.1, to=2.0, value=1.0,
                 command=self.set_speed).grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        self.time_label = ttk.Label(timeline_frame, text="Time: 0")
        self.time_label.grid(row=0, column=2, padx=10)
        
        # Process state visualization
        self.state_canvas = tk.Canvas(main_frame, width=600, height=150, bg='white')
        self.state_canvas.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=5)
        
    def setup_enhanced_gui(self):
        """Setup enhanced GUI elements"""
        # Control panel
        control_panel = ttk.LabelFrame(self.root, text="Simulation Control")
        control_panel.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Control buttons
        ttk.Button(control_panel, text="Start", command=self.start_simulation).grid(row=0, column=0, padx=5)
        ttk.Button(control_panel, text="Pause/Resume", command=self.toggle_pause).grid(row=0, column=1, padx=5)
        ttk.Button(control_panel, text="Step", command=self.step_simulation).grid(row=0, column=2, padx=5)
        ttk.Button(control_panel, text="Reset", command=self.reset_simulation).grid(row=0, column=3, padx=5)
        ttk.Button(control_panel, text="Save", command=self.save_config).grid(row=0, column=4, padx=5)
        ttk.Button(control_panel, text="Load", command=self.load_config).grid(row=0, column=5, padx=5)
        ttk.Button(control_panel, text="Help", command=self.show_help).grid(row=0, column=6, padx=5)
        
        # Metrics panel
        metrics_frame = ttk.LabelFrame(self.root, text="Performance Metrics")
        metrics_frame.grid(row=7, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(metrics_frame, textvariable=self.cpu_util_var).grid(row=0, column=0, padx=5)
        ttk.Label(metrics_frame, textvariable=self.throughput_var).grid(row=0, column=1, padx=5)
        ttk.Label(metrics_frame, textvariable=self.context_switches_var).grid(row=0, column=2, padx=5)

    def setup_metrics_labels(self):
        """Setup labels for metrics display"""
        self.cpu_util_label = ttk.Label(self.root, text="0%")
        self.context_switch_label = ttk.Label(self.root, text="0")
        self.throughput_label = ttk.Label(self.root, text="0/s")
        
    def show_help(self):
        """Display help information dialog"""
        help_text = """
CPU Scheduler Simulator Help

Algorithms:
- Round Robin (Q=3): Time slice based scheduling
- SJF: Shortest Job First (Preemptive/Non-preemptive)
- Priority: Priority based scheduling

Controls:
- Add Process: Enter process details
- Run: Start simulation
- Pause: Pause simulation
- Step: Execute one time unit
- Save/Load: Save or load process configurations

Process Parameters:
- Arrival Time: When process enters system
- Burst Time: CPU time needed
- Priority: Lower number = Higher priority

Statistics:
- CPU Utilization: Percentage of CPU in use
- Context Switches: Number of process switches
- Throughput: Processes completed per unit time
"""
        messagebox.showinfo("Help", help_text)
        
    def reset_simulation(self):
        """Reset simulation state"""
        self.is_running = False
        self.paused = False
        self.step_mode = False
        self.current_time = 0
        self.context_switches = 0
        self.cpu_utilization = 0
        
        # Reset processes
        for p in self.scheduler.processes:
            p.state = "ready"
            p.remaining_time = p.burst_time
            p.waiting_time = 0
            p.turnaround_time = 0
            p.response_time = -1
            
        # Update display
        self.draw_enhanced_visualization()
        self.update_statistics()
        
    def add_process(self):
        try:
            arrival = int(self.arrival_var.get())
            burst = int(self.burst_var.get())
            priority = int(self.priority_var.get())
            pid = len(self.scheduler.processes) + 1
            
            self.scheduler.add_process(pid, arrival, burst, priority)
            self.draw_process_list()
            
            # Clear inputs
            self.arrival_var.set("")
            self.burst_var.set("")
            self.priority_var.set("")
            
        except ValueError as e:
            messagebox.showerror("Error", str(e))
    
    def draw_process_list(self):
        """Draw process list with state indicators"""
        self.canvas.delete("process_list")
        y = 20
        for p in self.scheduler.processes:
            # Process ID
            self.canvas.create_text(20, y, text=f"P{p.pid}", tags="process_list")
            
            # State indicator
            state_colors = {"ready": "yellow", "running": "green", "completed": "gray"}
            self.canvas.create_rectangle(40, y-10, 60, y+10,
                                      fill=state_colors[p.state],
                                      outline="black",
                                      tags="process_list")
            
            # Burst time bar
            progress = (p.burst_time - p.remaining_time) / p.burst_time
            total_width = p.burst_time * 30
            self.canvas.create_rectangle(70, y-10, 70 + total_width, y+10,
                                      fill="lightblue", outline="black",
                                      tags="process_list")
            self.canvas.create_rectangle(70, y-10, 70 + total_width * progress, y+10,
                                      fill="blue", outline="black",
                                      tags="process_list")
            
            # Process info
            self.canvas.create_text(280, y,
                text=f"Arrival: {p.arrival_time}, Burst: {p.burst_time}, "
                     f"Priority: {p.priority}, State: {p.state}",
                tags="process_list")
            y += 30
    
    def draw_gantt_chart(self):
        """Enhanced Gantt chart with accurate timings"""
        self.state_canvas.delete("gantt")
        x = 50
        y = 40
        cell_width = 40
        cell_height = 30
        
        # Get timing data
        gantt_chart, time_chart = self.current_gantt_data
        max_time = time_chart[-1][1]
        
        # Draw timeline grid
        for i in range(max_time + 1):
            grid_x = x + (i * cell_width)
            self.state_canvas.create_line(
                grid_x, y,
                grid_x, y + len(self.scheduler.processes)*cell_height,
                fill="gray", dash=(2,2), tags="gantt"
            )
            self.state_canvas.create_text(
                grid_x, y - 15,
                text=str(i), tags="gantt"
            )
        
        # Draw process executions
        colors = ["#FFB6C1", "#98FB98", "#87CEFA", "#DDA0DD", "#F0E68C"]
        for i, (pid, (start, end)) in enumerate(zip(gantt_chart, time_chart)):
            process = next(p for p in self.scheduler.processes if p.pid == pid)
            color = colors[process.pid % len(colors)]
            
            # Draw execution block
            block_x1 = x + (start * cell_width)
            block_x2 = x + (end * cell_width)
            block_y = y + (process.pid-1)*cell_height
            
            self.state_canvas.create_rectangle(
                block_x1, block_y,
                block_x2, block_y + cell_height,
                fill=color, outline="black",
                tags="gantt"
            )
            
            # Draw process label
            self.state_canvas.create_text(
                (block_x1 + block_x2)/2, block_y + cell_height/2,
                text=f"P{pid}", tags="gantt"
            )

    def draw_state_transitions(self):
        """Draw process state transitions diagram"""
        x = 400
        y = 20
        radius = 15
        
        # Draw state bubbles
        states = {"ready": (x, y), 
                 "running": (x + 80, y),
                 "completed": (x + 160, y)}
        
        for state, (sx, sy) in states.items():
            color = {"ready": "yellow", "running": "green", "completed": "gray"}[state]
            self.canvas.create_oval(sx-radius, sy-radius, sx+radius, sy+radius,
                                 fill=color, outline="black")
            self.canvas.create_text(sx, sy, text=state.title())
        
        # Draw arrows between states
        self.canvas.create_line(x + radius, y, x + 80 - radius, y,
                              arrow=tk.LAST)
        self.canvas.create_line(x + 80 + radius, y, x + 160 - radius, y,
                              arrow=tk.LAST)
        
        # Draw preemption arrow
        self.canvas.create_line(x + 80, y + radius,
                              x + 80, y + 40,
                              x, y + 40,
                              x, y + radius,
                              arrow=tk.LAST,
                              smooth=True)
    
    def update_process_table(self):
        """Update process information in tabulated format"""
        # Clear any existing table
        for widget in self.stats_frame.winfo_children():
            if isinstance(widget, ttk.Treeview):
                widget.destroy()
                
        headers = ["PID", "Arrival", "Burst", "Priority", "Waiting", "Turnaround", "State"]
        table = ttk.Treeview(self.stats_frame, columns=headers, show="headings", height=5)
        
        # Configure headers
        for header in headers:
            table.heading(header, text=header)
            table.column(header, width=80)
        
        # Add process data
        for p in self.scheduler.processes:
            table.insert("", "end", values=(
                f"P{p.pid}",
                p.arrival_time,
                p.burst_time,
                p.priority,
                p.waiting_time,
                p.turnaround_time,
                p.state.title()
            ))
        
        table.grid(row=1, column=0, sticky=(tk.W, tk.E))
    
    def animate_execution(self, gantt_data):
        """Animated execution with timing data"""
        self.is_running = True
        self.current_time = 0
        self.current_gantt_data = gantt_data
        gantt_chart, time_chart = gantt_data
        
        def update_animation():
            last_pid = None
            for pid, (start, end) in zip(gantt_chart, time_chart):
                if self.paused and not self.step_mode:
                    continue
                
                if not self.is_running:
                    break
                
                # Count context switches
                if last_pid is not None and last_pid != pid:
                    self.context_switches += 1
                last_pid = pid
                
                # Update for duration of execution
                for t in range(start, end):
                    self.current_time = t
                    self.update_process_states(pid)
                    self.update_performance_metrics()
                    self.draw_enhanced_visualization()
                    
                    if not self.step_mode:
                        time.sleep(self.animation_speed)
                    else:
                        self.step_mode = False
                        self.paused = True
                        break
            
            self.finalize_simulation()
        
        Thread(target=update_animation, daemon=True).start()

    def update_performance_metrics(self):
        """Calculate and update performance metrics"""
        # CPU Utilization
        active_time = sum(1 for p in self.scheduler.processes if p.state == "running")
        self.cpu_utilization = (active_time / self.current_time) * 100 if self.current_time > 0 else 0
        
        # Throughput
        completed = sum(1 for p in self.scheduler.processes if p.state == "completed")
        throughput = completed / self.current_time if self.current_time > 0 else 0
        
        # Update displays
        self.cpu_util_var.set(f"CPU Utilization: {self.cpu_utilization:.1f}%")
        self.throughput_var.set(f"Throughput: {throughput:.2f} processes/unit")
        self.context_switches_var.set(f"Context Switches: {self.context_switches}")

    def draw_enhanced_visualization(self):
        """Enhanced visualization with fixed CPU meter"""
        self.draw_process_list()
        self.draw_gantt_chart()
        self.draw_cpu_meter()
        self.draw_state_transitions()
        self.update_process_table()
        
        self.time_label.config(text=f"Time: {self.current_time}")
        self.calculate_metrics()
        self.root.update()

    def toggle_pause(self):
        """Pause/Resume simulation"""
        self.paused = not self.paused
        
    def step_simulation(self):
        """Enable single-step mode"""
        self.step_mode = True
        self.paused = False
        
    def save_config(self):
        """Save process configuration to file"""
        try:
            processes = []
            for p in self.scheduler.processes:
                processes.append({
                    'pid': p.pid,
                    'arrival_time': p.arrival_time,
                    'burst_time': p.burst_time,
                    'priority': p.priority
                })
            
            filename = 'process_config.json'
            with open(filename, 'w') as f:
                json.dump(processes, f, indent=2)
            messagebox.showinfo("Success", f"Configuration saved to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save configuration: {str(e)}")
    
    def load_config(self):
        """Load process configuration from file"""
        try:
            filename = 'process_config.json'
            if not os.path.exists(filename):
                messagebox.showerror("Error", "No saved configuration found")
                return
                
            with open(filename, 'r') as f:
                processes = json.load(f)
            
            # Reset current processes
            self.scheduler.processes.clear()
            
            # Load saved processes
            for p in processes:
                self.scheduler.add_process(
                    p['pid'],
                    p['arrival_time'],
                    p['burst_time'],
                    p['priority']
                )
            
            self.draw_process_list()
            messagebox.showinfo("Success", f"Loaded {len(processes)} processes")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {str(e)}")
    
    def draw_cpu_meter(self):
        """Draw CPU utilization meter"""
        meter_width = 400
        meter_height = 30
        x = 100
        y = 120
        
        # Background bar
        self.state_canvas.create_rectangle(x, y, x + meter_width, y + meter_height,
                                         fill="white", outline="black")
        
        # Calculate real CPU utilization
        running_processes = sum(1 for p in self.scheduler.processes if p.state == "running")
        total_time = self.current_time if self.current_time > 0 else 1
        self.cpu_utilization = (running_processes / total_time) * 100
        
        # CPU usage bar
        used_width = int((meter_width * self.cpu_utilization) / 100)
        self.state_canvas.create_rectangle(x, y, x + used_width, y + meter_height,
                                         fill="green", outline="")
        
        # CPU percentage text
        self.state_canvas.create_text(x + meter_width/2, y + meter_height/2,
                                    text=f"CPU: {self.cpu_utilization:.1f}%")
    
    def update_process_states(self, pid):
        """Enhanced process state management with transitions"""
        current_time = self.current_time
        last_state = None
        
        for p in self.scheduler.processes:
            if p.pid == pid:
                # Transition to running
                if p.state != "running":
                    self.animate_transition(p, "ready", "running")
                    p.update_state("running", current_time)
                    if self.last_process_state != pid:
                        self.context_switches += 1
                
                p.remaining_time -= 1
                if p.remaining_time == 0:
                    self.animate_transition(p, "running", "completed")
                    p.update_state("completed", current_time)
                
                self.last_process_state = pid
                self.current_process = p
            
            elif p.state != "completed":
                if p.state == "running":
                    self.animate_transition(p, "running", "ready")
                p.update_state("ready", current_time)

    def animate_transition(self, process, from_state, to_state):
        """Animate process state transitions"""
        x = 400 + (80 if to_state == "running" else 160)
        y = 20
        radius = 15
        
        # Highlight transition path
        if from_state == "ready" and to_state == "running":
            self.canvas.create_line(400 + radius, y, x - radius, y,
                                  fill="red", width=2, tags="transition")
        elif from_state == "running" and to_state == "completed":
            self.canvas.create_line(480 + radius, y, x - radius, y,
                                  fill="red", width=2, tags="transition")
        elif from_state == "running" and to_state == "ready":
            self.canvas.create_line(480, y + radius,
                                  480, y + 40,
                                  400, y + 40,
                                  400, y + radius,
                                  fill="red", width=2, tags="transition")
        
        self.root.after(500, lambda: self.canvas.delete("transition"))

    def calculate_metrics(self):
        """Enhanced performance metrics calculation"""
        if self.current_time == 0:
            return
            
        # CPU Utilization (weighted by time spent)
        total_run_time = sum(len([t for t, s in p.state_history if s == "running"]) 
                            for p in self.scheduler.processes)
        self.cpu_utilization = (total_run_time / self.current_time) * 100
        
        # Throughput (completed processes per unit time)
        completed = sum(1 for p in self.scheduler.processes if p.state == "completed")
        throughput = completed / self.current_time
        
        # Average Response Time
        avg_response = sum(p.response_time for p in self.scheduler.processes 
                         if p.response_time >= 0) / len(self.scheduler.processes)
        
        # Update displays
        self.cpu_util_var.set(f"CPU: {self.cpu_utilization:.1f}%")
        self.throughput_var.set(f"Throughput: {throughput:.2f}")
        self.context_switches_var.set(f"Switches: {self.context_switches}")
        
    def start_simulation(self):
        """Start scheduling simulation with process limit check"""
        if len(self.scheduler.processes) < self.scheduler.min_processes:
            messagebox.showwarning("Warning", 
                f"Need minimum {self.scheduler.min_processes} processes to run simulation")
            return
            
        if self.is_running:
            return
            
        # Reset process states
        for p in self.scheduler.processes:
            p.state = "ready"
            p.remaining_time = p.burst_time
        
        # Run selected algorithm
        algo = self.algo_var.get()
        try:
            if (algo == "rr"):
                gantt_data = self.scheduler.round_robin()
            elif (algo == "sjf"):
                gantt_data = self.scheduler.sjf_nonpreemptive()
            elif (algo == "sjf_p"):
                gantt_data = self.scheduler.sjf_preemptive()
            elif (algo == "priority"):
                gantt_data = self.scheduler.priority_scheduling(False)
            else:
                gantt_data = self.scheduler.priority_scheduling(True)
                
            self.animate_execution(gantt_data)
            self.update_statistics()
        except Exception as e:
            messagebox.showerror("Error", f"Simulation error: {str(e)}")
    
    def update_statistics(self):
        self.stats_text.delete(1.0, tk.END)
        stats = "Statistics:\n"
        total_wait = 0
        total_turnaround = 0
        
        for p in self.scheduler.processes:
            stats += f"Process {p.pid}: Wait={p.waiting_time}, Turnaround={p.turnaround_time}\n"
            total_wait += p.waiting_time
            total_turnaround += p.turnaround_time
            
        avg_wait = total_wait / len(self.scheduler.processes)
        avg_turnaround = total_turnaround / len(self.scheduler.processes)
        stats += f"\nAverage Wait Time: {avg_wait:.2f}\n"
        stats += f"Average Turnaround Time: {avg_turnaround:.2f}"
        
        self.stats_text.insert(1.0, stats)

    def set_speed(self, value):
        """Set animation speed"""
        try:
            self.animation_speed = float(value)
        except ValueError:
            self.animation_speed = 1.0
            
    def finalize_simulation(self):
        """Clean up after simulation ends"""
        self.is_running = False
        for p in self.scheduler.processes:
            if p.state != "completed":
                p.state = "completed"
        self.draw_enhanced_visualization()
        self.calculate_metrics()
        messagebox.showinfo("Complete", "Simulation finished!")

if __name__ == "__main__":
    root = tk.Tk()
    app = SchedulerGUI(root)
    root.mainloop()
