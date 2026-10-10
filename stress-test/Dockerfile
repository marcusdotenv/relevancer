FROM eclipse-temurin:17-jdk

ARG GATLING_VERSION=3.9.5

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl unzip && \
    curl -fsSLO "https://repo1.maven.org/maven2/io/gatling/highcharts/gatling-charts-highcharts-bundle/${GATLING_VERSION}/gatling-charts-highcharts-bundle-${GATLING_VERSION}-bundle.zip" && \
    unzip -q gatling-charts-highcharts-bundle-${GATLING_VERSION}-bundle.zip -d /opt && \
    mv /opt/gatling-charts-highcharts-bundle-${GATLING_VERSION} /opt/gatling && \
    rm gatling-charts-highcharts-bundle-${GATLING_VERSION}-bundle.zip && \
    # gatling compiles the simulation inside its own folder, and the container runs with the host user
    chmod -R a+rwX /opt/gatling && \
    rm -rf /var/lib/apt/lists/*

ENV GATLING_HOME=/opt/gatling
ENV HOME=/tmp
WORKDIR /opt/gatling

ENTRYPOINT ["/opt/gatling/bin/gatling.sh"]
