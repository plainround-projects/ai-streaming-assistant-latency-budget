# Docker

## What it is

Docker runs programs in *containers*: isolated processes that carry their own copy of the files they need (the operating system's libraries, Python, your code), so the program behaves the same on any machine. An *image* is the read-only package a container starts from; a *container* is one running copy of an image.

## Why this repository uses it

Docker ships the server as one image with the locked packages, the code, the data and the built database. The repository's only Docker command is the image build.

## Where it appears

| File | What it does with Docker |
| --- | --- |
| `Dockerfile` | the image |
| `Makefile` (`docker-build`) | builds it |
| `.github/workflows/ci.yml` | the `image` job |

## How it works underneath

An image is built in *layers*. Each instruction in a Dockerfile adds a layer, and Docker caches layers: if an instruction and everything before it are unchanged, the cached layer is reused. That is why the Dockerfile copies the dependency list and installs packages before it copies the source code: code changes often and package lists rarely.

A container is an ordinary process on the Docker host's Linux kernel, fenced off by kernel features (separate file system view, process list, network). It has its own network address and only the ports you *publish* (`-p 8080:8080`, host port first) are reachable from outside. `docker run --network none` starts a container with no network at all. `docker ps` lists containers; `docker logs` shows what they printed.

On a Mac, Docker Desktop runs a small Linux virtual machine and all containers share it; its memory and disk are limited, which matters when many containers run.

## Walkthrough of this repository's use

The one Docker command:

```make
docker-build: ## build the server image
	docker build -t ai-streaming-assistant-latency-budget:dev .
```

- `docker-build: ## build the server image`: A target named `docker-build` that needs nothing first.
- `docker build -t ai-streaming-assistant-latency-budget:dev .`: Build a Docker image: `-t ai-streaming-assistant-latency-budget:dev .`.

What happens inside the build is in `dockerfile.md`. Pending capacity: run `make docker-build` after Docker Desktop is restarted with free disk (Docker.raw was at its 60 GiB cap on 2026-10-28).

## Try it yourself

Run these from the repository folder (after `make up`).

```bash
docker --version
```

Prints the installed Docker version.

```bash
docker images | grep streaming
```

Lists the image once built.

```bash
docker ps
```

Lists running containers.

## Mistakes people make

- Running as root inside the container. The images here create an `app` user and switch to it.
- Using the `latest` tag. The base image is pinned by version and digest.
- Baking secrets into an image. Settings come from environment variables at run time.
- Putting code before dependencies in the Dockerfile, which wastes the build cache.
- Forgetting that data inside a container disappears with it unless it is in a volume.

## Check yourself

1. What is the difference between an image and a container?
   *Answer:* An image is the packaged files; a container is a running copy of an image.
2. What is a layer?
   *Answer:* The result of one Dockerfile instruction, cached and reused if nothing before it changed.
3. What does `-p 8080:8080` do?
   *Answer:* Publishes container port 8080 on host port 8080.
4. What does `--network none` do?
   *Answer:* Starts the container with no network access.
5. Why is the container user not root?
   *Answer:* To limit the damage if the program is attacked.

## Further reading

- [Docker documentation](https://docs.docker.com/)
- [Docker build best practices](https://docs.docker.com/build/building/best-practices/)
