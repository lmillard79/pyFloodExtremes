import warnings

# Suppress PyTensor BLAS warning as runtime speeds are acceptable on this system
warnings.filterwarnings(
    "ignore", 
    message="PyTensor could not link to a BLAS installation"
)
