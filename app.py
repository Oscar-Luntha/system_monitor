import gi
gi.require_version("Gtk", "4.0")
gi.require_version('Notify', '0.7')
from gi.repository import Gtk, GLib, Notify
import psutil
import time
import threading

class MyApp(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="System Resource Monitor")
        self.set_margin_start(10)
        self.set_margin_end(10)
        self.set_margin_top(10)
        self.set_margin_bottom(10)
        self.set_default_size(600, 600)

        Notify.init("System Resource Monitor")
# Labels for CPU, Memor, Disk, and Network
        self.cpu_label = Gtk.Label(label="CPU Usage: Loading...", xalign=0)
        self.memory_label = Gtk.Label(label="Memory Usage: Loading...", xalign=0)
        self.disk_label = Gtk.Label(label="Disk Usage: Loading...", xalign=0)
        self.network_label = Gtk.Label(label="Network Usage: Loading...", xalign=0)
# Progress Bars for CPU, Memory, Disk, and Network
        self.cpu_bar = Gtk.ProgressBar()
        self.memory_bar = Gtk.ProgressBar()
        self.disk_bar = Gtk.ProgressBar()
        self.network_bar = Gtk.ProgressBar()

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        vbox.append(self.cpu_label)
        vbox.append(self.cpu_bar)
        vbox.append(self.memory_label)
        vbox.append(self.memory_bar)
        vbox.append(self.disk_label)
        vbox.append(self.disk_bar)
        vbox.append(self.network_label)
        vbox.append(self.network_bar)
 # Grid layout for input fields
        grid = Gtk.Grid()
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)

        cpu_label = Gtk.Label(label="CPU Threshold:")
        self.cpu_threshold_input = Gtk.SpinButton()
        self.cpu_threshold_input.set_range(0, 100)
        self.cpu_threshold_input.set_value(80)
        self.cpu_threshold_input.set_increments(1, 10)
        memory_label = Gtk.Label(label="Memory Threshold:")
        self.memory_threshold_input = Gtk.SpinButton()
        self.memory_threshold_input.set_range(0, 100)
        self.memory_threshold_input.set_value(80)
        self.memory_threshold_input.set_increments(1, 10)
        disk_label = Gtk.Label(label="Disk Threshold:")
        self.disk_threshold_input = Gtk.SpinButton()
        self.disk_threshold_input.set_range(0, 100)
        self.disk_threshold_input.set_value(80)
        self.disk_threshold_input.set_increments(1, 10)
        grid.attach(cpu_label, 0, 0, 1, 1)
        grid.attach(self.cpu_threshold_input, 1, 0, 1, 1)
        grid.attach(memory_label, 0, 1, 1, 1)
        grid.attach(self.memory_threshold_input, 1, 1, 1, 1)
        grid.attach(disk_label, 0, 2, 1, 1)
        grid.attach(self.disk_threshold_input, 1, 2, 1, 1)
        vbox.append(grid)

#Creatung a TreeView for processes
        self.process_liststore = Gtk.ListStore(str, int, float, float)
        self.process_view = Gtk.TreeView(model=self.process_liststore)

        # Columns for the process TreeView
        process_name_column = Gtk.TreeViewColumn("Process Name", Gtk.CellRendererText(), text=0)
        process_pid_column = Gtk.TreeViewColumn("PID", Gtk.CellRendererText(), text=1)
        cpu_column = Gtk.TreeViewColumn("CPU %", Gtk.CellRendererText(), text=2)
        memory_column = Gtk.TreeViewColumn("Memory %", Gtk.CellRendererText(), text=3)

        self.process_view.append_column(process_name_column)
        self.process_view.append_column(process_pid_column)
        self.process_view.append_column(cpu_column)
        self.process_view.append_column(memory_column)

        vbox.append(self.process_view)

 # creating a Toggle button to show/hide process list
        self.toggle_button = Gtk.Button(label="Show/Hide Process List")
        self.toggle_button.connect("clicked", self.toggle_process_list_visibility)
        vbox.append(self.toggle_button)

        # Header Bar with Refresh Button
        hb = Gtk.HeaderBar()
        self.set_titlebar(hb)
        refresh_button = Gtk.Button(icon_name="view-refresh-symbolic")
        refresh_button.connect("clicked", self.refresh_data)
        hb.pack_end(refresh_button)

        self.set_child(vbox)

 # Starting a thread to update resource usage
        self.thread = threading.Thread(target=self.update_resource_usage)
        self.thread.daemon = True
        self.thread.start()

