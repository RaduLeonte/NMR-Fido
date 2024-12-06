import os
import numpy as np
from functools import partial
from copy import deepcopy

from PySide6.QtCore import (
    Qt,
    QThreadPool, QRunnable, Slot,
    QSize,
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow,
    QGridLayout, QGroupBox, QHBoxLayout, QVBoxLayout,
    QToolBar,
    QWidget, QLabel, QLineEdit, QSlider, QPushButton, QSizePolicy, QFileDialog, QListWidget, QSplitter
)
from PySide6.QtGui import (
    QAction,
    QDragEnterEvent, QDropEvent,
    QImage, QPixmap, QColor,
    QPainter, QPen,
    QTransform,
    QDoubleValidator,
)
import pyqtgraph as pg

from src.spectrum import Spectrum


def start_app(args: list):
    spectrum: Spectrum = Spectrum()
    
    app: QApplication = QApplication(args)
    #app.setStyle("fusion")

    window: MainWindow = MainWindow(spectrum, app)
    window.show()

    app.exec()


class MainWindow(QMainWindow):
    def __init__(self, spectrum: Spectrum, app: QApplication) -> None:
        super().__init__()
        
        self.spectrum = spectrum
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
        
        self.setAcceptDrops(True)
        
        """Thread pool"""
        self.threadpool = QThreadPool()
        
        
        """
        Menu
        """
        #region Menu
        menu = self.menuBar()
        
        # File menu
        file_menu = menu.addMenu("File")
        
        new_project_action = QAction("New project", self)
        new_project_action.setEnabled(False)
        file_menu.addAction(new_project_action)
        
        open_project_action = QAction("Open project", self)
        open_project_action.setEnabled(False)
        file_menu.addAction(open_project_action)
        
        ## Open recent project submenu
        recent_projects = []
        recent_projects_submenu = file_menu.addMenu("Open recent project")
        
        if len(recent_projects) == 0:
            no_recent_projects_action = QAction("< no recent projects >", self)
            no_recent_projects_action.setEnabled(False)
            recent_projects_submenu.addAction(no_recent_projects_action)
        else:
            for recent_project in recent_projects:
                recent_projects_submenu.addAction(
                    QAction(recent_project, self)
                )

        recent_projects_submenu.addSeparator()
        
        clear_recent_projects = QAction("Clear recent projects", self)
        clear_recent_projects.setEnabled(False)
        recent_projects_submenu.addAction(clear_recent_projects)
        
        file_menu.addSeparator()

        
        import_file_action = QAction("Import file", self)
        import_file_action.triggered.connect(lambda: self.import_spectrum_button_callback(spectrum))
        file_menu.addAction(import_file_action)
        
        ## Import recent files submenu
        recent_files = []
        recent_files_submenu = file_menu.addMenu("Open recent files")
        
        if len(recent_files) == 0:
            no_recent_files_action = QAction("< no recent files >", self)
            no_recent_files_action.setEnabled(False)
            recent_files_submenu.addAction(no_recent_files_action)
        else:
            for recent_file in recent_files:
                recent_files_submenu.addAction(
                    QAction(recent_file, self)
                )

        recent_files_submenu.addSeparator()
        
        clear_recent_files = QAction("Clear recent files", self)
        clear_recent_files.setEnabled(False)
        recent_files_submenu.addAction(clear_recent_files)
        
        #endregion


        """
        Main container
        """
        layout = QHBoxLayout()
        
        splitter = QSplitter(Qt.Horizontal)
        
        '''
        Window Region: Spectra list
        '''
        #region Spectra list
        spectra_list_container = QGroupBox("Spectra List")
        spectra_list_container.setMinimumWidth(200)
        spectra_list_container_layout = QVBoxLayout()
        spectra_list_container_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        spectra_list = self.create_spectra_list()
        spectra_list_container_layout.addWidget(spectra_list)
        
        spectra_list_container_layout.addStretch()
        spectra_list_container.setLayout(spectra_list_container_layout)
        #endregion
        
        '''
        Window Region: Processing controls
        '''
        #region Processing controls
        controls_group = QGroupBox("Processing")
        controls_group.setMinimumWidth(300)
        #controls_group.setFixedWidth(400)
        #controls_group.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Expanding)
        controls_group_layout = QVBoxLayout()
        controls_group_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)

        for i in [0, 1]:
            controls_group_layout.addWidget(self.create_phasing_controls(i, spectrum))
        
        controls_group_layout.addStretch()
        controls_group.setLayout(controls_group_layout)
        #endregion
        
        '''
        Window Region: Spectrum display
        '''
        #region Spectrum display
        spectrum_container = QGroupBox("Display")
        spectrum_container.setMinimumWidth(500)
        spectrum_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        spectrum_container_layout = QVBoxLayout()
        
        
        """Plot grid"""
        plot_container = QWidget()
        plot_container_layout = QGridLayout()
        plot_container_layout.setHorizontalSpacing(0)
        plot_container_layout.setVerticalSpacing(0)
        
        """Main plot"""
        self.plot = pg.PlotWidget()
        plot_layout = pg.GraphicsLayout()
        self.plot.setCentralItem(plot_layout)
        self.plot_ax = pg.PlotItem()
        self.plot_ax.showAxis("right")
        self.plot_ax.hideAxis("left")
        self.plot_ax.getAxis("bottom").setLabel("Dim 0 [ppm]")
        self.plot_ax.getAxis("bottom").setTextPen("black")
        self.plot_ax.getAxis("right").setLabel("Dim 1\n[ppm]")
        self.plot_ax.getAxis("right").label.setRotation(0)
        self.plot_ax.getAxis("right").label.setTextWidth(60)
        self.plot_ax.getAxis("right").setTextPen("black")
        self.plot_ax.getViewBox().setBackgroundColor("w")
        self.plot.setBackground(QColor(0, 0, 0, 0))
        plot_layout.addItem(self.plot_ax)
        self.plot_contours = []
        self.plot_levels = []
        plot_container_layout.addWidget(self.plot, 1, 1)
        
        """Horizontal trace"""
        #plot_container_layout.addWidget(self.create_horizontal_trace(), 2, 1)
        
        """Plot axes"""
        
        # Add plot grid container to main
        plot_container.setLayout(plot_container_layout)
        spectrum_container_layout.addWidget(plot_container)
        
        # Add spectrum window region to main window
        spectrum_container.setLayout(spectrum_container_layout)
        #endregion
        
        
        """
        Splitter
        """
        splitter.addWidget(spectra_list_container)
        splitter.addWidget(controls_group)
        splitter.addWidget(spectrum_container)
        splitter.setSizes(
            [
                0.2*app_size.width(),
                0.2*app_size.width(),
                0.6*app_size.width()
            ]
        )
        layout.addWidget(splitter)
        
        content = QWidget()
        content.setLayout(layout)
        self.setCentralWidget(content)
        
        
    def dragEnterEvent(self, e: QDragEnterEvent) -> None:
        if e.mimeData().hasUrls():
            e.accept()
        else:
            e.ignore()
            
    
    def dropEvent(self, e: QDropEvent) -> None:
        files = e.mimeData().urls()
        file_paths = [f.toLocalFile() for f in files]
        accepted_extensions = [".fid", ".ft2"]
        valid_files = [file for file in file_paths if any(file.lower().endswith(ext) for ext in accepted_extensions)]
        
        for f in valid_files:
            self.import_spectrum(self.spectrum, f)


    def create_spectra_list(self) -> QListWidget:
        spectra_list = QListWidget()
        
        return spectra_list
        
        
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
        self.h_trace_line.setPen("black")
        return plot_graph_glw
    
    
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

    @Slot()
    def run(self):
        '''
        Initialise the runner function with passed args, kwargs.
        '''
        self.fn(*self.args, **self.kwargs)