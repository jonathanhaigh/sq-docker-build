FROM ubuntu:focal
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/London
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        bash \
        build-essential \
        ca-certificates \
        clang-11 \
        clang-format-11 \
        clang-tidy-11 \
        cmake \
        coreutils \
        curl \
        gcc-10 \
        g++-10 \
        git \
        lftp \
        libudev-dev \
        llvm-11 \
        ninja-build \
        openssh-client \
        python3 \
        python3-pip \
        tar \
        wget && \
    apt-get autoclean && \
    apt-get autoremove && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
RUN update-alternatives --install /usr/bin/g++ g++ /usr/bin/g++-10 100
RUN update-alternatives --install /usr/bin/clang++ clang++ /usr/bin/clang++-11 100
RUN update-alternatives --install /usr/bin/c++ c++ /usr/bin/clang++-11 100
RUN update-alternatives --install /usr/bin/gcc gcc /usr/bin/gcc-10 100
RUN update-alternatives --install /usr/bin/clang clang /usr/bin/clang-11 100
RUN update-alternatives --install /usr/bin/cc cc /usr/bin/clang-11 100
RUN update-alternatives --install /usr/bin/clang-tidy clang-tidy /usr/bin/clang-tidy-11 100
RUN update-alternatives --install /usr/bin/clang-format clang-format /usr/bin/clang-format-11 100
RUN update-alternatives --install /usr/bin/gcov gcov /usr/bin/gcov-10 100
RUN update-alternatives --install /usr/bin/llvm-cov llvm-cov /usr/bin/llvm-cov-11 100
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3 100
COPY llvm-gcov /usr/local/bin/llvm-gcov
RUN pip3 install cpp-coveralls
RUN pip3 install pytest
COPY entrypoint.py /entrypoint.py
ENTRYPOINT ["/entrypoint.py"]