# Initializing alerts
        self.cpu_alert = False
        self.memory_alert = False
        self.disk_alert = False

# Tracking process list visibility
        self.process_list_visible = True

    def refresh_data(self, button):
        self.update_data()

    def toggle_process_list_visibility(self, button):
        self.process_list_visible = not self.process_list_visible
        if self.process_list_visible:
            self.process_view.show()
        else:
            self.process_view.hide()

    def update_data(self):
# Getting the  CPU, Memory, Disk, and Network usage 
        cpu_usage = psutil.cpu_percent()
        memory_info = psutil.virtual_memory()
        disk_usage = psutil.disk_usage('/')
        net_io = psutil.net_io_counters()

        memory_usage = memory_info.percent
        disk_usage_percent = disk_usage.percent
        network_usage = net_io.bytes_sent + net_io.bytes_recv
# Updating the labels in the GUI
        GLib.idle_add(self.cpu_label.set_text, f"CPU Usage: {cpu_usage}%")
        GLib.idle_add(self.memory_label.set_text, f"Memory Usage: {memory_usage}%")
        GLib.idle_add(self.disk_label.set_text, f"Disk Usage: {disk_usage_percent}%")
        GLib.idle_add(self.network_label.set_text, f"Network Usage: {network_usage / (1024 * 1024):.2f} MB")

# Updating the progress bars
        GLib.idle_add(self.cpu_bar.set_fraction, cpu_usage / 100)
        GLib.idle_add(self.memory_bar.set_fraction, memory_usage / 100)
        GLib.idle_add(self.disk_bar.set_fraction, disk_usage_percent / 100)
        GLib.idle_add(self.network_bar.set_fraction, min(network_usage / (1024 * 1024 * 100), 1))  # Scale network usage

# Updating the process list
        if self.process_list_visible:
            self.update_process_list()

# Checking for threshold exceed and trigger notification
        self.check_threshold(cpu_usage, memory_usage, disk_usage_percent)

    def update_process_list(self):
        self.process_liststore.clear()
# Getting all processes and sort them by CPU and memory usage
        processes = []
        for process in psutil.process_iter(['name', 'pid', 'cpu_percent', 'memory_percent']):
            try:
                processes.append((process.info['name'], process.info['pid'], process.info['cpu_percent'], process.info['memory_percent']))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue

 # Sorting by CPU and memory usage and get the top 10
        processes.sort(key=lambda p: (p[2], p[3]), reverse=True)
        top_processes = processes[:10]

 # Adding top processes to the list stores
        for process in top_processes:
            self.process_liststore.append([process[0], process[1], process[2], process[3]])

    def check_threshold(self, cpu_usage, memory_usage, disk_usage_percent):
        cpu_threshold = self.cpu_threshold_input.get_value()
        memory_threshold = self.memory_threshold_input.get_value()
        disk_threshold = self.disk_threshold_input.get_value()

        if cpu_usage >= cpu_threshold and not self.cpu_alert:
            notification = Notify.Notification.new(
                "CPU Usage Alert",
                f"CPU usage exceeded {cpu_threshold}%! Current value: {cpu_usage}%",
                "dialog-warning"
            )
            notification.show()
            self.cpu_alert = True
        elif cpu_usage < cpu_threshold:
            self.cpu_alert = False

        if memory_usage >= memory_threshold and not self.memory_alert:
            notification = Notify.Notification.new(
                "Memory Usage Alert",
                f"Memory usage exceeded {memory_threshold}%! Current value: {memory_usage}%",
                "dialog-warning"
            )
            notification.show()
            self.memory_alert = True
        elif memory_usage < memory_threshold:
            self.memory_alert = False

        if disk_usage_percent >= disk_threshold and not self.disk_alert:
            notification = Notify.Notification.new(
                "Disk Usage Alert",
                f"Disk usage exceeded {disk_threshold}%! Current value: {disk_usage_percent}%",
                "dialog-warning"
            )
            notification.show()
            self.disk_alert = True
        elif disk_usage_percent < disk_threshold:
            self.disk_alert = False

    def update_resource_usage(self):
        while True:
            self.update_data()
            time.sleep(2)

class SystemMonitorApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.system.monitor")

    def do_activate(self):
        window = MyApp(self)
        window.show()

    def do_startup(self):
        Gtk.Application.do_startup(self)

if __name__ == "__main__":
    app = SystemMonitorApp()
    app.run(None)
