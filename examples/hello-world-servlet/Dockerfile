FROM ubuntu:14.04
RUN apt-get update -y \
    && apt-get install -y software-properties-common \
    && apt-add-repository ppa:openjdk-r/ppa \
    && apt-get update -y \ 
    && apt-get install -y openjdk-8-jre openjdk-8-jdk maven wget \
    && wget http://www.apache.org/dist/tomcat/tomcat-8/v8.5.24/bin/apache-tomcat-8.5.24.tar.gz \
    && gunzip apache-tomcat-8.5.24.tar.gz && tar -xvf apache-tomcat-8.5.24.tar
ADD . /src
WORKDIR /src
RUN mvn clean compile && mvn war:war \
    && mv /apache-tomcat-8.5.24/webapps/ROOT /apache-tomcat-8.5.24/webapps/ROOT.bak \
    && cp /src/target/ROOT.war /apache-tomcat-8.5.24/webapps/ROOT.war
EXPOSE 8080
CMD ["/apache-tomcat-8.5.24/bin/catalina.sh", "run"]
