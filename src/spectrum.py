import nmrglue as ng

import processing

class Spectrum:

    def __init__(self):
        self.dic = []
        self.data = []
        
        self.dim0_p0 = 0
        self.dim0_p1 = 0
        self.dim1_p0 = 0
        self.dim1_p1 = 0
        
        
    def load(self) -> None:
        self.dic, self.data = ng.pipe.read("src/test.ft2")
        
        self.dim0_uc = ng.pipe.make_uc(self.dic, self.data, dim=0)
        self.dim0_ppm_scale = self.dim0_uc.ppm_scale()
        
        self.dim1_uc = ng.pipe.make_uc(self.dic, self.data, dim=1)
        self.dim1_ppm_scale = self.dim1_uc.ppm_scale()
        
        
    def reset_phase(self) -> None:
        self.dim0_p0 = 0
        self.dim0_p1 = 0
        self.dim1_p0 = 0
        self.dim1_p1 = 0
        
        
    def phase(self, values) -> None:
        self.dim0_p0 = values[0][0]
        self.dim0_p1 = values[0][1]
        self.dim1_p0 = values[1][0]
        self.dim1_p1 = values[1][1]
        
        for i in [0, 1]:
            continue