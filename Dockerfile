FROM ubuntu:focal
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/London
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
		build-essential \
        ca-certificates \
		clang-11 \
        clang-tidy-11 \
		cmake \
		gcc-10 \
		g++-10 \
		git \
        ninja-build \
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
