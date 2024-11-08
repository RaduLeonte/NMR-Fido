'''Initialize main window.'''

import sys
import numpy as np
import nmrglue as ng
import matplotlib.pyplot as plt
from functools import partial
from copy import deepcopy


from PyQt6.QtCore import QSize, Qt, QThreadPool, QRunnable, pyqtSlot, QRectF
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QImage, QPixmap, QIcon, qRgb, QDoubleValidator, QColor, QPalette, QPainter, QPen

from spectrum import Spectrum


def start_app(args: list):
    spectrum: Spectrum = Spectrum()
    
    app: QApplication = QApplication(args)

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
        controls_group.setFixedWidth(600)
        controls_group.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Expanding)
        controls_group_layout = QVBoxLayout()
        
        '''
        Dimension 1
        '''
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
        
        spectrum_obj = QLabel(self)
        spectrum_obj.setObjectName("spectrum_obj")
        spectrum_obj.setStyleSheet("border-style: solid; border-width: 2px; border-color:black")
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
            #h_axis_top = Color("red")
            #h_axis_top.setFixedHeight(axis_size)
            #plot_container_layout.addWidget(h_axis_top, 0, 1)
            #
            #v_axis_left = Color("blue")
            #v_axis_left.setFixedWidth(axis_size)
            #plot_container_layout.addWidget(v_axis_left, 1, 0)
            #
            #v_axis_right = Color("green")
            #v_axis_right.setFixedWidth(axis_size)
            #plot_container_layout.addWidget(v_axis_right, 1, 2)
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
        
        
        spectrum_container.setLayout(spectrum_container_layout)
        layout.addWidget(spectrum_container)
        
        
        # Master container
        content = QWidget()
        content.setLayout(layout)
        self.setCentralWidget(content)


    def initialize_empty_spectrum(_) -> QPixmap:
        img = QImage(1, 1, QImage.Format.Format_Indexed8)
        img.fill(qRgb(50,50,50))
        return QPixmap.fromImage(img)


    def import_spectrum_button_callback(self, spectrum) -> None:
        # Load and display spectrum
        file_path = QFileDialog.getOpenFileName(
            self,
            'Open file',
            'c:\\',
        )  
        print(f"import_spectrum_button_callback opening:{file_path[0]}")
        
        spectrum.load(file_path[0])
        
        self.show_axis(spectrum)
        
        self.display_spectrum(spectrum)
        
        
        self.toggle_phasing_controls()
        return
    
    
    def import_demo_spectrum_button_callback(self, spectrum) -> None:
                # Load and display spectrum
        file_path = "src/test.fid"
        print(f"import_spectrum_button_callback opening:{file_path}")
        
        spectrum.load(file_path)
        
        self.show_axis(spectrum)
        
        self.display_spectrum(spectrum)
        
        
        self.toggle_phasing_controls()
        return


    def display_spectrum(self, spectrum: Spectrum) -> None:
        
        #print(spectrum.dim0_ppm_scale[0], spectrum.dim0_ppm_scale[-1])
        #print(spectrum.dim1_ppm_scale[0], spectrum.dim1_ppm_scale[-1])
        limits0 = [70, 40]
        limits1 = [135, 6]
        limits0 = [70, 40]
        limits1 = [135, 6]
        
        
        x_index_start = np.where(spectrum.dim0_ppm_scale == min(spectrum.dim0_ppm_scale, key=lambda x:abs(x-limits0[0])))[0][0]
        x_index_end = np.where(spectrum.dim0_ppm_scale == min(spectrum.dim0_ppm_scale, key=lambda x:abs(x-limits0[1])))[0][0]
        y_index_start = np.where(spectrum.dim1_ppm_scale == min(spectrum.dim1_ppm_scale, key=lambda x:abs(x-limits1[0])))[0][0]
        y_index_end = np.where(spectrum.dim1_ppm_scale == min(spectrum.dim1_ppm_scale, key=lambda x:abs(x-limits1[1])))[0][0]
        
        #print("x limits:", x_index_start, x_index_end)
        #print("y limits:", y_index_start, y_index_end)
        data = deepcopy(spectrum.data)
        #data = data[x_index_start:x_index_end, y_index_start:y_index_end]
        #data = data[650:1300, 1900:2200]
        
        data = np.flip(data, 0)
        
        if len(data) == 0:
            return

        #print(data)
        def _median_absolute_deviation(data, k=1.4826):
            """ Median Absolute Deviation: a "Robust" version of standard deviation.
                Indices variabililty of the sample.
                https://en.wikipedia.org/wiki/Median_absolute_deviation
            """
            data = np.ma.array(data).compressed()
            median = np.median(data)
            return k*np.median(np.abs(data - median))
        
        max_value = _median_absolute_deviation(data)*10
        min_value = _median_absolute_deviation(data)*5
        
        
        #print(data.max())
        
        normalized_array = (data - min_value) / (max_value - min_value)
        normalized_array = np.clip(normalized_array, 0, 1)  # Ensure values stay within [0, 1]
        
        cmap = plt.get_cmap("magma")
        rgba_array = cmap(normalized_array)
        rgb_array = (rgba_array[:, :, :3] * 255).astype(np.uint8)
        
        img = QImage(rgb_array.data, rgb_array.shape[1], rgb_array.shape[0], QImage.Format.Format_RGB888)
        
        pixmap = QPixmap.fromImage(img)
        
        spectrum_object = self.findChild(QLabel, "spectrum_obj")
        
        pixmap = pixmap.scaled(spectrum_object.width(), spectrum_object.height())
        spectrum_object.setPixmap(pixmap)
    
    
    def show_axis(self, spectrum) -> None:
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
            
            
            #print(ax_orientation, ax_ticks_w, ax_ticks_h, ax_ticks_w < ax_ticks_h)
            pixmap = QPixmap(ax_ticks_w, ax_ticks_h)
            pixmap.fill(QColor("#F0F0F0"))
            
            painter = QPainter(pixmap)
            pen = QPen()
            pen.setColor(QColor("#000000"))
            pen.setWidth(2)
            painter.setPen(pen)
            
            
            ax_ppm_scale = spectrum.dim1_ppm_scale if ax_orientation == "h" else spectrum.dim0_ppm_scale
            #print(spectrum.dim0_ppm_scale) # 15 N
            #print(spectrum.dim1_ppm_scale) # 13 C
            #print(ax_ppm_scale[0], ax_ppm_scale[-1])
            
            def generate_ticks(ppm_scale: np.array, axis_size: float, nr_ticks:int=6) -> list:
                print(ppm_scale)
                ticks_ppm = np.linspace(np.floor(ppm_scale[0]), np.ceil(ppm_scale[-1]), nr_ticks)
                print("Ticks ppm:", ticks_ppm)
                ticks_unitless = np.absolute((ticks_ppm - ppm_scale[0]) / (ppm_scale[0] - ppm_scale[-1]))
                print("Ticks unitless:", ticks_unitless)
                ticks_px = list(ticks_unitless * axis_size)
                ticks_px = [int(p) for p in ticks_px]
                print("Ticks px:", ticks_px)
                return ticks_ppm, ticks_px
                
            ticks_labels, ticks_positions = generate_ticks(ax_ppm_scale, max(ax_ticks_w, ax_ticks_h), 10)
            
            tick_length = 5   # length of each tick
            text_width = 40
            text_pos = 10
            text_height = 10

            # Loop to draw ticks vertically
            print(ax_orientation, ax_label_first)
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
        for i in [0, 1]:
            for j in [0, 1]:
                phasing_input = self.findChild(QLineEdit, f"dim{i}_p{j}_input")
                phasing_input.setEnabled(not phasing_input.isEnabled())
                
                phasing_slider = self.findChild(QSlider, f"dim{i}_p{j}_slider")
                phasing_slider.setEnabled(not phasing_slider.isEnabled())
     
     
     
    def threaded(self, *args):
        print(f"threaded self:{self}")
        print(f"threaded args:{args}")
        worker = Worker(*args)
        self.threadpool.start(worker)
    
    
    def phasing_input_callback(self, spectrum: Spectrum, identifier: str, *args) -> None:
        # reset on empty input
        phasing_input = self.findChild(QLineEdit, f"{identifier}_input")
        if phasing_input == None:
            return
        print("phasing_input", f"{identifier}_input", phasing_input.text())
        
        try:
            int(float(phasing_input.text()))
        except ValueError:
            return
        
        if phasing_input.text() == "":
            phasing_input.setText("0")
            self.findChild(
                QSlider, f"{identifier}_slider"
            ).setValue(
                0
            )
        else:
            self.findChild(
                QSlider, f"{identifier}_slider"
            ).setValue(
                int(float(
                    phasing_input.text()
                ))
            )
        
        # update plot
        self.update_plot(spectrum)
    
    
    def phasing_slider_callback(self, spectrum: Spectrum, identifier: str, *args) -> None:
        # change input
        if self.findChild(QLineEdit, f"{identifier}_input") == None:
            return
    
        self.findChild(
            QLineEdit, f"{identifier}_input"
        ).setText(
            str(
                self.findChild(QSlider, f"{identifier}_slider").value()
                )
        )
        
        # update plot
        self.update_plot(spectrum)
    
    
    def update_plot(self, spectrum: Spectrum) -> None:
        phasing_values = [
            self.findChild(QLineEdit, "dim0_p0_input").text(),
            self.findChild(QLineEdit, "dim0_p1_input").text(),
            self.findChild(QLineEdit, "dim1_p0_input").text(),
            self.findChild(QLineEdit, "dim1_p1_input").text()
        ]
        # Phase spectrum
        spectrum.phase([float(p) if p != "" else 0.0 for p in phasing_values])
        
        # Display phased spectrum
        self.display_spectrum(spectrum)


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