class Process:
    def __init__(self, pid, arrival_time, burst_time, priority=0):
        self.pid = pid
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.remaining_time = burst_time
        self.priority = priority
        self.waiting_time = 0
        self.turnaround_time = 0
        self.completion_time = 0
        self.response_time = -1
        self.state = "ready"  # ready, running, completed
        self.state_history = []  # Track state changes
        self.start_time = -1  # Track when process first starts
        
    def update_state(self, new_state, time):
        """Record state transition with timestamp"""
        if self.state != new_state:
            self.state = new_state
            self.state_history.append((time, new_state))
            
    def update_state(self, new_state, current_time):
        """Update process state and track metrics"""
        if self.state != new_state:
            self.state = new_state
            if new_state == "running":
                if self.start_time == -1:
                    self.start_time = current_time
                    self.response_time = current_time - self.arrival_time
            elif new_state == "completed":
                self.completion_time = current_time
                self.turnaround_time = self.completion_time - self.arrival_time
                self.waiting_time = self.turnaround_time - self.burst_time

class CPUScheduler:
    """CPU Scheduler implementation with various scheduling algorithms.
    Supports 3-10 processes with a fixed time quantum of 3."""
    
    def __init__(self):
        self.processes = []
        self.time_quantum = 3  # Fixed time quantum
        self.min_processes = 3
        self.max_processes = 10

    def validate_input(self, arrival_time, burst_time, priority):
        """Validates process parameters and enforces process limits."""
        if arrival_time < 0 or burst_time <= 0 or priority < 0:
            raise ValueError("Invalid input parameters")
        if len(self.processes) >= self.max_processes:
            raise ValueError(f"Maximum process limit ({self.max_processes}) reached")
        if len(self.processes) == 0 and arrival_time > 0:
            raise ValueError("First process must arrive at time 0")

    def check_minimum_processes(self):
        """Verify minimum process requirement"""
        if len(self.processes) < self.min_processes:
            raise ValueError(f"Need minimum {self.min_processes} processes to run scheduler")

    def add_process(self, pid, arrival_time, burst_time, priority=0):
        self.validate_input(arrival_time, burst_time, priority)
        self.processes.append(Process(pid, arrival_time, burst_time, priority))

    def round_robin(self):
        """Round Robin scheduling with fixed quantum=3"""
        self.check_minimum_processes()
        time = 0
        queue = []
        gantt_chart = []
        time_chart = []  # Track execution times
        completed_processes = 0
        
        while completed_processes < len(self.processes):
            # Add newly arrived processes to queue
            for process in self.processes:
                if (process.arrival_time <= time and 
                    process.remaining_time > 0 and 
                    process not in queue):
                    queue.append(process)
            
            if queue:
                current_process = queue.pop(0)
                execution_time = min(self.time_quantum, current_process.remaining_time)
                
                # Record execution period
                gantt_chart.append(current_process.pid)
                time_chart.append((time, time + execution_time))
                current_process.update_state("running", time)
                
                time += execution_time
                current_process.remaining_time -= execution_time
                
                if current_process.remaining_time == 0:
                    current_process.update_state("completed", time)
                    current_process.completion_time = time
                    current_process.turnaround_time = time - current_process.arrival_time
                    current_process.waiting_time = current_process.turnaround_time - current_process.burst_time
                    completed_processes += 1
                else:
                    queue.append(current_process)
                    current_process.update_state("ready", time)
            else:
                time += 1
        
        return gantt_chart, time_chart

    def sjf_nonpreemptive(self):
        """Non-preemptive SJF with improved timing"""
        self.check_minimum_processes()
        time = 0
        completed_processes = 0
        gantt_chart = []
        time_chart = []
        remaining_processes = self.processes.copy()

        while completed_processes < len(self.processes):
            ready_processes = [p for p in remaining_processes 
                             if p.arrival_time <= time]
            if not ready_processes:
                time += 1
                continue

            current_process = min(ready_processes, 
                                key=lambda p: (p.burst_time, p.arrival_time, p.pid))
            
            gantt_chart.append(current_process.pid)
            start_time = time
            time += current_process.burst_time
            time_chart.append((start_time, time))
            
            current_process.update_state("running", start_time)
            current_process.update_state("completed", time)
            current_process.completion_time = time
            current_process.turnaround_time = time - current_process.arrival_time
            current_process.waiting_time = current_process.turnaround_time - current_process.burst_time
            
            completed_processes += 1
            remaining_processes.remove(current_process)

        return gantt_chart, time_chart

    def sjf_preemptive(self):
        """Preemptive Shortest Job First scheduling with timing data"""
        time = 0
        completed = 0
        gantt_chart = []
        time_chart = []
        last_switch = None
        current_pid = None
        
        while completed < len(self.processes):
            ready = [p for p in self.processes 
                    if p.arrival_time <= time and p.remaining_time > 0]
            if not ready:
                time += 1
                continue

            # Break ties using process ID
            current = min(ready, key=lambda p: (p.remaining_time, p.pid))
            
            # Record process switch
            if current.pid != current_pid:
                if current_pid is not None:
                    time_chart.append((last_switch, time))
                gantt_chart.append(current.pid)
                last_switch = time
                current_pid = current.pid

            current.state = "running"
            if current.response_time == -1:
                current.response_time = time - current.arrival_time

            time += 1
            current.remaining_time -= 1

            if current.remaining_time == 0:
                time_chart.append((last_switch, time))
                current.completion_time = time
                current.turnaround_time = time - current.arrival_time
                current.waiting_time = current.turnaround_time - current.burst_time
                current.state = "completed"
                completed += 1
                current_pid = None

        return gantt_chart, time_chart

    def priority_scheduling(self, preemptive=False):
        """Priority scheduling with improved timing"""
        time = 0
        completed_processes = 0
        gantt_chart = []
        time_chart = []
        last_switch = 0
        
        while completed_processes < len(self.processes):
            ready_processes = [p for p in self.processes 
                             if p.arrival_time <= time and p.remaining_time > 0]
            if not ready_processes:
                time += 1
                continue

            current_process = min(ready_processes, 
                                key=lambda p: (p.priority, p.pid))
            
            if not gantt_chart or gantt_chart[-1] != current_process.pid:
                if gantt_chart:  # Record previous execution period
                    time_chart.append((last_switch, time))
                gantt_chart.append(current_process.pid)
                last_switch = time
                
            if preemptive:
                time += 1
                current_process.remaining_time -= 1
            else:
                exec_time = current_process.remaining_time
                time += exec_time
                current_process.remaining_time = 0

            if current_process.remaining_time == 0:
                time_chart.append((last_switch, time))
                current_process.completion_time = time
                current_process.turnaround_time = time - current_process.arrival_time
                current_process.waiting_time = current_process.turnaround_time - current_process.burst_time
                completed_processes += 1

        return gantt_chart, time_chart

    def display_gantt_chart(self, gantt_data):
        """Display enhanced Gantt chart with accurate timings"""
        gantt_chart, time_chart = gantt_data
        print("\nGantt Chart:")
        
        # Print top border
        print("╔" + "══════╦" * (len(gantt_chart)-1) + "══════╗")
        
        # Print process IDs
        print("║", end="")
        for pid in gantt_chart:
            print(f" P{pid:2} ║", end="")
        print()
        
        # Print bottom border
        print("╚" + "══════╩" * (len(gantt_chart)-1) + "══════╝")
        
        # Print timeline with actual times
        print(" ", end="")
        for start, end in time_chart:
            print(f"{start:<6}", end="")
        print(f"{time_chart[-1][1]}")  # Print final time

    def display_statistics(self):
        total_waiting_time = 0
        total_turnaround_time = 0

        for process in self.processes:
            total_waiting_time += process.waiting_time
            total_turnaround_time += process.turnaround_time
            print(f"Process {process.pid}: Waiting Time = {process.waiting_time}, Turnaround Time = {process.turnaround_time}")

        average_waiting_time = total_waiting_time / len(self.processes)
        average_turnaround_time = total_turnaround_time / len(self.processes)

        print(f"Total Waiting Time = {total_waiting_time}, Average Waiting Time = {average_waiting_time}")
        print(f"Total Turnaround Time = {total_turnaround_time}, Average Turnaround Time = {average_turnaround_time}")
        print("\nProcess States:")
        for process in self.processes:
            print(f"Process {process.pid}: {process.state}")
        print(f"Average Response Time = {sum(p.response_time for p in self.processes) / len(self.processes)}")

    def calculate_waiting_time(self, process, current_time):
        """Calculate accurate waiting time"""
        if process.state == "ready":
            return current_time - process.arrival_time - \
                   (process.burst_time - process.remaining_time)
        return process.waiting_time

    def menu(self):
        """Interactive menu for the CPU Scheduler."""
        while True:
            print("\nCPU Scheduler Menu")
            print("1. Add Process")
            print(f"2. Run Round Robin (Time Quantum: {self.time_quantum})")
            print("3. Run SJF (Non-preemptive)")
            print("4. Run SJF (Preemptive)")
            print("5. Run Priority (Non-preemptive)")
            print("6. Run Priority (Preemptive)")
            print("7. Display Statistics")
            print("8. Exit")
            
            try:
                choice = int(input("Enter your choice: "))
                if choice == 1:
                    if len(self.processes) < self.min_processes:
                        print(f"Note: Minimum {self.min_processes} processes required")
                    pid = len(self.processes) + 1
                    arrival_time = int(input("Enter arrival time: "))
                    burst_time = int(input("Enter burst time: "))
                    priority = int(input("Enter priority (lower number = higher priority): "))
                    self.add_process(pid, arrival_time, burst_time, priority)
                elif choice == 2:
                    self.display_gantt_chart(self.round_robin())
                elif choice == 3:
                    self.display_gantt_chart(self.sjf_nonpreemptive())
                elif choice == 4:
                    self.display_gantt_chart(self.sjf_preemptive())
                elif choice == 5:
                    self.display_gantt_chart(self.priority_scheduling(preemptive=False))
                elif choice == 6:
                    self.display_gantt_chart(self.priority_scheduling(preemptive=True))
                elif choice == 7:
                    self.display_statistics()
                elif choice == 8:
                    break
                else:
                    print("Invalid choice. Please try again.")
            except ValueError as e:
                print(f"Error: {str(e)}")
            except Exception as e:
                print(f"An unexpected error occurred: {str(e)}")

if __name__ == "__main__":
    scheduler = CPUScheduler()
    scheduler.menu()
