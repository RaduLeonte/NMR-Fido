'''Initialize main window.'''

import sys
import numpy as np
import nmrglue as ng
import matplotlib.pyplot as plt
from functools import partial
from copy import deepcopy
import pyqtgraph as pg


from PyQt6.QtCore import QSize, Qt, QThreadPool, QRunnable, pyqtSlot, QRectF
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QImage, QPixmap, QIcon, qRgb, QDoubleValidator, QColor, QPalette, QPainter, QPen, QResizeEvent

from spectrum import Spectrum


def start_app(args: list):
    spectrum: Spectrum = Spectrum()
    
    app: QApplication = QApplication(args)
    app.setStyle("fusion")

    window: MainWindow = MainWindow(spectrum)
    window.show()

    app.exec()


class MainWindow(QMainWindow):
    def __init__(self, spectrum) -> None:
        super().__init__()
        
        '''
        Window config
        '''
        self.setWindowTitle("NMR Fido")
        self.setWindowIcon(QIcon("python_icon.png"))
        
        # Minimum size
        min_size = (700, 400)
        self.setMinimumSize(QSize(*min_size))
        
        # Set init size based on screen aspect ratio
        screen_size = QApplication.primaryScreen().availableSize()
        if screen_size.width() >= screen_size.height():
            app_width = int(screen_size.width()*(2/3))
            app_size = QSize(app_width, int(app_width*(min_size[1]/min_size[0])))
        else:
            app_height = int(screen_size.height()*(2/3))
            app_size = QSize(int(app_height*(min_size[0]/min_size[1])), app_height)
        self.resize(app_size)
        
        self.threadpool = QThreadPool()

        # Main 
        layout = QHBoxLayout()
        
        '''
        Controls
        '''
        controls_group = QGroupBox("Phasing controls")
        controls_group.setFixedWidth(400)
        controls_group.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Expanding)
        controls_group_layout = QVBoxLayout()

        for i in [0, 1]:
            controls = QGroupBox(f"Dimension {i}")
            controls_layout = QVBoxLayout()
            
            # p0, p1
            for j in [0, 1]:
                pj_group = QWidget()
                pj_group_layout = QHBoxLayout()
                
                pj_label = QLabel(f"p{j}")
                pj_group_layout.addWidget(pj_label)
                
                pj_input = QLineEdit("0.0")
                pj_input.setObjectName(f"dim{i}_p{j}_input")
                pj_input.setEnabled(False)
                double_validator = QDoubleValidator()
                pj_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
                pj_input.setValidator(double_validator)
                pj_input.setMaximumWidth(50)
                pj_group_layout.addWidget(pj_input)
                pj_input.textChanged.connect(
                    partial(
                        self.threaded, self.phasing_input_callback, spectrum, f"dim{i}_p{j}"
                    )
                )
            
                pj_slider = QSlider(Qt.Orientation.Horizontal)
                pj_slider.setObjectName(f"dim{i}_p{j}_slider")
                pj_slider.setEnabled(False)
                pj_slider.setMinimum(-360)
                pj_slider.setMaximum(360)
                pj_slider.setValue(0)
                pj_slider.valueChanged.connect(
                    partial(
                        self.threaded, self.phasing_slider_callback, spectrum, f"dim{i}_p{j}"
                    )
                )
                pj_group_layout.addWidget(pj_slider)
                
                pj_group.setLayout(pj_group_layout)
                controls_layout.addWidget(pj_group)
        
            controls.setLayout(controls_layout)
            controls_group_layout.addWidget(controls)
            
            controls.setLayout(controls_layout)
            controls_group_layout.addWidget(controls)
        
        
        controls_group_layout.addStretch()
        controls_group.setLayout(controls_group_layout)
        #controls_group.resize(QSize(200, 800))
        layout.addWidget(controls_group)
        
        '''
        Spectrum
        '''
        spectrum_container = QGroupBox("Spectrum")
        spectrum_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        spectrum_container_layout = QVBoxLayout()
        
        import_spectrum_button = QPushButton(text="Import spectrum")
        import_spectrum_button.clicked.connect(lambda: self.import_spectrum_button_callback(spectrum))
        spectrum_container_layout.addWidget(import_spectrum_button)
        
        import_demo_spectrum_button = QPushButton(text="Import demo spectrum")
        import_demo_spectrum_button.clicked.connect(lambda: self.import_demo_spectrum_button_callback(spectrum))
        spectrum_container_layout.addWidget(import_demo_spectrum_button)
        
        plot_container_layout = QGridLayout()
        plot_container_layout.setHorizontalSpacing(0)
        plot_container_layout.setVerticalSpacing(0)
        
        spectrum_obj = SpectrumDisplay(self)
        spectrum_obj.setObjectName("spectrum_obj")
        #spectrum_obj.setStyleSheet("border-style: solid; border-width: 2px; border-color:black")
        spectrum_obj.setPixmap(self.initialize_empty_spectrum())
        plot_container_layout.addWidget(spectrum_obj, 1, 1)
        
        ax_h_height = 50
        ax_v_width = 100
        axs = [
            {"orientation": "h", "grid_pos": (0,1), "label_first": True},
            {"orientation": "v", "grid_pos": (1,0), "label_first": True},
            {"orientation": "v", "grid_pos": (1,2), "label_first": False},
            {"orientation": "h", "grid_pos": (2,1), "label_first": False}
        ]
        for ax_dict in axs:
            grid_pos = ax_dict["grid_pos"]
            orientation = ax_dict["orientation"]
            ax_label_name = "F2 [ppm]" if orientation == "h" else "F1 [ppm]"
            label_first = ax_dict["label_first"]
            
        
            # Axis container
            ax = QWidget()
            ax.setObjectName("spectrum_ax")
            ax.setVisible(False)
            if orientation == "h":
                ax.setFixedHeight(ax_h_height)
            else:
                ax.setFixedWidth(ax_v_width)
            #h_axis_bottom.setStyleSheet("border-style: solid; border-width: 2px; border-color:black")
            ax_layout = QVBoxLayout() if orientation == "h" else QHBoxLayout()
            ax_layout.setContentsMargins(0,0,0,0)
            ax_layout.setSpacing(0)
            
            # Ticks container
            ax_ticks = QLabel()
            ax_ticks.setObjectName("spectrum_ticks")
            
            # Axis label
            ax_label = QLabel(ax_label_name, alignment=Qt.AlignmentFlag.AlignCenter)
            
            if label_first:
                ax_layout.addWidget(ax_label)
                ax_layout.addWidget(ax_ticks)
            else:
                ax_layout.addWidget(ax_ticks)
                ax_layout.addWidget(ax_label)
            
            ax.setLayout(ax_layout)
            plot_container_layout.addWidget(ax, *grid_pos)
        
        
        
        
        spectrum_container_layout.addLayout(plot_container_layout)
        
        plot_graph = pg.PlotWidget()
        plot_graph.setVisible(False)
        plot_graph.setObjectName("horizontal_trace")
        plot_graph.setFixedHeight(200)
        background_color = QColor("FFFFFF")
        background_color.setAlpha(1)
        plot_graph.setBackground(background_color)
        plot_graph.getAxis("left").setTicks([])
        plot_graph.getAxis("left").setTextPen(background_color)
        plot_graph.getAxis("bottom").setTicks([])
        self.h_trace_line = plot_graph.plot()
        spectrum_container_layout.addWidget(plot_graph)
        
        spectrum_container.setLayout(spectrum_container_layout)
        layout.addWidget(spectrum_container)
        
        
        # Master container
        content = QWidget()
        content.setLayout(layout)
        self.setCentralWidget(content)


    def initialize_empty_spectrum(self) -> QPixmap:
        """Generate a 1x1 empty pixmap so the spectrum can be
        initialized with it.

        Returns:
            QPixmap: Empty pixmap.
        """
        img = QImage(0, 0, QImage.Format.Format_Indexed8)
        background_color = QColor("#F0F0F0")
        background_color.setAlpha(0)
        img.fill(background_color)
        return QPixmap.fromImage(img)
    
    
    def import_spectrum(self, spectrum: Spectrum, file_path: str) -> None:
        """Import spectrum from specified path.

        Args:
            spectrum (Spectrum): Main spectrum class.
            file_path (str): File path to fid file to import.
        """
        print(f"MainWindow.import_spectrum -> Loading:{file_path}")
        
        # Hand file off to spectrum class to load data and process.
        spectrum.load(file_path)
        
        # Enable spectrum axis.
        self.show_axis(spectrum)
        
        # Display processsed spectrum.
        self.display_spectrum(spectrum)
        
        # Enable phasing controls.
        self.toggle_phasing_controls()


    def import_spectrum_button_callback(self, spectrum: Spectrum) -> None:
        """Open a dialog for file browsing then imporrt
        specified fid file.

        Args:
            spectrum (Spectrum):  Main spectrum class.
        """
        files = QFileDialog.getOpenFileName(
            self,
            'Open file',
            'c:\\',
        )       
        self.import_spectrum(spectrum, files[0])
    
    
    def import_demo_spectrum_button_callback(self, spectrum: Spectrum) -> None:
        """Import demo spectrum from nmrglue wiki.

        Args:
            spectrum (Spectrum): Main spectrum class.
        """
        self.import_spectrum(spectrum, "src/test.fid")


    def display_spectrum(self, spectrum: Spectrum) -> None:    
        limitsX = [70, 40]
        limitsY = [135, 100]
        
        print(f"MainWindow.display_spectrum -> Dim1 X {spectrum.dim1_ppm_scale[0]=} {spectrum.dim1_ppm_scale[-1]=}")
        print(f"MainWindow.display_spectrum -> Dim0 Y {spectrum.dim0_ppm_scale[0]=} {spectrum.dim0_ppm_scale[-1]=}")
        x_index_start = np.where(spectrum.dim1_ppm_scale == min(spectrum.dim1_ppm_scale, key=lambda x:abs(x-limitsX[0])))[0][0]
        x_index_end = np.where(spectrum.dim1_ppm_scale == min(spectrum.dim1_ppm_scale, key=lambda x:abs(x-limitsX[1])))[0][0]
        
        y_index_start = np.where(spectrum.dim0_ppm_scale == min(spectrum.dim0_ppm_scale, key=lambda x:abs(x-limitsY[0])))[0][0]
        y_index_end = np.where(spectrum.dim0_ppm_scale == min(spectrum.dim0_ppm_scale, key=lambda x:abs(x-limitsY[1])))[0][0]
        
        data = deepcopy(spectrum.data)
    
        
        print(f"MainWindow.display_spectrum -> {data.shape=}")
        data = data[y_index_start:y_index_end, x_index_start:x_index_end]
        print(f"MainWindow.display_spectrum -> X limits {x_index_start=}; {x_index_end=}")
        print(f"MainWindow.display_spectrum -> Y limits {y_index_start=}; {y_index_end=}")
        
        #data = data[180:350, 1900:2160]
        
        data = np.flip(data, 0)
        
        h_trace_line = self.h_trace_line
        y = data[15]
        x = np.arange(0, len(y))
        h_trace_line.setData(x, y)
        
        print(f"MainWindow.display_spectrum -> {data.shape=}")
        
        if len(data) == 0:
            return

        def _median_absolute_deviation(data, k=1.4826):
            """ Median Absolute Deviation: a "Robust" version of standard deviation.
                Indices variabililty of the sample.
                https://en.wikipedia.org/wiki/Median_absolute_deviation
            """
            data = np.ma.array(data).compressed()
            median = np.median(data)
            return k*np.median(np.abs(data - median))
        
        max_value = _median_absolute_deviation(data)*30
        min_value = _median_absolute_deviation(data)*1
        print(f"MainWindow.display_spectrum -> {min_value=} {max_value=}")
        
        
        normalized_array = (data - min_value) / (max_value - min_value)
        normalized_array = np.clip(normalized_array, 0, 1)  # Ensure values stay within [0, 1]
        
        cmap = plt.get_cmap("magma")
        rgba_array = cmap(normalized_array)
        rgb_array = (rgba_array[:, :, :3] * 255).astype(np.uint8)
        
        img = QImage(rgb_array.data, rgb_array.shape[1], rgb_array.shape[0], QImage.Format.Format_RGB888)
        
        pixmap = QPixmap.fromImage(img)
        
        spectrum_object = self.findChild(QLabel, "spectrum_obj")
        
        pixmap = pixmap.scaled(spectrum_object.width(), spectrum_object.height())
        spectrum_object._pixmap = pixmap
        spectrum_object.setPixmap(pixmap)
    
    
    def show_axis(self, spectrum: Spectrum) -> None:
        axs = self.findChildren(QWidget, "spectrum_ax")
        axis_config = {
            "top": False,
            "left": False,
            "right": True,
            "bottom": True
        }
        for ax in axs:
            
            ax_ticks = ax.findChild(QLabel, "spectrum_ticks")
            ax_children = [c.objectName() for c in ax.children() if isinstance(c, QLabel)]
            ax_label_first = True if ax_children.index("spectrum_ticks") == 1 else False
            ax_orientation = "h" if ax_ticks.width() > ax_ticks.height() else "v"
            
            ax_position = ""
            if ax_orientation == "h" and ax_label_first:
                ax_position = "top"
            elif ax_orientation == "v" and ax_label_first:
                ax_position = "left"
            elif ax_orientation == "v" and not ax_label_first:
                ax_position = "right"
            elif ax_orientation == "h" and not ax_label_first:
                ax_position = "bottom"
                
            if axis_config[ax_position] != True:
                continue
            
            ax.setVisible(True)
            ax_ticks_w = ax_ticks.width()
            ax_ticks_h = ax_ticks.height()
            ax_orientation = "h" if ax_ticks.width() > ax_ticks.height() else "v"
            
            ax_label_name = f'{spectrum.dic["FDF2LABEL"]} [ppm]' if ax_orientation == "h" else f'{spectrum.dic["FDF1LABEL"]}\n[ppm]'
            ax_label = ax.findChild(QLabel, "")
            ax_label.setText(ax_label_name)
            
            

            pixmap = QPixmap(ax_ticks_w, ax_ticks_h)
            background_color = QColor("#F0F0F0")
            background_color.setAlpha(1)
            pixmap.fill(background_color)
            
            painter = QPainter(pixmap)
            pen = QPen()
            pen.setColor(QColor("#F0F0F0"))
            pen.setWidth(2)
            painter.setPen(pen)
            
            
            ax_ppm_scale = spectrum.dim1_ppm_scale if ax_orientation == "h" else spectrum.dim0_ppm_scale
            
            def generate_ticks(ppm_scale: np.array, axis_size: float, nr_ticks:int=6) -> list:
                ticks_ppm = np.linspace(np.floor(ppm_scale[0]), np.ceil(ppm_scale[-1]), nr_ticks)
                ticks_unitless = np.absolute((ticks_ppm - ppm_scale[0]) / (ppm_scale[0] - ppm_scale[-1]))
                ticks_px = list(ticks_unitless * axis_size)
                ticks_px = [int(p) for p in ticks_px]
                return ticks_ppm, ticks_px
                
            ticks_labels, ticks_positions = generate_ticks(ax_ppm_scale, max(ax_ticks_w, ax_ticks_h), 10)
            
            tick_length = 5   # length of each tick
            text_width = 40
            text_pos = 10
            text_height = 10

            # Loop to draw ticks vertically
            for i in range(len(ticks_positions)):
                p = ticks_positions[i]
                label = ticks_labels[i]
                if ax_orientation == "h":
                    if p - text_width < 0 or p + text_width > ax_ticks_w:
                        continue
                    
                    if ax_label_first:
                        ticks_start_pos = (p, ax_ticks_h)
                        ticks_end_pos = (p, ax_ticks_h-tick_length)
                        text_rectF = QRectF(p-text_width/2, ax_ticks_h-text_pos-text_height, text_width, text_height)
                    else:
                        ticks_start_pos = (p, 0)
                        ticks_end_pos = (p, tick_length)
                        text_rectF = QRectF(p-text_width/2, text_pos, text_width, text_height)
                else:
                    if p - text_height < 0 or p + text_height > ax_ticks_h:
                        continue
                    
                    if ax_label_first:
                        ticks_start_pos = (ax_ticks_w, p)
                        ticks_end_pos = (ax_ticks_w-tick_length, p)
                        text_rectF = QRectF(ax_ticks_w-text_pos-text_width, p-text_height/2, text_width, text_height)
                    else:
                        ticks_start_pos = (0, p)
                        ticks_end_pos = (tick_length, p)
                        text_rectF = QRectF(text_pos, p-text_height/2, text_width, text_height)
                    
                painter.drawLine(*ticks_start_pos, *ticks_end_pos)
                painter.drawText(
                    text_rectF,
                    Qt.AlignmentFlag.AlignCenter,
                    str(np.around(label, 2))
                )
            
            painter.end()
            ax_ticks.setPixmap(pixmap)
    
    
    def toggle_phasing_controls(self) -> None:
        """Find all phasing controls float inputs and sliders and
        enable them.
        """
        h_trace = self.findChild(pg.PlotWidget, "horizontal_trace")
        h_trace.setVisible(True)
        
        
        for i in [0, 1]:
            for j in [0, 1]:
                phasing_input = self.findChild(QLineEdit, f"dim{i}_p{j}_input")
                phasing_input.setEnabled(not phasing_input.isEnabled())
                
                phasing_slider = self.findChild(QSlider, f"dim{i}_p{j}_slider")
                phasing_slider.setEnabled(not phasing_slider.isEnabled())
    
    
    def threaded(self, *args):
        """Run a function (args[0]) with arguments (args[1:]) on a different thread.
        """
        worker = Worker(*args)
        self.threadpool.start(worker)
    
    
    def phasing_input_callback(self, spectrum: Spectrum, identifier: str, phasing_input_text: str) -> None:
        """Callback for phasing float inputs. On change, update the slider and rephase spectrum.

        Args:
            spectrum (Spectrum): Main spectrum class.
            identifier (str): Identifier of callee input.
            phasing_input_text (str): Current text content of the input.
        """
        print(f"MainWindow.phasing_input_callback -> {phasing_input_text}")
        # Select callee
        phasing_input = self.findChild(QLineEdit, f"{identifier}_input")
        # Immediately return if callee cannot be found
        if phasing_input == None:
            return
        
        # If the the input text content is not a valid float, return immediately.
        try:
            int(float(phasing_input_text))
        except ValueError:
            return
        
        # Find the float input's corresponding slider and set it to the input value.
        self.findChild(
            QSlider, f"{identifier}_slider"
        ).setValue(
            int(float(
                phasing_input_text
            ))
        )
        
        # Update the plot with new phasing values
        self.update_plot(spectrum)
    
    
    def phasing_slider_callback(self, spectrum: Spectrum, identifier: str, phasing_slider_value: int) -> None:
        """Callback for phasing slider. On change, update the float input and rephase spectrum.

        Args:
            spectrum (Spectrum): Main spectrum class.
            identifier (str): Identifier of callee slider.
            phasing_slider_value (int): Current slider value.
        """
        print(f"MainWindow.phasing_slider_callback -> {phasing_slider_value}")
        # Immediately return if callee slider cannot be found
        if self.findChild(QLineEdit, f"{identifier}_input") == None:
            return

        # Find the slider's corresponding float input and set its text content to the slider value.
        self.findChild(
            QLineEdit, f"{identifier}_input"
        ).setText(
            str(
                self.findChild(QSlider, f"{identifier}_slider").value()
                )
        )
        
        # Update the plot with new phasing values
        self.update_plot(spectrum)
    
    
    def update_plot(self, spectrum: Spectrum) -> None:
        """Update the spectrum's phasing values and reprocess it before displaying it.

        Args:
            spectrum (Spectrum): Main spectrum class.
        """
        # Get all phasing values from the inputs.
        phasing_values = [
            self.findChild(QLineEdit, "dim0_p0_input").text(),
            self.findChild(QLineEdit, "dim0_p1_input").text(),
            self.findChild(QLineEdit, "dim1_p0_input").text(),
            self.findChild(QLineEdit, "dim1_p1_input").text()
        ]
        
        # Set phasing values in the spectrum class
        spectrum.phase([float(p) if p != "" else 0.0 for p in phasing_values])
        
        # Display phased spectrum
        self.display_spectrum(spectrum)


class SpectrumDisplay(QLabel):
    def __init__(self, *args, **kwargs):
        QLabel.__init__(self)
        self._pixmap = MainWindow.initialize_empty_spectrum(self)
        #print(f"SpectrumDisplay -> {self._pixmap.size()=}")
        
    def resizeEvent(self, e: QResizeEvent):
        #print(f"SpectrumDisplay.resizeEvent -> {self._pixmap.size()=}")
        self.setPixmap(
            self._pixmap.scaled(
                self.width(), self.height()
            )
        )


class Worker(QRunnable):
    '''
    Worker thread

    Inherits from QRunnable to handler worker thread setup, signals and wrap-up.

    :param callback: The function callback to run on this worker thread. Supplied args and
                     kwargs will be passed through to the runner.
    :type callback: function
    :param args: Arguments to pass to the callback function
    :param kwargs: Keywords to pass to the callback function

    '''

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        # Store constructor arguments (re-used for processing)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    @pyqtSlot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        self.fn(*self.args, **self.kwargs)


class Color(QWidget):
    def __init__(self, color):
        super().__init__()
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color))
        self.setPalette(palette)