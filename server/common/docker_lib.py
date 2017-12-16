import common_functions
import fm_logger
import subprocess
import time

fmlogging = fm_logger.Logging()

    
class DockerLib(object):
    """Helper class for running Docker commands."""

    def __init__(self):
        self.docker_file_snippets = {}
        self.docker_file_snippets['aws'] = self._aws_df_snippet()
        self.docker_file_snippets['google_for_token'] = self._google_df_snippet_for_token()
        self.docker_file_snippets['gke'] = self._google_df_snippet()
        self.docker_file_snippets['google'] = self._google_df_snippet_gcloud()

    def _aws_df_snippet(self):
        df = ("FROM lmecld/clis:awscli\n")
        return df

    def _google_df_snippet(self):
        df_1 = ("FROM lmecld/clis:gkebase \n"
                "RUN export PATH=$PATH:/google-cloud-sdk/bin/ \n"
                "COPY . /src \n"
                "COPY google-creds/gcloud  /root/.config/gcloud \n"
                "WORKDIR /root/.config/gcloud \n"
                )
        return df_1

    def _google_df_snippet_gcloud(self):
        df_1 = ("FROM lmecld/clis:gcloud \n"
                "RUN export PATH=$PATH:/google-cloud-sdk/bin/ \n"
                "COPY . /src \n"
                "COPY google-creds/gcloud  /root/.config/gcloud \n"
                "WORKDIR /root/.config/gcloud \n"
                )
        return df_1

        
    def _google_df_snippet_for_token(self):
        cmd_1 = ("RUN sed -i "
                 "'s/{pat}access_token{pat}.*/{pat}access_token{pat}/' "
                 "credentials \n").format(pat="\\\"")

        cmd_2 = (" sed -i "
                 "\"s/{pat}access_token{pat}.*/{pat}access_token{pat}:{pat}$token{pat},/\" "
                 "credentials \n").format(pat="\\\"")

        fmlogging.debug("Sed pattern 1:%s" % cmd_1)
        fmlogging.debug("Sed pattern 2:%s" % cmd_2)

        df = ("FROM lmecld/clis:gcloud \n"
              "RUN sudo apt-get update && sudo apt-get install -y curl \n"
              "RUN /google-cloud-sdk/bin/gcloud components install beta \n"
              "COPY . /src \n"
              "COPY google-creds/gcloud  /root/.config/gcloud \n"
              "WORKDIR /root/.config/gcloud \n"
              "{cmd_1}"
              "RUN token=`/google-cloud-sdk/bin/gcloud beta auth application-default print-access-token` \ \n"
              " && {cmd_2}"
              "WORKDIR /src \n"
              )
        df = df.format(cmd_1=cmd_1, cmd_2=cmd_2)

        return df

    def get_dockerfile_snippet(self, key):
        """Return Dockerfile snippet."""
        return self.docker_file_snippets[key]

    def docker_login(self, username, password, proxy_endpoint):
        """Set up docker client to connect to a remote repository."""
        login_cmd = ("docker login -u {username} -p {password} "
                     "{proxy_endpoint}").format(username=username,
                                                password=password,
                                                proxy_endpoint=proxy_endpoint)
        fmlogging.debug("Login command:%s" % login_cmd)
        err, output = common_functions.execute_cmd(login_cmd)
        return err, output

    def build_container_image(self, cont_name, docker_file_name, df_context='', tag=''):
        """Build container image."""
        if tag:
            build_cmd = ("docker build -t {cont_name}:{tag} -f "
                         "{docker_file_name} "
                         "{df_context}").format(cont_name=cont_name,
                                                docker_file_name=docker_file_name,
                                                df_context=df_context,
                                                tag=tag)
        else:
            build_cmd = ("docker build -t {cont_name} -f {docker_file_name} {df_context}").format(cont_name=cont_name,
                                                                                                  docker_file_name=docker_file_name,
                                                                                                  df_context=df_context)
        fmlogging.debug("Docker build cmd:%s" % build_cmd)
        err, output = common_functions.execute_cmd(build_cmd)
        return err, output

    def custom_docker_build(self):
        from io import BytesIO
        from docker import Client
        import json
        import re
        doc_client = Client(base_url='unix://var/run/docker.sock', version='1.18')
        df1 = open(df_name, "r").read()
        f = BytesIO(df1.encode('utf-8'))
        resp = [line for line in doc_client.build(fileobj=f, rm=False, tag=cont_name + "-1")]

        try:
            parsed_lines = [json.loads(e).get('stream', '') for e in resp]
        except ValueError:
                # sometimes all the data is sent on a single line ????
                #
                # ValueError: Extra data: line 1 column 87 - line 1 column
                # 33268 (char 86 - 33267)
                line = resp[0]
                # This ONLY works because every line is formatted as
                # {"stream": STRING}
                parsed_lines = [
                    json.loads(obj).get('stream', '') for obj in
                    re.findall('{\s*"stream"\s*:\s*"[^"]*"\s*}', line)
                ]
        # -----

        fmlogger.error(parsed_lines)

    def remove_container_image(self, cont_name, reason_phrase=''):
        """Remove container image."""
        fmlogging.debug("Removing container image %s. Reason: %s" % (cont_name, reason_phrase))
        rm_cmd = ("docker rmi -f {cont_name}").format(cont_name=cont_name)
        fmlogging.debug("rm command:%s" % rm_cmd)
        err, output = common_functions.execute_cmd(rm_cmd)
        return err, output

    def push_container(self, cont_name):
        """Push container to a registry."""
        push_cmd = ("docker push {cont_name}").format(cont_name=cont_name)
        fmlogging.debug("Docker push cmd:%s" % push_cmd)
        err, output = common_functions.execute_cmd(push_cmd)
        return err, output

    def run_container(self, cont_name):
        """Run container asynchronously."""
        run_cmd = ("docker run -i -d --publish-all=true {cont_name}").format(cont_name=cont_name)
        fmlogging.debug("Docker run cmd:%s" % run_cmd)
        err, output = common_functions.execute_cmd(run_cmd)
        return err, output

    def run_container_with_env(self, cont_name, env_vars_dict):
        env_string = ""
        for key, value in env_vars_dict.iteritems():
            env_string = env_string + "-e " + '"' + key + '=' + value + '"' + " "
            fmlogging.debug("Environment string %s" % env_string)

        """Run container asynchronously."""
        run_cmd = ("docker run {env_string} -i -d --publish-all=true {cont_name}").format(
            env_string=env_string,
            cont_name=cont_name)
        fmlogging.debug("Docker run cmd:%s" % run_cmd)
        err, output = common_functions.execute_cmd(run_cmd)
        return err, output

    def run_container_sync(self, cont_name):
        """Run container in synchronous manner."""
        run_cmd = ("docker run {cont_name}").format(cont_name=cont_name)
        fmlogging.debug("Docker run cmd:%s" % run_cmd)
        err, output = common_functions.execute_cmd(run_cmd)
        return err, output

    def stop_container(self, cont_id, reason_phrase=''):
        """Stop container."""
        fmlogging.debug("Stopping container %s. Reason: %s" % (cont_id, reason_phrase))
        stop_cmd = ("docker stop {cont_id}").format(cont_id=cont_id)
        fmlogging.debug("stop command:%s" % stop_cmd)
        err, output = common_functions.execute_cmd(stop_cmd)
        return err, output

    def remove_container(self, cont_id, reason_phrase=''):
        """Remove container."""
        fmlogging.debug("Removing container %s. Reason: %s" % (cont_id, reason_phrase))
        rm_cmd = ("docker rm -f {cont_id}").format(cont_id=cont_id)
        fmlogging.debug("rm command:%s" % rm_cmd)
        err, output = common_functions.execute_cmd(rm_cmd)
        return err, output

    def get_logs(self, cont_id):
        fmlogging.debug("Retrieving container logs %s " % cont_id)
        logs_cmd = ("docker logs {cont_id}").format(cont_id=cont_id)
        fmlogging.debug("logs command:%s" % logs_cmd)

        output = ''
        err = ''
        count = 5

        # allows logs command to generate output
        time.sleep(4)
        i = 0
        while not output and i < count:
            err, output = common_functions.execute_cmd(logs_cmd)
            if output:
                break
            else:
                time.sleep(2)
                i = i + 1

        return err, output

    def filter_output(self, output):
        output_lines = []
        start = False
        for line in output.split("\n"):
            if start:
                output_lines.append(line)
            if line.find("Running in") >= 0:
                start = True
                output_lines = []

        # Pop off last three items
        output_lines.pop()
        output_lines.pop()
        output_lines.pop()

        return output_lines
