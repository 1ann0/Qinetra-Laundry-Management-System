# Learn Docker with QLMS

This is a guided learning track. The student runs the exercises and explains the result before moving to the next lesson. Google OAuth remains a separate guided phase.

## Start with the system we have

QLMS has a Next.js frontend, a FastAPI backend and a PostgreSQL database. The repository has no Dockerfile or Compose file yet. The current Docker example runs only PostgreSQL for isolated backend tests. It does not containerize QLMS or change its live hosting.

## Five useful terms

| Term | Meaning | QLMS example |
| --- | --- | --- |
| Image | A package containing the software and files needed to start a container | `postgres:17` packages PostgreSQL 17 |
| Container | An instance created from an image, with its own runtime configuration and writable files | Our temporary test database |
| Dockerfile | Instructions for building an image | A future backend Dockerfile will install Python dependencies and copy the API source |
| Port mapping | A connection from a port on your computer to a port inside a container | `127.0.0.1:55432:5432` connects local port 55432 to PostgreSQL's port 5432 |
| Volume | Storage managed separately from a container's writable layer | A future local development database can retain data when its container is replaced |

Containers are processes, not complete virtual machines. Docker Desktop uses a Linux environment to run Linux containers on Windows. Learn the image/container distinction first. [Docker containers](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-a-container/), [images](https://docs.docker.com/get-started/docker-concepts/the-basics/what-is-an-image/), [ports](https://docs.docker.com/get-started/docker-concepts/running-containers/publishing-ports/), [volumes](https://docs.docker.com/get-started/docker-concepts/running-containers/persisting-container-data/).

## Lesson 1: run and inspect one container yourself

Open the QLMS folder in Antigravity and use its PowerShell terminal. Keep Docker Desktop open.

First inspect what is present:

```powershell
docker version
docker image ls
docker ps -a
```

`image ls` lists downloaded/built images. `ps` lists running containers; `ps -a` also includes stopped containers. An image can exist when no container is running.

After the automated tests finish downloading `postgres:17`, run this single line for your own lesson:

```powershell
docker run --name qlms-docker-lesson --rm -d -p 127.0.0.1:55433:5432 -e POSTGRES_PASSWORD=lesson-only postgres:17
```

This is a disposable local database with an example password. It has no Qinetra records. Do not use it for real shop work. If Docker says the name or port is already in use, inspect `docker ps -a` and share the result instead of deleting unrelated containers.

| Part | Purpose |
| --- | --- |
| `run` | Create and start a container |
| `--name qlms-docker-lesson` | Give it a name you can use in later commands |
| `--rm` | Remove this container and its anonymous volumes when it stops |
| `-d` | Run it in the background so the terminal remains available |
| `-p 127.0.0.1:55433:5432` | Make PostgreSQL reachable through this computer's local port 55433 |
| `-e POSTGRES_PASSWORD=lesson-only` | Configure a password for this disposable database |
| `postgres:17` | Select the image and version tag |

Read the running state and logs:

```powershell
docker ps
docker logs --tail 20 qlms-docker-lesson
```

Look for a running container and a log message saying the database is ready to accept connections. In Docker Desktop, open **Containers**, select `qlms-docker-lesson`, and inspect **Logs**. This is the same container shown by the terminal.

Ask PostgreSQL to identify itself:

```powershell
docker exec qlms-docker-lesson psql -U postgres -c "SELECT version();"
```

`exec` runs a command inside an existing container. `psql` is the PostgreSQL command-line client. The SQL above only reads the database version.

When finished:

```powershell
docker stop qlms-docker-lesson
docker ps -a
docker image ls
```

Because you selected `--rm`, the lesson container disappears. The `postgres:17` image remains and can create another container. The lesson database is intentionally discarded. [Docker run reference](https://docs.docker.com/reference/cli/docker/container/run/).

Checkpoint: explain why the image remains after the container disappears. Then explain which port belongs to Windows and which belongs to PostgreSQL.

## What the QLMS test script does

`backend/tests/run-postgres-tests.ps1` follows the same lifecycle automatically:

1. Check the engine.
2. Start `postgres:17` with a unique container name and local port 55432.
3. Wait for PostgreSQL to accept connections.
4. Run Python tests from Windows. Each PostgreSQL test creates its own schema inside the disposable `qlms_test` database.
5. Stop and remove only that test container, even after a test failure.

Run it from the project root with `./backend/tests/run-postgres-tests.ps1`. It does not use the application's saved database credentials. Check the current result in [transaction-safety-check.md](transaction-safety-check.md); do not assume running a container means the tests passed.

## Lessons that follow

| Lesson | What we will do together | What you should be able to explain |
| --- | --- | --- |
| 2: package the API | Write `backend/Dockerfile` and `.dockerignore`, build an image, run FastAPI, inspect logs | Build time versus run time; dependencies; startup command; why secrets stay out of images |
| 3: connect services | Add Compose for the backend and disposable PostgreSQL, then package the frontend | Container networking, readiness, volumes and environment configuration |
| 4: repeat the build | Run tests against the packaged application and rebuild after a small change | A new image version versus a container restart; tags and reproducibility |
| 5: deploy an AWS sandbox | Choose a budget, push an image to ECR and run a small ECS/Fargate deployment | Image storage versus execution, permissions, logs, health checks and removing billable resources |

Compose describes multiple services in one configuration file. It does not make those services microservices by itself. Packaging the existing frontend and API does not require redesigning QLMS. [Docker Compose model](https://docs.docker.com/compose/intro/compose-application-model/).

For QLMS, the frontend's browser requests need a URL reachable by the browser. A Compose service name used between containers is not automatically a valid browser URL. We will check this when connecting Next.js and FastAPI.

## How this leads to AWS

The intended learning path is:

`Dockerfile → build an image → push it to Amazon ECR → run it with ECS/Fargate`

ECR stores container images. ECS manages container applications; Fargate runs them without requiring you to manage the underlying servers. This is a proposed learning route, not a deployment made today. [Amazon ECR](https://docs.aws.amazon.com/AmazonECR/latest/userguide/what-is-ecr.html), [ECS on Fargate](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/AWS_Fargate.html).

Keep the database decision separate: an AWS-hosted API can still use a suitably configured managed database. Do not move the live Supabase data or put the shop database into this disposable container merely to demonstrate Docker.

No AWS resource is created by these lessons today. Before that lesson, agree the region, spending limit, permissions, data environment and cleanup plan.

## Evidence and explanation

- Student practice is pending until the student runs the commands and reports the result.
- Capture one Docker Desktop image showing the named lesson container and its ready logs after the student completes the exercise. Save it in the existing evidence folder and link it from the development journal.
- Do not create repeated screenshots of an unchanged terminal or claim the whole application is containerized after running only PostgreSQL.
- Presentation line: "I used a PostgreSQL container to give the tests an isolated database with a known version. Next, I will package the API and explain how it connects to that database."
