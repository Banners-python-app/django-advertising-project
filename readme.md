1. In Dockerfile we are using buildkit and buildx so we need to install extra packages as mentioned in the Dockerfile RUN and also install buildx. For buildkit we need to enable it.
2. As we are using Jenkins foe CI-CD lets do some settings.
    1. Create GitHub app in account or in organizations
    2. Install Jenkins on EC2 or use labs, etc
    3. In Jenkins plugins install GitHub Branch Source, Github.