import nmrglue as ng
from copy import deepcopy

import processing

class Spectrum:

    def __init__(self):
        self.fid_dic = None
        self.fid_data = None
        
        self.dic = None
        self.data = None
        
        self.processor = None
        
        self.dim0_p0 = 0
        self.dim0_p1 = 0
        self.dim1_p0 = 0
        self.dim1_p1 = 0
        
        
    def load(self, file_path: str = "src/test.fid") -> None:
        self.fid_dic, self.fid_data = ng.pipe.read(file_path)

        
        self.process()
        
        self.dim0_uc = ng.pipe.make_uc(self.dic, self.data, dim=0)
        self.dim0_ppm_scale = self.dim0_uc.ppm_scale()
        
        self.dim1_uc = ng.pipe.make_uc(self.dic, self.data, dim=1)
        self.dim1_ppm_scale = self.dim1_uc.ppm_scale()
        
        
    def process(self) -> None:
        dic = deepcopy(self.fid_dic)
        data = deepcopy(self.fid_data)

        # process the direct dimension
        #dic, data = ng.pipe_proc.poly(dic, data) # not implemented
        dic, data = ng.pipe_proc.sp(dic, data, off=0.5, end=1.0, pow=2, c=1.0) # adjustable sine bell window
        dic, data = ng.pipe_proc.zf(dic, data, auto=True) # zero filling
        dic, data = ng.pipe_proc.ft(dic, data, auto=True) # fourier transform
        dic, data = ng.pipe_proc.ps(dic, data, p0=self.dim0_p0, p1=self.dim0_p1) # phase correction
        dic, data = ng.pipe_proc.di(dic, data) # delete imaginary part

        dic, data = ng.pipe_proc.tp(dic, data) # transpose
        
        # process the indirect dimension
        dic, data = ng.pipe_proc.sp(dic, data, off=0.5, end=1.0, pow=2, c=1.0) # adjustable sine bell window
        dic, data = ng.pipe_proc.zf(dic, data, auto=True)  # zero filling
        dic, data = ng.pipe_proc.ft(dic, data, auto=True) # fourier transform
        dic, data = ng.pipe_proc.ps(dic, data, p0=self.dim1_p0, p1=self.dim1_p1) # phase correction
        dic, data = ng.pipe_proc.di(dic, data) # delete imaginary part
        
        self.dic, self.data = ng.pipe_proc.tp(dic, data) # transpose
        return
        for function in self.processor:
            function_name = function[0]
            function_args = function[1]
            print(f"Processor: {function_name} -> {function_args}")
            dic, data = function_name(dic, data, *function_args)
        
        
    def reset_phase(self) -> None:
        self.dim0_p0 = 0
        self.dim0_p1 = 0
        self.dim1_p0 = 0
        self.dim1_p1 = 0
        
        
    def phase(self, values) -> None:
        self.dim0_p0 = values[0]
        self.dim0_p1 = values[1]
        self.dim1_p0 = values[2]
        self.dim1_p1 = values[3]
        
        self.process()
        
        
if __name__ == "__main__":
    dic, data = ng.pipe.read("test.fid")
    print(data.shape)