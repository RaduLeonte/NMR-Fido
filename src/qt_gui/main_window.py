'''Initialize main window.'''

import sys
import numpy as np
import nmrglue as ng
import matplotlib.pyplot as plt

from PyQt6.QtCore import QSize, Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QGroupBox, QHBoxLayout, QVBoxLayout, QGridLayout, QSizePolicy, QWidget, QLabel, QSlider, QPushButton
from PyQt6.QtGui import QImage, QPixmap, QIcon, qRgb

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
            dim1_controls = QGroupBox(f"Dimension {i}")
            dim1_controls_layout = QVBoxLayout()
            
            # p0
            dim1_p0_group = QWidget()
            dim1_p0_group_layout = QHBoxLayout()
            
            dim1_p0_label = QLabel("p0")
            dim1_p0_group_layout.addWidget(dim1_p0_label)
        
            dim1_p0_slider = QSlider(Qt.Orientation.Horizontal)
            dim1_p0_slider.setObjectName(f"dim{i}_p0_slider")
            dim1_p0_slider.setMinimum(-360)
            dim1_p0_slider.setMaximum(360)
            dim1_p0_slider.setValue(0)
            dim1_p0_slider.valueChanged.connect(lambda: self.update_plot(spectrum))
            dim1_p0_group_layout.addWidget(dim1_p0_slider)
            
            dim1_p0_group.setLayout(dim1_p0_group_layout)
            dim1_controls_layout.addWidget(dim1_p0_group)
            
            # p1
            dim1_p1_group = QWidget()
            dim1_p1_group_layout = QHBoxLayout()
            
            dim1_p1_label = QLabel("p1")
            dim1_p1_group_layout.addWidget(dim1_p1_label)
            
            dim1_p1_slider = QSlider(Qt.Orientation.Horizontal)
            dim1_p1_slider.setObjectName(f"dim{i}_p1_slider")
            dim1_p1_slider.setMinimum(-360)
            dim1_p1_slider.setMaximum(360)
            dim1_p1_slider.setValue(0)
            dim1_p1_slider.valueChanged.connect(lambda: self.update_plot(spectrum))
            dim1_p1_group_layout.addWidget(dim1_p1_slider)
            
            dim1_p1_group.setLayout(dim1_p1_group_layout)
            dim1_controls_layout.addWidget(dim1_p1_group)
        
            dim1_controls.setLayout(dim1_controls_layout)
            controls_group_layout.addWidget(dim1_controls)
            
            dim1_controls.setLayout(dim1_controls_layout)
            controls_group_layout.addWidget(dim1_controls)
        
        
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
        spectrum.load()
        self.display_spectrum(spectrum)
        return
    
    
    def display_spectrum(self, spectrum: Spectrum) -> None:
        
        limits0 = [135, 100]
        limits1 = [70, 40]
        
        print(spectrum.dim0_ppm_scale)
        print(spectrum.dim1_ppm_scale)
        x_index_start = np.where(spectrum.dim0_ppm_scale == min(spectrum.dim0_ppm_scale, key=lambda x:abs(x-limits0[0])))[0][0]
        x_index_end = np.where(spectrum.dim0_ppm_scale == min(spectrum.dim0_ppm_scale, key=lambda x:abs(x-limits0[1])))[0][0]
        y_index_start = np.where(spectrum.dim1_ppm_scale == min(spectrum.dim1_ppm_scale, key=lambda x:abs(x-limits1[0])))[0][0]
        y_index_end = np.where(spectrum.dim1_ppm_scale == min(spectrum.dim1_ppm_scale, key=lambda x:abs(x-limits1[1])))[0][0]
        
        print(x_index_start, x_index_end)
        print(y_index_start, y_index_end)
        data = spectrum.data[x_index_start:x_index_end, y_index_start:y_index_end]
        #data = data[650:1300, 1900:2200]
        
        data = np.flip(data, 0)

        max_value = data.max()
        min_value = 0
        
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
    
    
    def update_plot(self, spectrum: Spectrum) -> None:
        # Phase spectrum
        spectrum.phase([
            self.findChild(QSlider, "dim0_p0_slider").value(),
            self.findChild(QSlider, "dim0_p1_slider").value(),
            self.findChild(QSlider, "dim1_p0_slider").value(),
            self.findChild(QSlider, "dim1_p1_slider").value(),
        ])
        
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