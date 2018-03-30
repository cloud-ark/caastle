FROM lmecld/modernwebapps:jdk-maven as builder
ADD . /src
RUN cd /src && mvn clean compile && mvn war:war


FROM tomcat:8.0
RUN mv /usr/local/tomcat/webapps/ROOT /usr/local/tomcat/webapps/ROOT.bak
COPY --from=builder /src/target/ROOT.war /usr/local/tomcat/webapps/ROOT.war
EXPOSE 8080
CMD ["catalina.sh", "run"]
