from distutils.core import setup  
import py2exe  

includes = ["encodings", "encodings.*"]
options = {"py2exe":   
        {"compressed": 1, 
         "optimize": 2,   
         "ascii": 1,   
         "includes":includes,   
         "bundle_files": 1 }
}         
setup(  
    options = options,
    version = "0.5.0",  
    description = "zkeco console",  
    name = "py2exe samples",    
    windows = [{'script':'gui.py','dest_base':'zkecomng','uac_info':'requireAdministrator', "icon_resources": [(1, r"zkeco.ico")]}] 
)  