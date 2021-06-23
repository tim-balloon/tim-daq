from distutils.core import setup
from Cython.Build import cythonize
from distutils.core import Extension

def create_extension(ext_name):
    global language, libs, args, link_args
    path_parts = ext_name.split(".")
    path = "./{0}.pyx".format("/".join(path_parts))
    ext = Extension(ext_name, sources=[path], libraries=libs, language=language,
            extra_compile_args=args, extra_link_args=link_args)
    return ext

if __name__ == "__main__":
    libs = []#no external c libraries in this case
    language = "c"#chooses c rather than c++ since no c++ features were used
    args = ["-w", "-O3", "-ffast-math"]#assumes gcc is the compiler
    link_args = []#none here, could use -fopenmp for parallel code
    
    directives = {#saves typing @cython decorators and applies them globally
        "boundscheck": False,
        "wraparound": False,
        "initializedcheck": False,
        "cdivision": True,
        "nonecheck": False,
    }

    ext_names = [
        "cython_read",
    ]

    extensions = [create_extension(ext_name) for ext_name in ext_names]
    setup(ext_modules = cythonize(
            extensions, 
            
            compiler_directives=directives,
        )
    )


