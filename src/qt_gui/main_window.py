'''Initialize main window.'''

import os
import numpy as np
import nmrglue as ng
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from functools import partial
from copy import deepcopy
import pyqtgraph as pg
from contourpy import contour_generator


from PyQt6.QtCore import QSize, Qt, QThreadPool, QRunnable, pyqtSlot, QPointF, QRectF
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QImage, QPixmap, QIcon, qRgb, QDoubleValidator, QColor, QPalette, QPainter, QPen, QResizeEvent, QTransform

from spectrum import Spectrum


def start_app(args: list):
    spectrum: Spectrum = Spectrum()
    
    app: QApplication = QApplication(args)
    app.setStyle("fusion")

    window: MainWindow = MainWindow(spectrum, app)
    window.show()

    app.exec()


class MainWindow(QMainWindow):
    def __init__(self, spectrum: Spectrum, app: QApplication) -> None:
        super().__init__()
        
        self.app = app
        
        """
        Window config
        """
        self.setWindowTitle("NMR Fido")
        #self.setWindowIcon(QIcon("icon.png"))
        
        # Minimum size
        min_size = (820, 400)
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
        
        """Thread pool"""
        self.threadpool = QThreadPool()


        """
        Main container
        """
        layout = QHBoxLayout()
        
        '''
        Window Region: Phasing controls
        '''
        controls_group = QGroupBox("Phasing controls")
        controls_group.setFixedWidth(400)
        controls_group.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Expanding)
        controls_group_layout = QVBoxLayout()
        controls_group_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        for i in [0, 1]:
            controls_group_layout.addWidget(self.create_phasing_controls(i, spectrum))
        
        controls_group_layout.addStretch()
        controls_group.setLayout(controls_group_layout)
        #controls_group.resize(QSize(200, 800))
        layout.addWidget(controls_group)
        
        '''
        Window Region: Spectrum
        '''
        spectrum_container = QGroupBox("Spectrum")
        spectrum_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        spectrum_container_layout = QVBoxLayout()
        
        """Import buttons"""
        spectrum_container_layout.addLayout(self.create_import_buttons(spectrum))
        
        """Plot grid"""
        plot_container = QWidget()
        plot_container_layout = QGridLayout()
        plot_container_layout.setHorizontalSpacing(0)
        plot_container_layout.setVerticalSpacing(0)
        #plot_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        """Main plot"""
        #spectrum_obj = SpectrumDisplay(self)
        #spectrum_obj.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        #spectrum_obj.setObjectName("spectrum_obj")
        #spectrum_obj.setStyleSheet("border-style: solid; border-width: 1px; border-color:white")
        #spectrum_obj.setPixmap(self.initialize_empty_spectrum())
        #plot_container_layout.addWidget(spectrum_obj, 1, 1)
        
        self.plot = pg.PlotWidget()
        plot_layout = pg.GraphicsLayout()
        self.plot.setCentralItem(plot_layout)
        self.plot_ax = pg.PlotItem()
        self.plot_ax.showAxis("right")
        self.plot_ax.hideAxis("left")
        self.plot_ax.getAxis("bottom").setLabel("Dim 0 [ppm]", color="#FFFFFF")
        self.plot_ax.getAxis("bottom").setTextPen("w")
        self.plot_ax.getAxis("right").setLabel("Dim 1\n[ppm]", color="#FFFFFF")
        self.plot_ax.getAxis("right").label.setRotation(0)
        self.plot_ax.getAxis("right").label.setTextWidth(60)
        self.plot_ax.getAxis("right").setTextPen("w")
        #self.plot_ax.getAxis("right").label.adjustSize()
        #self.plot_ax.getAxis("right").setStyle(tickTextOffset=500)
        self.plot.setBackground(QColor(0, 0, 0, 0))
        plot_layout.addItem(self.plot_ax)
        self.plot_contours = []
        self.plot_levels = []
        plot_container_layout.addWidget(self.plot, 1, 1)
        
        """Horizontal trace"""
        plot_container_layout.addWidget(self.create_horizontal_trace(), 2, 1)
        
        """Plot axes"""
        #self.create_spectrum_axes(plot_container_layout)
        
        # Add plot grid container to main
        plot_container.setLayout(plot_container_layout)
        spectrum_container_layout.addWidget(plot_container)
        
        # Add spectrum window region to main window
        spectrum_container.setLayout(spectrum_container_layout)
        layout.addWidget(spectrum_container)
        
        
        """
        Master container
        """
        content = QWidget()
        content.setLayout(layout)
        self.setCentralWidget(content)
        
        
    def create_phasing_controls(self, dimension_index: int, spectrum: Spectrum) -> QGroupBox:
        controls = QGroupBox(f"Dimension {dimension_index}")
        controls_layout = QVBoxLayout()
        
        # p0, p1
        for j in [0, 1]:
            pj_group = QWidget()
            pj_group_layout = QHBoxLayout()
            
            pj_label = QLabel(f"p{j}")
            pj_group_layout.addWidget(pj_label)
            
            pj_input = QLineEdit("0.0")
            pj_input.setObjectName(f"dim{dimension_index}_p{j}_input")
            pj_input.setEnabled(False)
            double_validator = QDoubleValidator()
            pj_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pj_input.setValidator(double_validator)
            pj_input.setMaximumWidth(50)
            pj_group_layout.addWidget(pj_input)
            pj_input.textChanged.connect(
                partial(
                    self.threaded, self.phasing_input_callback, spectrum, f"dim{dimension_index}_p{j}"
                )
            )
        
            pj_slider = QSlider(Qt.Orientation.Horizontal)
            pj_slider.setObjectName(f"dim{dimension_index}_p{j}_slider")
            pj_slider.setEnabled(False)
            pj_slider.setMinimum(-360)
            pj_slider.setMaximum(360)
            pj_slider.setValue(0)
            pj_slider.valueChanged.connect(
                partial(
                    self.threaded, self.phasing_slider_callback, spectrum, f"dim{dimension_index}_p{j}"
                )
            )
            pj_group_layout.addWidget(pj_slider)
            
            pj_group.setLayout(pj_group_layout)
            controls_layout.addWidget(pj_group)

        controls.setLayout(controls_layout)
        return controls
    
    
    def create_import_buttons(self, spectrum: Spectrum) -> QHBoxLayout:
        import_spectrum_buttons_layout = QHBoxLayout()
        # Import spectrum button
        import_spectrum_button = QPushButton(text="Import spectrum")
        import_spectrum_button.clicked.connect(lambda: self.import_spectrum_button_callback(spectrum))
        import_spectrum_buttons_layout.addWidget(import_spectrum_button)
        
        # Import demo spectrum button
        import_demo_spectrum_button = QPushButton(text="Import demo spectrum")
        import_demo_spectrum_button.clicked.connect(lambda: self.import_demo_spectrum_button_callback(spectrum))
        import_spectrum_buttons_layout.addWidget(import_demo_spectrum_button)
        return import_spectrum_buttons_layout
    
    
    def create_horizontal_trace(self) -> pg.GraphicsLayoutWidget:
        plot_graph_glw = pg.GraphicsLayoutWidget()
        plot_graph_glw.setObjectName("horizontal_trace")
        plot_graph_glw.setVisible(False)
        plot_graph_glw.setFixedHeight(200)
        plot_graph_glw.setStyleSheet("background-color: rgba(0, 0, 0, 0)")
        plot_graph_glw.ci.layout.setContentsMargins(0,0,0,0)
        
        plot_graph = plot_graph_glw.addPlot()
        plot_graph.setMouseEnabled(x=False, y=False)
        plot_graph.hideButtons()
        plot_graph.setMenuEnabled(False)
        plot_graph.setContentsMargins(0,0,0,0)
        plot_graph.setDefaultPadding(0)
        background_color = QColor("FFFFFF")
        background_color.setAlpha(0)
        plot_graph_glw.setBackground(background_color)
        plot_graph.hideAxis("left")
        plot_graph.hideAxis("bottom")
        self.h_trace_line = plot_graph.plot()
        return plot_graph_glw


    def create_spectrum_axes(self, parent_layout) -> None:
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
            parent_layout.addWidget(ax, *grid_pos)
    
    
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
        
        
        self.setWindowTitle(f"NMR Fido - {os.path.basename(file_path)}")
        
        
        self.plot_ax.setLabels(bottom=f'{spectrum.dic["FDF2LABEL"]} [ppm]', right=f'{spectrum.dic["FDF1LABEL"]} [ppm]')
        
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
        #data = data[y_index_start:y_index_end, x_index_start:x_index_end]
        print(f"MainWindow.display_spectrum -> X limits {x_index_start=}; {x_index_end=}")
        print(f"MainWindow.display_spectrum -> Y limits {y_index_start=}; {y_index_end=}")
        
        data = data[180:350, 1900:2160]
        
        #data = np.flip(data, 0)
        
        if hasattr(self, "h_trace_line"):
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
        
        median_abs_value = _median_absolute_deviation(data)
        max_value = median_abs_value*20
        min_value = max_value*-1
        print(f"MainWindow.display_spectrum -> {min_value=} {max_value=}")
        

        data = data.transpose()
        data = np.flip(data, 1)
        data = np.flip(data, 0)
        base_level = median_abs_value*3
        nr_levels = 32
        multiplier = 1.2
        if len(self.plot_levels) == 0 :
            positive_levels = [base_level*np.power(multiplier, np.abs(x))*np.sign(x) for x in np.arange(1, nr_levels+1)]
            negative_levels = [x*-1 for x in positive_levels]
            self.plot_levels = positive_levels + negative_levels
            self.plot_levels.sort()
        
        x_range = (spectrum.dim1_ppm_scale[x_index_start], spectrum.dim1_ppm_scale[x_index_end])
        y_range = (spectrum.dim0_ppm_scale[y_index_start], spectrum.dim0_ppm_scale[y_index_end])
        print(f"MainWindow.display_spectrum -> {x_range=} {y_range=}")
        self.plot_ax.setXRange(*x_range)
        self.plot_ax.setYRange(*y_range)
        self.plot_ax.getViewBox().invertY(True)
        self.plot_ax.getViewBox().invertX(True)
        
        move_x = x_range[-1]
        move_y = y_range[-1]
        print(move_x, move_y)
        scale_x = (x_range[0] - x_range[-1]) / data.shape[0]
        scale_y = (y_range[0] - y_range[-1]) / data.shape[1]
        print(scale_x, scale_y)
        
        if len(self.plot_contours) == 0:
            for level in self.plot_levels:
                color = "#1f9c74" if level > 0 else "#fabd2e"

                #print(f"MainWindow.display_spectrum -> {level=}")
                c = pg.IsocurveItem(
                    data=data,
                    level=level,
                    pen=color
                )
                c.setPos(move_x, move_y)
                c.setTransform(QTransform.fromScale(scale_x, scale_y))
                #c.setZValue(10)
                self.plot_contours.append(c)
                self.plot_ax.addItem(c)
        else:
            for contour in self.plot_contours:
                contour.setData(data)
        print(f"MainWindow.display_spectrum -> done")
        self.app.processEvents()
        
    
    
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
        h_trace = self.findChild(pg.GraphicsLayoutWidget, "horizontal_trace")
        if h_trace:
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