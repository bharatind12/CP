# Dynamic Webpage extension

This is a simple working functionality for the cone-penetrometer (Built from a stepper motor)

Command to build it:
`docker buildx build --platform linux/arm/v7 -t {DOCKERHUB_REPO:TAG} --push .`

Command to run it:
`docker run -p 5000:5000 --device=/dev/cone_penetrometer:/dev/cone_penetrometer --name cone-penetrometer {DOCKERHUB_REPO:TAG}`

