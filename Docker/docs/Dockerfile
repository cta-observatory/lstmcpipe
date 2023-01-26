FROM docker.io/condaforge/miniforge3:22.9.0-1

LABEL maintainer="Thomas Vuillaume <thomas.vuillaume@lapp.in2p3.fr>"

RUN apt-get update && apt-get install -y git wget gcc make
COPY . lstmcpipe
# use libmamba solver as default one
RUN conda install -n base conda-libmamba-solver; conda config --set solver libmamba
RUN cd lstmcpipe \
    conda env update -f environment.yml -n base \
    conda install pandoc \
    pip install -r docs/requirements.txt \
    pip install .

RUN conda clean -a
