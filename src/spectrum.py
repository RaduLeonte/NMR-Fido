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
        
        self.processor = Processor()
        #dic, data = ng.pipe_proc.sp(dic, data, off=0.5, end=1.0, pow=2, c=1.0) # adjustable sine bell window
        self.processor.add_operation(ng.pipe_proc.sp, off=0.5, end=1.0, pow=2, c=1.0)
        #dic, data = ng.pipe_proc.zf(dic, data, auto=True) # zero filling
        self.processor.add_operation(ng.pipe_proc.zf, auto=True)
        #dic, data = ng.pipe_proc.ft(dic, data, auto=True) # fourier transform
        self.processor.add_operation(ng.pipe_proc.ft, auto=True)
        #dic, data = ng.pipe_proc.ps(dic, data, p0=self.dim0_p0, p1=self.dim0_p1) # phase correction
        self.processor.add_operation(ng.pipe_proc.ps, p0=lambda: self.dim0_p0, p1=lambda: self.dim0_p1)
        #dic, data = ng.pipe_proc.di(dic, data) # delete imaginary part
        self.processor.add_operation(ng.pipe_proc.di)

        #dic, data = ng.pipe_proc.tp(dic, data) # transpose
        self.processor.add_operation(ng.pipe_proc.tp)
        
        #dic, data = ng.pipe_proc.sp(dic, data, off=0.5, end=1.0, pow=2, c=1.0) # adjustable sine bell window
        self.processor.add_operation(ng.pipe_proc.sp, off=0.5, end=1.0, pow=2, c=1.0)
        #dic, data = ng.pipe_proc.zf(dic, data, auto=True)  # zero filling
        self.processor.add_operation(ng.pipe_proc.zf, auto=True)
        #dic, data = ng.pipe_proc.ft(dic, data, auto=True) # fourier transform
        self.processor.add_operation(ng.pipe_proc.ft, auto=True)
        #dic, data = ng.pipe_proc.ps(dic, data, p0=self.dim1_p0, p1=self.dim1_p1) # phase correction
        self.processor.add_operation(ng.pipe_proc.ps, p0=lambda: self.dim1_p0, p1=lambda: self.dim1_p1)
        #dic, data = ng.pipe_proc.di(dic, data) # delete imaginary part
        self.processor.add_operation(ng.pipe_proc.di)
        
        #self.dic, self.data = ng.pipe_proc.tp(dic, data) # transpose
        self.processor.add_operation(ng.pipe_proc.tp)
        
        
    def calcualate_ppm_scales(self) -> None:
        self.dim0_uc = ng.pipe.make_uc(self.dic, self.data, dim=0)
        self.dim0_ppm_scale = self.dim0_uc.ppm_scale()
        
        self.dim1_uc = ng.pipe.make_uc(self.dic, self.data, dim=1)
        self.dim1_ppm_scale = self.dim1_uc.ppm_scale()
        
        
    def load(self, file_path: str = "src/test.fid") -> None:
        self.fid_dic, self.fid_data = ng.pipe.read(file_path)

        
        self.process()

        
        
    def process(self) -> None:
        self.processor.run(self)
        self.calcualate_ppm_scales()
    
        
        
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


class Processor:
    
    def __init__(self):
        self.operations = []
        
        
    def add_operation(self, func, *args, **kwargs) -> None:
        self.operations.append((func, args, kwargs))
    
    
    def run(self, spectrum: Spectrum) -> None:
        dic = deepcopy(spectrum.fid_dic)
        data = deepcopy(spectrum.fid_data)
        for func, args, kwargs in self.operations:
            eval_args = [arg() if callable(arg) else arg for arg in args]
            eval_kwargs = {k: v() if callable(v) else v for k, v in kwargs.items()}
            #print(f"Processor.run {func.__name__} -> args:{eval_args}; kwargs:{eval_kwargs}")
            dic, data = func(dic, data, *eval_args, **eval_kwargs)
        
        spectrum.dic = dic
        spectrum.data = data


        
if __name__ == "__main__":
    dic, data = ng.pipe.read("test.fid")
    print(data.shape)