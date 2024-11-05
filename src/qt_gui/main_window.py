'''Initialize main window.'''

import sys
import numpy as np
import nmrglue as ng
import matplotlib.pyplot as plt
from functools import partial
from copy import deepcopy


from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import *
from PyQt6.QtGui import QImage, QPixmap, QIcon, qRgb, QDoubleValidator

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
                pj_input.textChanged.connect(partial(self.phasing_input_callback, spectrum, f"dim{i}_p{j}"))
                pj_group_layout.addWidget(pj_input)
            
                pj_slider = QSlider(Qt.Orientation.Horizontal)
                pj_slider.setObjectName(f"dim{i}_p{j}_slider")
                pj_slider.setEnabled(False)
                pj_slider.setMinimum(-360)
                pj_slider.setMaximum(360)
                pj_slider.setValue(0)
                pj_slider.valueChanged.connect(partial(self.phasing_slider_callback, spectrum, f"dim{i}_p{j}"))
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
        spectrum_container_layout = QGridLayout()
        
        import_spectrum_button = QPushButton(text="Import spectrum")
        import_spectrum_button.clicked.connect(lambda: self.import_spectrum_button_callback(spectrum))
        spectrum_container_layout.addWidget(import_spectrum_button)
        
        spectrum_obj = QLabel(self)
        spectrum_obj.setObjectName("spectrum_obj")
        spectrum_obj.setPixmap(self.initialize_empty_spectrum())
        spectrum_container_layout.addWidget(spectrum_obj)
        
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
        print(f"Opening: {file_path[0]}")
        
        spectrum.load(file_path[0])
        
        print("156", spectrum.data.shape)
        self.display_spectrum(spectrum)
        
        self.toggle_phasing_controls()
        return


    def display_spectrum(self, spectrum: Spectrum) -> None:
        
        print(spectrum.dim0_ppm_scale[0], spectrum.dim0_ppm_scale[-1])
        print(spectrum.dim1_ppm_scale[0], spectrum.dim1_ppm_scale[-1])
        limits0 = [135, 100]
        limits1 = [12, 6]
        
        x_index_start = np.where(spectrum.dim0_ppm_scale == min(spectrum.dim0_ppm_scale, key=lambda x:abs(x-limits0[0])))[0][0]
        x_index_end = np.where(spectrum.dim0_ppm_scale == min(spectrum.dim0_ppm_scale, key=lambda x:abs(x-limits0[1])))[0][0]
        y_index_start = np.where(spectrum.dim1_ppm_scale == min(spectrum.dim1_ppm_scale, key=lambda x:abs(x-limits1[0])))[0][0]
        y_index_end = np.where(spectrum.dim1_ppm_scale == min(spectrum.dim1_ppm_scale, key=lambda x:abs(x-limits1[1])))[0][0]
        
        #print("x limits:", x_index_start, x_index_end)
        #print("y limits:", y_index_start, y_index_end)
        data = deepcopy(spectrum.data)
        data = data[x_index_start:x_index_end, y_index_start:y_index_end]
        #data = data[650:1300, 1900:2200]
        
        data = np.flip(data, 0)
        
        if len(data) == 0:
            return

        #print(data)
        max_value = 10E9
        min_value = 1E9
        
        print(data.max())
        
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
    
    
    def toggle_phasing_controls(self) -> None:
        for i in [0, 1]:
            for j in [0, 1]:
                phasing_input = self.findChild(QLineEdit, f"dim{i}_p{j}_input")
                phasing_input.setEnabled(not phasing_input.isEnabled())
                
                phasing_slider = self.findChild(QSlider, f"dim{i}_p{j}_slider")
                phasing_slider.setEnabled(not phasing_slider.isEnabled())
     
    
    def phasing_input_callback(self, spectrum: Spectrum, identifier: str) -> None:
        # reset on empty input
        phasing_input = self.findChild(QLineEdit, f"{identifier}_input")
        print("phasing_input", f"{identifier}_input", phasing_input.text())
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
    
    
    def phasing_slider_callback(self, spectrum: Spectrum, identifier: str) -> None:
        # change input
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


def create_image(size, sigma):
    x, y = np.meshgrid(np.linspace(-1, 1, size), np.linspace(-1, 1, size))
    d = np.sqrt(x*x + y*y)
    a = np.exp(-(d**2 / (2.0 * sigma**2)))
    
    #a = np.random.randint(0, 256, (256, 256), dtype=np.uint8)
    a = a/np.max(a)
    a = (a*255).astype(np.uint8)
    
    h, w = a.shape
    img = QImage(a.data, w, h, QImage.Format.Format_Indexed8)
    pixmap = QPixmap.fromImage(img)
    return pixmap
