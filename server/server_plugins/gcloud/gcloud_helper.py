import os

from server.common import docker_lib
from server.common import fm_logger

fmlogger = fm_logger.Logging()


class GCloudHelper(object):
    
    def __init__(self):
        self.docker_handler = docker_lib.DockerLib()
    
    def get_access_token(self, df_dir, df, cont_name):
        fp = open(df_dir + "/Dockerfile.get-access-token", "w")
        fp.write(df)
        fp.close()

        err, output = self.docker_handler.build_container_image(
            cont_name,
            df_dir + "/Dockerfile.get-access-token",
            df_context=df_dir
        )
        
        err, output = self.docker_handler.run_container(cont_name)

        if err:
            error_msg = ("Error encountered in obtaining gcloud access token {e}").format(e=err)
            fmlogger.error(error_msg)
            raise Exception(error_msg)

        docker_image_id = output.strip()
        copy_creds_file = ("docker cp {docker_img}:/root/.config/gcloud/credentials.db {df_dir}/.").format(
            docker_img=docker_image_id,
            df_dir=df_dir
        )

        os.system(copy_creds_file)

        access_token = ''
        fp1 = open(df_dir + "/credentials.db")
        lines = fp1.readlines()
        for line in lines:
            if line.find("access_token") >= 0:
                line_contents = line.split(":")
                access_token = line_contents[1].strip().replace("\"", "").replace(",", "")
                fmlogger.debug("Access token:%s" % access_token)

        self.docker_handler.stop_container(docker_image_id)
        self.docker_handler.remove_container(docker_image_id)
        self.docker_handler.remove_container_image(cont_name)
        
        return access_token

        
